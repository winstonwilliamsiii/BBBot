$ErrorActionPreference = 'Stop'

$path = Join-Path $PSScriptRoot '..\pages\99_🔧_Admin_Control_Center.py'
$content = Get-Content -Raw -Encoding utf8 $path

$oldConfig = @'
DEFAULT_CONTROL_CENTER_URL = os.getenv("CONTROL_CENTER_API_URL", "http://localhost:5001")
MLFLOW_TRACKING_URI = get_mlflow_tracking_uri()
MLFLOW_URL = get_mlflow_server_url()
'@
$newConfig = @'
DEFAULT_CONTROL_CENTER_URL = os.getenv("CONTROL_CENTER_API_URL", "http://localhost:5001")
DEFAULT_MLFLOW_TRACKING_URI = get_mlflow_tracking_uri()
DEFAULT_MLFLOW_URL = get_mlflow_server_url()
'@

$oldHelpers = @'
    return False, host_reachable, "No MLflow endpoints were detected at this URL."


def resolve_control_center_api_url():
'@
$newHelpers = @'
    return False, host_reachable, "No MLflow endpoints were detected at this URL."


def _append_unique_url(candidate_urls, base_url: str):
    """Append a URL candidate once, preserving order."""
    if base_url and base_url not in candidate_urls:
        candidate_urls.append(base_url)


def _swap_loopback_host(base_url: str, replacement_host: str) -> str | None:
    """Swap localhost and 127.0.0.1 for Windows loopback fallback checks."""
    parsed = urlparse(base_url)
    if parsed.scheme.lower() not in ("http", "https"):
        return None

    hostname = parsed.hostname or ""
    if hostname not in ("localhost", "127.0.0.1") or hostname == replacement_host:
        return None

    auth = ""
    if parsed.username:
        auth = parsed.username
        if parsed.password:
            auth = f"{auth}:{parsed.password}"
        auth = f"{auth}@"

    port = f":{parsed.port}" if parsed.port else ""
    path = parsed.path or ""
    query = f"?{parsed.query}" if parsed.query else ""
    fragment = f"#{parsed.fragment}" if parsed.fragment else ""
    return f"{parsed.scheme}://{auth}{replacement_host}{port}{path}{query}{fragment}"


def resolve_mlflow_server_url():
    """Resolve a reachable MLflow server URL with loopback fallbacks."""
    cached_url = st.session_state.get("resolved_mlflow_server_url")
    cached_note = st.session_state.get("resolved_mlflow_server_note")
    if cached_url:
        return cached_url, cached_note or "Using cached MLflow server resolution."

    candidate_urls = []
    _append_unique_url(candidate_urls, DEFAULT_MLFLOW_URL)
    _append_unique_url(candidate_urls, _swap_loopback_host(DEFAULT_MLFLOW_URL, "127.0.0.1"))
    _append_unique_url(candidate_urls, _swap_loopback_host(DEFAULT_MLFLOW_URL, "localhost"))
    _append_unique_url(candidate_urls, "http://127.0.0.1:5000")
    _append_unique_url(candidate_urls, "http://localhost:5000")

    last_note = "No MLflow endpoints were detected at the configured URL."
    for base_url in candidate_urls:
        connected, _, probe_note = probe_mlflow_server(base_url)
        if connected:
            st.session_state.resolved_mlflow_server_url = base_url
            st.session_state.resolved_mlflow_server_note = probe_note
            return base_url, probe_note
        last_note = probe_note

    st.session_state.resolved_mlflow_server_url = DEFAULT_MLFLOW_URL
    st.session_state.resolved_mlflow_server_note = last_note
    return DEFAULT_MLFLOW_URL, last_note


def get_resolved_mlflow_tracking_uri() -> str:
    """Use the resolved MLflow server URL for HTTP tracking URIs."""
    tracking_uri = DEFAULT_MLFLOW_TRACKING_URI
    if urlparse(tracking_uri).scheme.lower() in ("http", "https"):
        resolved_url, _ = resolve_mlflow_server_url()
        return resolved_url
    return tracking_uri


def resolve_control_center_api_url():
'@

$oldLinks = @'
        st.markdown("### 🔗 Quick Links")
        st.markdown("#### External Services")
        st.markdown(f"[MLflow UI]({MLFLOW_URL})")
        st.markdown("[Airflow](http://localhost:8080)")
        st.markdown("[Airbyte](http://localhost:8000)")
        st.markdown("[Service Dashboard](../sites/Mansa_Bentley_Platform/service_dashboard.html)")
'@
$newLinks = @'
        st.markdown("### 🔗 Quick Links")
        st.markdown("#### External Services")
        resolved_mlflow_url, _ = resolve_mlflow_server_url()
        st.markdown(f"[MLflow UI]({resolved_mlflow_url})")
        st.markdown("[Airflow](http://localhost:8080)")
        st.markdown("[Airbyte](http://localhost:8000)")
        st.markdown("[Service Dashboard](../sites/Mansa_Bentley_Platform/service_dashboard.html)")
'@

$oldStatus = @'
        with col1:
            st.subheader("🔌 MLflow Server Status")
            mlflow_scheme = urlparse(MLFLOW_URL).scheme.lower()
            if mlflow_scheme not in ("http", "https"):
                st.warning(f"⚠️ MLflow UI URL must be HTTP/HTTPS. Current value: {MLFLOW_URL}")
                st.info("Set `MLFLOW_SERVER_URL` to your tracking server URL, e.g. `http://localhost:5000`")
            else:
                connected, host_reachable, probe_note = probe_mlflow_server(MLFLOW_URL)
                if connected:
                    st.success(f"✅ MLflow server reachable at {MLFLOW_URL}")
                    st.caption(probe_note)
                elif host_reachable:
                    st.warning(f"⚠️ Host is reachable at {MLFLOW_URL}, but MLflow endpoints were not detected.")
                    st.info("Verify `MLFLOW_SERVER_URL` points to the MLflow server and not another service.")
                else:
                    st.error(f"❌ Cannot connect to MLflow server at {MLFLOW_URL}")
                    backend_store_uri = get_mlflow_backend_store_uri()
                    st.info(
                        "Start MLflow: "
                        f"`python -m mlflow server --backend-store-uri \"{backend_store_uri}\" --host 0.0.0.0 --port 5000`"
                    )

        with col2:
            st.subheader("🔗 Quick Actions")
            if st.button("🔄 Refresh MLflow Data", type="primary", use_container_width=True):
                st.rerun()
            if st.button("🌐 Open MLflow UI", use_container_width=True):
                st.markdown(f"[Open MLflow UI]({MLFLOW_URL})")
'@
$newStatus = @'
        with col1:
            st.subheader("🔌 MLflow Server Status")
            configured_mlflow_url = DEFAULT_MLFLOW_URL
            resolved_mlflow_url, resolved_probe_note = resolve_mlflow_server_url()
            mlflow_scheme = urlparse(configured_mlflow_url).scheme.lower()
            if mlflow_scheme not in ("http", "https"):
                st.warning(
                    "⚠️ MLflow UI URL must be HTTP/HTTPS. "
                    f"Current value: {configured_mlflow_url}"
                )
                st.info(
                    "Set `MLFLOW_SERVER_URL` to your tracking server URL, "
                    "e.g. `http://localhost:5000`"
                )
            else:
                connected, host_reachable, probe_note = probe_mlflow_server(
                    resolved_mlflow_url
                )
                if connected:
                    if resolved_mlflow_url != configured_mlflow_url:
                        st.success(
                            "✅ MLflow server reachable at "
                            f"{resolved_mlflow_url} "
                            f"(resolved from {configured_mlflow_url})"
                        )
                    else:
                        st.success(
                            f"✅ MLflow server reachable at {resolved_mlflow_url}"
                        )
                    st.caption(probe_note or resolved_probe_note)
                elif host_reachable:
                    st.warning(
                        "⚠️ Host is reachable at "
                        f"{resolved_mlflow_url}, but MLflow endpoints "
                        "were not detected."
                    )
                    st.info(
                        "Verify `MLFLOW_SERVER_URL` points to the MLflow "
                        "server and not another service."
                    )
                else:
                    st.error(
                        f"❌ Cannot connect to MLflow server at {configured_mlflow_url}"
                    )
                    backend_store_uri = get_mlflow_backend_store_uri()
                    st.info(
                        "Start MLflow: "
                        f"`python -m mlflow server --backend-store-uri "
                        f"\"{backend_store_uri}\" --host 0.0.0.0 --port 5000`"
                    )

        with col2:
            st.subheader("🔗 Quick Actions")
            if st.button("🔄 Refresh MLflow Data", type="primary", use_container_width=True):
                st.session_state.pop("resolved_mlflow_server_url", None)
                st.session_state.pop("resolved_mlflow_server_note", None)
                st.rerun()
            if st.button("🌐 Open MLflow UI", use_container_width=True):
                st.markdown(f"[Open MLflow UI]({resolved_mlflow_url})")
'@

$oldRuns = @'
        try:
            import mlflow
            from mlflow.tracking import MlflowClient

            mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
            client = MlflowClient()
            experiments = client.search_experiments()
'@
$newRuns = @'
        try:
            import mlflow
            from mlflow.tracking import MlflowClient

            resolved_tracking_uri = get_resolved_mlflow_tracking_uri()
            mlflow.set_tracking_uri(resolved_tracking_uri)
            client = MlflowClient(tracking_uri=resolved_tracking_uri)
            experiments = client.search_experiments()
'@

$oldConfigPanel = @'
        with st.expander("⚙️ MLflow Configuration"):
            st.code(f"""
# MLflow Configuration
TRACKING_URI: {MLFLOW_TRACKING_URI}
SERVER_URL: {MLFLOW_URL}
BACKEND_STORE_URI: {get_mlflow_backend_store_uri()}

# Notes
- MLflow Training dashboard is merged into this ACC tab.
- Use SERVER_URL for web health checks/UI.
- Use BACKEND_STORE_URI for `mlflow db upgrade`.
            """, language="text")
'@
$newConfigPanel = @'
        with st.expander("⚙️ MLflow Configuration"):
            resolved_mlflow_url, _ = resolve_mlflow_server_url()
            resolved_tracking_uri = get_resolved_mlflow_tracking_uri()
            st.code(f"""
# MLflow Configuration
CONFIGURED_TRACKING_URI: {DEFAULT_MLFLOW_TRACKING_URI}
RESOLVED_TRACKING_URI: {resolved_tracking_uri}
CONFIGURED_SERVER_URL: {DEFAULT_MLFLOW_URL}
RESOLVED_SERVER_URL: {resolved_mlflow_url}
BACKEND_STORE_URI: {get_mlflow_backend_store_uri()}

# Notes
- MLflow Training dashboard is merged into this ACC tab.
- Use SERVER_URL for web health checks/UI.
- Use BACKEND_STORE_URI for `mlflow db upgrade`.
            """, language="text")
'@

$replacementMap = [ordered]@{
    $oldConfig = $newConfig
    $oldHelpers = $newHelpers
    $oldLinks = $newLinks
    $oldStatus = $newStatus
    $oldRuns = $newRuns
    $oldConfigPanel = $newConfigPanel
}

foreach ($entry in $replacementMap.GetEnumerator()) {
    if (-not $content.Contains($entry.Key)) {
        throw "Expected block not found during patch operation."
    }
    $content = $content.Replace($entry.Key, $entry.Value)
}

Set-Content -Path $path -Value $content -Encoding utf8
Write-Host "Patched $path"
