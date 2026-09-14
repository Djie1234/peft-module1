# PEFT 模块一复现与测试说明

本目录是在上游 PEFT 1.0.0 基础上完成的课程模块一成果。上游源码基线提交为
`1568ecae`，独立测试基线提交为 `79d938f`。测试范围包括 CSV 输入、DAG 读取、
PEFT 调度、DAG 合并、命令行参数与连续调度场景。

## PyCharm 中运行

1. 用 PyCharm 打开本目录 `peft-module1`。
2. 将项目解释器设为 `.venv\Scripts\python.exe`。
3. 右键 `run_module1_tests.py`，选择 **Run 'run_module1_tests'**。
4. 控制台应显示 `38 passed`，并生成：
   - `test-results\pytest-results.xml`
   - `test-results\coverage\index.html`
5. 右键 `demo_module1.py` 运行，可查看调度结果和 Gantt 图；图片同时保存到
   `test-results\peft-gantt.png`。

如果需要重新创建环境，可在项目根目录执行：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-compatible.txt
```

上游 `requirements.txt` 固定了较旧版本，不适用于 Python 3.11；本项目使用
`requirements-compatible.txt` 中已经验证的兼容版本。

## 一键测试包含内容

- 36 条课程独立自动化测试：`tests_module1\test_module1.py`
- 2 条上游回归测试：`peft\test\test_peft.py`
- JUnit XML 测试结果
- HTML 代码覆盖率报告

## 已验证缺陷

1. 连续调度第二个 DAG 时，OCT 使用偏移后的任务号直接索引计算矩阵，导致
   `IndexError`。
2. 默认节点重标号只支持整数连续标签，字符串或非连续标签会触发
   `TypeError`/`IndexError`。
3. 通信矩阵非对角线为零时，程序把断开的处理器当成零通信耗时，产生不可行调度。
4. 输入矩阵维度、空图、环图、负数与 NaN 缺少入口校验，错误延迟为难以理解的
   `AssertionError`、`IndexError` 或 `KeyError`。

修复后，独立测试与上游测试均通过，默认示例 makespan 仍为 122.0。
