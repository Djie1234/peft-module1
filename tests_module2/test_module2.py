"""New Module 2 cases; IDs map one-to-one to the delivered workbook."""

import networkx as nx
import numpy as np
import pytest

from peft.peft import ScheduleEvent, schedule_dag


def one_task():
    graph = nx.DiGraph()
    graph.add_node(0)
    return graph


def chain(weight=0):
    graph = nx.DiGraph()
    graph.add_edge(0, 1, weight=weight)
    return graph


def existing(*events):
    return {0: list(events)}


def test_m2_tc_001_exact_fit_before_first_job():
    """A [0, 2] free slot must not be lost when duration equals 2."""
    schedules, tasks, _ = schedule_dag(
        one_task(), [[2]], [[0]], proc_schedules=existing(ScheduleEvent(0, 2, 4, 0))
    )
    assert tasks[1] == ScheduleEvent(1, 0, 2, 0)
    assert [event.task for event in schedules[0]] == [1, 0]


def test_m2_tc_002_fractional_exact_fit_before_first_job():
    _, tasks, _ = schedule_dag(
        one_task(), [[1.5]], [[0]], proc_schedules=existing(ScheduleEvent(0, 1.5, 3, 0))
    )
    assert tasks[1] == ScheduleEvent(1, 0, 1.5, 0)


def test_m2_tc_003_exact_fit_with_nonzero_offset():
    _, tasks, _ = schedule_dag(
        one_task(), [[2]], [[0]], proc_schedules=existing(ScheduleEvent(0, 7, 9, 0)), time_offset=5
    )
    assert tasks[1] == ScheduleEvent(1, 5, 7, 0)


def test_m2_tc_004_larger_initial_gap_is_used():
    _, tasks, _ = schedule_dag(
        one_task(), [[2]], [[0]], proc_schedules=existing(ScheduleEvent(0, 3, 5, 0))
    )
    assert tasks[1] == ScheduleEvent(1, 0, 2, 0)


def test_m2_tc_005_smaller_initial_gap_is_skipped():
    _, tasks, _ = schedule_dag(
        one_task(), [[2]], [[0]], proc_schedules=existing(ScheduleEvent(0, 1, 3, 0))
    )
    assert tasks[1] == ScheduleEvent(1, 3, 5, 0)


def test_m2_tc_006_exact_fit_between_two_jobs():
    _, tasks, _ = schedule_dag(
        one_task(), [[2]], [[0]], proc_schedules=existing(
            ScheduleEvent(0, 0, 2, 0), ScheduleEvent(1, 4, 6, 0)
        )
    )
    assert tasks[2] == ScheduleEvent(2, 2, 4, 0)


def test_m2_tc_007_offset_inside_internal_gap():
    _, tasks, _ = schedule_dag(
        one_task(), [[1]], [[0]], proc_schedules=existing(
            ScheduleEvent(0, 0, 2, 0), ScheduleEvent(1, 5, 6, 0)
        ), time_offset=3
    )
    assert tasks[2] == ScheduleEvent(2, 3, 4, 0)


def test_m2_tc_008_existing_events_are_retained():
    old = ScheduleEvent(0, 3, 5, 0)
    schedules, tasks, _ = schedule_dag(
        one_task(), [[1]], [[0]], proc_schedules=existing(old)
    )
    assert old in schedules[0]
    assert tasks[0] == old


def test_m2_tc_009_predecessor_list_after_gap_insertion():
    _, _, mapping = schedule_dag(
        one_task(), [[2]], [[0]], proc_schedules=existing(ScheduleEvent(0, 2, 4, 0))
    )
    assert mapping[0] == (0, 1, [1])
    assert mapping[1] == (0, 0, [])


def test_m2_tc_010_input_dag_attributes_are_unchanged():
    graph = chain(2)
    before = nx.node_link_data(graph)
    schedule_dag(graph, [[1], [1]], [[0]])
    assert nx.node_link_data(graph) == before


def test_m2_tc_011_nonsquare_communication_matrix_rejected():
    with pytest.raises(ValueError, match="square"):
        schedule_dag(one_task(), [[1, 2]], [[0, 1, 2], [1, 0, 2]])


def test_m2_tc_012_nonfinite_communication_matrix_rejected():
    with pytest.raises(ValueError, match="finite"):
        schedule_dag(one_task(), [[1, 2]], [[0, np.inf], [1, 0]])


def test_m2_tc_013_negative_communication_matrix_rejected():
    with pytest.raises(ValueError, match="non-negative"):
        schedule_dag(one_task(), [[1, 2]], [[0, -1], [1, 0]])


def test_m2_tc_014_zero_processors_rejected():
    with pytest.raises(ValueError, match="at least one processor"):
        schedule_dag(one_task(), np.empty((1, 0)), np.empty((0, 0)))


def test_m2_tc_015_multiple_roots_rejected():
    graph = nx.DiGraph()
    graph.add_edges_from([(0, 2), (1, 2)], weight=1)
    with pytest.raises(ValueError, match="single root"):
        schedule_dag(graph, [[1], [1], [1]], [[0]])


def test_m2_tc_016_multiple_terminals_rejected():
    graph = nx.DiGraph()
    graph.add_edges_from([(0, 1), (0, 2)], weight=1)
    with pytest.raises(ValueError, match="single terminal"):
        schedule_dag(graph, [[1], [1], [1]], [[0]])


def test_m2_tc_017_noncontiguous_labels_without_relabel_rejected():
    graph = nx.DiGraph()
    graph.add_edge(10, 20, weight=1)
    with pytest.raises(ValueError, match="contiguous integers"):
        schedule_dag(graph, [[1], [1]], [[0]], relabel_nodes=False)


def test_m2_tc_018_wrong_graph_type_rejected():
    with pytest.raises(TypeError, match="DiGraph"):
        schedule_dag(nx.Graph([(0, 1)]), [[1], [1]], [[0]])


def test_m2_tc_019_one_dimensional_computation_matrix_rejected():
    with pytest.raises(ValueError, match="two-dimensional"):
        schedule_dag(one_task(), [1], [[0]])


def test_m2_tc_020_tuple_matrices_are_normalized():
    _, tasks, _ = schedule_dag(one_task(), ((3, 1),), ((0, 1), (1, 0)))
    assert tasks[0] == ScheduleEvent(0, 0, 1, 1)
