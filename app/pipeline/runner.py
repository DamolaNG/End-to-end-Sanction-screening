"""Main end-to-end pipeline runner."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass

import pandas as pd

from app.connectors.blackrock import BlackRockFundConnector, BlackRockHoldingsConnector
from app.connectors.sanctions import (
    EUSanctionsConnector,
    OFACSanctionsConnector,
    UNSanctionsConnector,
)
from app.core.config import Settings, get_settings
from app.core.database import get_engine, session_scope
from app.core.logging import get_logger
from app.models.tables import ScreeningRun
from app.services.matching import ScreeningEngine
from app.services.persistence import (
    create_screening_run,
    ensure_tables,
    finalize_screening_run,
    persist_connector_result,
    persist_quality_issues,
    replace_screening_results,
)
from app.services.quality import QualityChecker


@dataclass(slots=True)
class PipelineResult:
    """High-level pipeline execution summary."""

    run_id: str
    status: str
    total_matches: int


class PipelineRunner:
    """Coordinates ingestion, dbt transforms, screening, and marts refresh."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.logger = get_logger(self.__class__.__name__)
        self.quality_checker = QualityChecker(self.settings)
        self.matching_engine = ScreeningEngine(self.settings)

    def run(self, skip_dbt: bool = False) -> PipelineResult:
        """Execute the pipeline end to end."""

        engine = get_engine()
        ensure_tables(engine)

        sanctions_connectors = [
            UNSanctionsConnector(self.settings),
            EUSanctionsConnector(self.settings),
            OFACSanctionsConnector(self.settings),
        ]
        fund_connector = BlackRockFundConnector(self.settings)
        holdings_connector = BlackRockHoldingsConnector(self.settings)

        with session_scope() as session:
            run = create_screening_run(session, mode="sample" if self.settings.sample_data_mode else "live")
            all_quality_issues = []

            for connector in sanctions_connectors:
                result = connector.run()
                frame = pd.DataFrame(result.records)
                all_quality_issues.extend(self.quality_checker.validate_sanctions(result.source_system, frame))
                all_quality_issues.extend(
                    self.quality_checker.stale_source_issue(result.source_system, result.source_last_updated)
                )
                persist_connector_result(session, result)

            fund_result = fund_connector.run()
            holdings_result = holdings_connector.run()
            fund_frame = pd.DataFrame(fund_result.records)
            holdings_frame = pd.DataFrame(holdings_result.records)
            all_quality_issues.extend(self.quality_checker.validate_funds(fund_frame))
            all_quality_issues.extend(self.quality_checker.validate_holdings(holdings_frame))
            persist_connector_result(session, fund_result)
            persist_connector_result(session, holdings_result)
            persist_quality_issues(session, run.run_id, all_quality_issues)

        if not skip_dbt:
            self._run_dbt("run")
            self._run_dbt("test")

        with session_scope() as session:
            funds_df = pd.read_sql("select * from int_curated_funds", session.bind)
            holdings_df = pd.read_sql("select * from int_curated_holdings", session.bind)
            sanctions_df = pd.read_sql("select * from int_curated_sanctions_entities", session.bind)
            latest_run = pd.read_sql(
                "select run_id from screening_run order by started_at desc limit 1", session.bind
            ).iloc[0]
            result = self.matching_engine.screen(
                run_id=latest_run["run_id"],
                funds_df=funds_df,
                holdings_df=holdings_df,
                sanctions_df=sanctions_df,
            )
            replace_screening_results(session, latest_run["run_id"], result.matches, result.evidence)
            run_row = session.get(ScreeningRun, latest_run["run_id"])
            finalize_screening_run(
                session=session,
                run=run_row,
                matches_df=result.matches,
                funds_df=funds_df,
                holdings_df=holdings_df,
                sanctions_df=sanctions_df,
                stale_source_warning_count=len(
                    [issue for issue in all_quality_issues if issue.check_name == "stale_source"]
                ),
            )

        if not skip_dbt:
            self._run_dbt("run", select="marts")

        self.logger.info("pipeline_completed", total_matches=len(result.matches), run_id=str(latest_run["run_id"]))
        return PipelineResult(
            run_id=str(latest_run["run_id"]),
            status="completed",
            total_matches=int(len(result.matches)),
        )

    def _run_dbt(self, command: str, select: str | None = None) -> None:
        args = [
            "dbt",
            command,
            "--project-dir",
            str(self.settings.dbt_project_dir),
            "--profiles-dir",
            str(self.settings.dbt_profiles_dir),
        ]
        if select:
            args.extend(["--select", select])
        env = os.environ.copy()
        env.update(
            {
                "POSTGRES_HOST": self.settings.postgres_host,
                "POSTGRES_PORT": str(self.settings.postgres_port),
                "POSTGRES_DB": self.settings.postgres_db,
                "POSTGRES_USER": self.settings.postgres_user,
                "POSTGRES_PASSWORD": self.settings.postgres_password,
                "DATABASE_URL": self.settings.database_url,
            }
        )
        self.logger.info("running_dbt", command=command, select=select or "all")
        subprocess.run(args, check=True, env=env)
