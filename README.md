# CPSign-based service management (WIP)
## CPSign service workflow
![workflow_overview](/imgs/cpsign_workflow.png)

## Initial setup of workflow
### Create manager pod
In order to communicate with Pachyderm and the database we need to work from a pod within the cluster. First create a pod from the following yaml file: `logd-manager-pod.yaml` with the command `kubectl create -f logd-manager-pod.yaml --namespace=labinf`

To connect to the pod, use `kubectl exec -it <pod-name> bash`

### Creating and populate database
If a new database is desired, follow helm chart instructions and create a mysql server.

### Managing secrets
create or reuse

### Configure kubernetes (optional)
If desired, the manager pod comes with kubectl, but you need to provide your kube config file. Copy your rancher kubernetes config file to this location within the pod: `/root/.kube/config`.

**Protip:** `kubectl cp <src> <pod-name>:/root/.kube/config`

### Connecting workspace to pachd
To communicate with Pachyderm with pachctl, you need to either set the environment variable `ADDRESS` to the IP of the pachd service (i.e. `export ADDRESS=<pachd IP>`), or with pachctl's builtin port forward command: `pachctl port-forward --namespace=<desired namespace> &`

### Set up pachyderm pipelines
modify pipeline specifications as neccessary and create a repo called `config`, then create the pipelines from the specs

## Running training in workflow
The following steps assumes that you are connected to the `logd-manager` pod
### Upload configuration file to pachyderm for cpsign execution
Modify configuration.json as neccessary and add to pachyderm repo config: `pachctl put-file config master -o -f configuration.json`

### (Advanced) modify pachyderm pipeline
If you wish to modify the pipeline, edit the specification json in the cpsign-setup folder (which exists within the pod), then run: `pachctl update-pipeline -f spec-train.json`
