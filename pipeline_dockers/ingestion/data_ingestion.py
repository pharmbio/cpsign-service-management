# get data from database
# format data to CPSign-compatible format
# generate CPSign parameter file
# move data and params to output repo
import pymysql
from jinja2 import FileSystemLoader, Environment
from json import load
from os import environ, makedirs

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
lines = ["".join([value+"\t" for value in configuration["query"]["smi_columns"] + [""]]) + "\n"]
for (smiles, value) in result:
    lines.append("{}\t{}\t\n".format(smiles, value.to_eng_string() if value else ""))

# Write data to file
smi_file_name = configuration["query"]["smi_filename"]
if result:
    makedirs("/pfs/out/data", exist_ok=True)
    with open("/pfs/out/data/{}".format(smi_file_name), "w") as output:
        output.writelines(lines)
        output.flush()

# Generate params template with jinja2
file_loader = FileSystemLoader('./params/')
env = Environment(loader=file_loader)
template = env.get_template("params.j2")
param_file_content = template.render(data=configuration)

# NOTE: appending flags here as they are important for internal infrastructure in pachyderm pipeline stages and not really relevant for user
training_data_parameter = "trainfile" if configuration["cpsign-version"] == "0.6.16" else "train-data"
param_additional_lines = ["\n", "--{}\n/pfs/{}-ingestion/data/{}\n".format(training_data_parameter, configuration["workflow_name"], smi_file_name),
                          "--model-out\n/pfs/out/models/{}_model.jar".format(configuration["workflow_name"]),
                          "--logfile\n/pfs/out/logs/{}_logfile.log".format(configuration["workflow_name"])]
for line in param_additional_lines:
    param_file_content += line

# Add file to PFS
makedirs("/pfs/out/input")
with open("/pfs/out/input/params.txt", "w") as param_file:
    param_file.write(param_file_content)
