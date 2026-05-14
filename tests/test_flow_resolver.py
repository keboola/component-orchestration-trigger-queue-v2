import unittest
from unittest import mock

import requests

from flow_resolver import (
    FLOW_COMPONENT_ID,
    ORCHESTRATOR_COMPONENT_ID,
    resolve_component_id,
)


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


if __name__ == "__main__":
    unittest.main()
