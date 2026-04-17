from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


async def ensure_auth_schema(engine: AsyncEngine) -> None:
    """Add lightweight auth columns needed by newer login providers."""

    async with engine.begin() as connection:
        columns = await _get_column_names(connection, "users")
        if "google_subject" not in columns:
            await connection.execute(text("ALTER TABLE users ADD COLUMN google_subject VARCHAR(512)"))


async def _get_column_names(connection, table_name: str) -> set[str]:  # type: ignore[no-untyped-def]
    if connection.dialect.name == "postgresql":
        rows = await connection.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = current_schema()
                  AND table_name = :table_name
                """
            ),
            {"table_name": table_name},
        )
    else:
        rows = await connection.execute(text(f"PRAGMA table_info({table_name})"))

    names: set[str] = set()
    for row in rows.mappings():
        names.add(row.get("column_name") or row.get("name"))
    return names
