# get data from database
# format data to CPSign-compatible format
# generate CPSign parameter file
# move data and params to output repo
import pymysql, csv, operator, pandas as pd
from jinja2 import FileSystemLoader, Environment
from json import load
from os import environ, makedirs
from time import time
from math import ceil
from decimal import Decimal

configuration = None
try:
    with open("/pfs/config/configuration.json", "r") as config_file:
        configuration = load(config_file)
except FileNotFoundError:
    print("Config file does not exist, this probably won't work...")
    #TODO: create exit mechanism that functions from pachyderm worker and stores logs/stderr

DB_USERNAME = configuration["database"]["user"]
DB_HOSTNAME = configuration["database"]["host"]
DB_DATABASE = configuration["database"]["db_name"]

DB_PASSWORD = None
try:
    with open("/etc/creds/mysql-root-password", "r") as pwfile:
        DB_PASSWORD = pwfile.readline()
except FileNotFoundError:
    pass

data_limit = configuration["query"]["query_limit"]
data_query = configuration["query"]["database_query"].format(" limit {}".format(data_limit) if data_limit else "")
result = None

# Connect to DB and get result of query
sql_connection = pymysql.Connect(host=DB_HOSTNAME, user=DB_USERNAME, password=DB_PASSWORD, database=DB_DATABASE)

try:
    with sql_connection.cursor() as cursor:
        cursor.execute(data_query)
        result = cursor.fetchall()
finally:
    sql_connection.close()

# Reformat data
header = "".join([value+"\t" for value in configuration["query"]["smi_columns"]]) + "\n"
lines = [header]
for row in result:
    line = "".join(["{}\t".format(value if not isinstance(value, Decimal) else value.to_eng_string()) for value in row])[:-1] + "\n"
    lines.append(line)

# Write data to file
smi_file_name = configuration["query"]["smi_filename"]
if result:
    makedirs("/pfs/out/data", exist_ok=True)
    with open("/pfs/out/data/{}.csv".format(smi_file_name), "w") as output:
        output.writelines(lines)
        output.flush()

with open("/pfs/out/data/{}.csv".format(smi_file_name),'r') as f:
    df = pd.read_csv(f, sep='\t')
    D={}
    num_lines = len(df.axes[0])
    for i in range(0, num_lines-2):
        df.iloc[i, 0] = df.iloc[i, 0].replace('/','-')
        df.iloc[i, 0] = df.iloc[i, 0].replace(' ','_')
    for i in range(0, num_lines-2):
        if df.iloc[i, 0] not in D:
            D[df.iloc[i, 0]] = []
    for j in range(0, num_lines-2):
        if df.iloc[j,1] not in D[df.iloc[j,0]]:
            D.setdefault(df.iloc[j,0],[]).append(df.iloc[j,1]+'\t')
            if df.iloc[j,2]=='IC50' and df.iloc[j,3]>10000:
                D.setdefault(df.iloc[j,0],[]).append('0\n')
            elif df.iloc[j,2]=='IC50' and df.iloc[j,3]<=10000:
                D.setdefault(df.iloc[j,0],[]).append('1\n')
            elif df.iloc[j,2]=='Ki' and df.iloc[j,3]>5000:
                D.setdefault(df.iloc[j,0],[]).append('0\n')
            elif df.iloc[j,2]=='Ki' and df.iloc[j,3]<=5000:
                D.setdefault(df.iloc[j,0],[]).append('1\n')
            elif df.iloc[j,2]=='Kd' and df.iloc[j,3]>5000:
                D.setdefault(df.iloc[j,0],[]).append('0\n')
            elif df.iloc[j,2]=='Kd' and df.iloc[j,3]<=5000:
                D.setdefault(df.iloc[j,0],[]).append('1\n')
            elif df.iloc[j,2]=='EC50' and df.iloc[j,3]>10000:
                D.setdefault(df.iloc[j,0],[]).append('0\n')
            elif df.iloc[j,2]=='EC50' and df.iloc[j,3]<=10000:
                D.setdefault(df.iloc[j,0],[]).append('1\n')
    for key,value in D.items():
        with open(key + '.json', 'w+') as f:
            f.write(''.join(value))


# Generate params template with jinja2
file_loader = FileSystemLoader('./params/')
env = Environment(loader=file_loader)
template = env.get_template("params.j2")
param_file_content = template.render(data=configuration)

# CPSign version differences etc...
if configuration["cpsign-version"] == "0.6.16":
    training_data_parameter = "trainfile"
    problem_type_parameter = 'cptype'
else:
    training_data_parameter = "train-data"
    problem_type_parameter = 'ptype'

parallellism = configuration.get("parallellism", False)
if not parallellism:
    # NOTE: appending flags here as they are important for internal infrastructure in pachyderm pipeline stages and not really relevant for user
    param_additional_lines = [
        "\n--{}\n/pfs/{}-ingestion/data/{}".format(training_data_parameter, configuration["workflow_name"], smi_file_name),
        "\n--model-out\n/pfs/out/models/{}_model.jar".format(configuration["workflow_name"]),
        "\n--logfile\n/pfs/out/logs/{}_logfile.log".format(configuration["workflow_name"]),
        "\n--nr-models\n1"
    ]
    for line in param_additional_lines:
        param_file_content += line

    # Add file to PFS
    makedirs("/pfs/out/input", exist_ok=True)
    with open("/pfs/out/input/params.txt", "w") as param_file:
        param_file.write(param_file_content)

else:
    # generate one config per model for train, and additional config for precompute
    makedirs("/pfs/out/training", exist_ok=True)

    # train parameter files
    nr_models = configuration["cpsign"]["nr-models"]
    splits = configuration["parallellism"]["splits_per_model"]
    num_of_files = ceil(nr_models/splits)
    for i in range(1, num_of_files+1):
        train_file_content = template.render(data=configuration)
        index_current_file = (i-1)*splits+1
        file_splits = str(list(range(index_current_file, index_current_file+splits))).replace(" ", "")
        additional_train_params = [
            "\n--model-in\n/pfs/{}-precompute/precomputed.jar".format(configuration["workflow_name"]),
            "\n--model-out\n/pfs/out/models/partial_model_{}.jar".format(i),
            "\n--logfile\n/pfs/out/logs/partial_logfile_{}.log".format(i),
            "\n--splits\n{}".format(file_splits),
            "\n--seed\n{}".format(int(time()))
        ]
        for line in additional_train_params:
            train_file_content += line

        # Add file to PFS
        with open("/pfs/out/training/params_{}.txt".format(i), "w") as train_file:
            train_file.write(train_file_content)

    # precompute parameter file
    precompute_file_content = ""
    precompute_params = [
        "\n--{}\n/pfs/{}-ingestion/data/{}".format(training_data_parameter, configuration["workflow_name"], smi_file_name),
        "\n--model-out\n/pfs/out/precomputed.jar",
        "\n--model-name\n{}-precomputed".format(configuration["workflow_name"]),
        "\n--logfile\n/pfs/out/precompute_logfile.log",
        "\n--model-type\n{}".format(configuration["cpsign"][problem_type_parameter])
    ]
    for line in precompute_params:
        precompute_file_content += line

    # Add file to PFS
    makedirs("/pfs/out/precompute", exist_ok=True)
    with open("/pfs/out/precompute/params.txt", "w") as precompute_file:
        precompute_file.write(precompute_file_content)
