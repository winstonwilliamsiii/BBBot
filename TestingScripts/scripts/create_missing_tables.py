"""Create mansa_bot.alerts_log and mansa_bot.portfolios tables if missing."""
import pymysql

conn = pymysql.connect(
    host="127.0.0.1", port=3307, user="root", password="root", database="mansa_bot"
)
cur = conn.cursor()

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS alerts_log (
        id          BIGINT AUTO_INCREMENT PRIMARY KEY,
        bot_name    VARCHAR(50)   NOT NULL,
        alert_type  VARCHAR(50)   NOT NULL,
        message     TEXT,
        payload     JSON,
        channel     VARCHAR(100),
        status      VARCHAR(20)   DEFAULT 'sent',
        created_at  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_bot_created (bot_name, created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """
)

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS portfolios (
        id              BIGINT AUTO_INCREMENT PRIMARY KEY,
        bot_name        VARCHAR(50)    NOT NULL,
        symbol          VARCHAR(20)    NOT NULL,
        allocation_pct  DECIMAL(8,4),
        fund_name       VARCHAR(100),
        active          TINYINT(1)     DEFAULT 1,
        created_at      TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
        updated_at      TIMESTAMP      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY uq_bot_symbol (bot_name, symbol),
        INDEX idx_bot_active (bot_name, active)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """
)

conn.commit()
print("Tables created OK.")

# Seed bot universes
rows = [
    ("Triton", "IYT",  12.5, "Mansa Transportation"),
    ("Triton", "UNP",  12.5, "Mansa Transportation"),
    ("Triton", "CSX",  12.5, "Mansa Transportation"),
    ("Triton", "NSC",  12.5, "Mansa Transportation"),
    ("Triton", "UPS",  12.5, "Mansa Transportation"),
    ("Triton", "FDX",  12.5, "Mansa Transportation"),
    ("Triton", "DAL",  12.5, "Mansa Transportation"),
    ("Triton", "UBER", 12.5, "Mansa Transportation"),
    ("Vega",   "KOF",  11.1, "Mansa_Retail"),
    ("Vega",   "SBH",  11.1, "Mansa_Retail"),
    ("Vega",   "WMT",  11.1, "Mansa_Retail"),
    ("Vega",   "FDX",  11.1, "Mansa_Retail"),
    ("Vega",   "W",    11.1, "Mansa_Retail"),
    ("Vega",   "LULU", 11.1, "Mansa_Retail"),
    ("Vega",   "DG",   11.1, "Mansa_Retail"),
    ("Vega",   "KO",   11.1, "Mansa_Retail"),
    ("Vega",   "PG",   11.1, "Mansa_Retail"),
]
cur.executemany(
    "INSERT IGNORE INTO portfolios (bot_name, symbol, allocation_pct, fund_name) VALUES (%s, %s, %s, %s)",
    rows,
)
conn.commit()
print(f"Seeded {len(rows)} portfolio rows (duplicates skipped).")
conn.close()
