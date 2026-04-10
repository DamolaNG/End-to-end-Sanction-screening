# Interview Talking Points

## One-Minute Summary

SanctionSight is an end-to-end data engineering portfolio project that ingests public sanctions data from UN, EU, and OFAC sources, combines it with public BlackRock-style fund and holdings data, standardizes everything into a warehouse model, and screens holdings against sanctions entities using deterministic normalization plus configurable fuzzy matching. I built it as an analytical prototype for exposure monitoring, not as a regulated compliance system.

## What This Demonstrates

- Multi-source ingestion from heterogeneous public datasets.
- Medallion-style warehouse modeling with dbt.
- Entity normalization and explainable entity resolution.
- Operational metadata capture, data quality checks, and run history.
- End-user delivery via FastAPI and Streamlit.

## Why The Architecture Looks This Way

I separated the project into raw, staging, curated, screening, and marts because the screening logic is only as trustworthy as the lineage behind it. The raw layer preserves exactly what was ingested, dbt handles repeatable standardization and dashboard-ready models, and the Python screening service owns the matching logic because it is easier to evolve and explain there than purely in SQL.

## Key Design Tradeoffs

### Sample-first over fragile scraping

I intentionally added a deterministic sample mode because public fund and holdings pages can change often. For a portfolio project, reproducibility matters more than pretending the live scrape is always stable. The connector abstraction keeps the system extensible so stronger live providers can be swapped in later.

### Explainable scoring over opaque ML

I used weighted exact, alias, identifier, and fuzzy heuristics rather than a black-box classifier. That makes it easier to show how a match was produced, why it fell into a High, Medium, or Low confidence band, and which attributes influenced the score.

### Warehouse-first delivery

Instead of wiring the dashboard directly to raw Python objects, I modeled serving tables and marts. That mirrors how analytics and internal operational tools are usually delivered in real teams.

## Questions You’ll Likely Get

### How would you productionize this further?

I would add better source monitoring, alerting, provider abstractions for more holdings vendors, incremental processing, a manual review queue, CI/CD with environment promotion, and a stronger candidate-generation strategy for scale.

### Why not use embeddings or ML matching?

That is a possible next step, but for a sanctions-style prototype I wanted deterministic and auditable scoring first. Human reviewers need to understand why a candidate appeared, and exact or fuzzy evidence is easier to explain.

### What are the biggest risks?

The biggest risks are source drift, imperfect public data quality, and false positives from name-based matching. That is why the repo is framed as analytical screening support rather than compliance tooling.

### What part are you proudest of?

The strongest part is the full-stack integration. The project is not just a notebook or one script; it shows ingestion, storage, transformations, entity resolution, API serving, dashboard delivery, and operational controls in one coherent system.

## Strong Closing Line

If I were extending this in a real team, the next step would be to replace the sample BlackRock feed with a more stable holdings source, add review workflows, and operationalize the pipeline with CI, alerting, and environment-specific deployments.

