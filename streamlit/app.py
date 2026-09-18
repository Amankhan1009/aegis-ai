"""AegisAI Streamlit operations dashboard."""

import base64
import json
import re
from typing import Any

from api_client import (
    APIClientError,
    get_audit_events,
    get_metrics,
    health,
    login,
    process_ai,
    ready,
)

import streamlit as st

# ============================================================
# Page configuration and session state
# ============================================================

st.set_page_config(page_title="AegisAI Operations", page_icon="🛡️", layout="wide")

for state_key, default in {"token": None, "username": None, "role": None}.items():
    if state_key not in st.session_state:
        st.session_state[state_key] = default


# ============================================================
# Shared helpers
# ============================================================


def _jwt_claims(token: str) -> dict[str, Any]:
    """Read display-only JWT claims; the backend remains the authority."""
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))
    except (IndexError, UnicodeDecodeError, ValueError):
        return {}


def _show_api_error(exc: APIClientError) -> None:
    """Render expected API errors without exposing a Streamlit traceback."""
    messages = {
        401: "Your session is invalid or has expired. Please sign in again.",
        403: "You do not have permission to view this resource.",
        429: "The API rate limit was reached. Wait a moment and retry.",
        500: "The service reported an internal error. Check the request ID in backend logs.",
    }
    st.error(messages.get(exc.status_code, str(exc)))
    if exc.status_code == 401:
        for state_key in ("token", "username", "role"):
            st.session_state[state_key] = None


def _parse_metrics(payload: str) -> list[dict[str, Any]]:
    """Parse Prometheus exposition lines into rows for dashboard summaries."""
    rows: list[dict[str, Any]] = []
    pattern = re.compile(r"^([\w:]+)(?:\{([^}]*)\})?\s+([\d.eE+-]+)$")
    label_pattern = re.compile(r'(\w+)="((?:\\.|[^"\\])*)"')
    for line in payload.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        labels = {
            key: bytes(value, "utf-8").decode("unicode_escape")
            for key, value in label_pattern.findall(match.group(2) or "")
        }
        rows.append({"metric": match.group(1), "labels": labels, "value": float(match.group(3))})
    return rows


def _metric_total(rows: list[dict[str, Any]], metric: str, **labels: str) -> float:
    """Sum samples matching a Prometheus metric and optional labels."""
    return sum(
        row["value"]
        for row in rows
        if row["metric"] == metric
        and all(row["labels"].get(name) == value for name, value in labels.items())
    )


def _metric_card(label: str, value: float, help_text: str | None = None) -> None:
    """Display a concise metric with sensible number formatting."""
    formatted = f"${value:.6f}" if label == "Estimated cost" else f"{value:,.0f}"
    st.metric(label, formatted, help=help_text)


# ============================================================
# Authentication
# ============================================================


def _login_page() -> None:
    st.title("AegisAI Operations")
    st.caption("Enterprise AI Operations Platform")
    st.subheader("Sign in")
    with st.form("login_form"):
        username = st.text_input("Username", autocomplete="username")
        password = st.text_input("Password", type="password", autocomplete="current-password")
        submitted = st.form_submit_button("Sign in", type="primary")
    if submitted:
        try:
            result = login(username, password)
            claims = _jwt_claims(result["access_token"])
            st.session_state.token = result["access_token"]
            st.session_state.username = claims.get("sub", username)
            st.session_state.role = claims.get("role", "Unknown")
            st.rerun()
        except APIClientError as exc:
            _show_api_error(exc)
        except KeyError:
            st.error("The login response did not include an access token.")


# ============================================================
# Dashboard pages
# ============================================================


def _overview_page() -> None:
    st.header("Overview")
    st.caption("Live counters exported by the FastAPI service.")
    try:
        rows = _parse_metrics(get_metrics())
    except APIClientError as exc:
        _show_api_error(exc)
        return
    requests_total = _metric_total(rows, "aiops_requests_total")
    successes = _metric_total(rows, "aiops_requests_total", status="200")
    failures = requests_total - successes
    cards = st.columns(4)
    with cards[0]:
        _metric_card("Requests", requests_total)
    with cards[1]:
        _metric_card("Successful requests", successes)
    with cards[2]:
        _metric_card("Failed requests", failures)
    with cards[3]:
        _metric_card("Rate-limit hits", _metric_total(rows, "aiops_rate_limit_hits_total"))
    cards = st.columns(4)
    with cards[0]:
        _metric_card("Cache hits", _metric_total(rows, "aiops_cache_hits_total"))
    with cards[1]:
        _metric_card("Cache misses", _metric_total(rows, "aiops_cache_misses_total"))
    with cards[2]:
        _metric_card("LLM calls", _metric_total(rows, "aiops_llm_requests_total"))
    with cards[3]:
        _metric_card("Invalid outputs", _metric_total(rows, "aiops_llm_invalid_output_total"))
    _metric_card(
        "Estimated cost",
        _metric_total(rows, "aiops_estimated_cost_usd_total"),
        "Estimate based on configured model pricing; not a provider invoice.",
    )


def _structured_spec(enabled: bool, fields: str, allowed_values: str) -> dict | None:
    """Build the backend structured-output payload from optional form fields."""
    if not enabled:
        return None
    required_fields = [field.strip() for field in fields.split(",") if field.strip()]
    if not required_fields:
        raise ValueError("Add at least one required field for structured output.")
    spec: dict[str, Any] = {"required_fields": required_fields}
    if allowed_values.strip():
        parsed = json.loads(allowed_values)
        if not isinstance(parsed, dict):
            raise ValueError("Allowed values must be a JSON object.")
        spec["allowed_values"] = parsed
    return spec


def _ai_operations_page(fail_mode: str | None = None, show_header: bool = True) -> None:
    if show_header:
        st.header("AI Operations")
    if fail_mode is not None:
        st.caption(f"Submitting this request with `X-Fail-Mode: {fail_mode}`.")
    with st.form("ai_request_form"):
        prompt = st.text_area(
            "Prompt", placeholder="Ask the AI to summarize an operational incident."
        )
        temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
        structured = st.checkbox("Request structured JSON output")
        required_fields = st.text_input("Required JSON fields", placeholder="summary, severity")
        allowed_values = st.text_area(
            "Allowed values JSON (optional)",
            placeholder='{"severity": ["low", "medium", "high"]}',
        )
        submitted = st.form_submit_button("Run AI request", type="primary")
    if not submitted:
        return
    if not prompt.strip():
        st.warning("Enter a prompt before submitting.")
        return
    try:
        payload: dict[str, Any] = {"prompt": prompt, "temperature": temperature}
        spec = _structured_spec(structured, required_fields, allowed_values)
        if spec:
            payload["structured_output"] = spec
        with st.spinner("Calling the AI service..."):
            result = process_ai(st.session_state.token, payload, fail_mode)
    except (ValueError, json.JSONDecodeError) as exc:
        st.warning(f"Structured output configuration is invalid: {exc}")
        return
    except APIClientError as exc:
        _show_api_error(exc)
        return
    if result.get("validation_failed"):
        st.warning(
            "The model output failed structured validation; a controlled fallback was returned."
        )
    else:
        st.success("AI request completed.")
    st.subheader("Response")
    st.write(result.get("output", ""))
    if result.get("structured_result") is not None:
        st.subheader("Validated structured output")
        st.json(result["structured_result"])
    details = st.columns(3)
    details[0].metric("Request ID", result.get("request_id", "Unknown"))
    provider = result.get("provider", "Unknown")
    model = result.get("model", "Unknown")
    details[1].metric("Provider / model", f"{provider} / {model}")
    details[2].metric("Latency", f"{result.get('latency_ms', 0):,.2f} ms")
    st.caption(
        f"Tokens — input: {result.get('input_tokens', 0):,}; output: "
        f"{result.get('output_tokens', 0):,}. Validation: "
        f"{'failed' if result.get('validation_failed') else 'passed/not requested'}."
    )


def _failure_testing_page() -> None:
    st.header("Failure Testing")
    options = {
        "Normal": None,
        "Timeout": "timeout",
        "500 error": "error_500",
        "Rate limit": "rate_limit",
        "Invalid output": "invalid",
        "DB timeout": "db_timeout",
    }
    selected = st.selectbox("Scenario", list(options))
    st.info("Failure injection is intended for local/demo use and is sent only with this request.")
    _ai_operations_page(options[selected], show_header=False)


def _audit_page() -> None:
    st.header("Audit Events")
    st.caption("Audit event access is restricted to administrators.")
    filters = st.columns(3)
    actor = filters[0].text_input("Actor")
    outcome = filters[1].selectbox("Outcome", ["", "allowed", "success", "failure"])
    limit = filters[2].number_input("Limit", 1, 200, 50)
    if st.button("Load audit events", type="primary"):
        try:
            result = get_audit_events(st.session_state.token, int(limit), actor, outcome)
        except APIClientError as exc:
            _show_api_error(exc)
            return
        st.caption(f"Showing {result.get('count', 0)} event(s).")
        events = result.get("events", [])
        if events:
            st.dataframe(events, width="stretch", hide_index=True)
        else:
            st.info("No audit events match these filters.")


def _health_page() -> None:
    st.header("System Health")
    checks = (("Liveness", health), ("Readiness", ready))
    columns = st.columns(2)
    for column, (name, check) in zip(columns, checks, strict=True):
        with column:
            try:
                result = check()
                st.success(f"{name}: {result.get('status', 'ok')}")
                st.json(result)
            except APIClientError as exc:
                st.error(f"{name}: {exc}")


def _metrics_page() -> None:
    st.header("Metrics")
    st.caption("Prometheus metrics exported by the API.")
    try:
        raw = get_metrics()
    except APIClientError as exc:
        _show_api_error(exc)
        return
    rows = _parse_metrics(raw)
    relevant = [row for row in rows if row["metric"].startswith("aiops_")]
    st.dataframe(relevant, width="stretch", hide_index=True)
    with st.expander("Raw Prometheus exposition"):
        st.code(raw, language="text")


# ============================================================
# Application routing
# ============================================================


if not st.session_state.token:
    _login_page()
    st.stop()

st.sidebar.title("AegisAI")
st.sidebar.caption(f"Signed in as {st.session_state.username} ({st.session_state.role})")
page = st.sidebar.radio(
    "Navigation",
    [
        "Overview",
        "AI Operations",
        "Failure Testing",
        "Audit Events",
        "System Health",
        "Metrics",
        "Logout",
    ],
)
if page == "Logout":
    for state_key in ("token", "username", "role"):
        st.session_state[state_key] = None
    st.rerun()
elif page == "Overview":
    _overview_page()
elif page == "AI Operations":
    _ai_operations_page()
elif page == "Failure Testing":
    _failure_testing_page()
elif page == "Audit Events":
    _audit_page()
elif page == "System Health":
    _health_page()
elif page == "Metrics":
    _metrics_page()
