import logging
from typing import Optional

from kbcstorage.configurations import Configurations
from keboola.component.base import ComponentBase, sync_action
from keboola.component.exceptions import UserException
from keboola.component.sync_actions import SelectElement

from client import QueueApiClient, QueueApiClientException

KEY_SAPI_TOKEN = '#kbcToken'
KEY_STACK = 'kbcUrl'
KEY_CUSTOM_STACK = "custom_stack"
KEY_ORCHESTRATION_ID = "orchestrationId"
KEY_WAIT_UNTIL_FINISH = "waitUntilFinish"
KEY_VARIABLES = "variables"
KEY_VARIABLE_NAME = "name"
KEY_VARIABLE_VALUE = "value"
KEY_FAIL_ON_WARNING = "failOnWarning"

REQUIRED_PARAMETERS = [KEY_SAPI_TOKEN, KEY_ORCHESTRATION_ID]
REQUIRED_IMAGE_PARS = []

STACK_URL = "https://connection{STACK}.keboola.com"
CLOUD_STACK_URL = "https://connection{STACK}.keboola.cloud"
VALID_STACKS = ["", "eu-central-1.", "north-europe.azure."]


def get_stack_url(keboola_stack: str, custom_stack: Optional[str]):
    if keboola_stack == "Custom Stack":
        stack_url = CLOUD_STACK_URL.replace("{STACK}", custom_stack)
    else:
        stack_url = STACK_URL.replace("{STACK}", keboola_stack)
        if keboola_stack not in VALID_STACKS:
            raise QueueApiClientException(
                f"Invalid stack entered, make sure it is in the list of valid stacks {VALID_STACKS} ")
    return stack_url


class Component(ComponentBase):

    def __init__(self):
        super().__init__()
        self._runner_client: QueueApiClient
        self._configurations_client: Configurations

    def run(self) -> None:
        self.validate_configuration_parameters(REQUIRED_PARAMETERS)
        params = self.configuration.parameters
        self._init_clients()

        orch_id = params.get(KEY_ORCHESTRATION_ID)

        variables = params.get(KEY_VARIABLES)

        wait_until_finish = params.get(KEY_WAIT_UNTIL_FINISH, False)
        fail_on_warning = params.get(KEY_FAIL_ON_WARNING, True)

        try:
            orchestration_run = self._runner_client.run_orchestration(orch_id, variables)
        except QueueApiClientException as api_exc:
            raise UserException(api_exc) from api_exc

        logging.info(f"Orchestration run started with job ID {orchestration_run.get('id')}")

        if wait_until_finish:
            logging.info("Waiting till orchestration is finished")
            try:
                status = self._runner_client.wait_until_job_finished(orchestration_run.get('id'))
            except QueueApiClientException as api_exc:
                raise UserException(api_exc) from api_exc
            logging.info("Orchestration is finished")
            self.process_status(status, fail_on_warning)
        else:
            logging.info("Orchestration is being run. if you require the trigger to wait "
                         "till the orchestraion is finished, specify this in the configuration")

    def _init_clients(self):
        params = self.configuration.parameters
        sapi_token = params.get(KEY_SAPI_TOKEN)
        stack = params.get(KEY_STACK)
        custom_stack = params.get(KEY_CUSTOM_STACK, "")

        if not sapi_token:
            raise UserException("Storage API token must be provided!")
        if stack is None:
            raise UserException("Stack must be provided!")

        try:
            self._runner_client = QueueApiClient(sapi_token, stack, custom_stack)
        except QueueApiClientException as api_exc:
            raise UserException(api_exc) from api_exc

        stack_url = get_stack_url(stack, custom_stack)

        self._configurations_client = Configurations(stack_url, sapi_token, 'default')

    @staticmethod
    def process_status(status: str, fail_on_warning: bool) -> None:
        if not fail_on_warning and status.lower() == "warning":
            logging.warning("Orchestration ended in a warning")
        elif status.lower() != "success":
            raise UserException(f"Orchestration did not end in success, ended in {status}")

    @sync_action('list_orchestrations')
    def list_orchestration(self):
        self._init_clients()
        configurations = self._configurations_client.list('keboola.orchestrator')
        return [SelectElement(label=f"[{c['id']}] {c['name']}", value=int(c['id'])) for c in configurations]

    def _get_project_id(self) -> str:
        return self.configuration.parameters.get(KEY_SAPI_TOKEN, '').split('-')[0]


if __name__ == "__main__":
    try:
        comp = Component()
        comp.execute_action()
    except UserException as exc:
        logging.exception(exc)
        exit(1)
    except Exception as exc:
        logging.exception(exc)
        exit(2)
