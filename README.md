Orchestration Trigger App for Queue V2
=============

Trigger to start a Keboola Orchestration V2. 

**Table of contents:**

[TOC]

Prerequisites
============

There are two options for tokens that you can choose from:
 
* Create an API token with full access to all buckets and components.
* Create a [Limited Access SAPI Token](https://help.keboola.com/management/project/tokens/#limited-access-to-components) with access to the Flow, every component in the flow, and the buckets those components interact with.

Retrieve the orchestration ID from the link: </br>`...keboola.com/admin/projects/{PROJECT_ID}/orchestrations-v2/{ORCHESTRATION_ID}`

Make sure the orchestration you wish to run is an Orchestration V2:
- If the link to your orchestration contains **orchestrations-v2**: </br>`...keboola.com/admin/projects/{ProjectID}/orchestrations-v2/{OrchID}`, </br>Your orchestration is V2 and uses Queue V2.
- If the link to your orchestration contains **orchestrations**: </br>`...keboola.com/admin/projects/{ProjectID}/orchestrations/{OrchID}`, </br> Your orchestration is **NOT** V2 and you should use the [keboola.app-orchestrator-trigger application](https://github.com/keboola/app-orchestrator-trigger).



Configuration
=============

## Parameters
 - **Keboola Storage API token** (#kbcToken) – [REQ] API token with full access to all buckets and components, including buckets created in the future.
 - **Keboola stack** (kbcUrl) – [REQ] The specific Keboola stack:
     - `""`: Keboola AWS US,
     - `"eu-central-1."`: AWS EU,
     - `"north-europe.azure."`: Azure US
 - **Orchestration ID** (orchestrationId) – [REQ] The specific orchestration ID, obtained from the link.
 - **Wait for job finish and check jobs status** (waitUntilFinish) – [REQ] if set to `true`, the component will only finish executing once the triggered orchestration has stopped. If the orchestration ends in failure, the trigger job fails as well.
 - **Fail on warning** (failOnWarning) – [OPT] If set to `true`, the component will fail when the orchestration ends with a warning.


Sample Configuration
=============
```json
{
    "parameters": {
        "#kbcToken": "SECRET_VALUE",
        "kbcUrl": "",
        "orchestrationId": "832802120",
        "waitUntilFinish": true
    },
    "action": "run"
}
```

Development
-----------

If required, change the local data folder (`CUSTOM_FOLDER` placeholder) path to your custom path in
the `docker-compose.yml` file:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    volumes:
      - ./:/code
      - ./CUSTOM_FOLDER:/data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Clone this repository, initialize the workspace, and run the component with the following commands:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
docker-compose build
docker-compose run --rm dev
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run the test suite and lint check using this command:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
docker-compose run --rm test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Integration
===========

For information about deployment and integration with Keboola, please refer to the
[deployment section of the developer documentation](https://developers.keboola.com/extend/component/deployment/).
