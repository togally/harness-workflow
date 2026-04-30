"""playbook 子包（req-56（路书引擎升级）/ chg-01（推断器多语言注册化）/ chg-03（LLM provider 抽象层））

公开 API：
  init_playbook(root, skip=False, only=False, override_domains=None) -> int
  infer_domains(root, override_domains=None, detectors=None) -> (matched_mode, domains)
  render_skeleton(root, domains) -> int
  DomainDetector: 抽象基类
  DEFAULT_DETECTORS: list[DomainDetector]
  LLMProvider: LLM provider 抽象基类（chg-03）
  DEFAULT_PROVIDERS: list[type[LLMProvider]]
  auto_select_provider(providers=None) -> LLMProvider
  PlaybookContext: LLM 输入上下文 dataclass
  GeneratedContent: LLM 输出 dataclass
  NoopProvider: 降级 provider（无 LLM 时兜底）
"""
from harness_workflow.playbook.init import init_playbook
from harness_workflow.playbook.domain_inference import (
    infer_domains,
    DomainDetector,
    DEFAULT_DETECTORS,
    MavenMultiModuleDetector,
    GradleMultiModuleDetector,
    CargoWorkspaceDetector,
    DotNetSlnDetector,
    PythonModulesDetector,
    PythonDomainsDetector,
    AppDirDetector,
    PythonPackageFallbackDetector,
)
from harness_workflow.playbook.skeleton import render_skeleton
from harness_workflow.playbook.llm import (
    LLMProvider,
    DEFAULT_PROVIDERS,
    auto_select_provider,
    PlaybookContext,
    GeneratedContent,
    NoopProvider,
)

__all__ = [
    "init_playbook",
    "infer_domains",
    "render_skeleton",
    "DomainDetector",
    "DEFAULT_DETECTORS",
    "MavenMultiModuleDetector",
    "GradleMultiModuleDetector",
    "CargoWorkspaceDetector",
    "DotNetSlnDetector",
    "PythonModulesDetector",
    "PythonDomainsDetector",
    "AppDirDetector",
    "PythonPackageFallbackDetector",
    # chg-03: LLM provider abstraction
    "LLMProvider",
    "DEFAULT_PROVIDERS",
    "auto_select_provider",
    "PlaybookContext",
    "GeneratedContent",
    "NoopProvider",
]
