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
    with open("/pfs/hERG-config/configuration.json", "r") as config_file:
        configuration = load(config_file)
except FileNotFoundError:
    print("Config file does not exist, this probably won't work...")
    #TODO: create exit mechanism that functions from pachyderm worker and stores logs/stderr

preprocess_config = configuration.get("preprocessing")

DB_USERNAME = preprocess_config["database"]["user"]
DB_HOSTNAME = preprocess_config["database"]["host"]
DB_DATABASE = preprocess_config["database"]["db_name"]

DB_PASSWORD = None
try:
    with open("/etc/creds/mysql-root-password", "r") as pwfile:
        DB_PASSWORD = pwfile.readline()
except FileNotFoundError:
    pass

data_limit = preprocess_config["query"]["query_limit"]
data_query = preprocess_config["query"]["database_query"].format(" limit {}".format(data_limit) if data_limit else "")
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
header = "".join([value+"\t" for value in preprocess_config["query"]["query_columns"]])[:-1] + "\n"
lines = [header]
for row in result:
    line = "".join(["{}\t".format(value if not isinstance(value, Decimal) else value.to_eng_string()) for value in row])[:-1] + "\n"
    lines.append(line)

# Write data to file
smi_file_name = preprocess_config["query"]["smi_filename"]
if result:
    makedirs("/pfs/out/data", exist_ok=True)
    with open("/pfs/out/data/{}.csv".format(smi_file_name), "w") as output:
        output.writelines(lines)
        output.flush()

with open("/pfs/out/data/{}.csv".format(smi_file_name),'r') as f:
    df = pd.read_csv(f, sep='\t')
    D={}
    print(df)
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
        smi_header = "".join([value+"\t" for value in preprocess_config["query"]["smi_columns"]])[:-1] + "\n"
        with open("/pfs/out/data/" + smi_file_name + '.smi', 'w+') as f:
            f.writelines([smi_header])
            f.write(''.join(value))
