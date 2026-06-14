"""
One-command Plaid sync/export/load utility.

Usage:
  python scripts/plaid_sync_export_load.py --access-token <access_token>

Optional:
  --output-dir data/plaid
  --db-host 127.0.0.1 --db-port 3306 --db-user root --db-password root --db-name mydb

Environment fallbacks:
  PLAID_CLIENT_ID, PLAID_SECRET
  BUDGET_MYSQL_HOST/BUDGET_MYSQL_PORT/BUDGET_MYSQL_USER/BUDGET_MYSQL_PASSWORD/BUDGET_MYSQL_DATABASE
  MYSQL_HOST/MYSQL_PORT/MYSQL_USER/MYSQL_PASSWORD/MYSQL_DATABASE
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid.api_client import ApiClient
from plaid.configuration import Configuration
from plaid.model.transactions_sync_request import TransactionsSyncRequest

import mysql.connector


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plaid sync -> JSON export -> MySQL load")
    parser.add_argument("--access-token", required=True, help="Plaid access token")
    parser.add_argument("--output-dir", default="data/plaid", help="Directory for JSON artifacts")

    parser.add_argument("--db-host", default=None)
    parser.add_argument("--db-port", type=int, default=None)
    parser.add_argument("--db-user", default=None)
    parser.add_argument("--db-password", default=None)
    parser.add_argument("--db-name", default=None)

    parser.add_argument(
        "--docker-container",
        default=None,
        help="MySQL Docker container name (enables docker-native load mode)",
    )
    parser.add_argument(
        "--docker-mysql-user",
        default="root",
        help="MySQL user used inside Docker container",
    )
    parser.add_argument(
        "--docker-mysql-password",
        default="root",
        help="MySQL password used inside Docker container",
    )

    return parser.parse_args()


def env_first(*keys: str, default: str | None = None) -> str | None:
    for key in keys:
        value = os.getenv(key)
        if value:
            return value
    return default


def get_db_config(args: argparse.Namespace) -> dict[str, Any]:
    host = args.db_host or env_first("BUDGET_MYSQL_HOST", "MYSQL_HOST", default="127.0.0.1")
    port_value = args.db_port or env_first(
        "BUDGET_MYSQL_PORT",
        "MYSQL_PORT",
        default="3306",
    )
    port = int(str(port_value))
    user = args.db_user or env_first("BUDGET_MYSQL_USER", "MYSQL_USER", default="root")
    password = args.db_password or env_first("BUDGET_MYSQL_PASSWORD", "MYSQL_PASSWORD", default="root")
    database = args.db_name or env_first("BUDGET_MYSQL_DATABASE", "MYSQL_DATABASE", default="mydb")

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database": database,
    }


def build_plaid_client() -> plaid_api.PlaidApi:
    client_id = os.getenv("PLAID_CLIENT_ID", "").strip()
    secret = os.getenv("PLAID_SECRET", "").strip()

    if not client_id or not secret:
        raise RuntimeError("Missing PLAID_CLIENT_ID/PLAID_SECRET in environment")

    configuration = Configuration(
        host="https://sandbox.plaid.com",
        api_key={"clientId": client_id, "secret": secret},
    )
    return plaid_api.PlaidApi(ApiClient(configuration))


def sync_all_transactions(client: plaid_api.PlaidApi, access_token: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], str]:
    cursor = ""
    has_more = True
    added: list[dict[str, Any]] = []
    modified: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []

    while has_more:
        request = TransactionsSyncRequest(
            access_token=access_token,
            cursor=cursor,
            count=100,
        )
        response = client.transactions_sync(request)
        added.extend(response.get("added", []))
        modified.extend(response.get("modified", []))
        removed.extend(response.get("removed", []))
        has_more = bool(response.get("has_more", False))
        cursor = response.get("next_cursor") or ""

    return added, modified, removed, cursor


def export_json(output_dir: Path, access_token: str, added: list[dict[str, Any]], modified: list[dict[str, Any]], removed: list[dict[str, Any]], next_cursor: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"transactions_sync_{ts}.json"

    payload = {
        "generated_at": dt.datetime.now().isoformat(),
        "source": "plaid_transactions_sync",
        "access_token_suffix": access_token[-8:],
        "counts": {
            "added": len(added),
            "modified": len(modified),
            "removed": len(removed),
        },
        "next_cursor": next_cursor,
        "added": added,
        "modified": modified,
        "removed": removed,
    }

    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return json_path


def ensure_db_objects(conn: Any, database: str) -> None:
    with conn.cursor() as cursor:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}`")
        cursor.execute(f"USE `{database}`")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS plaid_transactions (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                transaction_id VARCHAR(128) UNIQUE,
                account_id VARCHAR(128),
                amount DECIMAL(14,2),
                iso_currency_code VARCHAR(16),
                unofficial_currency_code VARCHAR(16),
                category_primary VARCHAR(128),
                category_detailed VARCHAR(128),
                name VARCHAR(255),
                merchant_name VARCHAR(255),
                payment_channel VARCHAR(64),
                authorized_date DATE NULL,
                posted_date DATE NULL,
                pending BOOLEAN,
                raw_json JSON,
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
            """
        )
    conn.commit()


def load_transactions(
    conn: Any,
    database: str,
    rows: list[dict[str, Any]],
) -> tuple[int, int]:
    insert_sql = (
        "INSERT INTO plaid_transactions "
        "(transaction_id, account_id, amount, iso_currency_code, unofficial_currency_code, "
        "category_primary, category_detailed, name, merchant_name, payment_channel, "
        "authorized_date, posted_date, pending, raw_json) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
        "ON DUPLICATE KEY UPDATE "
        "amount=VALUES(amount), pending=VALUES(pending), posted_date=VALUES(posted_date), raw_json=VALUES(raw_json)"
    )

    values: list[tuple[Any, ...]] = []
    for item in rows:
        transaction_id = item.get("transaction_id")
        if not transaction_id:
            continue

        pfc = item.get("personal_finance_category") or {}
        values.append(
            (
                transaction_id,
                item.get("account_id"),
                item.get("amount") if item.get("amount") is not None else 0,
                item.get("iso_currency_code"),
                item.get("unofficial_currency_code"),
                pfc.get("primary"),
                pfc.get("detailed"),
                item.get("name"),
                item.get("merchant_name"),
                item.get("payment_channel"),
                item.get("authorized_date"),
                item.get("date"),
                1 if item.get("pending") else 0,
                json.dumps(item, default=str),
            )
        )

    with conn.cursor() as cursor:
        cursor.execute(f"USE `{database}`")
        cursor.executemany(insert_sql, values)
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM plaid_transactions")
        count_row = cursor.fetchone()
        total_rows = int(count_row[0]) if count_row else 0

    return len(values), total_rows


def _sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)

    text = str(value)
    text = text.replace("\\", "\\\\").replace("'", "''")
    return f"'{text}'"


def load_transactions_via_docker(
    args: argparse.Namespace,
    database: str,
    rows: list[dict[str, Any]],
) -> tuple[int, int]:
    if not args.docker_container:
        raise RuntimeError("Docker container name is required for Docker load mode")

    sql_lines = [
        f"CREATE DATABASE IF NOT EXISTS `{database}`;",
        f"USE `{database}`;",
        """
        CREATE TABLE IF NOT EXISTS plaid_transactions (
            id BIGINT PRIMARY KEY AUTO_INCREMENT,
            transaction_id VARCHAR(128) UNIQUE,
            account_id VARCHAR(128),
            amount DECIMAL(14,2),
            iso_currency_code VARCHAR(16),
            unofficial_currency_code VARCHAR(16),
            category_primary VARCHAR(128),
            category_detailed VARCHAR(128),
            name VARCHAR(255),
            merchant_name VARCHAR(255),
            payment_channel VARCHAR(64),
            authorized_date DATE NULL,
            posted_date DATE NULL,
            pending BOOLEAN,
            raw_json JSON,
            loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
        """,
    ]

    upserted = 0
    for item in rows:
        transaction_id = item.get("transaction_id")
        if not transaction_id:
            continue

        pfc = item.get("personal_finance_category") or {}
        values = [
            transaction_id,
            item.get("account_id"),
            item.get("amount") if item.get("amount") is not None else 0,
            item.get("iso_currency_code"),
            item.get("unofficial_currency_code"),
            pfc.get("primary"),
            pfc.get("detailed"),
            item.get("name"),
            item.get("merchant_name"),
            item.get("payment_channel"),
            item.get("authorized_date"),
            item.get("date"),
            1 if item.get("pending") else 0,
            json.dumps(item, default=str),
        ]
        literals = ", ".join(_sql_literal(v) for v in values)
        sql_lines.append(
            "INSERT INTO plaid_transactions "
            "(transaction_id, account_id, amount, iso_currency_code, "
            "unofficial_currency_code, category_primary, category_detailed, "
            "name, merchant_name, payment_channel, authorized_date, "
            "posted_date, pending, raw_json) "
            f"VALUES ({literals}) "
            "ON DUPLICATE KEY UPDATE "
            "amount=VALUES(amount), pending=VALUES(pending), "
            "posted_date=VALUES(posted_date), raw_json=VALUES(raw_json);"
        )
        upserted += 1

    sql_blob = "\n".join(sql_lines)
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".sql",
        encoding="utf-8",
        delete=False,
    ) as temp_sql:
        temp_sql.write(sql_blob)
        temp_sql_path = Path(temp_sql.name)

    container_sql_path = "/tmp/plaid_sync_load.sql"

    try:
        copy_cmd = [
            "docker",
            "cp",
            temp_sql_path.as_posix(),
            f"{args.docker_container}:{container_sql_path}",
        ]
        copy_result = subprocess.run(
            copy_cmd,
            text=True,
            capture_output=True,
            check=False,
        )
        if copy_result.returncode != 0:
            raise RuntimeError(
                "Docker SQL file copy failed: "
                + (copy_result.stderr.strip() or copy_result.stdout.strip())
            )

        import_shell = (
            f"mysql -u{args.docker_mysql_user} -p{args.docker_mysql_password} "
            f"< {container_sql_path}"
        )
        import_cmd = [
            "docker",
            "exec",
            args.docker_container,
            "sh",
            "-lc",
            import_shell,
        ]
        import_result = subprocess.run(
            import_cmd,
            text=True,
            capture_output=True,
            check=False,
        )
        if import_result.returncode != 0:
            raise RuntimeError(
                "Docker MySQL import failed: "
                + (import_result.stderr.strip() or import_result.stdout.strip())
            )
    finally:
        if temp_sql_path.exists():
            temp_sql_path.unlink()

        cleanup_cmd = [
            "docker",
            "exec",
            args.docker_container,
            "sh",
            "-lc",
            f"rm -f {container_sql_path}",
        ]
        subprocess.run(cleanup_cmd, text=True, capture_output=True, check=False)

    count_cmd = [
        "docker",
        "exec",
        args.docker_container,
        "sh",
        "-lc",
        (
            f"mysql -u{args.docker_mysql_user} -p{args.docker_mysql_password} "
            f"-N -B -e \"USE {database}; "
            "SELECT COUNT(*) FROM plaid_transactions;\""
        ),
    ]
    count_result = subprocess.run(
        count_cmd,
        text=True,
        capture_output=True,
        check=False,
    )
    if count_result.returncode != 0:
        raise RuntimeError(
            "Docker MySQL count query failed: "
            + (count_result.stderr.strip() or count_result.stdout.strip())
        )

    total_rows = int((count_result.stdout or "0").strip().splitlines()[-1])
    return upserted, total_rows


def main() -> None:
    load_dotenv(override=True)
    args = parse_args()

    client = build_plaid_client()
    added, modified, removed, next_cursor = sync_all_transactions(client, args.access_token)

    json_path = export_json(Path(args.output_dir), args.access_token, added, modified, removed, next_cursor)

    db_config = get_db_config(args)
    if args.docker_container:
        inserted_attempted, total_rows = load_transactions_via_docker(
            args,
            db_config["database"],
            added,
        )
    else:
        conn = mysql.connector.connect(
            host=db_config["host"],
            port=db_config["port"],
            user=db_config["user"],
            password=db_config["password"],
        )
        try:
            ensure_db_objects(conn, db_config["database"])
            inserted_attempted, total_rows = load_transactions(
                conn,
                db_config["database"],
                added,
            )
        finally:
            conn.close()

    print("SYNC_OK")
    print(f"added_count={len(added)} modified_count={len(modified)} removed_count={len(removed)}")
    print(f"json_path={json_path.as_posix()}")
    print(f"db_target={db_config['database']}.plaid_transactions")
    print(f"rows_upsert_attempted={inserted_attempted}")
    print(f"rows_current_total={total_rows}")


if __name__ == "__main__":
    main()
