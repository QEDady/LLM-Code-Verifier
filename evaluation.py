import argparse
import re
import subprocess
import time
import aiohttp
import tqdm
from chatgpt_api import generate_codes, generate_comment, generate_codes_async
from data import APPS, get_problems_range, stream_jsonl, modify_Human_eval, create_csv_file, generate_csv_file_name
from data import HUMAN_EVAL, HUMAN_EVAL_MODIFIED, HUMAN_EVAL_PROMPTS, RESULTS
from structural_similarity import structural_similarity_driver
from syntactic_similarity import syntactic_similarity_driver
import csv
import pprint
import pandas as pd
import json
import concurrent.futures
import asyncio



def run_test_HUMAN_EVAL(check_program):
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

def run_test_APPS(solution, input_str):
    res = None
    try:
        result = subprocess.run(['python3', '-c', solution], input=input_str.encode(), stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=10)
        if result.returncode != 0:
            err = result.stderr.decode()
            # print(err)
        else:
            try:
                res = result.stdout.decode().strip()
                # print(res)
            except ValueError as e:
                err = e
                # print(e)
    except subprocess.TimeoutExpired:
        print("Timeout")

    return res

def eval_Human_eval(model="gpt-3.5-turbo", n=5, t_refrence=0, t_samples=1, trial=1):
    csv_file_name, fieldnames, last_task_id_num = create_csv_file(dataset="HumanEval", model=model, n=n, 
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
                    err, pass_rate = run_test_HUMAN_EVAL(check_program)
                    row[f"err_{i}"] = err
                    row[f"pass_rate_{i}"] = pass_rate*100
                writer.writerow(row)

def eval_APPS(args, model="gpt-3.5-turbo", n=5, t_refrence=0, t_samples=1, trial=1):
    csv_file_name, fieldnames, last_task_id_num = create_csv_file(dataset="APPS", model=model, n=n, 
                                                 t_refrence=t_refrence, t_samples=t_samples, trial=trial)
    range = get_problems_range(args, 'APPS')
    row = {}
    print(range)
    with open(csv_file_name, mode='a', newline='') as csv_f:
        writer = csv.DictWriter(csv_f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL) 
        for problem in stream_jsonl(APPS):        
            problem_id = int(problem['task_id'].split('/')[-1])
            if problem_id >= range[0] and problem_id <= range[1]:
                if problem_id > last_task_id_num:
                    print(f"\nProcessing {problem['task_id']}")
                    row['task_id'] = problem['task_id']
                    row['prompt'] = problem['prompt']
                    codes = generate_codes(prompt=problem['prompt'], model=model, t_refrence=t_refrence, 
                                        t_samples=t_samples, n=n)
                    for code_idx, code in enumerate(codes):
                        if re.search(r"solve\(\)\s*$", code) is None:
                            code += "\nsolve()"
                        row[f"code_{code_idx}"] = code
                        tests_passed = 0
                        print(f"\tcode {code_idx+1}/6")
                        num_tests = len(problem['test']['inputs'])
                        for (input_str, output_str) in zip(problem['test']['inputs'], problem['test']['outputs']):
                            input_str = input_str.strip()
                            output_str = output_str.strip()
                            try:
                                res = run_test_APPS(code, input_str)
                            except Exception as e:
                                res = None
                            if res is None:
                                continue
                            tests_passed += (res == output_str.strip())
                        row[f"err_{code_idx}"] = None
                        row[f"pass_rate_{code_idx}"] = (tests_passed/num_tests)*100
                    writer.writerow(row)

async def eval_Human_eval_async(model="gpt-3.5-turbo", n=5, t_refrence=0, t_samples=1, trial=1):
    csv_file_name, fieldnames, last_task_id_num = create_csv_file(dataset="HumanEval-blabla", model=model, n=n, 
                                                 t_refrence=t_refrence, t_samples=t_samples, trial=trial)
    async with aiohttp.ClientSession() as session:
        tasks = []
        i = 0
        for problem in stream_jsonl(HUMAN_EVAL_MODIFIED):     
            i += 1   
            if int(problem['task_id'].split('/')[-1]) > last_task_id_num:
                print(f"Sending API Requests for {problem['task_id']}")
                task = generate_codes_async(session, problem=problem, 
                                            model=model, t_refrence=t_refrence, t_samples=t_samples, n=n)
                tasks.append(task)
            # if i == 10:
                # time.sleep(0.2)
                # i = 0
        results = await asyncio.gather(*tasks)

    with open(csv_file_name, mode='a', newline='') as csv_f:
        writer = csv.DictWriter(csv_f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL) 
        for problem, codes in results:
            print(f"Processing {problem['task_id']}")
            for i, code in enumerate(codes):
                row = {}
                row['task_id'] = problem['task_id']
                row['prompt'] = problem['prompt']
                row[f"code_{i}"] = code
                check_program = f"{code}\n{problem['test']}\nprint(check({problem['entry_point']}))"
                err, pass_rate = run_test_HUMAN_EVAL(check_program)
                row[f"err_{i}"] = err
                row[f"pass_rate_{i}"] = pass_rate*100
                writer.writerow(row)

def eval_Human_eval_multi_process(model="gpt-3.5-turbo", n=5, t_refrence=0, t_samples=1, trial=1):
    csv_file_name, fieldnames, last_task_id_num = create_csv_file(dataset="HumanEval-blabla", model=model, n=n, 
                                                 t_refrence=t_refrence, t_samples=t_samples, trial=trial)

    with open(csv_file_name, mode='a', newline='') as csv_f:
        writer = csv.DictWriter(csv_f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = {executor.submit(process_problem, problem, model, n, t_refrence, t_samples, 
                                       last_task_id_num): problem for problem in stream_jsonl(HUMAN_EVAL_MODIFIED)}
            for future in concurrent.futures.as_completed(futures):
                row = future.result()
                if row is not None:
                    writer.writerow(row)            


def process_problem(problem, model, n, t_refrence, t_samples, last_task_id_num):
    if int(problem['task_id'].split('/')[-1]) > last_task_id_num:
        row = {}
        print(f"Processing {problem['task_id']}")
        row['task_id'] = problem['task_id']
        row['prompt'] = problem['prompt']
        # start = time.time()
        codes = generate_codes(prompt=problem['prompt'], model=model, t_refrence=t_refrence, 
                               t_samples=t_samples, n=n)
        # end = time.time()
        # print(f"Task done in {end-start} seconds")
        for i, code in enumerate(codes):
            row[f"code_{i}"] = code
            check_program = f"{code}\n{problem['test']}\nprint(check({problem['entry_point']}))"
            err, pass_rate = run_test_HUMAN_EVAL(check_program)
            row[f"err_{i}"] = err
            row[f"pass_rate_{i}"] = pass_rate*100
        return row
    else:
        return None

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
            

def read_test(dataset, idx):
    if dataset == "APPS":
        file_name = APPS
    elif dataset == "HumanEval":
        file_name = HUMAN_EVAL_MODIFIED
    with open(file_name, 'r') as f:
        for line in f:
            problem = json.loads(line)
            problem_id = int(problem['task_id'].split('/')[-1])
            if problem_id == idx:
                print(f"{problem['test']}")
                break

def create_parser():
    parser = argparse.ArgumentParser(description="Evaluate the specified dataset ")
    parser.add_argument("-s","--start", default=0, type=int)
    parser.add_argument("-e","--end", default=None, type=int)
    parser.add_argument("-i", "--index", default=None, type=int)
    parser.add_argument("-d", "--debug", action="store_true")
    return parser

if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()

    # add_comments(comment_generation_model="gpt-3.5-turbo", rename_code_functions=True, csv_file_name="RESULTS/dataset_HumanEval_model_gpt-4-turbo-preview_n_5_tempr_0_temps_1_trial_1.csv")
    # print("Done 5 with renaming functions")
    # print("--------------")
    # add_comments("gpt-3.5-turbo","RESULTS/dataset_HumanEval_model_gpt-3.5-turbo_n_5_tempr_0_temps_1.5_trial_1.csv")
    # print("Done T 1.5")
    # print("--------------")
    # add_comments("gpt-3.5-turbo","RESULTS/dataset_HumanEval_model_gpt-4-turbo-preview_n_5_tempr_0_temps_1_trial_1.csv")
    # print("Done Gpt4")
    # print("--------------")
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(eval_Human_eval_async(model='gpt-3.5-turbo', n=5, t_refrence=0, t_samples=1, trial=1))
    trial = input("Press Enter trial number: ")
    eval_APPS(args, model='gpt-3.5-turbo', n=5, t_refrence=0, t_samples=1, trial=trial)

    # eval_Human_eval(model='gpt-3.5-turbo', n=5, t_refrence=0, t_samples=1, trial=trial)
    # eval_Human_eval(model='gpt-3.5-turbo', n=3, t_refrence=0, t_samples=1, trial=trial)
    # eval_Human_eval(model='gpt-3.5-turbo', n=10, t_refrence=0, t_samples=1, trial=trial)
    # eval_Human_eval(model='gpt-3.5-turbo', n=5, t_refrence=1, t_samples=1, trial=trial)
    # eval_Human_eval(model='gpt-3.5-turbo', n=5, t_refrence=0, t_samples=1.5, trial=trial)
    # eval_Human_eval(model='gpt-3.5-turbo', n=15, t_refrence=0, t_samples=1, trial=trial)
    # eval_Human_eval(model='gpt-3.5-turbo', n=15, t_refrence=1, t_samples=1, trial=trial)
    # eval_Human_eval(model='gpt-3.5-turbo', n=15, t_refrence=1, t_samples=1.3, trial=trial)

    # eval_Human_eval(model='gpt-4-turbo-preview', n=5, t_refrence=0, t_samples=1, trial=1)
    # eval_Human_eval(model='gpt-4-turbo-preview', n=3, t_refrence=0, t_samples=1, trial=1)
    # eval_Human_eval(model='gpt-4-turbo-preview', n=10, t_refrence=0, t_samples=1, trial=1)
    # eval_Human_eval(model='gpt-4-turbo-preview', n=5, t_refrence=1, t_samples=1, trial=1)
    # eval_Human_eval(model='gpt-4-turbo-preview', n=5, t_refrence=0, t_samples=1.5, trial=1)
    # read_test("APPS", 1)
    