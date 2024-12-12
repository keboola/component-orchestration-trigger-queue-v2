import logging
from typing import Optional, List

import requests
from kbcstorage.configurations import Configurations
from keboola.component.base import ComponentBase, sync_action
from keboola.component.exceptions import UserException
from keboola.component.sync_actions import SelectElement, ValidationResult

from client import QueueApiClient, QueueApiClientException

CURRENT_COMPONENT_ID = 'kds-team.app-orchestration-trigger-queue-v2'
FLOW_COMPONENT_ID = "keboola.orchestrator"

KEY_SAPI_TOKEN = '#kbcToken'
KEY_STACK = 'kbcUrl'
KEY_CUSTOM_STACK = "custom_stack"
KEY_ORCHESTRATION_ID = "orchestrationId"
KEY_WAIT_UNTIL_FINISH = "waitUntilFinish"
KEY_VARIABLES = "variables"
KEY_VARIABLE_NAME = "name"
KEY_VARIABLE_VALUE = "value"
KEY_FAIL_ON_WARNING = "failOnWarning"
KEY_TRIGGER_ACTION_ON_FAILURE = "triggerActionOnFailure"
KEY_ACTION_ON_FAILURE_SETTINGS = "actionOnFailureSettings"
KEY_TARGET_PROJECT = "targetProject"
KEY_CONFIGURATION_ID_ON_FAILURE = "failureConfigurationId"
KEY_VARIABLES_ON_FAILURE = "failureVariables"
KEY_PASS_VARIABLES = "passVariables"

REQUIRED_PARAMETERS = [KEY_SAPI_TOKEN, KEY_ORCHESTRATION_ID]
REQUIRED_IMAGE_PARS = []

STACK_URL = "https://connection.{STACK}keboola.com"
CLOUD_STACK_URL = "https://connection.{STACK}.keboola.cloud"
VALID_STACKS = ["", "eu-central-1.", "north-europe.azure.", "us-east4.gcp.", "europe-west3.gcp."]


def get_stack_url(keboola_stack: str, custom_stack: Optional[str]):
    if keboola_stack == "Custom Stack":
        stack_url = CLOUD_STACK_URL.replace("{STACK}", custom_stack)
    else:
        stack_url = STACK_URL.replace("{STACK}", keboola_stack)
        if keboola_stack not in VALID_STACKS:
            raise UserException(f"Invalid stack entered, make sure it is in the list of valid stacks {VALID_STACKS} ")
    return stack_url


def check_variables(variables) -> None:
    if any(v['name'] == '' for v in variables):
        raise UserException("There is a variable with empty name in the configuration. "
                            "Please provide a valid name or remove the variable row.")


class Component(ComponentBase):

    def __init__(self):
        super().__init__()
        self._target_project_on_failure = None
        self._runner_client: QueueApiClient
        self._failure_action_runner_client: QueueApiClient
        self._configurations_client: Configurations

    def run(self) -> None:
        self.validate_configuration_parameters(REQUIRED_PARAMETERS)
        params = self.configuration.parameters
        self._init_clients()

        orch_id = params.get(KEY_ORCHESTRATION_ID)

        variables = params.get(KEY_VARIABLES, [])
        check_variables(variables)

        wait_until_finish = params.get(KEY_WAIT_UNTIL_FINISH, False)
        fail_on_warning = params.get(KEY_FAIL_ON_WARNING, True)

        try:
            orchestration_run = self._runner_client.run_orchestration(orch_id, variables)
        except QueueApiClientException as api_exc:
            raise UserException(api_exc) from api_exc

        logging.info(f"Flow run started with job ID {orchestration_run.get('id')} and "
                     f"configuration ID {orch_id}")

        if wait_until_finish:
            try:
                logging.info("Waiting till flow is finished")
                status = self._runner_client.wait_until_job_finished(orchestration_run.get('id'))
                trigger_action_on_failure = params.get(KEY_TRIGGER_ACTION_ON_FAILURE, False)
                if trigger_action_on_failure and status.lower() != "success":
                    logging.info("Flow is finished")

                    job_to_trigger = params.get(
                        KEY_ACTION_ON_FAILURE_SETTINGS, {}
                    ).get(KEY_CONFIGURATION_ID_ON_FAILURE)

                    pass_variables_of_main_flow = params.get(
                        KEY_ACTION_ON_FAILURE_SETTINGS, {}
                    ).get(KEY_PASS_VARIABLES, [])

                    variables_on_failure = params.get(
                        KEY_ACTION_ON_FAILURE_SETTINGS, {}
                    ).get(KEY_VARIABLES_ON_FAILURE, [])
                    check_variables(variables_on_failure)

                    if pass_variables_of_main_flow:
                        variables_on_failure.extend(variables)

                    try:
                        action_on_failure_run = self._failure_action_runner_client.run_orchestration(
                            job_to_trigger,
                            variables_on_failure
                        )
                        project = params.get(KEY_ACTION_ON_FAILURE_SETTINGS, {}).get(KEY_TARGET_PROJECT)
                        if project == "current":
                            current_project_id = self.environment_variables.project_id
                            logging.warning("Flow failed, triggering flow with job ID "
                                            f"{action_on_failure_run.get('id')} and "
                                            f"configuration ID {str(job_to_trigger)} in "
                                            f"project {current_project_id}")
                        else:
                            logging.warning("Flow failed, triggering flow with job ID "
                                            f"{action_on_failure_run.get('id')} and "
                                            f"configuration ID {str(job_to_trigger)} in "
                                            f"project {self._get_project_id()}")

                        status_on_failure = self._failure_action_runner_client.wait_until_job_finished(
                            action_on_failure_run.get('id')
                        )
                        logging.info("Flow triggered on failure finished")
                        jobs_ids = [orchestration_run.get('id'), action_on_failure_run.get('id')]
                        configurations_ids = [orch_id, job_to_trigger]
                        project_ids = [self.environment_variables.project_id, self._get_project_id()]
                        is_current_project = True if project == "current" else False
                        self.process_action_status(
                            status_on_failure,
                            fail_on_warning,
                            jobs_ids,
                            configurations_ids,
                            project_ids,
                            is_current_project
                        )

                    except QueueApiClientException as api_exc:
                        raise UserException("Flow triggered on failure failed on: "
                                            f"{api_exc}") from api_exc
                else:
                    logging.info("Flow is finished")
                    self.process_status(status, fail_on_warning)

            except QueueApiClientException as api_exc:
                raise UserException(f"Flow run failed on: {api_exc}") from api_exc

        else:
            logging.info("Flow is being run. if you require the trigger to wait "
                         "till the flow is finished, specify this in the configuration")

    def _init_clients(self):
        params = self.configuration.parameters
        sapi_token = params.get(KEY_SAPI_TOKEN)
        stack = params.get(KEY_STACK)
        custom_stack = params.get(KEY_CUSTOM_STACK, "")

        if not sapi_token:
            raise UserException("Storage API token must be provided!")
        if stack is None:
            raise UserException("Stack must be provided!")

        stack_url = get_stack_url(stack, custom_stack)

        self._runner_client = self._get_clients(custom_stack, sapi_token, stack)
        self._configurations_client = Configurations(stack_url, sapi_token, 'default')

        if params.get(KEY_TRIGGER_ACTION_ON_FAILURE, False):
            if params.get(KEY_ACTION_ON_FAILURE_SETTINGS, {}).get(KEY_TARGET_PROJECT) == "current":
                token_on_failure = self.environment_variables.token
                stack_on_failure = self.environment_variables.stack_id
                # env url is different from stack url parameter, needs to be adjusted
                stack_url_on_failure = self.environment_variables.url.replace('v2/storage/', '')
                # custom stack is not needed in the current project
                custom_stack_on_failure = ''

                self._target_project_on_failure = self.environment_variables.project_id
                self._configurations_on_failure_client = Configurations(stack_url_on_failure,
                                                                        token_on_failure,
                                                                        'default')
                self._failure_action_runner_client = self._get_clients(custom_stack_on_failure,
                                                                       token_on_failure,
                                                                       stack_on_failure)
            else:
                self._target_project_on_failure = self._get_project_id()
                self._configurations_on_failure_client = self._configurations_client
                self._failure_action_runner_client = self._runner_client

    @staticmethod
    def _get_clients(custom_stack, sapi_token, stack):
        try:
            return QueueApiClient(sapi_token, stack, custom_stack)
        except QueueApiClientException as api_exc:
            raise UserException(api_exc) from api_exc

    @staticmethod
    def update_config(token: str, stack_url, component_id, configurationId, name, description=None, configuration=None,
                      state=None, changeDescription='', branch_id=None, is_disabled=False, **kwargs):
        """
        Update table from CSV file.

        Args:
            token: storage token
            component_id (str):
            name (str): The new table name (only alphanumeric and underscores)
            configuration (dict): configuration JSON; the maximum allowed size is 4MB
            state (dict): configuration JSON; the maximum allowed size is 4MB
            changeDescription (str): Escape character used in the CSV file.
            stack_url:
            is_disabled:

        Returns:
            table_id (str): Id of the created table.

        Raises:
            requests.HTTPError: If the API request fails.
        """
        logging.info(f"Updating configuration {configurationId} in component {component_id}")

        if not branch_id:
            url = f'{stack_url}/v2/storage/components/{component_id}/configs/{configurationId}'
        else:
            url = f'{stack_url}/v2/storage/branch/{branch_id}/components/{component_id}/configs/{configurationId}'

        parameters = {}

        parameters['configurationId'] = configurationId
        if configuration:
            parameters['configuration'] = configuration
        parameters['name'] = name

        if description is not None:
            parameters['description'] = description
        parameters['changeDescription'] = changeDescription
        parameters['isDisabled'] = is_disabled
        headers = {'Content-Type': 'application/json', 'X-StorageApi-Token': token}
        response = requests.put(url,
                                json=parameters,
                                headers=headers)

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise e
        else:
            return response.json()

    @staticmethod
    def process_status(status: str, fail_on_warning: bool) -> None:
        if not fail_on_warning and status.lower() == "warning":
            logging.warning("Flow ended in a warning")
        elif status.lower() != "success":
            raise UserException(f"Flow did not end in success, ended in {status}")

    @staticmethod
    def process_action_status(status: str, fail_on_warning: bool, jobs_ids: List[str], configurations_ids: List[str],
                              project_ids: List[str], current_project: bool) -> None:
        if not fail_on_warning:
            if not current_project:
                logging.warning(f"Flow with job ID {jobs_ids[0]} and "
                                f"configuration ID {str(configurations_ids[0])} failed. "
                                f"According to the configuration, the flow with job ID {jobs_ids[1]} "
                                f"and configuration ID {str(configurations_ids[1])} was "
                                f"triggered and ended with {status}")
            else:
                logging.warning(f"Flow with job ID {jobs_ids[0]} and configuration ID "
                                f"{str(configurations_ids[0])} from project {project_ids[0]} failed. "
                                f"According to the configuration, the flow with job ID {jobs_ids[1]} and "
                                f"configuration ID {str(configurations_ids[1])} from project {project_ids[1]} was "
                                f"triggered and ended with {status}")
        else:
            if not current_project:
                raise UserException(f"Flow with job ID {jobs_ids[0]} failed. "
                                    f"According to the configuration, the flow with job ID {jobs_ids[1]} and "
                                    f"configuration ID {str(configurations_ids[1])} was triggered"
                                    f" and ended with {status}")
            else:
                raise UserException(f"Flow with job ID {jobs_ids[0]} from project {project_ids[0]} failed. "
                                    f"According to the configuration, the flow with job ID {jobs_ids[1]} and "
                                    f"configuration ID {str(configurations_ids[1])} from project"
                                    f" {project_ids[1]} was triggered and ended with {status}")

    @sync_action('list_orchestrations')
    def list_orchestration(self):
        self._init_clients()
        configurations = self._configurations_client.list(FLOW_COMPONENT_ID)
        return [SelectElement(label=f"[{c['id']}] {c['name']}", value=c['id']) for c in configurations]

    @sync_action('list_configurations')
    def list_configurations(self):
        self._init_clients()
        configurations = self._configurations_on_failure_client.list(FLOW_COMPONENT_ID)
        return [SelectElement(label=f"[{c['id']}] {c['name']}", value=c['id']) for c in configurations]

    @sync_action('sync_trigger_metadata')
    def sync_trigger_metadata(self):
        self.validate_configuration_parameters(REQUIRED_PARAMETERS)
        params = self.configuration.parameters
        self._init_clients()
        flow_id = params.get(KEY_ORCHESTRATION_ID)
        stack = params.get(KEY_STACK)
        custom_stack = params.get(KEY_CUSTOM_STACK, "")
        stack_url = get_stack_url(stack, custom_stack)
        flow_url = self._compose_flow_url(flow_id, stack_url, self._get_project_id())
        flow_cfg = self._get_component_detail(self._configurations_client, FLOW_COMPONENT_ID, str(flow_id))

        info_message = (f"This configuration triggers flow named [{flow_cfg['name']}]({flow_url}) "
                        f"in project `{self._get_project_id()}`.")

        if params.get(KEY_TRIGGER_ACTION_ON_FAILURE, False):
            flow_id_on_failure = params.get(KEY_ACTION_ON_FAILURE_SETTINGS, {}).get(KEY_CONFIGURATION_ID_ON_FAILURE)
            flow_cfg_on_failure = self._get_component_detail(self._configurations_on_failure_client,
                                                             FLOW_COMPONENT_ID,
                                                             str(flow_id_on_failure))

            flow_url_on_failure = self._compose_flow_url(flow_id_on_failure, stack_url, self._target_project_on_failure)
            info_message += (f" If the flow fails, it will trigger flow [{flow_cfg_on_failure['name']}]"
                             f"({flow_url_on_failure}) in project {self._target_project_on_failure}.")
        return ValidationResult(info_message)

    @staticmethod
    def _get_component_detail(client: Configurations, component_id: str, configuration_id: str):
        try:
            return client.detail(component_id, configuration_id)
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return {"name": f"Component with id ({configuration_id}) not found!"}
            else:
                raise e

    @staticmethod
    def _compose_flow_url(flow_id, stack_url, project_id):
        orchestration_url = f"{stack_url}/admin/projects/{project_id}/flows/{flow_id}"
        return orchestration_url

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
