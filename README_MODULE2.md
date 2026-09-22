# PEFT 模块二 AI 辅助测试

本项目以模块一基线 `d38620b` 为起点，采用课程方案 2“AI 辅助测试”。AI 用于生成候选场景和脚本草案；颜子轩与余璨依据代码、输入契约和 JUnit 执行结果共同确认测试预期、缺陷归因、修复与回归结论。

## 测试结果

新增 M2-TC-001～M2-TC-020 共 20 条自动化测试，与 Excel 测试用例一一对应。修复前，模块二 20 条中 16 条通过、4 条失败；四条失败均对应 DEF-M2-001。修复首空隙 exact-fit 边界后，模块二 20/20 通过；模块一 36 条与原项目 2 条回归测试一并通过，全量结果为 58/58。

## 在 PyCharm 中运行

打开本目录作为项目，选择已安装依赖的 Python 3.11 解释器。右键运行根目录的 `run_module2_tests.py`，或在项目根目录执行：

```powershell
python -m pytest tests_module2 tests_module1 peft/test -q
```

测试结果会写入 `test-results/module2/`，该目录受 `.gitignore` 排除。

## 交付文件

- `tests_module2/test_module2.py`：M2-TC-001～020 自动化测试。
- `module2-deliverables/PEFT_模块二_测试用例清单.xlsx`：逐条测试用例、输入与预期结果。
- `module2-deliverables/PEFT_模块二_缺陷报告.docx`：DEF-M2-001 缺陷报告。
- `module2-deliverables/PEFT_模块二_测试报告.docx`：测试过程、AI 审查与回归结论。
- `module2-deliverables/AI过程记录.md`：23 条候选、排重和缺陷归并记录。
- `module2-deliverables/evidence/`：修复前后 pytest JUnit XML 证据。

## 已确认缺陷

在单处理器已有事件 `[2,4]`、新任务执行时间为 2、`time_offset=0` 的场景中，正确排程应使用完整首空隙 `[0,2]`。基线代码将任务错误排到 `[4,6]`，原因是 `_compute_eft` 使用严格条件 `> 0` 排除了刚好容纳任务的空隙。将该条件调整为 `>= 0` 后，相关边界测试和全量回归均通过。

## 小组协作

颜子轩与余璨合作完成模块二，贡献各占 50%。颜子轩侧重自动化测试实现、最小修复、测试执行和证据整理；余璨侧重测试用例复核、边界场景审查、缺陷分析归并和报告整理。详细说明见 `module2-deliverables/组员复核任务.md`。
