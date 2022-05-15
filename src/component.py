import logging
from client import QueueApiClient, QueueApiClientException

from keboola.component.base import ComponentBase
from keboola.component.exceptions import UserException

KEY_SAPI_TOKEN = '#kbcToken'
KEY_STACK = 'kbcUrl'
KEY_ORCHESTRATION_ID = "orchestrationId"
KEY_WAIT_UNTIL_FINISH = "waitUntilFinish"
KEY_VARIABLES = "variables"
KEY_VARIABLE_NAME = "name"
KEY_VARIABLE_VALUE = "value"

REQUIRED_PARAMETERS = [KEY_SAPI_TOKEN, KEY_ORCHESTRATION_ID]
REQUIRED_IMAGE_PARS = []


class Component(ComponentBase):

    def __init__(self):
        super().__init__()

    def run(self) -> None:
        self.validate_configuration_parameters(REQUIRED_PARAMETERS)
        self.validate_image_parameters(REQUIRED_IMAGE_PARS)
        params = self.configuration.parameters

        sapi_token = params.get(KEY_SAPI_TOKEN)
        stack = params.get(KEY_STACK)
        orch_id = params.get(KEY_ORCHESTRATION_ID)

        variables = params.get(KEY_VARIABLES)

        wait_until_finish = params.get(KEY_WAIT_UNTIL_FINISH, False)

        try:
            client = QueueApiClient(sapi_token, stack)
        except QueueApiClientException as api_exc:
            raise UserException(api_exc) from api_exc

        try:
            orchestration_run = client.run_orchestration(orch_id, variables)
        except QueueApiClientException as api_exc:
            raise UserException(api_exc) from api_exc

        logging.info(f"Orchestration run started with job ID {orchestration_run.get('id')}")

        if wait_until_finish:
            logging.info("Waiting till orchestration is finished")
            try:
                client.wait_until_job_finished(orchestration_run.get('id'))
            except QueueApiClientException as api_exc:
                raise UserException(api_exc) from api_exc
            logging.info("Orchestration is finished")
        else:
            logging.info("Orchestration is being run. if you require the trigger to wait "
                         "till the orchestraion is finished, specify this in the configuration")


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
