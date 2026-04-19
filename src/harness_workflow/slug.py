r"""Shared slugify utilities.

This module is introduced by req-26 / chg-01 and is reused by:

- `create_regression` (chg-01) — regression 产出目录命名必须 kebab-case 且以
  `reg-N-` 前缀开头（requirement AC-04）。
- `rename_requirement` / `rename_change` / `rename_bugfix` (chg-02) — rename
  目录时必须保留 `{id}-` 前缀并做统一 slug（requirement AC-02）。

约定（与 chg-01 plan.md 一致）：

- 英文字母小写化；
- 空格 → `-`；
- 中文 / 其他非 ASCII 字母字符保留为原字符（不做拼音化），与仓库既有
  `req-26-uav-split` / `bugfix-3-...` 的中英文混合命名惯例一致；
- 全角 / 半角标点（`:`、`：`、`?`、`？`、`/`、`\`、`*`、`"`、`<`、`>`、`|`
  等非法路径字符）过滤；
- 连续分隔符折叠为单个 `-`，首尾 `-` 裁掉；
- 空输入或全部被过滤的输入返回空串，由调用方负责兜底（例如用原 id 或固定
  fallback）。
"""

from __future__ import annotations

import re
import unicodedata

__all__ = ["slugify_preserve_unicode"]


# 明确禁止的路径字符集合（POSIX + Windows 交集 + 常见全角标点）。
# 注意：不包含点 `.`，因为部分命名允许 `v1.0.0`；若需要过滤由调用方自己处理。
_ILLEGAL_PATH_CHARS = set('/\\:*?"<>|\t\r\n\x00')
_FULLWIDTH_PUNCT = set("：？！，。；、·「」『』【】《》（）〔〕〈〉“”‘’…—")


def _is_preserved_char(ch: str) -> bool:
    """判断一个字符是否应被保留进 slug。

    保留规则：
    - ASCII 字母数字（小写化在外层处理）；
    - 连字符 `-` 与下划线 `_`（下划线也允许以兼容 `bugfix_id` 等历史命名）；
    - Unicode 字母类（含中文、日文、韩文等）；
    - Unicode 数字类（阿拉伯数字以外的数字字符，非强依赖，但不剔除）。
    """
    if ch in _ILLEGAL_PATH_CHARS:
        return False
    if ch in _FULLWIDTH_PUNCT:
        return False
    if ch in "-_":
        return True
    if ch.isalnum():
        # isalnum 在 Python 中对 Unicode 字母 / 数字均返回 True。
        return True
    return False


def slugify_preserve_unicode(value: str) -> str:
    """将任意字符串转为 kebab-case slug，保留非 ASCII 字母字符。

    - 英文字母统一小写；
    - 空格与被过滤的字符（标点等）折叠为单个 `-`；
    - 首尾 `-` 裁掉；
    - 若全部字符都被过滤，返回空串。

    示例：
        >>> slugify_preserve_unicode("issue with spaces")
        'issue-with-spaces'
        >>> slugify_preserve_unicode("Fix: Layout Bug?!")
        'fix-layout-bug'
        >>> slugify_preserve_unicode("uav-split 拆分")
        'uav-split-拆分'
        >>> slugify_preserve_unicode("完全中文问题")
        '完全中文问题'
        >>> slugify_preserve_unicode("   ")
        ''
    """
    if not value:
        return ""
    # 先做 NFKC 规范化，把全角英数折叠回半角，便于统一小写。
    normalized = unicodedata.normalize("NFKC", value)
    out_chars: list[str] = []
    for ch in normalized:
        lowered = ch.lower()
        if _is_preserved_char(lowered):
            out_chars.append(lowered)
        else:
            out_chars.append("-")
    collapsed = re.sub(r"-+", "-", "".join(out_chars)).strip("-")
    return collapsed
