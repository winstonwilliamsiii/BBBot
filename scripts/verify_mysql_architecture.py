#!/usr/bin/env python3
"""Verify and snapshot MySQL database architecture for BentleyBudgetBot.

Usage examples:
  python scripts/verify_mysql_architecture.py
  python scripts/verify_mysql_architecture.py --port 3307 --output data/mysql_schema_snapshot.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import pymysql

DEFAULT_DATABASES = [
    "bbbot1",
    "mansa_bot",
    "mlflow_db",
    "mansa_quant",
    "Bentley_Budget",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify MySQL schema architecture")
    parser.add_argument("--host", default=os.getenv("MYSQL_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MYSQL_PORT", "3306")))
    parser.add_argument("--user", default=os.getenv("MYSQL_USER", "root"))
    parser.add_argument("--password", default=os.getenv("MYSQL_PASSWORD", "root"))
    parser.add_argument(
        "--databases",
        nargs="*",
        default=DEFAULT_DATABASES,
        help="Databases expected to exist",
    )
    parser.add_argument(
        "--output",
        default="data/mysql_schema_snapshot.json",
        help="JSON output file for schema snapshot",
    )
    return parser.parse_args()


def fetch_tables(cur: pymysql.cursors.Cursor, db_name: str) -> list[str]:
    cur.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
        ORDER BY table_name
        """,
        (db_name,),
    )
    return [row[0] for row in cur.fetchall()]


def fetch_columns(cur: pymysql.cursors.Cursor, db_name: str, table_name: str) -> list[dict[str, str]]:
    cur.execute(
        """
        SELECT column_name, column_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
        """,
        (db_name, table_name),
    )
    return [
        {
            "name": row[0],
            "type": row[1],
            "nullable": row[2],
            "default": "" if row[3] is None else str(row[3]),
        }
        for row in cur.fetchall()
    ]


def main() -> int:
    args = parse_args()

    try:
        conn = pymysql.connect(
            host=args.host,
            port=args.port,
            user=args.user,
            password=args.password,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.Cursor,
        )
    except Exception as exc:
        print(f"ERROR: MySQL connection failed: {exc}")
        return 2

    snapshot: dict[str, object] = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "connection": {
            "host": args.host,
            "port": args.port,
            "user": args.user,
        },
        "expected_databases": args.databases,
        "missing_databases": [],
        "databases": {},
    }

    with conn:
        with conn.cursor() as cur:
            cur.execute("SHOW DATABASES")
            existing_databases_raw = [row[0] for row in cur.fetchall()]
            existing_databases = {name.lower(): name for name in existing_databases_raw}

            missing = [db for db in args.databases if db.lower() not in existing_databases]
            snapshot["missing_databases"] = missing

            for db_name in args.databases:
                lookup_name = existing_databases.get(db_name.lower())
                if lookup_name is None:
                    continue

                table_names = fetch_tables(cur, lookup_name)
                db_info: dict[str, object] = {
                    "resolved_name": lookup_name,
                    "table_count": len(table_names),
                    "tables": {},
                }

                for table_name in table_names:
                    db_info["tables"][table_name] = {
                        "columns": fetch_columns(cur, lookup_name, table_name)
                    }

                snapshot["databases"][db_name] = db_info

    output_path = args.output
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(snapshot, fh, indent=2)

    print("MySQL architecture verification complete.")
    print(f"Snapshot saved: {output_path}")

    missing_databases = snapshot.get("missing_databases", [])
    if missing_databases:
        print("Missing databases:")
        for name in missing_databases:
            print(f"  - {name}")
        return 1

    print("All expected databases are present.")
    for db_name, db_info in snapshot["databases"].items():
        table_count = db_info.get("table_count", 0)
        print(f"  - {db_name}: {table_count} table(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
