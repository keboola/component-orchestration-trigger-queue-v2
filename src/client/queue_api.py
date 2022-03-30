import json
import time
from requests.exceptions import HTTPError
from keboola.http_client import HttpClient

QUEUE_V2_URL = "https://queue.{STACK}keboola.com"


class QueueApiClientException(Exception):
    pass


class QueueApiClient(HttpClient):
    def __init__(self, sapi_token, keboola_stack):
        auth_header = {"X-StorageApi-Token": sapi_token}
        job_url = QUEUE_V2_URL.replace("{STACK}", keboola_stack)
        super().__init__(job_url, auth_header=auth_header)

    def run_orchestration(self, orch_id):
        data = {"component": "keboola.orchestrator",
                "mode": "run",
                "config": orch_id}
        header = {'Content-Type': 'application/json'}

        try:
            return self.post(endpoint_path="jobs", headers=header, data=json.dumps(data))
        except HTTPError as http_err:
            raise QueueApiClientException(http_err) from http_err

    def wait_until_job_finished(self, job_id):
        is_finished = False
        while not is_finished:
            try:
                is_finished = self.get(endpoint_path=f"jobs/{job_id}").get("isFinished")
            except HTTPError as http_err:
                raise QueueApiClientException(http_err) from http_err
            time.sleep(10)
