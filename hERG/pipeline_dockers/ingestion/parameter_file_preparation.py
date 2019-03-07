from jinja2 import FileSystemLoader, Environment
from json import load
from os import makedirs
from math import ceil
from time import time



def write_to_pfs(filename, content, subfolder, create_subfolder=True):
    if create_subfolder:
        makedirs("/pfs/out/{}".format(subfolder), exist_ok=True)

    with open("/pfs/out/{}/{}".format(subfolder, filename), "w") as f:
        f.write(content)

def range_generator(range_list):
    [start, stop, step] = range_list
    exponents = list(range(start, stop, step))
    exponents.append(stop)
    return [2**x for x in exponents]


configuration = None
try:
    with open("/pfs/hERG-config/configuration.json", "r") as config_file:
        configuration = load(config_file)
except FileNotFoundError:
    print("Config file does not exist, this probably won't work...")
    #TODO: create exit mechanism that functions from pachyderm worker and stores logs/stderr

smi_file_name = configuration["query"]["smi_filename"]


# Generate params template with jinja2
file_loader = FileSystemLoader('./params/')
env = Environment(loader=file_loader)
template = env.get_template("params.j2")
general_template_content = template.render(data=configuration['cpsign'])


# precompute block
precompute = configuration.get("precompute")
if precompute:
    # precompute parameter file
    precompute_file_content = "" + general_template_content + '\n' + template.render(data=precompute)

    precompute_params = [
        "\n--train-data\n/pfs/{}-ingestion/data/{}".format(configuration["workflow_name"], smi_file_name),
        "\n--model-out\n/pfs/out/precomputed.jar",
        "\n--logfile\n/pfs/out/precompute_logfile.log"
    ]
    for line in precompute_params:
        precompute_file_content += line

    write_to_pfs("params.txt", precompute_file_content, "precompute")

# crossvalidate block
crossvalidate = configuration.get("crossvalidate")
if crossvalidate:
    # precompute parameter file
    gridsearch = crossvalidate.get("gridsearch", False)

    # generic parameters for crossvalidate
    crossvalidate_file_content = "" + general_template_content + '\n' + template.render(data=crossvalidate)
    crossvalidate_params = [
        "\n--model-in\n/pfs/{}-precompute/precomputed.jar".format(configuration["workflow_name"]),
        "\n--result-format\n1",
        "\n--seed\n{}".format(int(time())),
    ]
    for line in crossvalidate_params:
        crossvalidate_file_content += line

    # prepare parameter ranges for combinations of params
    cost_range =  range_generator(gridsearch["cost-range"]) if gridsearch.get("cost-range", False) else gridsearch["cost"]
    gamma_range =  range_generator(gridsearch["gamma-range"]) if gridsearch.get("gamma-range", False)  else gridsearch["gamma"]
    epsilon_range = range_generator(gridsearch["epsilon-range"]) if gridsearch.get("epsilon-range", False) else gridsearch["epsilon"]

    # create parameter file for each combination of gamma, epsilon and cost
    for cost in cost_range:
        for gamma in gamma_range:
            for epsilon in epsilon_range:
                datum_name = "g{}_e{}_c{}".format(gamma, epsilon, cost)

                datum_crossvalidate_file_content = \
                    "{} \
                    \n--output\n/pfs/out/scores/scores__{}__.json \
                    \n--logfile\n/pfs/out/logs/datum_{}_logfile.log \
                    \n--cost\n{} \
                    \n--gamma\n{} \
                    \n--epsilon\n{}".format(
                        crossvalidate_file_content, datum_name, datum_name, cost, gamma, epsilon
                    )

                write_to_pfs("params_{}.txt".format(datum_name), datum_crossvalidate_file_content, "crossvalidate_datums")


# training block
training = configuration.get('train')

# input data depends on if precompute is used or not
if precompute:
    input_data = "\n--model-in\n/pfs/{}-precompute/precomputed.jar".format(configuration["workflow_name"])
else:
    input_data = "\n--train-data\n/pfs/{}-ingestion/data/{}".format(configuration["workflow_name"], smi_file_name)

# generic parameters for training
train_file_content = "" + general_template_content + '\n' + template.render(data=training) + input_data


parallelism = training.get("parallelism", False)
if parallelism:
    # train parameter files depend on parallelism and splits in config
    nr_models = training["nr-models"]
    splits = training["parallelism"]["splits_per_job"]
    num_of_files = ceil(nr_models/splits)
    for i in range(1, num_of_files+1):
        parallel_train_file_content = "" + train_file_content
        index_current_file = (i-1)*splits+1
        file_splits = str(list(range(index_current_file, index_current_file+splits))).replace(" ", "")
        # FIXME: uneven splits with even nr models yelds wrong filerange?
        additional_train_params = [
            "\n--model-out\n/pfs/out/models/partial_model_{}.jar".format(i),
            "\n--logfile\n/pfs/out/logs/partial_logfile_{}.log".format(i),
            "\n--splits\n{}".format(file_splits),
            "\n--seed\n{}".format(int(time()))
        ]
        for line in additional_train_params:
            parallel_train_file_content += line

        write_to_pfs("params_{}.txt".format(i), parallel_train_file_content, "training")

else:
    # non-parallelism training params
    param_additional_lines = [
        "\n--model-out\n/pfs/out/models/{}_model.jar".format(configuration["workflow_name"]),
        "\n--logfile\n/pfs/out/logs/{}_logfile.log".format(configuration["workflow_name"])
    ]
    for line in param_additional_lines:
        train_file_content += line

    write_to_pfs("params.txt", train_file_content, "training")
