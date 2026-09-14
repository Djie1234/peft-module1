"""Module 1 functional, boundary, equivalence-class, and scenario tests."""

from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pytest

from peft import dag_merge, gantt, peft


FIXTURES = Path(__file__).resolve().parents[1] / "test"


def _write_csv(path, text):
    path.write_text(text, encoding="utf-8")
    return path


def _two_task_dag(nodes=(0, 1), weight=1.0):
    graph = nx.DiGraph()
    graph.add_nodes_from(nodes)
    graph.add_edge(nodes[0], nodes[1], weight=weight)
    return graph


def _assert_no_processor_overlap(proc_schedules):
    for jobs in proc_schedules.values():
        ordered = sorted(jobs, key=lambda job: job.start)
        assert all(left.end <= right.start for left, right in zip(ordered, ordered[1:]))


def _assert_precedence(dag, task_schedules, communication_matrix):
    for predecessor, successor, data in dag.edges(data=True):
        pred_event = task_schedules[predecessor]
        succ_event = task_schedules[successor]
        delay = 0.0
        if pred_event.proc != succ_event.proc:
            delay = data["weight"] / communication_matrix[pred_event.proc, succ_event.proc]
        assert succ_event.start >= pred_event.end + delay


def test_tc_001_read_integer_csv(tmp_path):
    path = _write_csv(tmp_path / "integer.csv", ",P0,P1\nT0,1,2\nT1,3,4\n")
    assert np.array_equal(peft.readCsvToNumpyMatrix(path), np.array([[1.0, 2.0], [3.0, 4.0]]))


def test_tc_002_read_csv_without_trailing_newline(tmp_path):
    path = _write_csv(tmp_path / "no_newline.csv", ",P0\nT0,2.5")
    assert np.array_equal(peft.readCsvToNumpyMatrix(path), np.array([[2.5]]))


def test_tc_003_read_decimal_and_negative_csv(tmp_path):
    path = _write_csv(tmp_path / "decimal.csv", ",P0,P1\nT0,-1.5,0.25\n")
    assert np.allclose(peft.readCsvToNumpyMatrix(path), np.array([[-1.5, 0.25]]))


def test_tc_004_read_csv_to_dict(tmp_path):
    path = _write_csv(tmp_path / "dictionary.csv", ",P0,P1\nT0,1,2\nT1,3,4\n")
    result = peft.readCsvToDict(path)
    assert list(result) == [0, 1]
    assert np.array_equal(result[1], np.array([3.0, 4.0]))


def test_tc_005_missing_csv_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        peft.readCsvToNumpyMatrix(tmp_path / "missing.csv")


def test_tc_006_malformed_csv_raises_value_error(tmp_path):
    path = _write_csv(tmp_path / "malformed.csv", ",P0\nT0,not-a-number\n")
    with pytest.raises(ValueError):
        peft.readCsvToNumpyMatrix(path)


def test_tc_007_read_dag_omits_zero_edges():
    dag = peft.readDagMatrix(FIXTURES / "peftgraph_task_connectivity.csv")
    assert all(data["weight"] != 0 for _, _, data in dag.edges(data=True))


def test_tc_008_read_dag_preserves_weight():
    dag = peft.readDagMatrix(FIXTURES / "peftgraph_task_connectivity.csv")
    assert dag[0][1]["weight"] == 17.0


def test_tc_009_canonical_schedule_makespan():
    dag = peft.readDagMatrix(FIXTURES / "peftgraph_task_connectivity.csv")
    comm = peft.readCsvToNumpyMatrix(FIXTURES / "peftgraph_resource_BW.csv")
    comp = peft.readCsvToNumpyMatrix(FIXTURES / "peftgraph_task_exe_time.csv")
    proc_schedules, _, _ = peft.schedule_dag(dag, comp, comm)
    assert max(job.end for jobs in proc_schedules.values() for job in jobs) == 122.0


def test_tc_010_canonical_schedule_has_all_tasks():
    dag = peft.readDagMatrix(FIXTURES / "peftgraph_task_connectivity.csv")
    comm = peft.readCsvToNumpyMatrix(FIXTURES / "peftgraph_resource_BW.csv")
    comp = peft.readCsvToNumpyMatrix(FIXTURES / "peftgraph_task_exe_time.csv")
    _, task_schedules, _ = peft.schedule_dag(dag, comp, comm)
    assert set(task_schedules) == set(range(10))
    assert all(event is not None for event in task_schedules.values())


def test_tc_011_canonical_schedule_has_three_processors():
    dag = peft.readDagMatrix(FIXTURES / "peftgraph_task_connectivity.csv")
    comm = peft.readCsvToNumpyMatrix(FIXTURES / "peftgraph_resource_BW.csv")
    comp = peft.readCsvToNumpyMatrix(FIXTURES / "peftgraph_task_exe_time.csv")
    proc_schedules, _, _ = peft.schedule_dag(dag, comp, comm)
    assert set(proc_schedules) == {0, 1, 2}


def test_tc_012_processor_jobs_do_not_overlap():
    dag = peft.readDagMatrix(FIXTURES / "peftgraph_task_connectivity.csv")
    comm = peft.readCsvToNumpyMatrix(FIXTURES / "peftgraph_resource_BW.csv")
    comp = peft.readCsvToNumpyMatrix(FIXTURES / "peftgraph_task_exe_time.csv")
    proc_schedules, _, _ = peft.schedule_dag(dag, comp, comm)
    _assert_no_processor_overlap(proc_schedules)


def test_tc_013_dependencies_respect_communication_delay():
    dag = peft.readDagMatrix(FIXTURES / "peftgraph_task_connectivity.csv")
    comm = peft.readCsvToNumpyMatrix(FIXTURES / "peftgraph_resource_BW.csv")
    comp = peft.readCsvToNumpyMatrix(FIXTURES / "peftgraph_task_exe_time.csv")
    _, task_schedules, _ = peft.schedule_dag(dag, comp, comm)
    _assert_precedence(dag, task_schedules, comm)


def test_tc_014_dictionary_output_covers_all_tasks():
    dag = peft.readDagMatrix(FIXTURES / "peftgraph_task_connectivity.csv")
    comm = peft.readCsvToNumpyMatrix(FIXTURES / "peftgraph_resource_BW.csv")
    comp = peft.readCsvToNumpyMatrix(FIXTURES / "peftgraph_task_exe_time.csv")
    _, task_schedules, dictionary = peft.schedule_dag(dag, comp, comm)
    assert set(dictionary) == set(task_schedules)


def test_tc_015_single_task_chooses_fastest_processor():
    dag = nx.DiGraph()
    dag.add_node(0)
    proc_schedules, task_schedules, _ = peft.schedule_dag(
        dag, np.array([[5.0, 2.0, 3.0]]), np.ones((3, 3)) - np.eye(3)
    )
    assert task_schedules[0] == peft.ScheduleEvent(0, 0, 2.0, 1)
    assert len(proc_schedules[1]) == 1


def test_tc_016_time_offset_is_applied():
    dag = nx.DiGraph()
    dag.add_node(0)
    _, task_schedules, _ = peft.schedule_dag(
        dag, np.array([[2.0, 4.0]]), np.array([[0.0, 1.0], [1.0, 0.0]]), time_offset=7
    )
    assert task_schedules[0].start == 7


def test_tc_017_single_processor_boundary():
    dag = _two_task_dag(weight=10.0)
    proc_schedules, task_schedules, _ = peft.schedule_dag(
        dag, np.array([[1.0], [2.0]]), np.array([[0.0]])
    )
    assert task_schedules[1].start == 1.0
    _assert_no_processor_overlap(proc_schedules)


def test_tc_018_string_nodes_are_relabelled_by_default():
    dag = _two_task_dag(nodes=("start", "finish"))
    _, task_schedules, _ = peft.schedule_dag(
        dag, np.array([[1.0, 2.0], [2.0, 1.0]]), np.array([[0.0, 1.0], [1.0, 0.0]])
    )
    assert set(task_schedules) == {0, 1}


def test_tc_019_noncontiguous_nodes_are_relabelled_by_default():
    dag = _two_task_dag(nodes=(10, 20))
    _, task_schedules, _ = peft.schedule_dag(
        dag, np.array([[1.0, 2.0], [2.0, 1.0]]), np.array([[0.0, 1.0], [1.0, 0.0]])
    )
    assert set(task_schedules) == {0, 1}


def test_tc_020_relabel_false_accepts_contiguous_nodes():
    dag = _two_task_dag()
    _, task_schedules, _ = peft.schedule_dag(
        dag, np.array([[1.0, 2.0], [2.0, 1.0]]), np.array([[0.0, 1.0], [1.0, 0.0]]), relabel_nodes=False
    )
    assert set(task_schedules) == {0, 1}


def test_tc_021_row_count_mismatch_is_rejected():
    with pytest.raises(ValueError, match="row"):
        peft.schedule_dag(
            _two_task_dag(), np.array([[1.0, 2.0]]), np.array([[0.0, 1.0], [1.0, 0.0]])
        )


def test_tc_022_processor_count_mismatch_is_rejected():
    with pytest.raises(ValueError, match="processor"):
        peft.schedule_dag(
            _two_task_dag(), np.ones((2, 3)), np.array([[0.0, 1.0], [1.0, 0.0]])
        )


def test_tc_023_disconnected_processors_are_rejected():
    with pytest.raises(ValueError, match="off-diagonal"):
        peft.schedule_dag(_two_task_dag(), np.ones((2, 2)), np.zeros((2, 2)))


def test_tc_024_empty_dag_is_rejected():
    with pytest.raises(ValueError, match="at least one"):
        peft.schedule_dag(nx.DiGraph(), np.empty((0, 1)), np.array([[0.0]]))


def test_tc_025_cyclic_graph_is_rejected():
    dag = nx.DiGraph([(0, 1), (1, 0)])
    nx.set_edge_attributes(dag, 1.0, "weight")
    with pytest.raises(ValueError, match="acyclic"):
        peft.schedule_dag(dag, np.ones((2, 1)), np.array([[0.0]]))


def test_tc_026_negative_execution_time_is_rejected():
    with pytest.raises(ValueError, match="non-negative"):
        peft.schedule_dag(_two_task_dag(), np.array([[1.0], [-1.0]]), np.array([[0.0]]))


def test_tc_027_nan_execution_time_is_rejected():
    with pytest.raises(ValueError, match="finite"):
        peft.schedule_dag(_two_task_dag(), np.array([[1.0], [np.nan]]), np.array([[0.0]]))


def test_tc_028_merge_two_dags_adds_common_entry_and_exit():
    merged = dag_merge.merge_dags(_two_task_dag(), _two_task_dag())
    assert len(merged) == 6
    assert len([node for node in merged if merged.in_degree(node) == 0]) == 1
    assert len([node for node in merged if merged.out_degree(node) == 0]) == 1


def test_tc_029_merge_connector_edges_have_zero_weight():
    merged = dag_merge.merge_dags(_two_task_dag(), _two_task_dag())
    root = next(node for node in merged if merged.in_degree(node) == 0)
    terminal = next(node for node in merged if merged.out_degree(node) == 0)
    assert all(merged[root][node]["weight"] == 0 for node in merged.successors(root))
    assert all(merged[node][terminal]["weight"] == 0 for node in merged.predecessors(terminal))


def test_tc_030_merge_does_not_modify_inputs():
    left = _two_task_dag()
    right = _two_task_dag()
    left_snapshot = nx.node_link_data(left)
    right_snapshot = nx.node_link_data(right)
    dag_merge.merge_dags(left, right)
    assert nx.node_link_data(left) == left_snapshot
    assert nx.node_link_data(right) == right_snapshot


def test_tc_031_skip_relabeling_preserves_distinct_labels():
    left = _two_task_dag(nodes=(0, 1))
    right = _two_task_dag(nodes=(2, 3))
    merged = dag_merge.merge_dags(left, right, skip_relabeling=True)
    assert {0, 1, 2, 3}.issubset(merged.nodes)


def test_tc_032_skip_relabeling_rejects_overlapping_labels():
    with pytest.raises(nx.NetworkXError):
        dag_merge.merge_dags(_two_task_dag(), _two_task_dag(), skip_relabeling=True)


def test_tc_033_merge_three_dags():
    merged = dag_merge.merge_dags(_two_task_dag(), _two_task_dag(), _two_task_dag())
    assert len(merged) == 8
    assert nx.is_directed_acyclic_graph(merged)


def test_tc_034_argument_parser_defaults():
    args = peft.generate_argparser().parse_args([])
    assert args.dag_file.endswith("peftgraph_task_connectivity.csv")
    assert args.loglevel == "INFO"
    assert args.showDAG is False
    assert args.showGantt is False


def test_tc_035_argument_parser_custom_values():
    args = peft.generate_argparser().parse_args(["-d", "dag.csv", "-l", "DEBUG", "--showGantt"])
    assert args.dag_file == "dag.csv"
    assert args.loglevel == "DEBUG"
    assert args.showGantt is True


def test_tc_036_repeated_scheduling_on_existing_processors():
    dag = peft.readDagMatrix(FIXTURES / "canonicalgraph_task_connectivity.csv")
    comm = peft.readCsvToNumpyMatrix(FIXTURES / "canonicalgraph_resource_BW.csv")
    comp = peft.readCsvToNumpyMatrix(FIXTURES / "canonicalgraph_task_exe_time.csv")
    first_proc, _, _ = peft.schedule_dag(dag, comp, comm)
    second_proc, second_tasks, _ = peft.schedule_dag(
        dag, comp, comm, proc_schedules=first_proc, time_offset=10
    )
    assert set(second_tasks) == set(range(20))
    assert sum(len(jobs) for jobs in second_proc.values()) == 20
    _assert_no_processor_overlap(second_proc)
