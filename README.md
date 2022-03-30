Orchestration Trigger app for Queue V2
=============

Trigger to start a Keboola Orchestration


**Table of contents:**

[TOC]

Prerequisites
=============

Get the [Storage API token](https://help.keboola.com/management/project/tokens/)

Get the orchestration id from the link :  https://connection.keboola.com/admin/projects/{PROJECT_ID}/orchestrations-v2/{ORCHESTRATION_ID}


Configuration
=============

##Parameters
 - KBC Storage API token (#kbcToken) - [REQ] 
 - KBC Stack (kbcUrl) - [REQ] Specific stack in Keboola "" : Keboola AWS US,  "eu-central-1." : AWS EU, "north-europe.azure." : Azure US
 - Orchestration ID (orchestrationId) - [REQ] specific ID of orchestration taken from the link
 - Wait for job finish and check jobs status (waitUntilFinish) - [REQ] if set to true the component will only finish executing once the orchestration it triggered has stopped




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