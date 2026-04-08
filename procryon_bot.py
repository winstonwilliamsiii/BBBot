from __future__ import annotations

import logging
import os
from dataclasses import asdict, dataclass
from typing import Any, Optional

import numpy as np
import requests
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

try:
    import mlflow
    from mlflow.tracking import MlflowClient

    MLFLOW_AVAILABLE = True
except ImportError:
    mlflow = None
    MlflowClient = None
    MLFLOW_AVAILABLE = False

try:
    from bbbot1_pipeline.mlflow_config import get_mlflow_tracking_uri
except ImportError:
    get_mlflow_tracking_uri = None

try:
    from frontend.components.mt5_connector import MT5Connector

    MT5_CONNECTOR_AVAILABLE = True
except ImportError:
    MT5Connector = None
    MT5_CONNECTOR_AVAILABLE = False


logger = logging.getLogger(__name__)


def _as_bool(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _as_int(value: Optional[str], default: int) -> int:
    try:
        return int(str(value).strip())
    except (AttributeError, TypeError, ValueError):
        return default


def _as_float(value: Optional[str], default: float) -> float:
    try:
        return float(str(value).strip())
    except (AttributeError, TypeError, ValueError):
        return default


def _clean_env_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    if "#" in text:
        prefix, suffix = text.split("#", 1)
        if suffix.strip() and (" " in suffix or "\t" in suffix):
            text = prefix.strip()

    return text or None


@dataclass
class ProcryonConfig:
    n_neighbors: int = 3
    spread_feature_count: int = 3
    execution_feature_count: int = 5
    execution_threshold: float = 0.55
    fastapi_base_url: str = "http://127.0.0.1:5001"
    mt5_api_url: str = "http://localhost:8002"
    mlflow_experiment: str = "Procryon_MT5_Arbitrage"
    trading_platform: str = "MT5"
    preferred_brokers: tuple[str, ...] = ("ftmo", "axi")
    objective: str = (
        "Cluster spread regimes with KNN and optimize execution decisions "
        "with a feed-forward neural network for MT5-connected FTMO and AXI "
        "accounts."
    )

    @classmethod
    def from_env(cls) -> "ProcryonConfig":
        return cls(
            n_neighbors=_as_int(os.getenv("PROCRYON_KNN_NEIGHBORS"), 3),
            spread_feature_count=_as_int(
                os.getenv("PROCRYON_SPREAD_FEATURE_COUNT"),
                3,
            ),
            execution_feature_count=_as_int(
                os.getenv("PROCRYON_EXECUTION_FEATURE_COUNT"),
                5,
            ),
            execution_threshold=_as_float(
                os.getenv("PROCRYON_EXECUTION_THRESHOLD"),
                0.55,
            ),
            fastapi_base_url=(
                _clean_env_text(os.getenv("PROCRYON_FASTAPI_URL"))
                or _clean_env_text(os.getenv("FASTAPI_BASE_URL"))
                or "http://127.0.0.1:5001"
            ),
            mt5_api_url=(
                _clean_env_text(os.getenv("MT5_API_URL"))
                or "http://localhost:8002"
            ),
            mlflow_experiment=_clean_env_text(os.getenv(
                "PROCRYON_MLFLOW_EXPERIMENT",
                "Procryon_MT5_Arbitrage",
            )) or "Procryon_MT5_Arbitrage",
            trading_platform=(
                _clean_env_text(os.getenv("PROCRYON_TRADING_PLATFORM"))
                or "MT5"
            ),
            preferred_brokers=("ftmo", "axi"),
            objective=_clean_env_text(os.getenv(
                "PROCRYON_OBJECTIVE",
                (
                    "Cluster spread regimes with KNN and optimize execution "
                    "decisions with a feed-forward neural network for "
                    "MT5-connected FTMO and AXI accounts."
                ),
            )) or (
                "Cluster spread regimes with KNN and optimize execution "
                "decisions with a feed-forward neural network for "
                "MT5-connected FTMO and AXI accounts."
            ),
        )


class ProcryonBot:
    def __init__(self, config: Optional[ProcryonConfig] = None):
        self.config = config or ProcryonConfig.from_env()
        self.spread_data: list[list[float]] = []
        self.spread_labels: list[int] = []
        self.execution_data: list[list[float]] = []
        self.execution_labels: list[int] = []
        self.knn: Optional[KNeighborsClassifier] = None
        self.execution_scaler = StandardScaler()
        self.fnn: Optional[MLPClassifier] = None
        self.last_training_metrics: dict[str, float] = {}

    def _validate_vector(
        self,
        values: list[float],
        expected_size: int,
        label: str,
    ) -> list[float]:
        if len(values) != expected_size:
            raise ValueError(
                f"{label} must contain {expected_size} values; "
                f"got {len(values)}"
            )
        return [float(item) for item in values]

    def ingest_spread(self, spread_vector: list[float], label: int) -> None:
        spread = self._validate_vector(
            spread_vector,
            self.config.spread_feature_count,
            "spread_vector",
        )
        self.spread_data.append(spread)
        self.spread_labels.append(int(label))

    def ingest_execution_features(
        self,
        features: list[float],
        label: int,
    ) -> None:
        execution_features = self._validate_vector(
            features,
            self.config.execution_feature_count,
            "execution_features",
        )
        self.execution_data.append(execution_features)
        self.execution_labels.append(int(label))

    def bootstrap_demo_models(self) -> dict[str, float]:
        if self.spread_data or self.execution_data:
            return self.train_all(log_to_mlflow=False)

        spread_samples = [
            ([0.0008, 0.0005, 0.0011], 0),
            ([0.0012, 0.0009, 0.0015], 0),
            ([0.0035, 0.0028, 0.0042], 1),
            ([0.0041, 0.0032, 0.0048], 1),
            ([0.0060, 0.0055, 0.0068], 1),
            ([0.0010, 0.0007, 0.0013], 0),
        ]
        execution_samples = [
            ([35, 0.90, 6, 2, 0.80], 1),
            ([80, 0.45, 14, 7, 0.30], 0),
            ([42, 0.75, 8, 3, 0.72], 1),
            ([120, 0.35, 18, 9, 0.20], 0),
            ([28, 0.88, 5, 2, 0.85], 1),
            ([95, 0.40, 16, 8, 0.25], 0),
        ]

        for spread_vector, label in spread_samples:
            self.ingest_spread(spread_vector, label)

        for features, label in execution_samples:
            self.ingest_execution_features(features, label)

        return self.train_all(log_to_mlflow=False)

    def train_knn(self) -> dict[str, float]:
        if len(self.spread_data) < 2:
            raise RuntimeError(
                "At least two spread samples are required to train KNN"
            )

        x_train = np.array(self.spread_data, dtype=float)
        y_train = np.array(self.spread_labels, dtype=int)
        neighbors = max(1, min(self.config.n_neighbors, len(x_train)))

        self.knn = KNeighborsClassifier(n_neighbors=neighbors)
        self.knn.fit(x_train, y_train)

        metrics = {
            "knn_train_accuracy": float(self.knn.score(x_train, y_train)),
            "knn_samples": float(len(x_train)),
        }
        self.last_training_metrics.update(metrics)
        return metrics

    def train_fnn(
        self,
        x_train: Optional[list[list[float]]] = None,
        y_train: Optional[list[int]] = None,
        epochs: int = 10,
    ) -> dict[str, float]:
        features = x_train or self.execution_data
        labels = y_train or self.execution_labels

        if len(features) < 4:
            raise RuntimeError(
                "At least four execution samples are required to train the FNN"
            )

        if len(set(int(label) for label in labels)) < 2:
            raise RuntimeError(
                "Execution labels must contain at least two classes"
            )

        execution_matrix = np.array(features, dtype=float)
        execution_labels = np.array(labels, dtype=int)
        scaled = self.execution_scaler.fit_transform(execution_matrix)

        self.fnn = MLPClassifier(
            hidden_layer_sizes=(32, 16),
            activation="relu",
            max_iter=max(250, epochs * 40),
            random_state=42,
        )
        self.fnn.fit(scaled, execution_labels)

        metrics = {
            "fnn_train_accuracy": float(
                self.fnn.score(scaled, execution_labels)
            ),
            "fnn_samples": float(len(execution_matrix)),
        }
        self.last_training_metrics.update(metrics)
        return metrics

    def train_all(self, log_to_mlflow: bool = True) -> dict[str, float]:
        metrics = {}
        metrics.update(self.train_knn())
        metrics.update(self.train_fnn())
        if log_to_mlflow:
            self.log_training_run(metrics)
        return metrics

    def classify_spread(self, spread_vector: list[float]) -> int:
        if self.knn is None:
            raise RuntimeError("KNN model has not been trained")
        spread = self._validate_vector(
            spread_vector,
            self.config.spread_feature_count,
            "spread_vector",
        )
        return int(self.knn.predict([spread])[0])

    def execution_probability(self, features: list[float]) -> float:
        if self.fnn is None:
            raise RuntimeError("Execution model has not been trained")
        execution_features = self._validate_vector(
            features,
            self.config.execution_feature_count,
            "execution_features",
        )
        scaled = self.execution_scaler.transform([execution_features])
        probabilities = self.fnn.predict_proba(scaled)
        return float(probabilities[0][1])

    def decide_execution(self, features: list[float]) -> bool:
        return (
            self.execution_probability(features)
            >= self.config.execution_threshold
        )

    def evaluate_opportunity(
        self,
        spread_vector: list[float],
        execution_features: list[float],
    ) -> dict[str, Any]:
        cluster = self.classify_spread(spread_vector)
        probability = self.execution_probability(execution_features)
        execute = probability >= self.config.execution_threshold
        average_spread_bps = float(
            np.mean(np.abs(np.array(spread_vector, dtype=float))) * 10000
        )
        return {
            "cluster": cluster,
            "execution_probability": probability,
            "execute": execute,
            "average_spread_bps": average_spread_bps,
            "objective": self.config.objective,
            "platform": self.config.trading_platform,
            "preferred_brokers": list(self.config.preferred_brokers),
        }

    def configure(self, overrides: dict[str, Any]) -> dict[str, Any]:
        updated = {}
        for key, value in overrides.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                updated[key] = value
        return {
            "updated": updated,
            "config": asdict(self.config),
        }

    def _dependency_status(self) -> dict[str, bool]:
        return {
            "numpy": True,
            "sklearn": True,
            "mlflow": MLFLOW_AVAILABLE,
            "mt5_connector": MT5_CONNECTOR_AVAILABLE,
        }

    def _resolve_mt5_credentials(self, broker_name: str) -> dict[str, Any]:
        prefix = broker_name.upper()
        api_url = (
            _clean_env_text(os.getenv(f"{prefix}_MT5_API_URL"))
            or _clean_env_text(os.getenv("MT5_API_URL"))
            or self.config.mt5_api_url
        )
        user = (
            _clean_env_text(os.getenv(f"{prefix}_MT5_USER"))
            or _clean_env_text(os.getenv("MT5_USER"))
            or _clean_env_text(os.getenv("MT5_LOGIN"))
        )
        password = (
            _clean_env_text(os.getenv(f"{prefix}_MT5_PASSWORD"))
            or _clean_env_text(os.getenv("MT5_PASSWORD"))
        )
        host = (
            _clean_env_text(os.getenv(f"{prefix}_MT5_SERVER"))
            or _clean_env_text(os.getenv(f"{prefix}_MT5_HOST"))
            or _clean_env_text(os.getenv("MT5_SERVER"))
            or _clean_env_text(os.getenv("MT5_HOST"))
        )
        port = _as_int(
            _clean_env_text(os.getenv(f"{prefix}_MT5_PORT"))
            or _clean_env_text(os.getenv("MT5_PORT")),
            443,
        )
        missing = [
            name
            for name, value in {
                "user": user,
                "password": password,
                "host": host,
            }.items()
            if not value
        ]
        return {
            "api_url": api_url,
            "user": user,
            "password": password,
            "host": host,
            "port": port,
            "missing": missing,
        }

    def check_fastapi(self) -> dict[str, Any]:
        base_url = self.config.fastapi_base_url.rstrip("/")
        last_error = "No health endpoint responded"
        for path in ("/healthz", "/health"):
            url = f"{base_url}{path}"
            try:
                response = requests.get(url, timeout=2)
                if response.ok:
                    return {
                        "reachable": True,
                        "url": url,
                        "status_code": response.status_code,
                    }
            except requests.RequestException as exc:
                last_error = str(exc)
        return {
            "reachable": False,
            "url": base_url,
            "error": last_error,
        }

    def current_fastapi_status(self) -> dict[str, Any]:
        return {
            "reachable": True,
            "url": self.config.fastapi_base_url.rstrip("/"),
            "detail": "In-process FastAPI status assumed healthy",
        }

    def check_mlflow(self) -> dict[str, Any]:
        if not MLFLOW_AVAILABLE or get_mlflow_tracking_uri is None:
            return {
                "reachable": False,
                "reason": "mlflow support is not installed",
            }

        tracking_uri = get_mlflow_tracking_uri()
        try:
            mlflow.set_tracking_uri(tracking_uri)
            if (
                tracking_uri.startswith("http://")
                or tracking_uri.startswith("https://")
            ):
                response = requests.get(
                    f"{tracking_uri.rstrip('/')}/health",
                    timeout=3,
                )
                response.raise_for_status()
            client = MlflowClient()
            experiments = client.search_experiments(max_results=5)
            return {
                "reachable": True,
                "tracking_uri": tracking_uri,
                "experiment_count": len(experiments),
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "reachable": False,
                "tracking_uri": tracking_uri,
                "error": str(exc),
            }

    def check_brokers(self, attempt_login: bool = False) -> dict[str, Any]:
        results: dict[str, Any] = {}
        if not MT5_CONNECTOR_AVAILABLE or MT5Connector is None:
            for broker_name in self.config.preferred_brokers:
                results[broker_name] = {
                    "platform": "MT5",
                    "health": False,
                    "connected": False,
                    "reason": "MT5 connector not available",
                }
            return results

        for broker_name in self.config.preferred_brokers:
            credentials = self._resolve_mt5_credentials(broker_name)
            connector = MT5Connector(credentials["api_url"])
            connector.request_timeout = min(connector.request_timeout, 2.0)
            connector.connect_retries = 1
            connector.connect_retry_delay = 0.0
            health = connector.health_check()
            connected = False
            account_info = None

            if attempt_login and health and not credentials["missing"]:
                connected = bool(
                    connector.connect(
                        credentials["user"],
                        credentials["password"],
                        credentials["host"],
                        credentials["port"],
                    )
                )
                if connected:
                    account_info = connector.get_account_info()
                    connector.disconnect()

            results[broker_name] = {
                "platform": "MT5",
                "api_url": credentials["api_url"],
                "health": health,
                "connected": connected,
                "missing_credentials": credentials["missing"],
                "account_info": account_info,
            }

        return results

    def health_snapshot(
        self,
        attempt_broker_login: bool = False,
        probe_fastapi: bool = True,
    ) -> dict[str, Any]:
        return {
            "name": "Procryon",
            "objective": self.config.objective,
            "platform": self.config.trading_platform,
            "models_ready": self.knn is not None and self.fnn is not None,
            "training_metrics": self.last_training_metrics,
            "dependencies": self._dependency_status(),
            "fastapi": (
                self.check_fastapi()
                if probe_fastapi
                else self.current_fastapi_status()
            ),
            "mlflow": self.check_mlflow(),
            "brokers": self.check_brokers(attempt_login=attempt_broker_login),
        }

    def status(self) -> dict[str, Any]:
        return {
            "id": 5,
            "name": "Procryon",
            "strategy": "MT5 Spread Arbitrage",
            "objective": self.config.objective,
            "models_ready": self.knn is not None and self.fnn is not None,
            "preferred_brokers": list(self.config.preferred_brokers),
            "platform": self.config.trading_platform,
        }

    def log_training_run(self, metrics: dict[str, float]) -> dict[str, Any]:
        if not MLFLOW_AVAILABLE or get_mlflow_tracking_uri is None:
            return {"logged": False, "reason": "mlflow unavailable"}

        tracking_uri = get_mlflow_tracking_uri()
        try:
            mlflow.set_tracking_uri(tracking_uri)
            mlflow.set_experiment(self.config.mlflow_experiment)
            with mlflow.start_run(run_name="procryon_training"):
                mlflow.log_param("platform", self.config.trading_platform)
                mlflow.log_param(
                    "preferred_brokers",
                    ",".join(self.config.preferred_brokers),
                )
                mlflow.log_param(
                    "spread_feature_count",
                    self.config.spread_feature_count,
                )
                mlflow.log_param(
                    "execution_feature_count",
                    self.config.execution_feature_count,
                )
                for key, value in metrics.items():
                    mlflow.log_metric(key, float(value))
            return {"logged": True, "tracking_uri": tracking_uri}
        except Exception as exc:  # noqa: BLE001
            logger.warning("Procryon MLflow logging failed: %s", exc)
            return {
                "logged": False,
                "tracking_uri": tracking_uri,
                "error": str(exc),
            }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bot = ProcryonBot()
    bot.bootstrap_demo_models()
    print(bot.status())
    print(
        bot.evaluate_opportunity(
            [0.0036, 0.0029, 0.0041],
            [30, 0.85, 6, 2, 0.78],
        )
    )
