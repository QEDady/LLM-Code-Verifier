import io
import pprint
import subprocess
from typing import Iterable, Dict
import gzip
import json
import os
import re
import csv
from reindent import run as run_reindent
import textwrap

ROOT = os.path.dirname(os.path.abspath(__file__))
HUMAN_EVAL = os.path.join(ROOT, "DATASETS", "human-eval.jsonl")
HUMAN_EVAL_MODIFIED = os.path.join(ROOT, "DATASETS", "human-eval-modified.jsonl")
HUMAN_EVAL_PROMPTS = os.path.join(ROOT, "PROMPTS", "human-eval-prompts.jsonl")
RESULTS = os.path.join(ROOT, "RESULTS")
APPS = os.path.join(ROOT, "DATASETS", "APPS", "data_split", "train_and_test.json")
APPS_TEST = os.path.join(ROOT, "DATASETS", "APPS", "data_split", "test.json")
APPS_TRAIN = os.path.join(ROOT, "DATASETS", "APPS", "data_split", "train.json")

def reindent_code(codestr):
    """
    Given code string, reindent it in the same way that the
    Github dataset was indented
    """
    codestr = io.StringIO(codestr)
    ret = io.StringIO()

    run_reindent(
        codestr, 
        ret, 
        config = {
            "dry-run": False,
            "help": False,
            "to": 10,
            "from": -1,
            "tabs": True,
            "encoding": "utf-8",
            "is-tabs": False,
            "tabsize": 10,
            "all-tabs": False
        }
    )

    return ret.getvalue()

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

def load_prompts(args, dataset):
    if dataset == 'HumanEval':
        load_prompts_HumanEval()
    elif dataset == 'APPS':
        load_prompts_APPS(args)

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


def generate_prompt_APPS(args, test_case_path, prompt_path, solutions_path, starter_path=None):
    _input = "\nQUESTION:\n"
    with open(prompt_path, "r") as f:
        data = f.readlines()
        data = "".join(data)
    _input += data
    # if starter_path != None:
    #     with open(starter_path, "r") as f:
    #         data = f.readlines()
    #         data = "".join(data)
    #         data = "\n" + data 
    #     _input += data
    # else:
    #     pass

    # with open(test_case_path, "r") as f:
    #     data = json.load(f)
    # call-based format or user-input format
    _input += "\nUse Call-Based format and function signature solve()"

    return _input

def get_problems(args):
    argsdict = vars(args)

    with open(APPS_TEST, "r") as f:
        problems = json.load(f)
    problems = sorted(problems) 

    if not os.path.exists(args.save):
        print('Creating save directory')
        os.makedirs(args.save, exist_ok=True)
    if not args.end:
        codes_loc = os.path.join(args.save, f"all_codes.json")
    else:
        codes_loc = os.path.join(args.save, f"{args.start}-{args.end}_codes.json")

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

def modify_sol(solution):
    modified_sol = f"def solve():\n"
    modified_sol += textwrap.indent(solution.strip(), '    ')
    # modified_sol = re.sub(r"input\(\)", "str(x)", modified_sol)
    modified_sol = re.sub(r'print\((.*)\)', r'return \1', modified_sol)
    modified_sol = re.sub(r'\bmain\(\)\s*$', r'return main()', modified_sol, re.MULTILINE)
    modified_sol += "\n"
    return modified_sol

def load_solutions(solutions_path):
    with open (solutions_path, "r") as f:
        solutions = f.readlines()
        solutions = "".join(solutions)
        solutions = json.loads(solutions)

    solution = modify_sol(solutions[0])
    return solution

def load_prompts_APPS(args):

    problems = get_problems(args)
    for index, problem in enumerate(problems):
        prob_path = os.path.join("DATASETS", problem)
        test_case_path = os.path.join(prob_path, "input_output.json")
        prompt_path = os.path.join(prob_path, "question.txt")
        starter_path = os.path.join(prob_path, "starter_code.py")
        solutions_path = os.path.join(prob_path, "solutions.json")
        if not os.path.exists(starter_path):
                starter_path = None
        if not os.path.exists(test_case_path) or not os.path.exists(solutions_path) or not os.path.exists(prompt_path):
            continue

        prompt_text = generate_prompt_APPS(args, test_case_path, prompt_path, solutions_path, starter_path)
        solution = load_solutions(solutions_path)
        tests = get_tests_APPS(test_case_path)

        tests_passed = 0
        num_tests = len(tests['inputs'])
        for i, (input_str, output_str) in enumerate(zip(tests['inputs'], tests['outputs'])):
            input_str = input_str.strip()
            output_str = output_str.strip()

            # print(f"{i+1}/{num_tests}")
            test_str = f"def check(candidate):\n    passed = 0\n\n"
            if output_str.isdigit():
                test_str += f"    passed += int(candidate()) == {output_str}\n"
            elif '\n' in output_str or '\n' in output_str:
                output_str = output_str.split()
                output_str = f"[{', '.join(str(int(x)) if x.isdigit() else x for x in output_str)}]"
                test_str += f"    passed += candidate() == {output_str}\n"
            else:
                test_str += f"    passed += candidate() == {output_str}\n"
            test_str += "\n    return passed"
            check_program = f"{solution}\n{test_str}\nprint(check(solve))"
            # print(check_program)

            try:
                tests_passed += run_test(check_program, input_str)
            except Exception as e:
                # print(e)
                pass
            
            # break
        print(f"problem {index+1}/{len(problems)}: {tests_passed/num_tests}")

def run_test(solution, input_str):
    passed = 0
    try:
        result = subprocess.run(['python3', '-c', solution], input=input_str.encode(), stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=10)
    except subprocess.TimeoutExpired:
        print("Timeout")
        return
    if result.returncode != 0:
        err = result.stderr.decode()
        # print(err)
    else:
        try:
            err = None
            passed = float(result.stdout.decode().split('\n')[-2])
        except ValueError as e:
            err = e
            # print(e)
    return passed

def get_tests_APPS(test_case_path):
    with open(test_case_path, "r") as f:
        tests = f.readlines()
        tests = "".join(tests)
        tests = json.loads(tests)
    return tests

def modify_test_APPS(test_case_path):
    test_str = ''
    multi_line = False
    multi_value = False
    with open(test_case_path, "r") as f:
        tests = f.readlines()
        tests = "".join(tests)
        tests = json.loads(tests)

        try: 
            if '\n' in tests['inputs'][0].strip() or '\n' in tests['outputs'][0].strip():
                multi_line = True
            elif ' ' in tests['inputs'][0].strip() or ' ' in tests['outputs'][0].strip():
                multi_value = True
            test_str += f"def check(candidate):\n    total_tests_xyz = {len(tests['inputs'])}\n    passed_tests_xyz = 0\n\n"
            for i, test in enumerate(tests['inputs']):
                test = test.split()
                test = f"[{', '.join(str(int(x)) if x.isdigit() else x for x in test)}]"
                test_str += f"    passed_tests_xyz += candidate({test.strip()}) == {tests['outputs'][i].strip()}\n"
            test_str += "\n    return passed_tests_xyz / total_tests_xyz"
        except:
            pass
    return test_str, multi_line, multi_value

if __name__ == "__main__":
    import argparse

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

    load_prompts(args, "APPS")
