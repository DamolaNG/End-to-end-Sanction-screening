"""CLI entrypoint for the SanctionSight pipeline."""

from __future__ import annotations

import argparse

from app.pipeline.runner import PipelineRunner


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the SanctionSight pipeline.")
    parser.add_argument("--skip-dbt", action="store_true", help="Skip dbt run/test steps.")
    args = parser.parse_args()

    runner = PipelineRunner()
    result = runner.run(skip_dbt=args.skip_dbt)
    print(
        f"Pipeline completed with run_id={result.run_id}, "
        f"status={result.status}, total_matches={result.total_matches}"
    )


if __name__ == "__main__":
    main()
