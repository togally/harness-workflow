"""平台配置备份和恢复工具

此模块提供平台配置的备份、恢复和状态查询功能。
支持的平台：codex, qoder, cc
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional

import yaml

# 平台配置路径映射
PLATFORM_CONFIGS = {
    "codex": {
        "source": "AGENTS.md",
        "backup_dir": "codex",
    },
    "qoder": {
        "source": ".qoder/skills/harness/SKILL.md",
        "backup_dir": "qoder",
    },
    "cc": {
        "source": ".claude/commands",
        "backup_dir": "cc",
    },
    "kimi": {
        "source": ".kimi/skills/harness/SKILL.md",
        "backup_dir": "kimi",
    },
}

BACKUP_BASE = ".workflow/context/backup"
PLATFORMS_FILE = ".workflow/state/platforms.yaml"

# 所有支持的平台
ALL_PLATFORMS = ["codex", "qoder", "cc", "kimi"]


def ensure_backup_dir(root: str = ".") -> Path:
    """确保备份目录存在

    Args:
        root: 项目根目录

    Returns:
        备份基目录的 Path 对象
    """
    backup_path = Path(root) / BACKUP_BASE
    backup_path.mkdir(parents=True, exist_ok=True)
    return backup_path


def _get_platform_config(platform: str) -> Optional[dict]:
    """获取平台配置信息

    Args:
        platform: 平台名称

    Returns:
        平台配置字典，如果平台不存在返回 None
    """
    return PLATFORM_CONFIGS.get(platform)


def backup_config(platform: str, root: str = ".") -> bool:
    """将平台配置移动到备份目录

    Args:
        platform: 平台名称 (codex/qoder/cc)
        root: 项目根目录

    Returns:
        是否成功备份
    """
    config = _get_platform_config(platform)
    if not config:
        return False

    root_path = Path(root).resolve()
    source_path = root_path / config["source"]

    # 源文件/目录不存在，无需备份
    if not source_path.exists():
        return False

    # 确保备份目录存在
    backup_base = ensure_backup_dir(root)
    backup_target = backup_base / config["backup_dir"]

    # 如果备份目标已存在，先删除
    if backup_target.exists():
        if backup_target.is_dir():
            backup_target.rmdir() if not any(backup_target.iterdir()) else _rmtree(backup_target)
        else:
            backup_target.unlink()

    # 移动源到备份目录
    source_path.rename(backup_target)
    return True


def restore_config(platform: str, root: str = ".") -> bool:
    """从备份恢复配置

    Args:
        platform: 平台名称 (codex/qoder/cc)
        root: 项目根目录

    Returns:
        是否成功恢复（如果备份不存在返回 False）
    """
    config = _get_platform_config(platform)
    if not config:
        return False

    root_path = Path(root).resolve()
    backup_base = root_path / BACKUP_BASE
    backup_source = backup_base / config["backup_dir"]

    # 备份不存在
    if not backup_source.exists():
        return False

    target_path = root_path / config["source"]

    # 确保目标父目录存在
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # 如果目标已存在，先删除
    if target_path.exists():
        if target_path.is_dir():
            _rmtree(target_path)
        else:
            target_path.unlink()

    # 移动备份到原位置
    backup_source.rename(target_path)
    return True


def get_backup_status(root: str = ".") -> dict[str, bool]:
    """获取各平台的备份状态

    Args:
        root: 项目根目录

    Returns:
        {"codex": True, "qoder": False, "cc": True} 表示哪些平台有备份
    """
    root_path = Path(root).resolve()
    backup_base = root_path / BACKUP_BASE

    status = {}
    for platform in PLATFORM_CONFIGS:
        backup_path = backup_base / PLATFORM_CONFIGS[platform]["backup_dir"]
        status[platform] = backup_path.exists()

    return status


def get_active_platforms(root: str = ".") -> dict[str, bool]:
    """获取各平台的当前激活状态（配置是否存在）

    Args:
        root: 项目根目录

    Returns:
        {"codex": True, "qoder": False, "cc": True} 表示哪些平台配置已激活
    """
    root_path = Path(root).resolve()

    status = {}
    for platform in PLATFORM_CONFIGS:
        source_path = root_path / PLATFORM_CONFIGS[platform]["source"]
        status[platform] = source_path.exists()

    return status


def _rmtree(path: Path) -> None:
    """递归删除目录

    Args:
        path: 要删除的目录路径
    """
    import shutil
    shutil.rmtree(path)


def get_backup_path(platform: str, root: str = ".") -> Path:
    """获取指定平台的备份路径

    Args:
        platform: 平台名称 (codex/qoder/cc)
        root: 项目根目录

    Returns:
        备份路径的 Path 对象
    """
    config = _get_platform_config(platform)
    if not config:
        raise ValueError(f"Unknown platform: {platform}")

    root_path = Path(root).resolve()
    return root_path / BACKUP_BASE / config["backup_dir"]


def get_platform_file_patterns(platform: str) -> list[str]:
    """获取指定平台对应的文件模式列表

    Args:
        platform: 平台名称 (codex/qoder/cc)

    Returns:
        该平台对应的文件路径模式列表
    """
    patterns = {
        "codex": [
            "AGENTS.md",
            ".codex/skills/",
        ],
        "qoder": [
            ".qoder/commands/",
            ".qoder/rules/",
        ],
        "cc": [
            ".claude/commands/",
        ],
        "kimi": [
            ".kimi/skills/",
        ],
    }
    return patterns.get(platform, [])


def read_platforms_config(root: str = ".") -> dict:
    """
    读取平台配置状态

    Args:
        root: 项目根目录

    Returns:
        {"enabled": ["codex", "cc"], "disabled": ["qoder"], "last_updated": "2026-04-13"}
        如果文件不存在，返回默认配置（全部启用）
    """
    root_path = Path(root).resolve()
    config_path = root_path / PLATFORMS_FILE

    if not config_path.exists():
        return {
            "enabled": ALL_PLATFORMS.copy(),
            "disabled": [],
            "last_updated": ""
        }

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config if config else {
        "enabled": ALL_PLATFORMS.copy(),
        "disabled": [],
        "last_updated": ""
    }


def write_platforms_config(enabled: list[str], root: str = ".") -> None:
    """
    写入平台配置状态

    Args:
        enabled: 启用的平台列表
        root: 项目根目录
    """
    root_path = Path(root).resolve()
    config_path = root_path / PLATFORMS_FILE

    # 确保目录存在
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # 计算禁用列表
    disabled = [p for p in ALL_PLATFORMS if p not in enabled]

    config = {
        "enabled": enabled,
        "disabled": disabled,
        "last_updated": str(date.today())
    }

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


def sync_platforms_state(selected: list[str], root: str = ".") -> dict:
    """
    同步平台状态：备份未选择的，恢复已选择的

    Args:
        selected: 用户选择的平台列表
        root: 项目根目录

    Returns:
        操作结果摘要 {"backed_up": [...], "restored": [...], "kept": [...]}
    """
    result = {
        "backed_up": [],
        "restored": [],
        "kept": [],
        "need_generate": []
    }

    # 读取当前配置状态
    current_config = read_platforms_config(root)
    current_enabled = set(current_config.get("enabled", ALL_PLATFORMS))
    selected_set = set(selected)

    # 找出需要备份的平台（当前启用但未选择）
    to_backup = current_enabled - selected_set
    for platform in to_backup:
        if backup_config(platform, root):
            result["backed_up"].append(platform)

    # 找出需要恢复的平台（当前禁用但已选择）
    to_restore = selected_set - current_enabled
    for platform in to_restore:
        if restore_config(platform, root):
            result["restored"].append(platform)
        else:
            # 没有备份，需要生成
            result["need_generate"].append(platform)

    # 找出保持不变的平台
    kept = current_enabled & selected_set
    result["kept"] = list(kept)

    # 更新配置文件
    write_platforms_config(selected, root)

    return result
