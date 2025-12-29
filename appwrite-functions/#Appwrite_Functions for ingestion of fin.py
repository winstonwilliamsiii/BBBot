#Appwrite_Functions for ingestion of financial data
import os
import json
import pymysql
from appwrite.client import Client
from appwrite.services.account import Account
from appwrite.services.databases import Databases

# ---- CONFIG ----
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

AGGREGATOR = os.getenv("AGGREGATOR", "plaid")  # plaid, cashpro, capitalone, capitalview

# ---- DB CONNECTION ----
def get_db():
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        ssl={"ssl": True}
    )

# ---- TOKEN LOADER ----
def load_access_token(user_id, tenant_id):
    # Replace with Appwrite DB lookup
    # tokens collection: { user_id, tenant_id, aggregator, access_token }
    return "ACCESS_TOKEN_FROM_DB"

# ---- AGGREGATOR ROUTER ----
def fetch_transactions(access_token):
    if AGGREGATOR == "plaid":
        from plaid import Client
        client = Client(
            client_id=os.getenv("PLAID_CLIENT_ID"),
            secret=os.getenv("PLAID_SECRET"),
            environment=os.getenv("PLAID_ENV", "sandbox")
        )
        resp = client.Transactions.get(access_token, start_date="2024-01-01", end_date="2025-12-31")
        return resp.get("transactions", [])

    elif AGGREGATOR == "cashpro":
        # TODO: integrate Bank of America CashPro API
        return []

    elif AGGREGATOR == "capitalone":
        # TODO: integrate Capital One DevExchange
        return []

    elif AGGREGATOR == "capitalview":
        # TODO: integrate CapitalView API
        return []

    return []

# ---- NORMALIZER ----
def normalize_transaction(tx, user_id, tenant_id):
    return {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "account_id": tx.get("account_id"),
        "amount": tx.get("amount"),
        "date": tx.get("date"),
        "merchant": tx.get("name"),
        "category": tx.get("category", ["uncategorized"])[0],
        "raw_json": json.dumps(tx)
    }

# ---- MAIN HANDLER ----
def main(req, res):
    try:
        body = json.loads(req.body)
        user_id = body["user_id"]
        tenant_id = body["tenant_id"]

        # Load token
        access_token = load_access_token(user_id, tenant_id)

        # Fetch data
        transactions = fetch_transactions(access_token)

        # Normalize
        normalized = [normalize_transaction(tx, user_id, tenant_id) for tx in transactions]

        # Insert into MySQL
        conn = get_db()
        cursor = conn.cursor()

        sql = """
        INSERT INTO transactions
        (tenant_id, user_id, account_id, amount, date, merchant, category, raw_json)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """

        for row in normalized:
            cursor.execute(sql, (
                row["tenant_id"], row["user_id"], row["account_id"],
                row["amount"], row["date"], row["merchant"],
                row["category"], row["raw_json"]
            ))

        conn.commit()
        cursor.close()
        conn.close()

        return res.json({
            "ok": True,
            "count": len(normalized),
            "aggregator": AGGREGATOR
        })

    except Exception as e:
        return res.json({"ok": False, "error": str(e)})