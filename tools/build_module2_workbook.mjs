// Rebuild the delivered workbook from the untouched official appendix-1 template.
// Set CODEX_ARTIFACT_TOOL_PATH to the bundled artifact_tool.mjs entrypoint.
import { pathToFileURL } from "node:url";

const entry = process.env.CODEX_ARTIFACT_TOOL_PATH;
if (!entry || process.argv.length !== 4) {
  throw new Error("Usage: set CODEX_ARTIFACT_TOOL_PATH, then node build_module2_workbook.mjs TEMPLATE.xlsx OUTPUT.xlsx");
}
const { FileBlob, SpreadsheetFile } = await import(pathToFileURL(entry).href);
const [templatePath, outputPath] = process.argv.slice(2);
const wb = await SpreadsheetFile.importXlsx(await FileBlob.load(templatePath));
const info = wb.worksheets.getItemAt(0);
const cases = wb.worksheets.getItemAt(1);

for (const [cell, value] of Object.entries({
  E7: "PEFT d38620b + Module 2 fix", J7: "课程作业", E8: "PEFT 模块二 AI 测试",
  J8: "SQA-2026-M2", E9: "颜子轩（AI 辅助）", J9: "2026-09-20",
  E10: "组员复核待确认", J10: "待确认", E11: "课程教师", J11: "待确认",
})) info.getRange(cell).values = [[value]];

// id, item, title, criticality, defect-regression, precondition, input, step, expected, actual, method
const data = [
  ["001","插入调度","首空隙恰好容纳整时任务","High","是","单处理器已有任务[2,4]","新任务耗时2，偏移0","运行同号pytest函数","新任务[0,2]，已有任务[2,4]","修复后[0,2]；基线错误为[4,6]","边界值/缺陷回归"],
  ["002","插入调度","首空隙恰好容纳小数任务","High","是","已有任务[1.5,3]","新任务耗时1.5","运行同号pytest函数","新任务[0,1.5]","修复后[0,1.5]；基线[3,4.5]","边界值/缺陷回归"],
  ["003","插入调度","非零偏移下恰好填满首空隙","High","是","已有任务[7,9]","耗时2，偏移5","运行同号pytest函数","新任务[5,7]","修复后[5,7]；基线[9,11]","边界值/缺陷回归"],
  ["004","插入调度","首空隙大于任务时长","Medium","否","已有任务[3,5]","耗时2，偏移0","运行同号pytest函数","新任务[0,2]","[0,2]","边界邻域"],
  ["005","插入调度","首空隙小于任务时长","Medium","否","已有任务[1,3]","耗时2，偏移0","运行同号pytest函数","新任务[3,5]","[3,5]","边界邻域"],
  ["006","插入调度","两已有任务之间恰好填满","High","否","已有任务[0,2]与[4,6]","耗时2","运行同号pytest函数","新任务[2,4]","[2,4]","内部空隙边界"],
  ["007","插入调度","偏移落在内部空隙","Medium","否","已有任务[0,2]与[5,6]","耗时1，偏移3","运行同号pytest函数","新任务[3,4]","[3,4]","时间偏移场景"],
  ["008","调度输出","已有任务事件保留","Medium","否","已有事件[3,5]","新增任务耗时1","运行同号pytest函数","原事件仍在处理器及任务表","原事件均保留","状态保持"],
  ["009","调度输出","空隙插入后的前驱映射","High","是","已有任务[2,4]","新增任务耗时2","运行同号pytest函数","原任务前驱为新任务；新任务无前驱","修复后符合；基线映射错误","输出一致性/缺陷回归"],
  ["010","输入副作用","调用者DAG不被修改","Medium","否","两节点链，边权2","计算时长各1","运行同号pytest函数","调用前后DAG节点/边属性一致","一致","副作用检查"],
  ["011","输入校验","非方阵通信矩阵拒绝","Medium","否","单任务，双处理器","2×3通信矩阵","运行同号pytest函数","抛ValueError，含square","按预期抛错","无效等价类"],
  ["012","输入校验","无穷大通信值拒绝","Medium","否","单任务，双处理器","通信矩阵含Inf","运行同号pytest函数","抛ValueError，含finite","按预期抛错","无效等价类"],
  ["013","输入校验","负通信值拒绝","Medium","否","单任务，双处理器","通信矩阵含-1","运行同号pytest函数","抛ValueError，含non-negative","按预期抛错","无效等价类"],
  ["014","输入校验","零处理器拒绝","Medium","否","单任务","计算矩阵1×0","运行同号pytest函数","抛ValueError，含processor","按预期抛错","边界值"],
  ["015","图结构","多根DAG拒绝","Medium","否","0→2与1→2","三任务单处理器","运行同号pytest函数","抛ValueError，含single root","按预期抛错","无效图结构"],
  ["016","图结构","多终点DAG拒绝","Medium","否","0→1与0→2","三任务单处理器","运行同号pytest函数","抛ValueError，含single terminal","按预期抛错","无效图结构"],
  ["017","节点编号","禁重标号下非连续编号拒绝","Medium","否","节点10→20","relabel_nodes=False","运行同号pytest函数","抛ValueError，含contiguous integers","按预期抛错","无效等价类"],
  ["018","图类型","无向图拒绝","Medium","否","NetworkX Graph","两节点","运行同号pytest函数","抛TypeError，含DiGraph","按预期抛错","无效等价类"],
  ["019","矩阵维度","一维计算矩阵拒绝","Medium","否","单任务","计算矩阵[1]","运行同号pytest函数","抛ValueError，含two-dimensional","按预期抛错","无效等价类"],
  ["020","输入兼容","元组矩阵输入正常化","Low","否","单任务双处理器","计算((3,1),)，通信((0,1),(1,0))","运行同号pytest函数","选择处理器1，时间[0,1]","处理器1，[0,1]","有效等价类"],
];

const rows = data.map(([id,item,title,priority,regression,pre,input,step,expected,actual,method]) => [
  `M2-TC-${id}`, item, title, priority, "是", regression, pre, input,
  `执行 tests_module2/test_module2.py::test_m2_tc_${id}_${({
    "001":"exact_fit_before_first_job", "002":"fractional_exact_fit_before_first_job",
    "003":"exact_fit_with_nonzero_offset", "004":"larger_initial_gap_is_used",
    "005":"smaller_initial_gap_is_skipped", "006":"exact_fit_between_two_jobs",
    "007":"offset_inside_internal_gap", "008":"existing_events_are_retained",
    "009":"predecessor_list_after_gap_insertion", "010":"input_dag_attributes_are_unchanged",
    "011":"nonsquare_communication_matrix_rejected", "012":"nonfinite_communication_matrix_rejected",
    "013":"negative_communication_matrix_rejected", "014":"zero_processors_rejected",
    "015":"multiple_roots_rejected", "016":"multiple_terminals_rejected",
    "017":"noncontiguous_labels_without_relabel_rejected", "018":"wrong_graph_type_rejected",
    "019":"one_dimensional_computation_matrix_rejected", "020":"tuple_matrices_are_normalized"
  })[id]}。${step}`, expected, actual, "OK", method,
]);
cases.getRange("A2:M21").values = rows;
cases.getRange("A2:M21").format.wrapText = true;
cases.getRange("A2:M21").format.verticalAlignment = "center";
cases.getRange("A2:M21").format.rowHeight = 44;
cases.getRange("C:C").format.columnWidth = 30;
cases.getRange("G:J").format.columnWidth = 32;
cases.getRange("K:K").format.columnWidth = 30;
cases.getRange("M:M").format.columnWidth = 22;
cases.freezePanes.freezeRows(1);
const result = await SpreadsheetFile.exportXlsx(wb);
await result.save(outputPath);
console.log(`wrote ${rows.length} cases: ${outputPath}`);
