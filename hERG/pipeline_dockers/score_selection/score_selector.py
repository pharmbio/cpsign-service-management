from json import load
from os import listdir, makedirs

configuration = None
try:
    with open("/pfs/hERG-config/configuration.json", "r") as config_file:
        configuration = load(config_file)
except FileNotFoundError:
    print("Config file does not exist, this probably won't work...")


# iterate over all score files
scores_directory = "/pfs/{}-crossvalidate/scores/".format(configuration['workflow_name'])
efficiency = 1.0
candidate_scores = {}
best_score = ""

# gather candidate parameter sets with lowest efficiency value
for score_file in listdir(scores_directory):
    with open(scores_directory + score_file, 'r') as content:
        score = load(content)
    print("Checking file {}".format(score_file))
    # accessing value for arbitrary key containing "efficiency"
    for key in list(score['plot'].keys()):
        if "efficiency" in key:
            current_efficiency = score['plot'][key][0]
            print("Current eff: {}, previous eff: {}".format(current_efficiency, efficiency))
            if current_efficiency <= efficiency:
                efficiency = current_efficiency
                best_score = score_file
                candidate_scores[best_score] = efficiency

# filter out only filenames with lowest efficiency in candidates
filtered_candidate_scores = {cost: candidate_scores[cost] for cost in candidate_scores.keys() if candidate_scores[cost] == efficiency}

# find lowest cost among candidates if several have the same efficiency
if len(filtered_candidate_scores) > 1:
    low = float(list(filtered_candidate_scores.keys())[0].split('__')[1].split('_')[2][1:])
    for candidate in filtered_candidate_scores:
        cand_cost = float(candidate.split('__')[1].split('_')[2][1:])
        if cand_cost < low:
            best_score = candidate


parameter_arguments = []
parameters = (best_score.split('__')[1].split('_'))
for parameter in parameters:
    if parameter[0] == 'g': # gamma
        parameter_arguments.append("\n--gamma\n{}".format(parameter[1:]))
    if parameter[0] == 'e': # epsilon
        parameter_arguments.append("\n--epsilon\n{}".format(parameter[1:]))
    if parameter[0] == 'c': # cost
        parameter_arguments.append("\n--cost\n{}".format(parameter[1:]))
    if parameter[0] == 'E': # epsilon-svr
        parameter_arguments.append("\n--epsilon-svr\n{}".format(parameter[1:]))
    if parameter[0] == 'b': # beta
        parameter_arguments.append("\n--nonconf-beta\n{}".format(parameter[1:]))


print("Found best efficieny with following parameters: \n{}".format(parameter_arguments))

makedirs("/pfs/out/training", exist_ok=True)
train_file_directory = "/pfs/{}-ingestion/training/".format(configuration['workflow_name'])
for train_file in listdir(train_file_directory):
    with open(train_file_directory + train_file, 'r') as origin, open("/pfs/out/training/" + train_file, 'w') as new:
        training_content = origin.read()
        for p in parameter_arguments:
            training_content += p
        new.writelines(training_content)
