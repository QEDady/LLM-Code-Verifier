import argparse
import csv
import json
import pprint
import re
import subprocess

import pandas as pd

from chatgpt_api import generate_codes, generate_java_codes
from data import APPS, APPS_JAVA, HUMAN_EVAL_MODIFIED, create_csv_file, generate_csv_file_name, get_random_tasks, get_tasks_range, stream_jsonl
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

def eval_Human_eval_from_file(model="gpt-3.5-turbo", n=5, t_refrence=0, t_samples=1, trial=1):
    csv_file_name, fieldnames, last_task_id_num = create_csv_file(dataset="HumanEval", model=model, n=n, 
                                                 t_refrence=t_refrence, t_samples=t_samples, trial=trial)
    
    codes_file_name, _, _ = create_csv_file(dataset="HumanEval", model=model, n=n, 
                                                 t_refrence=t_refrence, t_samples=t_samples, trial=1)
    pass_rate = 0
    err = None
    row = {}

    with open(csv_file_name, mode='a', newline='') as csv_f, open(codes_file_name, mode = 'r') as codes_f:
        writer = csv.DictWriter(csv_f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL) 
        reader = csv.DictReader(codes_f, quoting=csv.QUOTE_ALL)
        for problem in stream_jsonl(HUMAN_EVAL_MODIFIED):        
            read_row = next(reader)
            if int(problem['task_id'].split('/')[-1]) > last_task_id_num:
                print(f"Processing {problem['task_id']}")
                row['task_id'] = problem['task_id']
                row['prompt'] = problem['prompt']
                for i in range (n+1):
                    code = read_row[f"code_{i}"]
                    row[f"code_{i}"] = code
                    check_program = f"{code}\n{problem['test']}\nprint(check({problem['entry_point']}))"
                    err, pass_rate = run_test_HUMAN_EVAL(check_program)
                    row[f"err_{i}"] = err
                    row[f"pass_rate_{i}"] = pass_rate*100
                writer.writerow(row)

def run_test_APPS(solution, input_str):
    try:
        result = subprocess.run(['python3', '-c', solution], input=input_str.encode(), stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=10)
        if result.returncode == 0:
                return result.stdout.decode().strip()
    except subprocess.TimeoutExpired:
        print("Timeout")
        res = 'Timeout'
    except Exception:
        res = None

def run_tests_on_code(code, test_cases):
    tests_passed = 0
    num_tests = len(test_cases['inputs'])
    
    for input_str, output_str in zip(test_cases['inputs'], test_cases['outputs']):
        try:
            input_str = input_str.strip()
            output_str = output_str.strip()
        except:
            num_tests -= 1
            continue

        try:
            res = run_test_APPS(code, input_str)
        except Exception:
            res = None

        if res is None or res == 'Timeout':
            num_tests -= 1
            continue

        tests_passed += (res == output_str)
    
    test_pass_rate = (tests_passed / num_tests) * 100 if num_tests != 0 else 0
    error_message = 'All tests timed out' if num_tests == 0 else None
    
    return test_pass_rate, error_message

def process_task(task, model, n, t_refrence, t_samples):
    row = {
        'task_id': task['task_id'],
        'prompt': task['prompt']
    }
    codes= generate_codes(prompt=task['prompt'], model=model, t_refrence=t_refrence, t_samples=t_samples, n=n)

    for code_idx, code in enumerate(codes):
        if re.search(r"solve\(\)\s*$", code) is None:
            code += "\nsolve()"

        print(f"\tcode {code_idx + 1}/{len(codes)}")
        test_pass_rate, error_message = run_tests_on_code(code, task['test'])

        row[f"code_{code_idx}"] = code
        row[f"err_{code_idx}"] = error_message
        row[f"pass_rate_{code_idx}"] = test_pass_rate

    return row

def eval_APPS(args, model="gpt-3.5-turbo", n=5, t_refrence=0, t_samples=1, trial=1):
    csv_file_name, fieldnames, task_ids = create_csv_file(dataset="APPS", model=model, n=n, 
                                                 t_refrence=t_refrence, t_samples=t_samples, trial=trial)
    
    tasks_range = get_tasks_range(args, 'APPS')
    tasks_size = max(args.number - len(task_ids), 0)
    random_tasks = get_random_tasks(APPS, tasks_size, task_ids)

    with open(csv_file_name, mode='a', newline='') as csv_f:
        writer = csv.DictWriter(csv_f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL) 

        for i, task in enumerate(random_tasks):     
            task_id = int(task['task_id'].split('/')[-1])
            if f"APPS/{task_id}" in task_ids or not (tasks_range[0] <= task_id <= tasks_range[1]):
                continue

            print(f"\n[{len(task_ids) + i + 1}] Processing {task['task_id']}")
            row = process_task(task, model, n, t_refrence, t_samples)
            writer.writerow(row)

def run_test_case_java(code, input_str):
    with open('code.java', 'w') as file:
        file.write(code)

    compile_result = subprocess.run(['javac', 'code.java'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=1)
    if compile_result.returncode != 0:
        print("Error in compilation: ", compile_result.stderr.decode())
        return None
    
    run_result = subprocess.run(['java', 'code'], input=input_str.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2)
    if run_result.returncode != 0:
        print("Error in running the code: ", run_result.stderr.decode())
        return None
    
    return run_result.stdout.decode().strip()

def evaluate_code_java(code, test_cases):
    tests_passed = 0
    num_tests = len(test_cases['inputs'])
    
    for input_str, output_str in zip(test_cases['inputs'], test_cases['outputs']):
        try:
            input_str = input_str.strip()
            output_str = output_str.strip()

            # print("Input: ", input_str)
            # print("Expected Output: ", output_str)
            res = run_test_case_java(code, input_str)
            # print("Output: ", res)
            if res == output_str:
                tests_passed += 1
        except TimeoutError as e:
            print("Timeout!!")
            num_tests -= 1
            continue

        except Exception as e:
            print("Error in running the test case: ", e)
            continue
    
    return (tests_passed / num_tests) * 100 if num_tests != 0 else 0

def process_java_task(task, model, n, t_refrence, t_samples):
    row = {
        'task_id': task['task_id'],
        'prompt': task['prompt']
    }
    codes= generate_java_codes(prompt=task['prompt'], model=model, t_refrence=t_refrence, t_samples=t_samples, n=n)

    for code_idx, code in enumerate(codes):
        print(f"\tcode {code_idx + 1}/{len(codes)}")
        test_pass_rate = evaluate_code_java(code, task['test'])
        print(f"Test pass rate: {test_pass_rate}")

        row[f"code_{code_idx}"] = code
        row[f"pass_rate_{code_idx}"] = test_pass_rate
    
    return row

def eval_APPS_java(args, model="gpt-3.5-turbo", n=5, t_refrence=0.7, t_samples=0.7, trial=10):
    csv_file_name, fieldnames, task_ids = create_csv_file(dataset="APPS_JAVA", model=model, n=n, 
                                                 t_refrence=t_refrence, t_samples=t_samples, trial=trial)
    
    tasks_size = max(args.number - len(task_ids), 0)
    random_tasks = get_random_tasks(APPS, tasks_size, task_ids)

    with open(csv_file_name, mode='a', newline='') as csv_f:
        writer = csv.DictWriter(csv_f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL) 

        for i, task in enumerate(random_tasks):     
            task_id = int(task['task_id'].split('/')[-1])
            if f"APPS/{task_id}" in task_ids:
                continue

            print(f"\n----------------------------------[{len(task_ids) + i + 1}] Processing {task['task_id']}----------------------------------")
            row = process_java_task(task, model, n, t_refrence, t_samples)
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
                pprint.pprint(problem['test'])
                break

def create_parser():
    parser = argparse.ArgumentParser(description="Evaluate the specified dataset ")
    parser.add_argument("-n","--number", default=100, type=int)
    parser.add_argument("-s","--start", default=0, type=int)
    parser.add_argument("-e","--end", default=None, type=int)
    parser.add_argument("-i", "--index", default=None, type=int)
    return parser

if __name__ == '__main__':

    parser = create_parser()
    args = parser.parse_args()

#     add_comments(comment_generation_model="gpt-4-turbo-preview", csv_file_name="RESULTS/dataset_HumanEval_model_gpt-3.5-turbo_n_5_tempr_0_temps_1_trial_1.csv")
#     print("Done 5 without renaming functions and got 4 comments")
    # print("--------------")
    # add_comments("gpt-3.5-turbo","RESULTS/dataset_HumanEval_model_gpt-3.5-turbo_n_5_tempr_0_temps_1.5_trial_1.csv")
    # print("Done T 1.5")
    # print("--------------")
    # add_comments("gpt-3.5-turbo","RESULTS/dataset_HumanEval_model_gpt-4-turbo-preview_n_5_tempr_0_temps_1_trial_1.csv")
    # print("Done Gpt4")
    # print("--------------")
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(eval_Human_eval_async(model='gpt-3.5-turbo', n=5, t_refrence=0, t_samples=1, trial=1))
        
    # eval_APPS(args, model='gpt-3.5-turbo', n=5, t_refrence=1, t_samples=1, trial=10)
    eval_APPS_java(args, model='gpt4-api', n=5, t_refrence=0.7, t_samples=0.7, trial=10)
