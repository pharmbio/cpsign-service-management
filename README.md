# Setup

## Configure kubernetes
Put a copy of your kubernetes config file here: /root/.kube/config
protip: "kubectl cp <src> <pod-name>:/root/.kube/config"

## Connecting workspace to pachd
pachctl port-forward --namespace=labinf &

# Running cpsign

## Upload parameter file to pachyderm for cpsign execution
modify params.txt as neccessary and add to pachyderm repo input:
pachctl put-file input master -o -f params.txt

## (Advanced) modify pachyderm pipeline
If you wish to modify the pipeline, edit the specification json in the cpsign-setup folder, the run
pachctl update-pipeline -f spec-train.json

## Add new smiles data from chembl
When new chembl data is available in the logd-mysql-chembl database, run the data ingestion script to query and insert into the pachyderm data repo:
python3 data_ingestion.py