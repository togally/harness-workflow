---
id: sug-64
title: "测试命名规约：禁止以单一 src 函数名作为测试文件名（用业务概念命名）"
status: pending
created_at: 2026-04-29
priority: medium
---

bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）round-2 regression 诊断 H-D 次主导：tests/test_use_flow_layout.py 文件命名直接绑定 _use_flow_layout 函数名，函数被 bugfix-11 方向 C 删除时该测试文件命名失效（30 TC 全 import 该函数，必须整文件 git rm + 新建 test_bugfix_11_flow_layout.py），是 H-B 路径阻力的客观载体——subagent 妥协选'保函数本体改返回值恒 True'部分动机就来自'怕动这 30 TC'。建议：team development-standards 加测试命名规约——禁止 test_<src_function_name>.py 形态，必须用业务概念命名（如 test_create_requirement_layout.py / test_bugfix_layout_unconditional.py）；reviewer checklist 加该 lint。来源：bugfix-11 regression round-2 diagnosis-round2.md §7 #3。
