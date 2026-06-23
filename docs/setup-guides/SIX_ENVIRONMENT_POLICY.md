# Six-Environment Policy

Bentley Budget Bot uses six canonical Python environments. The goal is to keep runtime services isolated while avoiding unlimited venv drift.

## Canonical Map

| Environment | Purpose | Canonical requirements file |
| --- | --- | --- |
| `.venv-streamlit` | Streamlit dashboard and data exploration | `docs/requirements/requirements-streamlit.txt` |
| `.venv-api` | FastAPI control center and local service API | `docs/requirements/requirements-api.txt` |
| `.venv-rhea` | Classical ML services and Altair | `docs/requirements/requirements-rhea.txt` |
| `.venv-bots` | Shared broker/runtime services for PyTorch-based bots | `docs/requirements/requirements-bots.txt` |
| `.venv-tf` | TensorFlow-based bot training and inference | `docs/requirements/requirements-tf.txt` |
| `.venv-dogon` | Dogon isolated training/runtime environment | `docs/requirements/requirements-dogon.txt` |

## Boundary Rules

- Keep local Python services in their own venvs.
- Keep Docker for infrastructure only: MySQL, Redis, MLflow, Airflow, Airbyte.
- Do not put infra dependencies into service venvs unless the service directly imports them.
- Prefer shared runtime envs over per-bot envs when the dependency graph is compatible.

## Compatibility Notes

- Altair is intentionally routed into `.venv-rhea` to stay within the six-env policy.
- Dogon training stays isolated because it has its own model-train dependency stack.
- TensorFlow training and inference stay in `.venv-tf` so the runtime can avoid PyTorch and broker conflicts.

## CI Expectations

- `.github/workflows/validate-six-env-policy.yml` verifies the environment map, VS Code interpreter defaults, launch targets, and policy documentation.
