### WORKFLOW: 
# get data from chembl database
# format data to CPSign-compatible format
# add data to pachyderm repo

import python_pachyderm
import pymysql
from jinja2 import Template
from json import load
from os import environ

configuration = None
try:
    with open(environ.get("CONFIG_FILE"), "r") as config_file:
        configuration = load(config_file)
except FileNotFoundError:
    print("Config file does not exist, this probably won't work...")
    #TODO: create exit mechanism that functions from pachyderm worker and stores logs/stderr

DB_PASSWORD = configuration.get("DB_PASSWORD", None) #NOTE: should not be provided plain in json...
DB_USERNAME = configuration["database"]["user"]
DB_HOSTNAME = configuration["database"]["host"]
DB_DATABASE = configuration["database"]["db_name"]

if not DB_PASSWORD:
    try:
        with open("/etc/creds/rootpw", "r") as pwfile:
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
    with open("/pfs/out/data/{}".format(smi_file_name), "w") as output:
        output.writelines(lines)
        output.flush()

# Generate params template with jinja2
# TODO: jinja generate params.txt and populate with training data file name
jinja_template_file = ""
jinja_params = configuration["cpsign"]
with open(jinja_template_file) as tmpl:
    template = Template(tmpl.read())
param_file_content = template.render(data=jinja_params)

param_additional_lines = ["\n", "--train-data\n/pfs/{}-ingestion/data/{}\n".format(configuration["workflow_name"], smi_file_name)]
for line in param_additional_lines:
    param_file_content += line

# Add file to PFS
# TODO: rewrite to use pfs out as pipeline repo, 
with open("/pfs/out/input/params.txt", "w") as param_file:
    param_file.write(param_file_content)
