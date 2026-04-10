"""Prefect workflow for SanctionSight."""

from __future__ import annotations

from prefect import flow, task

from app.pipeline.runner import PipelineRunner


@task(name="run-sanctionsight-pipeline", retries=1, retry_delay_seconds=10)
def run_pipeline_task(skip_dbt: bool = False) -> dict[str, str | int]:
    runner = PipelineRunner()
    result = runner.run(skip_dbt=skip_dbt)
    return {"run_id": result.run_id, "status": result.status, "total_matches": result.total_matches}


@flow(name="sanctionsight-daily-screening")
def sanctionsight_flow(skip_dbt: bool = False) -> dict[str, str | int]:
    return run_pipeline_task(skip_dbt=skip_dbt)


if __name__ == "__main__":
    sanctionsight_flow()
