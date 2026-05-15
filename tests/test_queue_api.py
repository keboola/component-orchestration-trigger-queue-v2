import json
import unittest
from unittest import mock

from client import QueueApiClient


def _make_response(status_code=200, text='{"id":"job-1"}'):
    response = mock.MagicMock()
    response.status_code = status_code
    response.text = text
    response.raise_for_status.return_value = None
    return response


class TestRunOrchestration(unittest.TestCase):

    def _build_client(self):
        return QueueApiClient(sapi_token="t-123", keboola_stack="-", custom_stack="")

    def test_default_component_id_is_orchestrator(self):
        client = self._build_client()
        with mock.patch.object(client, "post_raw", return_value=_make_response()) as post_raw:
            client.run_orchestration("123", variables=None)

        payload = json.loads(post_raw.call_args.kwargs["data"])
        self.assertEqual(payload["component"], "keboola.orchestrator")
        self.assertEqual(payload["config"], "123")
        self.assertEqual(payload["mode"], "run")

    def test_explicit_component_id_is_used(self):
        client = self._build_client()
        with mock.patch.object(client, "post_raw", return_value=_make_response()) as post_raw:
            client.run_orchestration("123", variables=None, component_id="keboola.flow")

        payload = json.loads(post_raw.call_args.kwargs["data"])
        self.assertEqual(payload["component"], "keboola.flow")


if __name__ == "__main__":
    unittest.main()
