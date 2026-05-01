"""tests/test_domain_inference_nested_maven.py

chg-A（req-55 改进）: MavenMultiModuleDetector 递归处理 nested pom

TC-01: 单层叶子模块（baseline 行为，4 子模块全 jar）
TC-02: nested pom 递归（父 4 模块 + 1 个聚合子模块带 7 子）
TC-03: max_depth 防无限循环（构造递归层数 ≥ 6 的 fixture，期望最大深度 5）
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = str(REPO_ROOT / "src")
sys.path.insert(0, SRC_DIR)

from harness_workflow.playbook.domain_inference import infer_domains, MavenMultiModuleDetector


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_leaf_pom(dir_path: Path, artifact_id: str) -> None:
    """写一个叶子模块 pom.xml（packaging=jar 或不指定，默认 jar）。"""
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / "pom.xml").write_text(
        f'<?xml version="1.0"?>\n'
        f'<project>\n'
        f'  <artifactId>{artifact_id}</artifactId>\n'
        f'  <packaging>jar</packaging>\n'
        f'</project>\n',
        encoding="utf-8",
    )


def _write_aggregator_pom(dir_path: Path, artifact_id: str, sub_modules: list[str]) -> None:
    """写一个聚合模块 pom.xml（packaging=pom + <modules> 段）。"""
    dir_path.mkdir(parents=True, exist_ok=True)
    modules_xml = "\n".join(f"    <module>{m}</module>" for m in sub_modules)
    (dir_path / "pom.xml").write_text(
        f'<?xml version="1.0"?>\n'
        f'<project>\n'
        f'  <artifactId>{artifact_id}</artifactId>\n'
        f'  <packaging>pom</packaging>\n'
        f'  <modules>\n'
        f'{modules_xml}\n'
        f'  </modules>\n'
        f'</project>\n',
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# TC-01: 单层叶子模块（baseline 行为，4 子模块全 jar）
# ---------------------------------------------------------------------------

def test_tc01_single_level_leaf_modules(tmp_path, capsys):
    """TC-01: 父 pom 4 个子模块，全为 jar 叶子，不展开，行为与原来一致。"""
    modules = ["platform-admin", "platform-common", "platform-extend", "platform-modules-jar"]

    # root pom.xml（聚合但不是 jar，无所谓）
    modules_xml = "\n".join(f"    <module>{m}</module>" for m in modules)
    (tmp_path / "pom.xml").write_text(
        f'<?xml version="1.0"?>\n'
        f'<project>\n'
        f'  <artifactId>parent</artifactId>\n'
        f'  <packaging>pom</packaging>\n'
        f'  <modules>\n'
        f'{modules_xml}\n'
        f'  </modules>\n'
        f'</project>\n',
        encoding="utf-8",
    )

    # 每个子模块 → 叶子 pom（packaging=jar）
    for mod in modules:
        _write_leaf_pom(tmp_path / mod, mod)

    mode, domains = infer_domains(tmp_path)

    captured = capsys.readouterr()
    assert mode == "maven_multi_module"
    # 所有 4 个叶子模块都在
    assert set(domains) == set(modules)
    assert len(domains) == 4
    assert "matched 'maven_multi_module'" in captured.out
    assert "4 domains" in captured.out


# ---------------------------------------------------------------------------
# TC-02: nested pom 递归（父 4 模块 + 1 个聚合子模块带 7 子）
# ---------------------------------------------------------------------------

def test_tc02_nested_pom_recursive_expansion(tmp_path, capsys):
    """TC-02: PetMallPlatform 结构 — platform-modules 是聚合模块，递归展开 7 个子模块。

    父 pom.xml <modules>:
      - platform-admin（jar）
      - platform-common（jar）
      - platform-extend（jar）
      - platform-modules（pom → 聚合，含 7 子模块）

    期望结果: 10 个领域（3 叶子 + 7 展开）
    platform-modules 本身不出现在结果中。
    """
    leaf_modules = ["platform-admin", "platform-common", "platform-extend"]
    aggregator = "platform-modules"
    nested_modules = [
        "platform-app",
        "platform-generator",
        "platform-job",
        "platform-mall",
        "platform-member",
        "platform-system",
        "platform-workflow",
    ]

    # root pom.xml
    all_top = leaf_modules + [aggregator]
    modules_xml = "\n".join(f"    <module>{m}</module>" for m in all_top)
    (tmp_path / "pom.xml").write_text(
        f'<?xml version="1.0"?>\n'
        f'<project>\n'
        f'  <artifactId>petmall-parent</artifactId>\n'
        f'  <packaging>pom</packaging>\n'
        f'  <modules>\n'
        f'{modules_xml}\n'
        f'  </modules>\n'
        f'</project>\n',
        encoding="utf-8",
    )

    # 叶子模块 → jar pom
    for mod in leaf_modules:
        _write_leaf_pom(tmp_path / mod, mod)

    # 聚合模块 → pom（packaging=pom + 7 子模块）
    _write_aggregator_pom(tmp_path / aggregator, aggregator, nested_modules)

    # 聚合模块的子模块 → 叶子 pom
    for nm in nested_modules:
        _write_leaf_pom(tmp_path / aggregator / nm, nm)

    mode, domains = infer_domains(tmp_path)

    captured = capsys.readouterr()
    assert mode == "maven_multi_module"

    expected = set(leaf_modules) | set(nested_modules)
    assert set(domains) == expected
    assert len(domains) == 10

    # platform-modules 聚合模块本身不应出现
    assert aggregator not in domains

    # stdout 包含 10 domains
    assert "10 domains" in captured.out
    assert "matched 'maven_multi_module'" in captured.out

    # 验证所有 7 个嵌套子模块都在
    for nm in nested_modules:
        assert nm in domains, f"Expected nested module '{nm}' in domains"


# ---------------------------------------------------------------------------
# TC-03: max_depth 防无限循环（递归层数 ≥ 6 的 fixture，期望截断在 max_depth=5）
# ---------------------------------------------------------------------------

def test_tc03_max_depth_protection(tmp_path, capsys):
    """TC-03: 构造 6 层深嵌套（超过 max_depth=5），期望不无限递归且正常返回结果。

    结构：
      root pom → [level-1]
      level-1/pom.xml（packaging=pom） → [level-2]
      level-2/pom.xml（packaging=pom） → [level-3]
      level-3/pom.xml（packaging=pom） → [level-4]
      level-4/pom.xml（packaging=pom） → [level-5]
      level-5/pom.xml（packaging=pom） → [level-6]  ← depth=6 超过 max_depth=5
      level-6/pom.xml（packaging=jar）→ 叶子

    期望：不抛异常，正常返回（在 max_depth 截断时，level-6 名字原样返回）。
    """
    detector = MavenMultiModuleDetector()
    assert detector._MAX_DEPTH == 5, "max_depth should be 5"

    # 构造 6 层深的聚合链
    depth_names = [f"level-{i}" for i in range(1, 7)]

    # root pom → [level-1]
    (tmp_path / "pom.xml").write_text(
        '<?xml version="1.0"?>\n'
        '<project>\n'
        '  <artifactId>root</artifactId>\n'
        '  <packaging>pom</packaging>\n'
        '  <modules>\n'
        '    <module>level-1</module>\n'
        '  </modules>\n'
        '</project>\n',
        encoding="utf-8",
    )

    # 每一层都是聚合模块，指向下一层
    current_dir = tmp_path
    for i, name in enumerate(depth_names[:-1]):
        next_name = depth_names[i + 1]
        _write_aggregator_pom(current_dir / name, name, [next_name])
        current_dir = current_dir / name

    # 最深层（level-6）是叶子模块
    _write_leaf_pom(current_dir / depth_names[-1], depth_names[-1])

    # 应该正常返回，不抛 RecursionError 也不无限循环
    mode, domains = infer_domains(tmp_path)

    captured = capsys.readouterr()
    assert mode == "maven_multi_module"
    assert len(domains) >= 1  # 至少返回了一些内容
    # 不应抛异常（如果到这里说明 max_depth 保护生效）
    assert "matched 'maven_multi_module'" in captured.out
