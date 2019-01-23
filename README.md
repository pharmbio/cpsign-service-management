# CPSign-based service management (WIP)
## CPSign service workflow
![workflow_overview](/imgs/cpsign_workflow.png)

## Initial setup of workflow
### Create manager pod
In order to communicate with Pachyderm and the preferred database, you need to work from a pod within the cluster. Thus first create a pod from the following yaml file: `manager-pod.yaml` with the command `kubectl create -f manager-pod.yaml --namespace=labinf` .

To connect to the pod, use `kubectl exec -it <pod-name> bash` .

### Creating and populate database
By following [this helm chart](https://github.com/helm/charts/tree/master/stable/mysql)'s instructions, it should be relatively quick to deploy a mysql server pod within the cluster. Depending on one's scenario, it may be necessary to enter custom flags' values different than the default ones available in the related `values.yaml` file. In this specific case, installing the helm chart with default values is more than enough since the underlying k8s cluster supports dynamic provisioning for persistent storages. Only exceptions might be to double-check `resource.request` and `resource.limits` for the mysql pod.

### Managing secrets
create or reuse

### Configure kubernetes (optional)
If desired, the manager pod comes with `kubectl`installed, but you need to provide your kube `config` file. Copy your kubernetes config file to this location within the pod: `/root/.kube/config`.

**Protip:** `kubectl cp <src> <pod-name>:/root/.kube/config`

### Connecting workspace to pachd
To communicate with Pachyderm via its command-line tool `pachctl`, one needs to either set the environment variable `ADDRESS` equal to the IP of the `pachd` service (i.e. `export ADDRESS=<pachd IP>`), or to execute the `pachctl`'s built-in `port-forward` command like so: `pachctl port-forward --namespace=<desired namespace> &` .

### Set up pachyderm pipelines
Modify pipeline specifications as neccessary and create a repo called `config`, then create the pipelines from the specs.

## Running training in workflow
The following steps assumes that you are connected to the `logd-manager` pod
### Upload configuration file to pachyderm for cpsign execution
Modify the json file `configuration.json` as neccessary and add it to the pachyderm repo `config`via the command: `pachctl put-file config master -o -f configuration.json` .

### (Advanced) modify pachyderm pipeline
If you wish to modify the pipeline, edit the specification json under the `cpsign-setup` folder (which exists within the pod), then run: `pachctl update-pipeline -f spec-train.json` .
