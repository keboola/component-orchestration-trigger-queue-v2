"""Resolve whether a configuration ID refers to a keboola.flow or a keboola.orchestrator."""
import logging
from typing import Any

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
