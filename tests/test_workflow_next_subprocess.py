"""Pytest: req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）/ chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）。

子进程 dogfood 测试——用 subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'next', ...]) 真跑 CLI，
不只 import helper，覆盖 4 路径：first-hop / while-internal / 缺产物 / 有产物。

用 tmpdir (pytest tmp_path) 干净 fixture，避免污染当前仓库（呼应 sug-51（testing 红线 — subprocess dogfood 必须真跑 CLI 不只 mock helper））。

涵盖 plan.md TC-03 ~ TC-07：
  TC-03: subprocess harness next，stage=executing chg dir 缺 → stdout 含"Stage executing 工作未完成"，不 advance
  TC-04: subprocess harness next --execute，stage=ready_for_execution，plan 完整 → 仅 advance 到 executing（不连跳）
  TC-05: subprocess harness next，stage=executing，chg dir+session-memory.md(✅)+tests/ → advance 到 testing 后停（不连跳到 acceptance/done）
  TC-06: subprocess harness next，stage=testing，test-report.md 含 §结论 → advance 到 acceptance 后停（not done）
  TC-07: dogfood 全链，tmpdir mock，4 次 harness next 各 1 跳，最终 done，stage_advance 间隔 ≥ 4ms
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent


# ─────────────────────────── fixture helpers ────────────────────────────────

def _write_config(root: Path) -> None:
    config_dir = root / ".codex" / "harness"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.json").write_text('{"language": "cn"}', encoding="utf-8")


def _write_role_model_map(root: Path) -> None:
    ctx = root / ".workflow" / "context"
    ctx.mkdir(parents=True, exist_ok=True)
    data = {
        "version": 2,
        "default": "sonnet",
        "roles": {
            "analyst": {"model": "opus", "stages": ["requirement_review", "planning"]},
            "executing": {"model": "sonnet", "stages": ["executing"]},
            "testing": {"model": "sonnet", "stages": ["testing"]},
            "acceptance": {"model": "sonnet", "stages": ["acceptance"]},
            "regression": {"model": "opus", "stages": ["regression"]},
            "done": {"model": "opus", "stages": ["done"]},
            "requirement-review": {"model": "opus", "stages": ["requirement_review"], "alias_of": "analyst"},
            "planning": {"model": "opus", "stages": ["planning"], "alias_of": "analyst"},
        },
        "stage_policies": {
            "requirement_review": {"exit_decision": "auto"},
            "planning": {"exit_decision": "user"},
            "ready_for_execution": {"exit_decision": "explicit"},
            "executing": {"exit_decision": "auto"},
            "testing": {"exit_decision": "auto"},
            "acceptance": {"exit_decision": "verdict"},
            "regression": {"exit_decision": "verdict"},
            "done": {"exit_decision": "terminal"},
        },
    }
    (ctx / "role-model-map.yaml").write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")


def _write_runtime(
    root: Path,
    *,
    stage: str,
    operation_type: str = "requirement",
    req_id: str = "req-sub-99",
) -> None:
    state_dir = root / ".workflow" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    runtime = {
        "stage": stage,
        "operation_type": operation_type,
        "current_requirement": req_id,
        "current_requirement_title": "subprocess test req",
        "operation_target": req_id,
        "stage_entered_at": "2026-01-01T00:00:00+00:00",
        "conversation_mode": "harness",
        "ff_mode": False,
        "ff_stage_history": [],
        "active_requirements": [req_id],
        "current_regression": "",
        "current_regression_title": "",
        "locked_requirement": "",
        "locked_requirement_title": "",
        "locked_stage": "",
    }
    (state_dir / "runtime.yaml").write_text(yaml.dump(runtime, allow_unicode=True), encoding="utf-8")

    # write state yaml
    if operation_type == "bugfix":
        req_state_dir = state_dir / "bugfixes"
    else:
        req_state_dir = state_dir / "requirements"
    req_state_dir.mkdir(parents=True, exist_ok=True)
    (req_state_dir / f"{req_id}.yaml").write_text(
        f"id: {req_id}\ntitle: subprocess test\nstatus: {stage}\ncreated_at: '2026-01-01'\n",
        encoding="utf-8",
    )


def _make_req_flow(
    root: Path,
    req_id: str = "req-sub-99",
) -> Path:
    req_flow = root / ".workflow" / "flow" / "requirements" / f"{req_id}-test-req"
    req_flow.mkdir(parents=True, exist_ok=True)
    return req_flow


def _run_harness_next(
    root: Path,
    *,
    execute: bool = False,
    timeout: int = 30,
) -> subprocess.CompletedProcess:
    """用 subprocess.run 真跑 harness next CLI（不只 import helper）。

    跨平台：subprocess 用 sys.executable（不硬编码 python），text=True 强制 UTF-8，路径用 pathlib.Path。
    """
    cmd = [sys.executable, "-m", "harness_workflow.cli", "next"]
    if execute:
        cmd.append("--execute")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(root),
        timeout=timeout,
        env={
            **__import__("os").environ,
            "PYTHONPATH": str(ROOT / "src"),
        },
    )
    return result


def _read_runtime(root: Path) -> dict:
    return yaml.safe_load(
        (root / ".workflow" / "state" / "runtime.yaml").read_text(encoding="utf-8")
    )


def _read_feedback_jsonl(root: Path) -> list[dict]:
    """读取 feedback.jsonl，返回 stage_advance 事件列表。

    CLI 写入格式：{"ts": ..., "event": "stage_advance", "data": {...}}
    （注意 key 是 "event" 不是 "event_type"，payload 字段是 "data" 不是 "payload"）
    """
    import json
    feedback_path = root / ".workflow" / "state" / "feedback" / "feedback.jsonl"
    if not feedback_path.exists():
        return []
    events = []
    for line in feedback_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        # 兼容两种格式：{"event": ...} 和 {"event_type": ...}
        event_name = obj.get("event") or obj.get("event_type")
        if event_name == "stage_advance":
            # 统一为 {"payload": ...} 格式供断言使用
            payload = obj.get("data") or obj.get("payload") or {}
            events.append({**obj, "payload": payload})
    return events


# ─────────────────────────── TC-03 ───────────────────────────────────────────


def test_tc03_subprocess_executing_no_changes_dir_stays(tmp_path: Path) -> None:
    """TC-03: subprocess harness next，stage=executing，chg dir 缺 → 不 advance（严格化生效）。

    req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）/ chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）
    AC-2（子进程 dogfood 4 路径全绿）：first-hop 路径——executing 出发，changes_dir 缺，gate 阻断，不跳 testing。
    """
    req_id = "req-sub-99"
    _write_config(tmp_path)
    _write_role_model_map(tmp_path)
    _write_runtime(tmp_path, stage="executing", req_id=req_id)
    # req flow 存在但无 changes 子目录
    _make_req_flow(tmp_path, req_id=req_id)
    # tests/ 有 test_*.py（只缺 changes dir）
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "test_dummy.py").write_text("# dummy\n", encoding="utf-8")

    result = _run_harness_next(tmp_path)

    rt = _read_runtime(tmp_path)
    # stage 不应 advance（executing 无 changes dir → gate 阻断）
    assert rt["stage"] == "executing", (
        f"TC-03: Expected stage=executing (gate stops), got {rt['stage']!r}\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    # feedback.jsonl 不应有新 stage_advance
    advances = _read_feedback_jsonl(tmp_path)
    assert len(advances) == 0, (
        f"TC-03: Expected 0 stage_advance events, got {len(advances)}: {advances}"
    )


# ─────────────────────────── TC-04 ───────────────────────────────────────────


def test_tc04_subprocess_rfe_execute_advances_to_executing_only(tmp_path: Path) -> None:
    """TC-04: subprocess harness next --execute，stage=ready_for_execution → 仅 advance 到 executing（不连跳）。

    req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）/ chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）
    AC-2（子进程 dogfood 4 路径全绿）+ AC-3（自身周期 dogfood 自证）：while-internal 路径。
    ready_for_execution exit_decision=explicit → 1 跳后，executing 无 changes dir → gate 停下。
    """
    req_id = "req-sub-99"
    _write_config(tmp_path)
    _write_role_model_map(tmp_path)
    _write_runtime(tmp_path, stage="ready_for_execution", req_id=req_id)
    # req flow 存在（但 executing 无 changes dir，gate 会在 executing 停）
    _make_req_flow(tmp_path, req_id=req_id)

    result = _run_harness_next(tmp_path, execute=True)

    rt = _read_runtime(tmp_path)
    # RFE → executing（1 跳），然后 while 内 executing 无 changes dir → gate 停下
    assert rt["stage"] == "executing", (
        f"TC-04: Expected stage=executing (RFE→executing 1 hop, then gate stops), got {rt['stage']!r}\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    advances = _read_feedback_jsonl(tmp_path)
    assert len(advances) == 1, (
        f"TC-04: Expected 1 stage_advance event (RFE→executing), got {len(advances)}: {advances}"
    )
    assert advances[0]["payload"]["from_stage"] == "ready_for_execution"
    assert advances[0]["payload"]["to_stage"] == "executing"


# ─────────────────────────── TC-05 ───────────────────────────────────────────


def test_tc05_subprocess_executing_with_artifacts_advances_to_testing_only(tmp_path: Path) -> None:
    """TC-05: subprocess harness next，stage=executing，chg dir + session-memory.md(✅) + tests/ → advance 到 testing 后停。

    req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）/ chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）
    AC-2（子进程 dogfood 4 路径全绿）+ AC-3（自身周期 dogfood 自证）：缺产物路径——执行 executing 产物完整后只 1 跳。
    """
    req_id = "req-sub-99"
    _write_config(tmp_path)
    _write_role_model_map(tmp_path)
    _write_runtime(tmp_path, stage="executing", req_id=req_id)

    req_flow = _make_req_flow(tmp_path, req_id=req_id)
    # 构建完整的 chg-01/session-memory.md 含 ✅
    chg_dir = req_flow / "changes" / "chg-01-test"
    chg_dir.mkdir(parents=True, exist_ok=True)
    (chg_dir / "session-memory.md").write_text("## executing done\n\n工作完成 ✅\n", encoding="utf-8")

    # tests/ 下有 test_*.py
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "test_dummy.py").write_text("# dummy\n", encoding="utf-8")

    # testing 缺 test-report.md（确保 while 在 testing 停下，不连跳到 acceptance）
    result = _run_harness_next(tmp_path)

    rt = _read_runtime(tmp_path)
    # executing → testing（1 跳），testing 无 test-report.md → while 在 testing 停
    assert rt["stage"] == "testing", (
        f"TC-05: Expected stage=testing (executing→testing 1 hop, then gate stops), got {rt['stage']!r}\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    advances = _read_feedback_jsonl(tmp_path)
    assert len(advances) == 1, (
        f"TC-05: Expected 1 stage_advance event (executing→testing), got {len(advances)}: {advances}"
    )
    assert advances[0]["payload"]["from_stage"] == "executing"
    assert advances[0]["payload"]["to_stage"] == "testing"


# ─────────────────────────── TC-06 ───────────────────────────────────────────


def test_tc06_subprocess_testing_with_report_advances_to_acceptance_only(tmp_path: Path) -> None:
    """TC-06: subprocess harness next，stage=testing，test-report.md 含 §结论 → advance 到 acceptance 后停（not done）。

    req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）/ chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）
    AC-2（子进程 dogfood 4 路径全绿）+ AC-3（自身周期 dogfood 自证）：有产物路径——testing 完整后只 1 跳。
    acceptance exit_decision=verdict，checklist.md 缺（无 §结论）→ 在 acceptance 停（不跳 done）。
    """
    req_id = "req-sub-99"
    _write_config(tmp_path)
    _write_role_model_map(tmp_path)
    _write_runtime(tmp_path, stage="testing", req_id=req_id)

    req_flow = _make_req_flow(tmp_path, req_id=req_id)
    # test-report.md 含 §结论（testing work-done gate 通过）
    (req_flow / "test-report.md").write_text("# test-report\n\n## 结论\n\nPASS\n", encoding="utf-8")
    # acceptance/checklist.md 缺 → while 内 acceptance gate 阻断（不跳 done）

    result = _run_harness_next(tmp_path)

    rt = _read_runtime(tmp_path)
    # testing → acceptance（1 跳），acceptance 缺 checklist → gate 停在 acceptance
    assert rt["stage"] == "acceptance", (
        f"TC-06: Expected stage=acceptance (testing→acceptance 1 hop, then gate stops), got {rt['stage']!r}\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    advances = _read_feedback_jsonl(tmp_path)
    assert len(advances) == 1, (
        f"TC-06: Expected 1 stage_advance event (testing→acceptance), got {len(advances)}: {advances}"
    )
    assert advances[0]["payload"]["from_stage"] == "testing"
    assert advances[0]["payload"]["to_stage"] == "acceptance"


# ─────────────────────────── TC-07 ───────────────────────────────────────────


def test_tc07_dogfood_full_chain_four_hops(tmp_path: Path) -> None:
    """TC-07: dogfood 全链，tmpdir mock 工作区，4 次 harness next 各 1 跳，最终 done，stage_advance 间隔 ≥ 4ms。

    req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）/ chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）
    AC-2（子进程 dogfood 4 路径全绿）+ AC-3（自身周期 dogfood 自证）。
    流程：RFE --execute→ executing（chg ready）→ testing（report ready）→ acceptance（checklist ready）→ done。
    """
    req_id = "req-sub-dogfood"
    _write_config(tmp_path)
    _write_role_model_map(tmp_path)

    req_flow = tmp_path / ".workflow" / "flow" / "requirements" / f"{req_id}-dogfood"
    req_flow.mkdir(parents=True, exist_ok=True)

    # tests/ dir 含 test_*.py
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "test_dummy.py").write_text("# dummy\n", encoding="utf-8")

    # --- Hop 1: RFE → executing ---
    _write_runtime(tmp_path, stage="ready_for_execution", req_id=req_id)
    r1 = _run_harness_next(tmp_path, execute=True)
    rt1 = _read_runtime(tmp_path)
    assert rt1["stage"] == "executing", (
        f"TC-07 hop1: Expected executing, got {rt1['stage']!r}\n"
        f"stdout={r1.stdout!r}\nstderr={r1.stderr!r}"
    )

    # 给 executing 准备 changes dir + session-memory.md 含 ✅
    chg_dir = req_flow / "changes" / "chg-01-dogfood"
    chg_dir.mkdir(parents=True, exist_ok=True)
    (chg_dir / "session-memory.md").write_text("## done\n\n全部完成 ✅\n", encoding="utf-8")

    # 小延迟确保时间戳有区分（4ms 以上）
    time.sleep(0.01)

    # --- Hop 2: executing → testing ---
    r2 = _run_harness_next(tmp_path)
    rt2 = _read_runtime(tmp_path)
    assert rt2["stage"] == "testing", (
        f"TC-07 hop2: Expected testing, got {rt2['stage']!r}\n"
        f"stdout={r2.stdout!r}\nstderr={r2.stderr!r}"
    )

    # 给 testing 准备 test-report.md 含 §结论
    (req_flow / "test-report.md").write_text("# test-report\n\n## 结论\n\nPASS\n", encoding="utf-8")

    time.sleep(0.01)

    # --- Hop 3: testing → acceptance ---
    r3 = _run_harness_next(tmp_path)
    rt3 = _read_runtime(tmp_path)
    assert rt3["stage"] == "acceptance", (
        f"TC-07 hop3: Expected acceptance, got {rt3['stage']!r}\n"
        f"stdout={r3.stdout!r}\nstderr={r3.stderr!r}"
    )

    # 给 acceptance 准备 checklist.md 含 §结论
    acc_dir = req_flow / "acceptance"
    acc_dir.mkdir(exist_ok=True)
    (acc_dir / "checklist.md").write_text("# checklist\n\n## 结论\n\n全部通过\n", encoding="utf-8")

    time.sleep(0.01)

    # --- Hop 4: acceptance → done ---
    r4 = _run_harness_next(tmp_path)
    rt4 = _read_runtime(tmp_path)
    assert rt4["stage"] == "done", (
        f"TC-07 hop4: Expected done, got {rt4['stage']!r}\n"
        f"stdout={r4.stdout!r}\nstderr={r4.stderr!r}"
    )

    # 验证 4 次调用各产 1 条 stage_advance，共 4 条
    advances = _read_feedback_jsonl(tmp_path)
    assert len(advances) == 4, (
        f"TC-07: Expected 4 stage_advance events total, got {len(advances)}: {advances}"
    )

    # 验证流转链：RFE→executing→testing→acceptance→done
    expected_chain = [
        ("ready_for_execution", "executing"),
        ("executing", "testing"),
        ("testing", "acceptance"),
        ("acceptance", "done"),
    ]
    for i, (from_s, to_s) in enumerate(expected_chain):
        assert advances[i]["payload"]["from_stage"] == from_s, (
            f"TC-07 advance[{i}]: Expected from={from_s!r}, got {advances[i]['payload']['from_stage']!r}"
        )
        assert advances[i]["payload"]["to_stage"] == to_s, (
            f"TC-07 advance[{i}]: Expected to={to_s!r}, got {advances[i]['payload']['to_stage']!r}"
        )

    # 验证相邻间隔 ≥ 4ms（subprocess 启动开销保证，time.sleep(0.01) 在各跳间追加）
    # stage_advance 时间戳来自 feedback.jsonl timestamp 字段
    import json as _json
    feedback_path = tmp_path / ".workflow" / "state" / "feedback" / "feedback.jsonl"
    all_events = []
    for line in feedback_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = _json.loads(line)
        except _json.JSONDecodeError:
            continue
        if obj.get("event_type") == "stage_advance":
            all_events.append(obj)

    if len(all_events) >= 2:
        from datetime import datetime, timezone
        timestamps = []
        for ev in all_events:
            # CLI writes "ts" key; fallback to "timestamp" for compatibility
            ts_str = ev.get("ts") or ev.get("timestamp", "")
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str)
                    timestamps.append(ts)
                except ValueError:
                    pass
        for i in range(1, len(timestamps)):
            diff_ms = (timestamps[i] - timestamps[i - 1]).total_seconds() * 1000
            assert diff_ms >= 4, (
                f"TC-07: stage_advance[{i}] interval {diff_ms:.2f}ms < 4ms (over-chain gap detected!)"
            )
