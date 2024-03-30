from typing import Iterable, Dict
import gzip
import json
import os
import re
import csv

ROOT = os.path.dirname(os.path.abspath(__file__))
HUMAN_EVAL = os.path.join(ROOT, "DATASETS", "human-eval.jsonl")
HUMAN_EVAL_MODIFIED = os.path.join(ROOT, "DATASETS", "human-eval-modified.jsonl")
HUMAN_EVAL_PROMPTS = os.path.join(ROOT, "PROMPTS", "human-eval-prompts.jsonl")
RESULTS = os.path.join(ROOT, "RESULTS")

def create_csv_file(dataset = "HumanEval", model="gpt-4-turbo-preview", n=5, t_refrence=0, t_samples=1, trial=1):
    csv_file_name = f'dataset_{dataset}_model_{model}_n_{n}_tempr_{t_refrence}_temps_{t_samples}_trial_{trial}.csv'
    csv_file_name = os.path.join(RESULTS, csv_file_name)
    fieldnames = ["task_id", "prompt"]
    last_task_id_num = -1
    for i in range(n+1):
        fieldnames.append(f"code_{i}")
    
    for i in range(n+1):
        fieldnames.append(f"pass_rate_{i}")
    
    for i in range(n+1):
        fieldnames.append(f"err_{i}")

    if os.path.exists(csv_file_name):
        with open(csv_file_name, mode='r') as csv_f:
            reader = csv.DictReader(csv_f)
            last_row = None
            for row in reader:
                last_row = row
            if last_row is not None:
                last_task_id_num = int(last_row['task_id'].split('/')[-1])
    else:
        with open(csv_file_name, mode='w', newline='') as csv_f:
            writer = csv.DictWriter(csv_f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()

    return csv_file_name, fieldnames, last_task_id_num

def modify_human_eval_tests(test):
    # Initialize the total number of tests and the number of passed tests
    pattern = r"assert.*candidate"
    matches = re.findall(pattern, test)
    insertion = f"""
    total_tests_xyz = {len(matches)}
    passed_tests_xyz = 0
    """
    pattern = r"(def check\(candidate\):)"
    replacement = r"\1" + insertion
    test = re.sub(pattern, replacement, test)

    # Replace all assert True statements with always-true statements
    test = re.sub(r"assert\s+True.*\n", "True==True\n", test)

    assert_statement_pattern = r"assert.*candidate.*?(?=assert.*candidate|$)"
    assert_statments = re.findall(assert_statement_pattern, test, re.DOTALL)
    quoted_str_pattern = r",\s+\".*\".*"
    for assert_statement in assert_statments:
        test_statement = re.sub(r"assert", r"passed_tests_xyz+=", assert_statement)
        test_statement = re.sub(quoted_str_pattern, "", test_statement)
        test = re.sub(re.escape(assert_statement), test_statement, test)  

    test += "\n    return passed_tests_xyz / total_tests_xyz"
    return test

def modify_Human_eval():
    with open(HUMAN_EVAL, 'r') as f, open(HUMAN_EVAL_MODIFIED, 'w') as new_f:
        for line in f:
            if any(not x.isspace() for x in line):
                problem = json.loads(line)
                problem['test'] = modify_human_eval_tests(problem['test'])
                json_str = json.dumps(problem)
                new_f.write(json_str + '\n')

def load_prompts_HumanEval():
    with open(HUMAN_EVAL_MODIFIED, 'r') as f, open(HUMAN_EVAL_PROMPTS, 'w') as prompts_f:
        for line in f:
            if any(not x.isspace() for x in line):
                problem = json.loads(line)
                prompt = problem['prompt']
                prompts = {
                    'task_id': problem['task_id'],
                    'prompt': prompt,
                }
                json_str = json.dumps(prompts)
                prompts_f.write(json_str + '\n')

def load_prompts(dataset):
    if dataset == 'HumanEval':
        load_prompts_HumanEval()

def stream_jsonl(filename: str) -> Iterable[Dict]:
    """
    Parses each jsonl line and yields it as a dictionary
    """
    if filename.endswith(".gz"):
        with open(filename, "rb") as gzfp:
            with gzip.open(gzfp, 'rt') as fp:
                for line in fp:
                    if any(not x.isspace() for x in line):
                        yield json.loads(line)
    else:
        with open(filename, "r") as fp:
            for line in fp:
                if any(not x.isspace() for x in line):
                    yield json.loads(line)

def write_jsonl(filename: str, data: Iterable[Dict], append: bool = False):
    """
    Writes an iterable of dictionaries to jsonl
    """
    if append:
        mode = 'ab'
    else:
        mode = 'wb'
    filename = os.path.expanduser(filename)
    if filename.endswith(".gz"):
        with open(filename, mode) as fp:
            with gzip.GzipFile(fileobj=fp, mode='wb') as gzfp:
                for x in data:
                    gzfp.write((json.dumps(x) + "\n").encode('utf-8'))
    else:
        with open(filename, mode) as fp:
            for x in data:
                fp.write((json.dumps(x) + "\n").encode('utf-8'))
