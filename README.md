![workflow_overview](/imgs/cpsign_workflow.png)

# Setup
## Create Logd-manager pod
First create a pod from the following yaml file: `logd-manager-pod.yaml` with the command `kubectl create -f logd-manager-pod.yaml --namespace=labinf`

## Configure kubernetes
Once the previous step is done, copy your rancher kubernetes config file to this location within the pod: `/root/.kube/config`.

**Protip:** `kubectl cp <src> <pod-name>:/root/.kube/config`

## Connecting workspace to pachd
Connect to the logd-manger pod with `kubectl exec -it <pod-name> bash` and perform the following command: `pachctl port-forward --namespace=labinf &`

# Running cpsign
The following steps assumes that you are connected to the `logd-manager` pod
## Upload parameter file to pachyderm for cpsign execution
Modify params.txt as neccessary and add to pachyderm repo input: `pachctl put-file input master -o -f params.txt`

## (Advanced) modify pachyderm pipeline
If you wish to modify the pipeline, edit the specification json in the cpsign-setup folder (which exists within the pod), then run: `pachctl update-pipeline -f spec-train.json`

## Add new smiles data from chembl
When new chembl data are available in the `logd-mysql-chembl` database, manually run the data ingestion script to query and insert into the pachyderm data repo: `python3 data_ingestion.py`
