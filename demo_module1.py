"""PyCharm-friendly PEFT reproduction demo with a saved Gantt chart."""

import argparse
from pathlib import Path

from peft import gantt, peft


def main():
    parser = argparse.ArgumentParser(description="Run the canonical PEFT scheduling demo")
    parser.add_argument("--no-show", action="store_true", help="Save the chart without opening a window")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent
    fixture_dir = project_root / "test"
    result_dir = project_root / "test-results"
    result_dir.mkdir(exist_ok=True)

    dag = peft.readDagMatrix(fixture_dir / "peftgraph_task_connectivity.csv")
    communication = peft.readCsvToNumpyMatrix(fixture_dir / "peftgraph_resource_BW.csv")
    computation = peft.readCsvToNumpyMatrix(fixture_dir / "peftgraph_task_exe_time.csv")
    proc_schedules, task_schedules, _ = peft.schedule_dag(
        dag, computation_matrix=computation, communication_matrix=communication
    )

    print("PEFT canonical example reproduced successfully")
    print(f"Tasks: {len(task_schedules)} | Processors: {len(proc_schedules)}")
    for processor, jobs in proc_schedules.items():
        print(f"Processor {processor}: {jobs}")
    makespan = max(job.end for jobs in proc_schedules.values() for job in jobs)
    print(f"Makespan: {makespan:.1f}")

    chart_path = result_dir / "peft-gantt.png"
    gantt.showGanttChart(proc_schedules, output_file=chart_path, show=not args.no_show)
    print(f"Gantt chart: {chart_path}")


if __name__ == "__main__":
    main()
