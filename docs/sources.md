# Source Descriptions

SanctionSight ingests public sanctions records from three official sanctions sources and combines them with public BlackRock-style fund and holdings snapshots for analytical exposure screening. Because public source structures can change over time, the project includes a deterministic sample-data mode and cached snapshot fallback for demo reliability.

## Official Sanctions Source Pages

### United Nations

- Official source page: [United Nations Security Council Consolidated List](https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list)
- Machine-readable export used by the connector: `https://scsanctions.un.org/resources/xml/en/consolidated.xml`

### European Union

- Official dataset page: [Consolidated list of persons, groups and entities subject to EU financial sanctions](https://data.europa.eu/data/datasets/consolidated-list-of-persons-groups-and-entities-subject-to-eu-financial-sanctions?locale=en)
- Machine-readable export used by the connector: `https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content`

### OFAC

- Official source page: [OFAC Sanctions List Service](https://ofac.treasury.gov/sanctions-list-service)
- Machine-readable export used by the connector: `https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.XML`

## Provider Holdings Source

### BlackRock

- Public product and holdings pages are treated as public analytical source material.
- Because site structures can change, the repository defaults to deterministic sample snapshots and cached fallback behavior for local demos.

Every connector is wrapped behind an interface that supports metadata capture, retries, timeout handling, raw snapshot storage, and source-specific extension. This keeps the ingestion surface modular so the same downstream models can be reused if more providers or sanctions lists are added later.
