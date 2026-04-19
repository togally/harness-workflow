"""ff --auto 决策点数据模型与 `决策汇总.md` 生成逻辑（req-29 / chg-03）。

本模块只负责"数据层 + 契约层"，**不**碰 `harness ff` CLI 入口（那是 chg-04
的职责）。与 req-29 / requirement.md 第 5 章"决策边界与 --auto-accept 规约"
对齐：

- 5.1 **必须阻塞等人的决策类别**：硬编码为 ``BLOCKING_CATEGORIES``，供
  ``is_blocking_decision`` 做关键字匹配；真正的阻塞/放行路由由 chg-04 的
  CLI 入口决定。
- 5.2 **decisions-log 双轨约定**：
  - agent 运行时记录 → ``.workflow/flow/requirements/{req-id}/decisions-log.md``
    （由 ``append_decision`` / ``read_decision_log`` 读写）
  - 用户验收汇总  → ``artifacts/{branch}/requirements/{req-id}-{slug}/决策汇总.md``
    （由 ``write_decision_summary`` 写盘；``render_decision_summary``
    为纯函数仅渲染内容）
- 5.3 **--auto-accept 三档**：风险等级由 ``DecisionPoint.risk`` 显式标记为
  ``low`` / ``medium`` / ``high``，本模块不做交互路由。

本模块**不依赖** ``workflow_helpers``，仅被 chg-04 的 CLI 层与本 change 的
测试 import，避免反向依赖与文件膨胀。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

__all__ = [
    "DecisionPoint",
    "append_decision",
    "read_decision_log",
    "render_decision_summary",
    "write_decision_summary",
    "BLOCKING_CATEGORIES",
    "is_blocking_decision",
]


# ---------------------------------------------------------------------------
# 5.1 阻塞清单（requirement.md 第 5.1 节硬编码，顺序与文案保持一致）
# ---------------------------------------------------------------------------
BLOCKING_CATEGORIES: list[str] = [
    "破坏性 IO：rm -rf / DROP TABLE / 物理删除文件或目录",
    "不可逆 git：--force push / reset --hard / amend 已推 commit",
    "跨 req / 跨 change 修改：越界改别的需求或变更的交付产物",
    "archive 物理删除 / 清仓：删除或覆盖已归档内容",
    "涉及凭证 / 网络的写入：token / secret / 远程服务变更",
    "敏感配置修改：.claude/settings.json / .env / 平台或 agent 配置文件",
    "依赖变更：package.json / pyproject.toml / Cargo.toml 等 dependencies 增删",
    "数据模型 / schema 变更：DB migration / collection 结构重定义",
]


# 阻塞匹配用的关键字（与 5.1 每条描述对齐，便于简单 keyword 匹配）。
# 顺序与 ``BLOCKING_CATEGORIES`` 一致，索引对应。
_BLOCKING_KEYWORDS: list[tuple[str, ...]] = [
    ("rm -rf", "drop table", "物理删除", "rm ", "unlink"),
    ("--force", "reset --hard", "push --force", "amend"),
    ("跨 req", "跨 change", "越界", "越权"),
    ("archive 物理删除", "清仓", "覆盖已归档", "删除归档"),
    ("token", "secret", "凭证", "credential", "远程服务"),
    (".claude/settings", ".env", "platform config", "agent 配置"),
    ("package.json", "pyproject.toml", "cargo.toml", "dependencies"),
    ("db migration", "schema 变更", "schema change", "collection 结构"),
]


# ---------------------------------------------------------------------------
# DecisionPoint dataclass
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class DecisionPoint:
    """单条自主决策点记录。

    字段顺序与 req-29 AC-02 一致；frozen=True 让记录在日志写入后不可变，
    避免 agent 写一半又回头改同 id 的歧义。
    """

    id: str
    """如 ``dec-001``，单调递增，由 ``append_decision`` 分配。"""

    timestamp: str
    """ISO8601 时间戳（chg-04 自己决定是否带时区）。"""

    stage: str
    """``requirement_review`` / ``planning`` / ``executing`` / ``testing``。"""

    risk: str
    """``low`` / ``medium`` / ``high``，对应 5.3 --auto-accept 三档。"""

    description: str
    """一句话描述决策点。"""

    options: list[str]
    """可选项列表；渲染/序列化时保持插入顺序。"""

    choice: str
    """实际选择。"""

    reason: str
    """一句话理由。"""


# ---------------------------------------------------------------------------
# 日志文件读写（5.2 flow 侧）
# ---------------------------------------------------------------------------
_LOG_HEADER = "# Decisions Log\n\n"

# 单条记录序列化模板（每条记录一个 fenced YAML block，字段顺序固定）。
_RECORD_FENCE_OPEN = "```yaml decision"
_RECORD_FENCE_CLOSE = "```"


def _log_path(root: Path, req_id: str) -> Path:
    return root / ".workflow" / "flow" / "requirements" / req_id / "decisions-log.md"


def _escape_yaml_scalar(value: str) -> str:
    """把任意字符串塞进 YAML double-quoted scalar，转义 `\"` 与 `\\`。"""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _serialize(point: DecisionPoint) -> str:
    """把一条决策点序列化为 fenced YAML block 文本（含首尾栅栏）。"""
    opts_rendered = "\n".join(f'  - "{_escape_yaml_scalar(o)}"' for o in point.options)
    if not point.options:
        opts_rendered = "  []"
    # YAML 的 options 用 block sequence；其余字段用 double-quoted 标量，零歧义。
    lines = [
        _RECORD_FENCE_OPEN,
        f'id: "{_escape_yaml_scalar(point.id)}"',
        f'timestamp: "{_escape_yaml_scalar(point.timestamp)}"',
        f'stage: "{_escape_yaml_scalar(point.stage)}"',
        f'risk: "{_escape_yaml_scalar(point.risk)}"',
        f'description: "{_escape_yaml_scalar(point.description)}"',
    ]
    if point.options:
        lines.append("options:")
        lines.append(opts_rendered)
    else:
        lines.append("options: []")
    lines.append(f'choice: "{_escape_yaml_scalar(point.choice)}"')
    lines.append(f'reason: "{_escape_yaml_scalar(point.reason)}"')
    lines.append(_RECORD_FENCE_CLOSE)
    return "\n".join(lines) + "\n"


_SCALAR_RE = re.compile(r'^(\w+):\s*"((?:[^"\\]|\\.)*)"\s*$')
_EMPTY_OPTIONS_RE = re.compile(r"^options:\s*\[\]\s*$")
_OPTIONS_HEADER_RE = re.compile(r"^options:\s*$")
_OPTION_ITEM_RE = re.compile(r'^\s*-\s+"((?:[^"\\]|\\.)*)"\s*$')


def _unescape_yaml_scalar(value: str) -> str:
    return value.replace('\\"', '"').replace("\\\\", "\\")


def _parse_block(block_lines: list[str]) -> DecisionPoint | None:
    """把单个 fenced YAML block 的内容解析回 ``DecisionPoint``。"""
    fields: dict[str, str] = {}
    options: list[str] = []
    i = 0
    n = len(block_lines)
    while i < n:
        line = block_lines[i]
        if _EMPTY_OPTIONS_RE.match(line):
            options = []
            i += 1
            continue
        if _OPTIONS_HEADER_RE.match(line):
            i += 1
            while i < n:
                m = _OPTION_ITEM_RE.match(block_lines[i])
                if not m:
                    break
                options.append(_unescape_yaml_scalar(m.group(1)))
                i += 1
            continue
        m = _SCALAR_RE.match(line)
        if m:
            fields[m.group(1)] = _unescape_yaml_scalar(m.group(2))
        i += 1

    required = ("id", "timestamp", "stage", "risk", "description", "choice", "reason")
    if not all(k in fields for k in required):
        return None
    return DecisionPoint(
        id=fields["id"],
        timestamp=fields["timestamp"],
        stage=fields["stage"],
        risk=fields["risk"],
        description=fields["description"],
        options=list(options),
        choice=fields["choice"],
        reason=fields["reason"],
    )


def _iter_blocks(text: str) -> Iterable[list[str]]:
    """从日志文本里按 fenced YAML block 逐段切出内容行（不含栅栏）。"""
    lines = text.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        if lines[i].strip() == _RECORD_FENCE_OPEN:
            i += 1
            buf: list[str] = []
            while i < n and lines[i].strip() != _RECORD_FENCE_CLOSE:
                buf.append(lines[i])
                i += 1
            yield buf
            if i < n:
                i += 1  # 跳过闭栅栏
        else:
            i += 1


_NEXT_ID_RE = re.compile(r"^dec-(\d+)$")


def _next_decision_id(existing: Sequence[DecisionPoint]) -> str:
    """基于已有记录的 id 分配下一个 ``dec-NNN``（3 位补零，单调递增）。"""
    max_n = 0
    for point in existing:
        m = _NEXT_ID_RE.match(point.id)
        if m:
            n = int(m.group(1))
            if n > max_n:
                max_n = n
    return f"dec-{max_n + 1:03d}"


def append_decision(root: Path, req_id: str, decision: DecisionPoint) -> None:
    """把一条决策点追加到 flow 侧的 ``decisions-log.md``。

    - 文件不存在 → 自动创建目录并写入表头 ``# Decisions Log``。
    - 决策 id 由调用方显式给出，也可以传入 ``DecisionPoint(id="", ...)``
      交由本函数按已有最大 ``dec-NNN`` +1 自动分配（即插即用场景）。
    - 不做同 id 去重（chg-04 若需要覆盖应显式删除旧行）；但会在尾部
      保持空行与 block 分隔的一致视觉。
    """
    path = _log_path(root, req_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = read_decision_log(root, req_id) if path.exists() else []
    if not decision.id:
        decision = DecisionPoint(
            id=_next_decision_id(existing),
            timestamp=decision.timestamp,
            stage=decision.stage,
            risk=decision.risk,
            description=decision.description,
            options=list(decision.options),
            choice=decision.choice,
            reason=decision.reason,
        )

    if not path.exists():
        path.write_text(_LOG_HEADER, encoding="utf-8")

    with path.open("a", encoding="utf-8") as fh:
        fh.write(_serialize(decision))
        fh.write("\n")


def read_decision_log(root: Path, req_id: str) -> list[DecisionPoint]:
    """读 flow 侧的 ``decisions-log.md``，解析回 ``list[DecisionPoint]``。

    文件不存在 → 返回空列表；无法解析的 block → 跳过，不抛异常。
    """
    path = _log_path(root, req_id)
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    out: list[DecisionPoint] = []
    for block in _iter_blocks(text):
        point = _parse_block(block)
        if point is not None:
            out.append(point)
    return out


# ---------------------------------------------------------------------------
# 决策汇总.md 渲染（5.2 artifacts 侧）
# ---------------------------------------------------------------------------
_RISK_ORDER = ("high", "medium", "low")
_RISK_TITLES = {
    "high": "## 高风险决策（human-must-ack）",
    "medium": "## 中风险决策",
    "low": "## 低风险决策",
}


def render_decision_summary(decisions: list[DecisionPoint]) -> str:
    """把决策点列表渲染为 ``决策汇总.md`` 的 Markdown 内容（纯函数）。

    分组规则：按 ``risk`` 字段 high → medium → low 三档分组；未知 risk 值
    并入 ``low`` 分组以保证不漏。每组内按 ``id`` 的原始顺序输出。每条决策
    渲染字段：时间 / stage / 描述 / 可选项 / 选择 / 理由。
    """
    total = len(decisions)
    counts = {"high": 0, "medium": 0, "low": 0}
    grouped: dict[str, list[DecisionPoint]] = {"high": [], "medium": [], "low": []}
    for p in decisions:
        bucket = p.risk if p.risk in grouped else "low"
        grouped[bucket].append(p)
        counts[bucket] += 1

    header = [
        "# 决策汇总",
        "",
        f"共 {total} 条自主决策点：high={counts['high']}，medium={counts['medium']}，low={counts['low']}。",
        "",
    ]

    if total == 0:
        header.append("_本需求 --auto 模式下未产生自主决策点。_")
        header.append("")
        return "\n".join(header)

    body: list[str] = []
    for risk in _RISK_ORDER:
        bucket = grouped[risk]
        body.append(_RISK_TITLES[risk])
        body.append("")
        if not bucket:
            body.append("_本档无决策点。_")
            body.append("")
            continue
        for point in bucket:
            opts = "、".join(point.options) if point.options else "（无）"
            body.append(f"### {point.id} — {point.description}")
            body.append("")
            body.append(f"- 时间：{point.timestamp}")
            body.append(f"- 阶段：{point.stage}")
            body.append(f"- 描述：{point.description}")
            body.append(f"- 可选项：{opts}")
            body.append(f"- 选择：{point.choice}")
            body.append(f"- 理由：{point.reason}")
            body.append("")

    return "\n".join(header + body)


def _find_requirement_slug_dir(root: Path, req_id: str, branch: str) -> Path:
    """在 ``artifacts/{branch}/requirements/`` 下找 ``{req_id}-*`` 目录。

    返回第一个匹配的目录；找不到时回退到 ``{req_id}``（chg-04 可能会自己
    先建目录）。
    """
    base = root / "artifacts" / branch / "requirements"
    if base.is_dir():
        for child in sorted(base.iterdir()):
            if child.is_dir() and (child.name == req_id or child.name.startswith(f"{req_id}-")):
                return child
    return base / req_id


def write_decision_summary(root: Path, req_id: str, branch: str) -> Path:
    """读日志 → 渲染 → 落盘 ``决策汇总.md``，返回写入路径。

    路径契约（5.2 artifacts 侧）：
    ``artifacts/{branch}/requirements/{req-id}-{slug}/决策汇总.md``

    ``{slug}`` 由 ``_find_requirement_slug_dir`` 从现有目录推断；找不到则
    回退到 ``{req_id}`` 并自动创建目录。
    """
    decisions = read_decision_log(root, req_id)
    content = render_decision_summary(decisions)
    target_dir = _find_requirement_slug_dir(root, req_id, branch)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "决策汇总.md"
    target.write_text(content, encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# 5.1 阻塞检测
# ---------------------------------------------------------------------------
def is_blocking_decision(decision: DecisionPoint) -> bool:
    """简单 keyword 匹配，判断是否命中 5.1 的 8 条阻塞类别。

    匹配面：``description`` + 全部 ``options`` 文本，统一小写后做 substring
    检索。只要命中任意一条 ``_BLOCKING_KEYWORDS`` 下的关键字即视为阻塞。
    本函数不负责"停下等人"的路由动作，仅返回布尔值供 chg-04 CLI 判定。
    """
    haystack_parts = [decision.description, *decision.options]
    haystack = "\n".join(haystack_parts).lower()
    for keywords in _BLOCKING_KEYWORDS:
        for kw in keywords:
            if kw.lower() in haystack:
                return True
    return False
