import json
import unittest
from unittest import mock

import requests

from client import QueueApiClient, QueueApiClientException
from client.queue_api import MAX_CONSECUTIVE_POLL_FAILURES


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

    def test_empty_success_body_raises_queue_exception(self):
        # A 2xx response with an empty/non-JSON body must surface as a legible
        # QueueApiClientException instead of an uncaught json.JSONDecodeError.
        client = self._build_client()
        empty = _make_response(status_code=200, text="")
        with mock.patch.object(client, "post_raw", return_value=empty):
            with self.assertRaises(QueueApiClientException):
                client.run_orchestration("123", variables=None)

    def test_non_json_error_body_raises_queue_exception(self):
        # An HTTP error whose body is not JSON (e.g. an HTML gateway 502 page) must
        # surface as a QueueApiClientException, not an uncaught json.JSONDecodeError.
        client = self._build_client()
        error_response = mock.MagicMock()
        error_response.status_code = 502
        error_response.text = "<html><body>502 Bad Gateway</body></html>"
        response = mock.MagicMock()
        response.status_code = 502
        response.text = "<html><body>502 Bad Gateway</body></html>"
        response.raise_for_status.side_effect = requests.HTTPError(response=error_response)
        with mock.patch.object(client, "post_raw", return_value=response):
            with self.assertRaises(QueueApiClientException):
                client.run_orchestration("123", variables=None)


class TestWaitUntilJobFinished(unittest.TestCase):

    def _build_client(self):
        return QueueApiClient(sapi_token="t-123", keboola_stack="-", custom_stack="")

    @mock.patch("client.queue_api.time.sleep", return_value=None)
    def test_happy_path_returns_status(self, _sleep):
        client = self._build_client()
        details = [{"isFinished": False}, {"isFinished": True, "status": "success"}]
        with mock.patch.object(client, "get", side_effect=details) as get:
            self.assertEqual(client.wait_until_job_finished("job-1"), "success")
        self.assertEqual(get.call_count, 2)

    @mock.patch("client.queue_api.time.sleep", return_value=None)
    def test_transient_poll_error_is_retried(self, _sleep):
        # A read timeout / connection error while polling must not abort the wait.
        client = self._build_client()
        side_effect = [
            requests.exceptions.ReadTimeout("Read timed out."),
            requests.exceptions.ConnectionError("Connection reset"),
            {"isFinished": True, "status": "success"},
        ]
        with mock.patch.object(client, "get", side_effect=side_effect) as get:
            self.assertEqual(client.wait_until_job_finished("job-1"), "success")
        self.assertEqual(get.call_count, 3)

    @mock.patch("client.queue_api.time.sleep", return_value=None)
    def test_persistent_poll_error_is_reraised(self, _sleep):
        # A persistent outage still fails loudly after the bounded retries.
        client = self._build_client()
        error = requests.exceptions.ReadTimeout("Read timed out.")
        with mock.patch.object(client, "get", side_effect=error) as get:
            with self.assertRaises(requests.exceptions.ReadTimeout):
                client.wait_until_job_finished("job-1")
        self.assertEqual(get.call_count, MAX_CONSECUTIVE_POLL_FAILURES + 1)

    @mock.patch("client.queue_api.time.sleep", return_value=None)
    def test_http_error_still_raises_queue_exception(self, _sleep):
        client = self._build_client()
        with mock.patch.object(client, "get", side_effect=requests.HTTPError("404")) as get:
            with self.assertRaises(QueueApiClientException):
                client.wait_until_job_finished("job-1")
        self.assertEqual(get.call_count, 1)


if __name__ == "__main__":
    unittest.main()
