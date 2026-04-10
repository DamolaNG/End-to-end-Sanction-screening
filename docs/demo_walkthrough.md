# Demo Walkthrough

## 1. Open With The Problem

SanctionSight answers a straightforward analytics question: if I ingest public sanctions lists and public fund holdings, can I build a repeatable pipeline that flags possible exposure to sanctioned or similarly named entities and explain why those candidates were surfaced?

## 2. Show The Architecture

Walk through the architecture diagram in the README and explain the flow:

1. Python connectors ingest sanctions and holdings data.
2. Raw snapshots are persisted to disk and PostgreSQL.
3. dbt standardizes raw records into curated entity models.
4. The screening engine generates candidate matches and evidence.
5. Dashboard-ready marts power the API and Streamlit app.

## 3. Explain Why Sample Mode Exists

Call out that public websites can drift, so the project includes a deterministic sample mode for reliable demos. Emphasize that this is a portfolio design choice that prioritizes repeatability while still keeping the connector interfaces extensible for live sources later.

## 4. Show What Gets Screened

Use the sample dataset profile from the README:

- 4 funds
- 8 holdings
- 9 sanctions entities
- A mix of identifier, exact-name, alias, and fuzzy-match scenarios

## 5. Walk The Dashboard

### Overview

Show the total funds screened, total holdings screened, sanctions records loaded, and candidate match counts. Explain that the dashboard is reading from mart tables rather than ad hoc logic in the UI.

### Match Explorer

Filter to High confidence and show an identifier or exact-match example. Then switch to a Medium or Low candidate to explain transparency and human review.

### Fund Exposure View

Pick one fund with flagged holdings and show how the candidate matches roll up to a fund-level exposure view.

### Data Quality & Pipeline Health

Show row counts, freshness, and validation output to reinforce that this is an operational data platform, not just a dashboard.

## 6. Close With Tradeoffs

Finish by saying that the system is intentionally framed as a public-data analytical prototype. It is useful for exposure monitoring and entity-resolution demonstration, but candidate matches are not legal determinations and require human review.

