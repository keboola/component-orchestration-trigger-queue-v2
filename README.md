Orchestration Trigger app for Queue V2
=============

Trigger to start a Keboola Orchestration V2. 

**Table of contents:**

[TOC]

Prerequisites
============

There are two options with tokens that you can choose:
 
* Create an API token with Full access to all buckets and components.
* Create a [Limited Access SAPI Token](https://help.keboola.com/management/project/tokens/#limited-access-to-components) with access to the Flow, and every single component in the flow and the buckets those components interact with


Get the orchestration id from the link :  ...keboola.com/admin/projects/{PROJECT_ID}/orchestrations-v2/{ORCHESTRATION_ID}

Make sure the orchestration you wish to run is an Orchestration V2. 

If the link to your of your orchestration contains **orchestrations-v2** : 
...keboola.com/admin/projects/{ProjectID}/orchestrations-v2/{OrchID}
Your orchestration is V2 and therefore uses Queue V2.

If the link to your of your orchestration contains **orchestrations** :
...keboola.com/admin/projects/{ProjectID}/orchestrations/{OrchID}
Your orchestration is **NOT** V2 and you should use the [keboola.app-orchestrator-trigger application](https://github.com/keboola/app-orchestrator-trigger)



Configuration
=============

##Parameters
 - KBC Storage API token (#kbcToken) - [REQ] API token with full access to all buckets and components including buckets created in the future
 - KBC Stack (kbcUrl) - [REQ] Specific stack in Keboola "" : Keboola AWS US,  "eu-central-1." : AWS EU, "north-europe.azure." : Azure US
 - Orchestration ID (orchestrationId) - [REQ] specific ID of orchestration taken from the link
 - Wait for job finish and check jobs status (waitUntilFinish) - [REQ] if set to true the component will only finish executing once the orchestration it triggered has stopped, if the orchestration ends in failure, then the tirgger job fails as well
 - Fail on warning (failOnWarning) - [OPT] if set to true, the component will fail when the status of the orchestration ends with a warning.




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

If required, change local data folder (the `CUSTOM_FOLDER` placeholder) path to your custom path in
the `docker-compose.yml` file:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    volumes:
      - ./:/code
      - ./CUSTOM_FOLDER:/data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Clone this repository, init the workspace and run the component with following command:

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

For information about deployment and integration with KBC, please refer to the
[deployment section of developers documentation](https://developers.keboola.com/extend/component/deployment/)