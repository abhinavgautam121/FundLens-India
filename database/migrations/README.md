# Schema evolution

This is the initial schema (v1). `database/connection.py` is the source of truth;
`database/schema.sql` is the equivalent SQLite creation script. `create_all()` creates missing
tables, **not** migrations of existing tables. No pre-existing application database was replaced.

For future schema changes, back up the database and implement explicit versioned migrations
(Alembic is a sensible next step), with an upgrade test against a copy of existing data.
Do not delete an uploaded database merely to apply a schema change. The synthetic demo database
can be regenerated independently. PostgreSQL additionally needs a driver such as psycopg.
