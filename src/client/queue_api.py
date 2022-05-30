import json
import time
import requests
from typing import Dict, Optional, List
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests.exceptions import HTTPError
from keboola.http_client import HttpClient

QUEUE_V2_URL = "https://queue.{STACK}keboola.com"
CLOUD_URL = "https://queue.{STACK}.keboola.cloud"
VALID_STACKS = ["", "eu-central-1.", "north-europe.azure."]


class QueueApiClientException(Exception):
    pass


class QueueApiClient(HttpClient):
    def __init__(self, sapi_token: str, keboola_stack: str, custom_stack: Optional[str]) -> None:
        auth_header = {"X-StorageApi-Token": sapi_token}
        if keboola_stack == "Custom Stack":
            job_url = CLOUD_URL.replace("{STACK}", custom_stack)
        else:
            job_url = QUEUE_V2_URL.replace("{STACK}", keboola_stack)
            self.validate_stack(keboola_stack)
        super().__init__(job_url, auth_header=auth_header)

    @staticmethod
    def validate_stack(stack: str) -> None:
        if stack not in VALID_STACKS:
            raise QueueApiClientException(
                f"Invalid stack entered, make sure it is in the list of valid stacks {VALID_STACKS} ")

    def run_orchestration(self, orch_id: str, variables: Optional[List[Dict]]) -> Dict:
        data = {"component": "keboola.orchestrator",
                "mode": "run",
                "config": orch_id}
        if variables:
            data["variableValuesData"] = {"values": variables}
        header = {'Content-Type': 'application/json'}

        response = self.post_raw(endpoint_path="jobs", headers=header, data=json.dumps(data))  # noqa
        self._handle_http_error(response)
        return json.loads(response.text)

    def wait_until_job_finished(self, job_id: str) -> None:
        is_finished = False
        while not is_finished:
            try:
                is_finished = self.get(endpoint_path=f"jobs/{job_id}").get("isFinished")
            except HTTPError as http_err:
                raise QueueApiClientException(http_err) from http_err
            time.sleep(10)

    @staticmethod
    def _handle_http_error(response):
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            response_error = json.loads(e.response.text)
            if response_error.get('code') == 400:
                raise QueueApiClientException(
                    f"{response_error.get('error')}. Exception code {response_error.get('code')}.\n"
                    f"Make sure the Orchestration ID set is a Orchestration V2, "
                    f"follow the documentation to find out what type of orchestration your project is using") from e
            raise QueueApiClientException(
                f"{response_error.get('error')}. Exception code {response_error.get('code')}") from e

    # override to continue on failure
    def _requests_retry_session(self, session=None):
        session = session or requests.Session()
        retry = Retry(
            total=self.max_retries,
            read=self.max_retries,
            connect=self.max_retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=self.status_forcelist
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session
