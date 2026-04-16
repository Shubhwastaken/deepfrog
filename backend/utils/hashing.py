"""
File hashing for idempotency.

Computes a combined SHA-256 hash of both uploaded files (invoice + BOL).
If the same pair of files is submitted again, the hash matches and the
existing job is returned instead of creating a duplicate.
"""

import hashlib


def compute_file_hash(invoice_path: str, bol_path: str) -> str:
    """
    SHA-256 hash of both files combined.

    Reads files in 8KB chunks to handle large documents
    without loading everything into memory.
    """
    sha256 = hashlib.sha256()

    for path in [invoice_path, bol_path]:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                sha256.update(chunk)

    return sha256.hexdigest()
