import argparse
import csv
import gzip
import io
import json
import os
import pprint
import random
import re
import subprocess
from typing import Dict, Iterable, List

# Define the root directory
ROOT = os.path.dirname(os.path.abspath(__file__))

# Define paths to datasets and results
APPS = os.path.join(ROOT, "DATASETS", "apps.jsonl")
APPS_JAVA = os.path.join(ROOT, "DATASETS", "apps_java.jsonl")
APPS_TEST = os.path.join(ROOT, "DATASETS", "APPS", "data_split", "test.json")
APPS_TRAIN = os.path.join(ROOT, "DATASETS", "APPS", "data_split", "train.json")
HUMAN_EVAL = os.path.join(ROOT, "DATASETS", "human-eval.jsonl")
HUMAN_EVAL_MODIFIED = os.path.join(ROOT, "DATASETS", "human-eval-modified.jsonl")
HUMAN_EVAL_PROMPTS = os.path.join(ROOT, "PROMPTS", "human-eval-prompts.jsonl")
RESULTS = os.path.join(ROOT, "RESULTS")

def generate_csv_file_name(dataset, model, n, t_refrence, t_samples, trial):
    name = f'dataset_{dataset}_model_{model}_n_{n}_tempr_{t_refrence}_temps_{t_samples}_trial_{trial}.csv'
    return os.path.join(RESULTS, name)

def create_csv_file(dataset = "HumanEval", model="gpt-4-turbo-preview", n=5, t_refrence=0, t_samples=1, trial=1):
    csv_file_name = generate_csv_file_name(dataset, model, n, t_refrence, t_samples, trial)
    fieldnames = ["task_id", "prompt"] + [f"code_{i}" for i in range(n+1)] + [f"pass_rate_{i}" for i in range(n+1)] + [f"err_{i}" for i in range(n+1)]
    task_ids = []

    if os.path.exists(csv_file_name):
        with open(csv_file_name, mode='r') as csv_f:
            reader = csv.DictReader(csv_f)
            task_ids = [row['task_id'] for row in reader]
    else:
        with open(csv_file_name, mode='w', newline='') as csv_f:
            writer = csv.DictWriter(csv_f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()

    return csv_file_name, fieldnames, task_ids

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
    test = re.sub(r"assert\s+True.*\n", "", test)

    assert_statement_pattern = r"assert.*?candidate.*?(?=assert.*candidate|for|$)"
    assert_statments = re.findall(assert_statement_pattern, test, re.DOTALL)
    quoted_str_pattern = r",\s+\".*\".*"
    for assert_statement in assert_statments:
        test_statement = re.sub(quoted_str_pattern, "", assert_statement)
        test_statement = re.sub(r"assert", r"\n    try:\n        passed_tests_xyz+=", test_statement)
        test_statement += r"\n    except:\n        pass\n"
        test = re.sub(re.escape(assert_statement), test_statement, test)  

    test += "\n    return passed_tests_xyz / total_tests_xyz"
    return test
    # return modify_human_eval_tests_manual(test)

def modify_human_eval_tests_manual(test):
    with open ("write.jsonl", "w") as f:
        f.write(test)
    
    input('Press Enter to continue...')
    with open ("write.jsonl", "r") as f:
        test = f.readlines()
        test = "".join(test)

    return test
        
def modify_Human_eval():
    with open(HUMAN_EVAL, 'r') as f, open(HUMAN_EVAL_MODIFIED, 'w') as new_f:
        for line in f:
            if any(not x.isspace() for x in line):
                problem = json.loads(line)
                print(f"{problem['task_id']}:")
                # if problem['task_id'] == "HumanEval/53":
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

def load_prompts(args, dataset):
    if dataset == 'HumanEval':
        load_prompts_HumanEval()
    # elif dataset == 'APPS':
    #     load_prompts_APPS(args)

def get_random_tasks(filename: str, sample_size: int, exclude_ids: List[str] = None) -> List[Dict]:
    if exclude_ids is None:
        exclude_ids = []
    data = [task for task in stream_jsonl(filename) if task['task_id'] not in exclude_ids]

    if sample_size > len(data):
        return data
    
    return random.sample(data, sample_size)

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


def generate_prompt_APPS(prompt_path):
    _input = "\nQUESTION:\n"
    with open(prompt_path, "r") as f:
        data = f.readlines()
        data = "".join(data)
    _input += data
    # call-based format or user-input format
    _input += "\nUse user-input-Based format and function signature solve()"

    return _input

def get_tasks_range(args, dataset):
    argsdict = vars(args)
    if dataset == "HumanEval":
        size = 164
    elif dataset == "APPS":
        size = 3765

    if args.index:
        range = (args.index, args.index)
    elif args.end:
        range = (args.start, args.end if args.end < size else size-1)
    else:
        range = (0, size-1)
    return range
    
def get_problems_APPS(args):
    argsdict = vars(args)

    with open(APPS_TEST, "r") as f:
        problems = json.load(f)
    problems = sorted(problems) 

    if args.index:
        problems = [problems[args.index]]
    else:
        if args.start > len(problems) or args.start < 0:
            print(f"start index {args.start} > number of problems {len(problems)}")
            return
        start = args.start
        if args.end is None or args.end > len(problems):
            end = len(problems)
        else:
            end = args.end
        problems = problems[start:end]
    
    return problems

def load_solution_APPS(solutions_path):
    with open (solutions_path, "r") as f:
        solutions = f.readlines()
        solutions = "".join(solutions)
        solutions = json.loads(solutions)

    return solutions[random.randint(0, len(solutions)-1)]
    # solution = "def solve():\n"
    # solution += textwrap.indent(solutions[0], "    ")
    # solution += "\nsolve()"   

def get_tests_APPS(test_case_path):
    with open(test_case_path, "r") as f:
        tests = f.readlines()
        tests = "".join(tests)
        tests = json.loads(tests)
    tests_size = len(tests['inputs'])
    end = min(35, tests_size)
    tests = {
        "inputs": tests['inputs'][:end],
        "outputs": tests['outputs'][:end]
    }
    return tests

def get_starter_APPS(starter_path):
    with open(starter_path, "r") as f:
        starter = f.readlines()
        starter = "".join(starter)
    return starter

def create_APPS_jsonl(args):
    problems = get_problems_APPS(args)
    idx = 0
    with open(APPS, "w") as f:
        for problem in problems:
            prob_path = os.path.join("DATASETS", problem)
            test_case_path = os.path.join(prob_path, "input_output.json")
            prompt_path = os.path.join(prob_path, "question.txt")
            starter_path = os.path.join(prob_path, "starter_code.py")
            solutions_path = os.path.join(prob_path, "solutions.json")
            if not os.path.exists(starter_path):
                    starter_path = None
            if not os.path.exists(test_case_path) or not os.path.exists(solutions_path) or not os.path.exists(prompt_path):
                continue

            prompt = generate_prompt_APPS(prompt_path)
            solution = load_solution_APPS(solutions_path)
            tests = get_tests_APPS(test_case_path)
            entry_point = get_starter_APPS(starter_path) if starter_path else None
            problem = {
                "task_id": f"APPS/{idx}",
                "prompt": prompt,
                "entry_point": entry_point,
                "canonical_solution": solution,
                "test": tests
            }
            json_line = json.dumps(problem)
            f.write(json_line + '\n')
            idx += 1

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run a tranined model to generate Python code.")
    parser.add_argument("-t","--test_loc", default="data_split/test.json", type=str)
    parser.add_argument("-r","--root", default="../", type=str, help="where the data is stored.")
    parser.add_argument("-l","--load", default="~/apps/models/checkpoints/final", type=str)
    parser.add_argument("--peeking", default=0.0, type=float)
    parser.add_argument("--num-beams", default=5, type=int)
    parser.add_argument("-s","--start", default=0, type=int)
    parser.add_argument("-e","--end", default=None, type=int)
    parser.add_argument("-i", "--index", default=None, type=int)
    parser.add_argument("-d", "--debug", action="store_true")
    parser.add_argument("--save", type=str, default="./results")
 
    args = parser.parse_args()

    create_APPS_jsonl(args)
    # modify_Human_eval()
#     load_prompts(args, "APPS")
