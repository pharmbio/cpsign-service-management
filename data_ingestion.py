### WORKFLOW: 
# get data from chembl database
# format data to CPSign-compatible format
# add data to pachyderm repo

def fileToBinary(filepath):
    bytesArray = None
    with open(filepath, 'r') as _file:
        bytesArray = bytes(_file.read(None), "UTF-8")

    return bytesArray


import python_pachyderm
import pymysql

DB_PASSWORD = ""
DB_USERNAME = "root"
DB_HOST = "logd-chembl-mysql"
DB_DATABASE = "chembl_24"

try:
    with open("/etc/creds/rootpw", "r") as pwfile:
        DB_PASSWORD = pwfile.readline()
except FileNotFoundError:
    pass

if DB_PASSWORD == "":
    DB_PASSWORD = str(input("Password for db user root: "))

#data_limit = input("Limit: >")
data_query = "SELECT cs.canonical_smiles, cp.acd_logd FROM compound_structures cs, compound_properties cp  WHERE cs.molregno = cp.molregno limit 10000;"
result = None

# Connect to DB and get result of query
sql_connection = pymysql.Connect(host=DB_HOST, user=DB_USERNAME, password=DB_PASSWORD, database=DB_DATABASE)

try:
    with sql_connection.cursor() as cursor:
        cursor.execute(data_query)    
        result = cursor.fetchall()
finally:
    sql_connection.close()

# Reformat data
lines = ["canonical_smiles\tacd_logd\t\n"]
for (smiles, value) in result:
    lines.append("{}\t{}\t\n".format(smiles, value.to_eng_string() if value else ""))

# Write data to file
smi_file_name = "chembl_training_data.smi"
if result:
    with open("./{}".format(smi_file_name), "w") as output:
        output.writelines(lines)
        output.flush()

# Add file to PFS
pfs_client = python_pachyderm.PfsClient()
with pfs_client.commit("data", "master") as cmt:
    pfs_client.put_file_bytes(cmt, "/{}".format(smi_file_name), fileToBinary("./{}".format(smi_file_name)))

