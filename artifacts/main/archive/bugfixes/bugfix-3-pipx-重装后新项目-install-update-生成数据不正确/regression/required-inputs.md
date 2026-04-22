# Regression Required Inputs — bugfix-3

诊断已独立定位两处 update 侧 bug（详见 `diagnosis.md`），流程可以直接 `--confirm` 并回到 testing；以下信息非阻塞，但若用户能补充会让 executing 阶段的测试用例优先级更准。

## 1. Current Problem

- Issue summary：pipx 重装后在目标项目 `/Users/jiazhiwei/claudeProject/PetMallPlatform` 跑 `harness install` + `harness update`，用户感知"生成的数据不对"
- Related regression：bugfix-3 regression（独立诊断，未调用 `--testing`）
- Linked change：尚未产生 chg

## 2. Required Human Inputs

| Item | Required | Notes |
| --- | --- | --- |
| 现象归属确认 | 建议 | 用户所说"不对"是指以下哪一条？ A) `.workflow/context/roles/*.md` 缺"对人文档"等新章节；B) `legacy-cleanup/` 下堆积 `experience/index.md-N` 垃圾；C) runtime.yaml 残留 `operation_target: req-02`；D) 其他（请描述） |
| 期望行为 | 建议 | update 是否应"无条件覆盖 scaffold_v2 受管文件"，还是"仅对 hash 不匹配但等于模板的视为已同步"？ |
| 清理范围 | 可选 | 是否希望一次性清理目标项目已产生的 `legacy-cleanup/.workflow/context/experience/index.md*` 副本？ |

## 3. Human Response Section

- 现象归属：
- 期望行为：
- 清理范围：

## 4. Next Step

- 主 agent：即便无用户补充，也可执行 `harness regression --confirm` → `harness regression --testing` 开始补用例
- 若用户指定"D) 其他"，testing 需先把新现象纳入用例集再进入修复
