# Architecture

SanctionSight is structured as a medallion-style analytics platform with raw ingestion, dbt-based standardization, Python-based screening logic, and dashboard/API serving layers. The project is a public-data analytical prototype intended for resume and portfolio use, not a legal compliance system.

The raw layer stores exact source snapshots on disk and snapshot metadata plus row-level payloads in PostgreSQL. The staging layer standardizes UN, EU, OFAC, and BlackRock payloads into consistent source-aligned schemas. The curated layer deduplicates sanctions entities and BlackRock holdings/funds into entity-ready models. The screening layer stores run history, match candidates, and scoring evidence. The marts layer produces dashboard-ready exposure, health, and entity-match views.

