"""Resolve whether a configuration ID refers to a keboola.flow or a keboola.orchestrator."""
import logging
from typing import Any, Dict, List

import requests

FLOW_COMPONENT_ID = "keboola.flow"
ORCHESTRATOR_COMPONENT_ID = "keboola.orchestrator"

FLOW_UNAVAILABLE_STATUS_CODES = (403, 404)


def resolve_component_id(configurations_client: Any, configuration_id: str) -> str:
    """
    Return FLOW_COMPONENT_ID if a non-disabled keboola.flow configuration with the given ID
    exists on the project the client points to; otherwise return ORCHESTRATOR_COMPONENT_ID.

    Falls back to ORCHESTRATOR_COMPONENT_ID when the flow configuration is disabled or when
    Storage API indicates that keboola.flow is not available for the caller — HTTP 404
    (no migrated flow exists) or HTTP 403 (the component is not enabled / the token has no
    access on this project). Re-raises any other HTTP error so unexpected failures are not
    silently downgraded.
    """
    try:
        config = configurations_client.detail(FLOW_COMPONENT_ID, configuration_id)
    except requests.HTTPError as exc:
        if _is_flow_unavailable(exc):
            logging.debug(
                "keboola.flow not available for id=%s (HTTP %s); falling back to keboola.orchestrator",
                configuration_id,
                _status_code(exc),
            )
            return ORCHESTRATOR_COMPONENT_ID
        raise

    if config.get("isDisabled"):
        logging.debug(
            "keboola.flow config id=%s is disabled; falling back to keboola.orchestrator",
            configuration_id,
        )
        return ORCHESTRATOR_COMPONENT_ID

    logging.debug("Resolved id=%s as keboola.flow", configuration_id)
    return FLOW_COMPONENT_ID


def list_triggerable_configurations(configurations_client: Any) -> List[Dict[str, str]]:
    """
    Return a merged list of configurations this component can trigger.

    Combines keboola.flow and keboola.orchestrator configurations from the project and picks
    one entry per configuration ID using the same rules as ``resolve_component_id``:

    * keboola.flow exists and is not disabled -> keboola.flow
    * keboola.flow is disabled and keboola.orchestrator exists -> keboola.orchestrator
    * only keboola.flow exists and is enabled -> keboola.flow
    * only keboola.orchestrator exists -> keboola.orchestrator

    A disabled keboola.flow with no orchestrator counterpart is skipped — the trigger path
    would resolve it as keboola.orchestrator and fail with "config not found", so listing it
    in the picker would be misleading.

    Each entry is a dict ``{"id": str, "name": str, "component_id": str}``. Results are
    grouped by component type (Conditional Flow first, then Flow) and sorted by name within
    each group for stable UI output.
    """
    flows_by_id = {str(c["id"]): c for c in _safe_list(configurations_client, FLOW_COMPONENT_ID)}
    orchestrators_by_id = {str(c["id"]): c for c in _safe_list(configurations_client, ORCHESTRATOR_COMPONENT_ID)}

    merged: List[Dict[str, str]] = []
    for cfg_id in set(flows_by_id) | set(orchestrators_by_id):
        entry = _pick_entry(cfg_id, flows_by_id.get(cfg_id), orchestrators_by_id.get(cfg_id))
        if entry is not None:
            merged.append(entry)

    merged.sort(key=_sort_key)
    return merged


def _sort_key(entry: Dict[str, str]):
    is_orchestrator = entry["component_id"] == ORCHESTRATOR_COMPONENT_ID
    return (is_orchestrator, entry["name"].lower())


def _pick_entry(cfg_id: str, flow: Any, orchestrator: Any):
    if flow is not None and not flow.get("isDisabled"):
        return {"id": cfg_id, "name": flow["name"], "component_id": FLOW_COMPONENT_ID}
    if flow is not None and orchestrator is not None:
        return {"id": cfg_id, "name": orchestrator["name"], "component_id": ORCHESTRATOR_COMPONENT_ID}
    if flow is not None:
        return None
    return {"id": cfg_id, "name": orchestrator["name"], "component_id": ORCHESTRATOR_COMPONENT_ID}


def _safe_list(configurations_client: Any, component_id: str) -> List[Dict]:
    """
    List configurations of a component.

    Treats HTTP 404 (component missing) and HTTP 403 (component not enabled / no access) as
    an empty list so the picker still works on projects where keboola.flow is not available.
    """
    try:
        return configurations_client.list(component_id)
    except requests.HTTPError as exc:
        if _is_flow_unavailable(exc):
            logging.debug(
                "Listing %s returned HTTP %s; treating as empty",
                component_id,
                _status_code(exc),
            )
            return []
        raise


def _is_flow_unavailable(exc: requests.HTTPError) -> bool:
    return exc.response is not None and exc.response.status_code in FLOW_UNAVAILABLE_STATUS_CODES


def _status_code(exc: requests.HTTPError) -> str:
    return str(exc.response.status_code) if exc.response is not None else "?"
