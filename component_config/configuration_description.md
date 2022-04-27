### Prerequisites 

Get the orchestration id from the link :  ...keboola.com/admin/projects/{PROJECT_ID}/orchestrations-v2/{ORCHESTRATION_ID}

Make sure the orchestration you wish to run is an Orchestration V2. 

If the link to your of your orchestration contains **orchestrations-v2** : 
...keboola.com/admin/projects/{PROJECT_ID}/orchestrations-v2/{ORCHESTRATION_ID}
Your orchestration is V2 and therefore uses Queue V2.

If the link to your of your orchestration contains **orchestrations** :
...keboola.com/admin/projects/{PROJECT_ID}/orchestrations/{ORCHESTRATION_ID}
Your orchestration is **NOT** V2 and you should use the [keboola.app-orchestrator-trigger application](https://github.com/keboola/app-orchestrator-trigger)

### Authorization

Generate a dedicated [Limited Access SAPI Token](https://help.keboola.com/management/project/tokens/#limited-access-to-components) 
with restricted access and custom access to the Orchestrator component.