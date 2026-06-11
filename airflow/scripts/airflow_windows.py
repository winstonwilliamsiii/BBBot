"""Windows-compatible Airflow configuration and wrapper."""

from pathlib import Path
import os
import sys
import warnings


REPO_ROOT = Path(__file__).resolve().parents[2]
AIRFLOW_HOME = REPO_ROOT / "airflow_config"
AIRFLOW_DAGS = REPO_ROOT / "airflow" / "dags"
DEFAULT_SQL_CONN = "mysql+pymysql://root:root@127.0.0.1:3307/mansa_bot"


if not hasattr(os, "register_at_fork"):

    def register_at_fork(*_args, **_kwargs):
        """Dummy implementation for Windows."""
        return None

    os.register_at_fork = register_at_fork
    print("Applied Windows compatibility patch for os.register_at_fork")


os.environ.setdefault("AIRFLOW__CORE__MP_START_METHOD", "spawn")
os.environ.setdefault("AIRFLOW__CORE__EXECUTOR", "LocalExecutor")
os.environ.setdefault("AIRFLOW__CORE__LOAD_EXAMPLES", "False")
os.environ.setdefault("AIRFLOW_HOME", str(AIRFLOW_HOME))
os.environ.setdefault("AIRFLOW__CORE__DAGS_FOLDER", str(AIRFLOW_DAGS))
os.environ.setdefault("AIRFLOW__DATABASE__SQL_ALCHEMY_CONN", DEFAULT_SQL_CONN)
os.environ.setdefault("AIRFLOW__CORE__SQL_ALCHEMY_CONN", DEFAULT_SQL_CONN)

warnings.filterwarnings("ignore", message=".*can be run on POSIX-compliant.*")


def get_sql_alchemy_conn() -> str:
    """Resolve the configured SQLAlchemy connection string."""
    from airflow.configuration import conf

    return conf.get(
        "database",
        "sql_alchemy_conn",
        fallback=conf.get("core", "sql_alchemy_conn", fallback=DEFAULT_SQL_CONN),
    )


def print_airflow_status() -> bool:
    """Import Airflow and print the effective runtime configuration."""
    try:
        import airflow
        from airflow.configuration import conf

        mp_method = conf.get("core", "mp_start_method", fallback="fork")
        executor = conf.get("core", "executor", fallback="SequentialExecutor")
        sql_conn = get_sql_alchemy_conn()

        print(
            f"✅ Airflow {airflow.__version__} loaded successfully "
            "with Windows compatibility"
        )
        print(f"📋 Configuration: MP Method={mp_method}, Executor={executor}")
        print(f"🗄️ SQL Connection: {sql_conn}")
        return True
    except Exception as exc:
        print(f"❌ Error loading Airflow: {exc}")
        return False


def test_mysql_connection() -> bool:
    """Test MySQL connection before initializing Airflow."""
    try:
        sql_conn = get_sql_alchemy_conn()

        if "mysql" not in sql_conn:
            print("🔍 Using non-MySQL database, skipping connection test")
            return True

        import pymysql
        from urllib.parse import urlparse

        parsed = urlparse(sql_conn.replace("mysql+pymysql://", "mysql://"))
        connection = pymysql.connect(
            host=parsed.hostname,
            port=parsed.port or 3306,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip("/"),
            charset="utf8mb4",
        )

        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ MySQL connection successful: {version[0]}")

        connection.close()
        return True
    except Exception as exc:
        print(f"❌ MySQL connection failed: {exc}")
        print("💡 Make sure Docker MySQL is running on 127.0.0.1:3307")
        return False


def init_airflow_db() -> None:
    """Initialize Airflow database safely."""
    try:
        if not test_mysql_connection():
            print("❌ Database connection test failed. Cannot initialize.")
            return

        from airflow.utils.db import initdb

        initdb()
        print("✅ Airflow database initialized successfully")
    except Exception as exc:
        print(f"❌ Database initialization failed: {exc}")


def start_webserver() -> None:
    """Start the Airflow webserver with Windows-safe settings."""
    try:
        from airflow.cli.commands.webserver_command import webserver

        print("🌐 Starting Airflow webserver on http://localhost:8080")
        webserver(["-p", "8080"])
    except Exception as exc:
        print(f"❌ Webserver start failed: {exc}")


def start_scheduler() -> None:
    """Start the Airflow scheduler with Windows-safe settings."""
    try:
        from airflow.cli.commands.scheduler_command import scheduler

        print("⏱️ Starting Airflow scheduler")
        scheduler([])
    except Exception as exc:
        print(f"❌ Scheduler start failed: {exc}")


def list_airflow_config() -> None:
    """List Airflow configuration safely."""
    try:
        from airflow.configuration import conf

        print("\n📋 Current Airflow Configuration:")
        for section in conf.sections():
            print(f"[{section}]")
            for key, value in conf.items(section):
                print(f"  {key} = {value}")
            print()
    except Exception as exc:
        print(f"❌ Config listing failed: {exc}")


if __name__ == "__main__":
    if not print_airflow_status():
        sys.exit(1)

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "init":
            init_airflow_db()
        elif command == "config":
            list_airflow_config()
        elif command == "test":
            test_mysql_connection()
        elif command == "webserver":
            start_webserver()
        elif command == "scheduler":
            start_scheduler()
        else:
            print(
                "Available commands: init, config, test, webserver, scheduler"
            )
    else:
        print("Airflow Windows compatibility wrapper loaded.")
        print(
            "Usage: python airflow_windows.py "
            "[init|config|test|webserver|scheduler]"
        )