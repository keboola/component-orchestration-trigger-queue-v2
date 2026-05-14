"""Resolve whether a configuration ID refers to a keboola.flow or a keboola.orchestrator."""
import logging
from typing import Any, Dict, List

import requests

FLOW_COMPONENT_ID = "keboola.flow"
ORCHESTRATOR_COMPONENT_ID = "keboola.orchestrator"


def resolve_component_id(configurations_client: Any, configuration_id: str) -> str:
    """
    Return FLOW_COMPONENT_ID if a non-disabled keboola.flow configuration with the given ID
    exists on the project the client points to; otherwise return ORCHESTRATOR_COMPONENT_ID.

    Falls back to ORCHESTRATOR_COMPONENT_ID on HTTP 404 (no migrated flow exists) and when the
    flow configuration is disabled. Re-raises any other HTTP error so unexpected failures are
    not silently downgraded.
    """
    try:
        config = configurations_client.detail(FLOW_COMPONENT_ID, configuration_id)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            logging.debug(
                "No keboola.flow config for id=%s (404); falling back to keboola.orchestrator",
                configuration_id,
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

    Combines keboola.flow and keboola.orchestrator configurations from the project. When the
    same configuration ID exists under both components, picks one entry per these rules:

    * keboola.flow exists and is not disabled -> keboola.flow
    * keboola.flow is disabled and keboola.orchestrator exists -> keboola.orchestrator
    * only keboola.flow exists (enabled or disabled) -> keboola.flow
    * only keboola.orchestrator exists -> keboola.orchestrator

    Each entry is a dict ``{"id": str, "name": str, "component_id": str}``. Results are sorted
    by name (case-insensitive) for stable UI output.
    """
    flows_by_id = {str(c["id"]): c for c in _safe_list(configurations_client, FLOW_COMPONENT_ID)}
    orchestrators_by_id = {str(c["id"]): c for c in _safe_list(configurations_client, ORCHESTRATOR_COMPONENT_ID)}

    merged: List[Dict[str, str]] = []
    for cfg_id in set(flows_by_id) | set(orchestrators_by_id):
        merged.append(_pick_entry(cfg_id, flows_by_id.get(cfg_id), orchestrators_by_id.get(cfg_id)))

    merged.sort(key=lambda item: item["name"].lower())
    return merged


def _pick_entry(cfg_id: str, flow: Any, orchestrator: Any) -> Dict[str, str]:
    if flow is not None and not flow.get("isDisabled"):
        return {"id": cfg_id, "name": flow["name"], "component_id": FLOW_COMPONENT_ID}
    if flow is not None and orchestrator is not None:
        return {"id": cfg_id, "name": orchestrator["name"], "component_id": ORCHESTRATOR_COMPONENT_ID}
    if flow is not None:
        return {"id": cfg_id, "name": flow["name"], "component_id": FLOW_COMPONENT_ID}
    return {"id": cfg_id, "name": orchestrator["name"], "component_id": ORCHESTRATOR_COMPONENT_ID}


def _safe_list(configurations_client: Any, component_id: str) -> List[Dict]:
    """List configurations of a component. Treats HTTP 404 as an empty list."""
    try:
        return configurations_client.list(component_id)
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            logging.debug("Listing %s returned 404; treating as empty", component_id)
            return []
        raise
