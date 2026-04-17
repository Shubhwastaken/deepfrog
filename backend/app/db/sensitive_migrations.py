from __future__ import annotations

import json
from collections.abc import Iterable

from cryptography.exceptions import InvalidTag
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.pii import decrypt_pii_value, get_pii_codec


SENSITIVE_STRING_COLUMNS: dict[str, tuple[str, ...]] = {
    "users": ("email", "google_subject"),
    "otp_challenges": ("email",),
    "jobs": (
        "owner_email",
        "invoice_path",
        "bill_of_lading_path",
        "report_path",
    ),
}


async def migrate_sensitive_storage(engine: AsyncEngine) -> None:
    """Encrypt legacy plaintext rows and convert job results to encrypted text storage."""

    codec = get_pii_codec()

    async with engine.begin() as connection:
        if connection.dialect.name == "postgresql":
            await _migrate_postgres_results_column(connection)

        for table_name, columns in SENSITIVE_STRING_COLUMNS.items():
            await _encrypt_plaintext_columns(connection, table_name, columns, codec)

        await _encrypt_plaintext_job_results(connection, codec)


async def _migrate_postgres_results_column(connection) -> None:  # type: ignore[no-untyped-def]
    result = await connection.execute(
        text(
            """
            SELECT data_type, udt_name
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'jobs'
              AND column_name = 'results'
            """
        )
    )
    row = result.mappings().first()
    if row is None:
        return

    if row["data_type"] in {"json", "jsonb"} or row["udt_name"] in {"json", "jsonb"}:
        await connection.execute(text("ALTER TABLE jobs ALTER COLUMN results TYPE TEXT USING results::text"))


async def _encrypt_plaintext_columns(
    connection,  # type: ignore[no-untyped-def]
    table_name: str,
    columns: Iterable[str],
    codec,
) -> None:
    for column_name in columns:
        rows = await connection.execute(
            text(f"SELECT id, {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL")
        )
        for row in rows.mappings():
            raw_value = row[column_name]
            if raw_value is None:
                continue
            if isinstance(raw_value, str) and codec.is_encrypted(raw_value):
                try:
                    codec.decrypt(raw_value)
                    continue
                except InvalidTag:
                    plaintext = decrypt_pii_value(raw_value)
                else:
                    plaintext = raw_value
            else:
                plaintext = str(raw_value)

            await connection.execute(
                text(f"UPDATE {table_name} SET {column_name} = :value WHERE id = :id"),
                {
                    "id": row["id"],
                    "value": codec.encrypt(plaintext),
                },
            )


async def _encrypt_plaintext_job_results(connection, codec) -> None:  # type: ignore[no-untyped-def]
    rows = await connection.execute(text("SELECT id, results FROM jobs WHERE results IS NOT NULL"))
    for row in rows.mappings():
        raw_value = row["results"]
        if raw_value is None:
            continue

        if isinstance(raw_value, str):
            if codec.is_encrypted(raw_value):
                try:
                    codec.decrypt(raw_value)
                    continue
                except InvalidTag:
                    serialized = decrypt_pii_value(raw_value)
            else:
                serialized = raw_value
        else:
            serialized = json.dumps(raw_value)

        await connection.execute(
            text("UPDATE jobs SET results = :value WHERE id = :id"),
            {
                "id": row["id"],
                "value": codec.encrypt(serialized),
            },
        )
