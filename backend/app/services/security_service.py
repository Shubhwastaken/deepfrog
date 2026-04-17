from __future__ import annotations

from sqlalchemy import text

from app.db.session import get_engine

ENCRYPTION_PREFIX = "enc::"
PASSWORD_HASH_PREFIXES = ("pbkdf2_", "argon2", "$2")


def _prefix(value: str | None, length: int = 28) -> str | None:
    if value is None:
        return None
    return value[:length]


def _is_encrypted(value: str | None) -> bool:
    return bool(value and value.startswith(ENCRYPTION_PREFIX))


def _is_password_hash(value: str | None) -> bool:
    if not value:
        return False
    return value.startswith(PASSWORD_HASH_PREFIXES)


async def get_security_storage_proof() -> dict:
    """Return admin-facing proof that sensitive PostgreSQL fields are encrypted at rest."""

    async with get_engine().connect() as connection:
        user_count = (
            await connection.execute(text("SELECT COUNT(*) AS total_users FROM users"))
        ).mappings().one()
        user_security = (
            await connection.execute(
                text(
                    """
                    SELECT
                        SUM(CASE WHEN email LIKE 'enc::%' THEN 1 ELSE 0 END) AS encrypted_email_rows,
                        SUM(CASE WHEN google_subject IS NULL OR google_subject LIKE 'enc::%' THEN 1 ELSE 0 END)
                            AS encrypted_google_subject_rows,
                        SUM(CASE
                            WHEN password_hash LIKE 'pbkdf2_%'
                              OR password_hash LIKE 'argon2%'
                              OR password_hash LIKE '$2%'
                            THEN 1 ELSE 0
                        END) AS hashed_password_rows
                    FROM users
                    """
                )
            )
        ).mappings().one()
        job_count = (
            await connection.execute(text("SELECT COUNT(*) AS total_jobs FROM jobs"))
        ).mappings().one()
        job_security = (
            await connection.execute(
                text(
                    """
                    SELECT
                        SUM(CASE WHEN owner_email LIKE 'enc::%' THEN 1 ELSE 0 END) AS encrypted_owner_email_rows,
                        SUM(CASE WHEN invoice_path LIKE 'enc::%' THEN 1 ELSE 0 END) AS encrypted_invoice_path_rows,
                        SUM(CASE WHEN bill_of_lading_path LIKE 'enc::%' THEN 1 ELSE 0 END) AS encrypted_bill_path_rows,
                        SUM(CASE WHEN report_path IS NULL OR report_path LIKE 'enc::%' THEN 1 ELSE 0 END) AS encrypted_report_path_rows,
                        SUM(CASE WHEN results IS NULL OR results LIKE 'enc::%' THEN 1 ELSE 0 END) AS encrypted_results_rows
                    FROM jobs
                    """
                )
            )
        ).mappings().one()
        user_rows = (
            await connection.execute(
                text(
                    """
                    SELECT id, email, google_subject, password_hash, is_active, created_at
                    FROM users
                    ORDER BY created_at DESC
                    LIMIT 5
                    """
                )
            )
        ).mappings().all()
        job_rows = (
            await connection.execute(
                text(
                    """
                    SELECT
                        id,
                        status,
                        owner_email,
                        invoice_path,
                        bill_of_lading_path,
                        report_path,
                        results,
                        created_at
                    FROM jobs
                    ORDER BY created_at DESC
                    LIMIT 5
                    """
                )
            )
        ).mappings().all()

    return {
        "encryption_prefix": ENCRYPTION_PREFIX,
        "user_summary": {
            "total_users": int(user_count["total_users"] or 0),
            "encrypted_email_rows": int(user_security["encrypted_email_rows"] or 0),
            "encrypted_google_subject_rows": int(user_security["encrypted_google_subject_rows"] or 0),
            "hashed_password_rows": int(user_security["hashed_password_rows"] or 0),
        },
        "job_summary": {
            "total_jobs": int(job_count["total_jobs"] or 0),
            "encrypted_owner_email_rows": int(job_security["encrypted_owner_email_rows"] or 0),
            "encrypted_invoice_path_rows": int(job_security["encrypted_invoice_path_rows"] or 0),
            "encrypted_bill_path_rows": int(job_security["encrypted_bill_path_rows"] or 0),
            "encrypted_report_path_rows": int(job_security["encrypted_report_path_rows"] or 0),
            "encrypted_results_rows": int(job_security["encrypted_results_rows"] or 0),
        },
        "user_samples": [
            {
                "id": row["id"],
                "email_prefix": _prefix(row["email"]),
                "email_encrypted": _is_encrypted(row["email"]),
                "google_subject_prefix": _prefix(row["google_subject"]),
                "google_subject_encrypted": row["google_subject"] is None or _is_encrypted(row["google_subject"]),
                "password_hash_prefix": _prefix(row["password_hash"]),
                "password_hashed": _is_password_hash(row["password_hash"]),
                "is_active": bool(row["is_active"]),
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            }
            for row in user_rows
        ],
        "job_samples": [
            {
                "id": row["id"],
                "status": row["status"],
                "owner_email_prefix": _prefix(row["owner_email"]),
                "owner_email_encrypted": _is_encrypted(row["owner_email"]),
                "invoice_path_prefix": _prefix(row["invoice_path"]),
                "invoice_path_encrypted": _is_encrypted(row["invoice_path"]),
                "bill_path_prefix": _prefix(row["bill_of_lading_path"]),
                "bill_path_encrypted": _is_encrypted(row["bill_of_lading_path"]),
                "report_path_prefix": _prefix(row["report_path"]),
                "report_path_encrypted": row["report_path"] is None or _is_encrypted(row["report_path"]),
                "results_prefix": _prefix(row["results"]),
                "results_encrypted": row["results"] is None or _is_encrypted(row["results"]),
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            }
            for row in job_rows
        ],
    }
