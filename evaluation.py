import subprocess
import tqdm
from chatgpt_api import generate_codes, generate_comment
from data import stream_jsonl, modify_Human_eval, create_csv_file, generate_csv_file_name
from data import HUMAN_EVAL, HUMAN_EVAL_MODIFIED, HUMAN_EVAL_PROMPTS, RESULTS
from structural_similarity import structural_similarity_driver
from syntactic_similarity import syntactic_similarity_driver
import csv
import pprint
import pandas as pd
import json


def run_test(check_program):
    try:
        result = subprocess.run(['python3', '-c', check_program], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=10)
        
        if result.returncode != 0:
            err = result.stderr.decode()
            pass_rate = 0
        else:
            try:
                err = None
                pass_rate = float(result.stdout.decode().split('\n')[-2])
            except ValueError as e:
                pass_rate = 0
                err = e
    except subprocess.TimeoutExpired:
        err = "Timeout"
        pass_rate = 0

    return err, pass_rate

def eval_Human_eval(model="gpt-3.5-turbo", n=5, t_refrence=0, t_samples=1, trial=1):
    csv_file_name, fieldnames, last_task_id_num = create_csv_file(dataset="HumanEval-blabla", model=model, n=n, 
                                                 t_refrence=t_refrence, t_samples=t_samples, trial=trial)
    pass_rate = 0
    err = None
    row = {}

    with open(csv_file_name, mode='a', newline='') as csv_f:
        writer = csv.DictWriter(csv_f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        for problem in stream_jsonl(HUMAN_EVAL_MODIFIED):
            if int(problem['task_id'].split('/')[-1]) > last_task_id_num:
                print(f"Processing {problem['task_id']}")
                row['task_id'] = problem['task_id']
                row['prompt'] = problem['prompt']
                codes = generate_codes(prompt=problem['prompt'], model=model, t_refrence=t_refrence, 
                                       t_samples=t_samples, n=n)
                
                for i, code in enumerate(codes):
                    row[f"code_{i}"] = code
                    check_program = f"{code}\n{problem['test']}\nprint(check({problem['entry_point']}))"
                    err, pass_rate = run_test(check_program)

                    row[f"err_{i}"] = err
                    row[f"pass_rate_{i}"] = pass_rate*100
                writer.writerow(row)


# Generate a comment for each code in the given dataset and appends it to the end of the row in the csv file.
# Pass either the csv_file_name directly or all the other parametrs to generate it according to the used convention. 
def add_comments(comment_generation_model = "gpt-3.5-turbo", rename_code_functions = False, csv_file_name = None, dataset = None, code_generation_model = None, n = None, t_refrence = None, t_samples = None, trial = None):
    if csv_file_name is None:
        csv_file_name = generate_csv_file_name(dataset, code_generation_model, n, t_refrence, t_samples, trial)
    
    df = pd.read_csv(csv_file_name)
    columns = list(df)
    for code_col in columns[2:]:
        if not str(code_col).startswith("code"):
            break
        new_column_name = comment_generation_model + "_" + str(code_col).replace("code", "comment")
        if rename_code_functions:
            new_column_name = "functions-renamed_" + new_column_name
        if list(df).count(new_column_name) !=0:
            print(new_column_name, " comments are already generated for this table")
            continue
        print("Starting with column", code_col)
        generated_comments = []
        task = 0
        for code in df[code_col]:
            generated_comments.append(generate_comment(model= comment_generation_model, code = code, rename_functions =rename_code_functions))
            print("Task", task, "done")
            task +=1
        df[new_column_name] = generated_comments
        print(new_column_name, "done")
        df.to_csv(csv_file_name, index=False)  
        df = pd.read_csv(csv_file_name)


def parse_csv(csv_file_name):
    codes = []
    with open(csv_file_name, mode='r') as csv_f:
        reader = csv.DictReader(csv_f)
        for row in reader:
            for i in range(6):
                codes.append(row[f'code_{i}'])
    return codes
            

def read_test():
    with open(HUMAN_EVAL_MODIFIED, 'r') as f:
        for line in f:
            problem = json.loads(line)
            if problem['task_id'] == "HumanEval/36":
                print(f"{problem['test']}")
                break


if __name__ == '__main__':
    add_comments(comment_generation_model="gpt-3.5-turbo", rename_code_functions=True, csv_file_name="RESULTS/dataset_HumanEval_model_gpt-4-turbo-preview_n_5_tempr_0_temps_1_trial_1.csv")
    print("Done 5 with renaming functions")
    print("--------------")
    # add_comments("gpt-3.5-turbo","RESULTS/dataset_HumanEval_model_gpt-3.5-turbo_n_5_tempr_0_temps_1.5_trial_1.csv")
    # print("Done T 1.5")
    # print("--------------")
    # add_comments("gpt-3.5-turbo","RESULTS/dataset_HumanEval_model_gpt-4-turbo-preview_n_5_tempr_0_temps_1_trial_1.csv")
    # print("Done Gpt4")
    # print("--------------")
    # eval_Human_eval(model='gpt-3.5-turbo', n=5, t_refrence=0, t_samples=1, trial=1)
    # eval_Human_eval(model='gpt-3.5-turbo', n=3, t_refrence=0, t_samples=1, trial=1)
    # eval_Human_eval(model='gpt-3.5-turbo', n=10, t_refrence=0, t_samples=1, trial=1)
    # eval_Human_eval(model='gpt-3.5-turbo', n=5, t_refrence=1, t_samples=1, trial=1)
    # eval_Human_eval(model='gpt-3.5-turbo', n=5, t_refrence=0, t_samples=1.5, trial=1)
    # eval_Human_eval(model='gpt-3.5-turbo', n=15, t_refrence=0, t_samples=1, trial=1)
    # eval_Human_eval(model='gpt-3.5-turbo', n=15, t_refrence=1, t_samples=1, trial=1)
   # eval_Human_eval(model='gpt-3.5-turbo', n=15, t_refrence=1, t_samples=1.3, trial=1)

    # eval_Human_eval(model='gpt-4-turbo-preview', n=5, t_refrence=0, t_samples=1, trial=1)
    # eval_Human_eval(model='gpt-4-turbo-preview', n=3, t_refrence=0, t_samples=1, trial=1)
    # eval_Human_eval(model='gpt-4-turbo-preview', n=10, t_refrence=0, t_samples=1, trial=1)
    # eval_Human_eval(model='gpt-4-turbo-preview', n=5, t_refrence=1, t_samples=1, trial=1)
    # eval_Human_eval(model='gpt-4-turbo-preview', n=5, t_refrence=0, t_samples=1.5, trial=1)
    # read_test()
    