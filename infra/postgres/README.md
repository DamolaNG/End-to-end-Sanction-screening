# Postgres Infra Notes

PostgreSQL is provided through `docker-compose.yml` for local development. Migrations are managed by Alembic, and dbt targets the same database through environment-driven connection settings.

