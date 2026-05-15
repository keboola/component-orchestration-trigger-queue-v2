import unittest
from unittest import mock

import requests

from flow_resolver import (
    FLOW_COMPONENT_ID,
    ORCHESTRATOR_COMPONENT_ID,
    list_triggerable_configurations,
    resolve_component_id,
)


def _http_error(status_code: int) -> requests.HTTPError:
    response = mock.MagicMock()
    response.status_code = status_code
    return requests.HTTPError(response=response)


def _client_with_lists(flows, orchestrators):
    client = mock.MagicMock()

    def _list(component_id):
        if component_id == FLOW_COMPONENT_ID:
            return flows
        if component_id == ORCHESTRATOR_COMPONENT_ID:
            return orchestrators
        raise AssertionError(f"Unexpected component_id: {component_id}")

    client.list.side_effect = _list
    return client


class TestResolveComponentId(unittest.TestCase):

    def test_returns_flow_when_enabled_flow_config_exists(self):
        client = mock.MagicMock()
        client.detail.return_value = {"id": "123", "isDisabled": False, "name": "f"}

        result = resolve_component_id(client, "123")

        self.assertEqual(result, FLOW_COMPONENT_ID)
        client.detail.assert_called_once_with("keboola.flow", "123")

    def test_returns_orchestrator_when_flow_config_is_disabled(self):
        client = mock.MagicMock()
        client.detail.return_value = {"id": "123", "isDisabled": True, "name": "f"}

        result = resolve_component_id(client, "123")

        self.assertEqual(result, ORCHESTRATOR_COMPONENT_ID)

    def test_returns_orchestrator_when_flow_config_does_not_exist(self):
        client = mock.MagicMock()
        response = mock.MagicMock()
        response.status_code = 404
        client.detail.side_effect = requests.HTTPError(response=response)

        result = resolve_component_id(client, "123")

        self.assertEqual(result, ORCHESTRATOR_COMPONENT_ID)

    def test_reraises_non_404_http_errors(self):
        client = mock.MagicMock()
        response = mock.MagicMock()
        response.status_code = 500
        client.detail.side_effect = requests.HTTPError("boom", response=response)

        with self.assertRaises(requests.HTTPError):
            resolve_component_id(client, "123")


class TestListTriggerableConfigurations(unittest.TestCase):

    def test_lone_orchestrator_is_listed_as_orchestrator(self):
        client = _client_with_lists(
            flows=[],
            orchestrators=[{"id": "111", "name": "Only Orch", "isDisabled": False}],
        )

        result = list_triggerable_configurations(client)

        self.assertEqual(
            result,
            [{"id": "111", "name": "Only Orch", "component_id": ORCHESTRATOR_COMPONENT_ID}],
        )

    def test_lone_enabled_flow_is_listed_as_flow(self):
        client = _client_with_lists(
            flows=[{"id": "222", "name": "Only Flow", "isDisabled": False}],
            orchestrators=[],
        )

        result = list_triggerable_configurations(client)

        self.assertEqual(
            result,
            [{"id": "222", "name": "Only Flow", "component_id": FLOW_COMPONENT_ID}],
        )

    def test_lone_disabled_flow_is_hidden(self):
        client = _client_with_lists(
            flows=[{"id": "222", "name": "Only Disabled Flow", "isDisabled": True}],
            orchestrators=[],
        )

        result = list_triggerable_configurations(client)

        self.assertEqual(result, [])

    def test_same_id_enabled_flow_wins_over_orchestrator(self):
        client = _client_with_lists(
            flows=[{"id": "333", "name": "Flow Name", "isDisabled": False}],
            orchestrators=[{"id": "333", "name": "Orch Name", "isDisabled": False}],
        )

        result = list_triggerable_configurations(client)

        self.assertEqual(
            result,
            [{"id": "333", "name": "Flow Name", "component_id": FLOW_COMPONENT_ID}],
        )

    def test_same_id_disabled_flow_falls_back_to_orchestrator(self):
        client = _client_with_lists(
            flows=[{"id": "444", "name": "Flow Name", "isDisabled": True}],
            orchestrators=[{"id": "444", "name": "Orch Name", "isDisabled": False}],
        )

        result = list_triggerable_configurations(client)

        self.assertEqual(
            result,
            [{"id": "444", "name": "Orch Name", "component_id": ORCHESTRATOR_COMPONENT_ID}],
        )

    def test_results_are_grouped_by_type_then_sorted_by_name(self):
        client = _client_with_lists(
            flows=[
                {"id": "1", "name": "zeta", "isDisabled": False},
                {"id": "4", "name": "Bravo", "isDisabled": False},
            ],
            orchestrators=[
                {"id": "2", "name": "Alpha", "isDisabled": False},
                {"id": "3", "name": "beta", "isDisabled": False},
            ],
        )

        result = list_triggerable_configurations(client)

        self.assertEqual(
            [(item["component_id"], item["name"]) for item in result],
            [
                (FLOW_COMPONENT_ID, "Bravo"),
                (FLOW_COMPONENT_ID, "zeta"),
                (ORCHESTRATOR_COMPONENT_ID, "Alpha"),
                (ORCHESTRATOR_COMPONENT_ID, "beta"),
            ],
        )

    def test_flow_list_404_is_treated_as_empty(self):
        client = mock.MagicMock()

        def _list(component_id):
            if component_id == FLOW_COMPONENT_ID:
                raise _http_error(404)
            return [{"id": "555", "name": "Orch", "isDisabled": False}]

        client.list.side_effect = _list

        result = list_triggerable_configurations(client)

        self.assertEqual(
            result,
            [{"id": "555", "name": "Orch", "component_id": ORCHESTRATOR_COMPONENT_ID}],
        )

    def test_non_404_list_error_is_propagated(self):
        client = mock.MagicMock()
        client.list.side_effect = _http_error(500)

        with self.assertRaises(requests.HTTPError):
            list_triggerable_configurations(client)


if __name__ == "__main__":
    unittest.main()
