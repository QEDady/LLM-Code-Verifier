from typing import Iterable, Dict
import gzip
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
HUMAN_EVAL = os.path.join(ROOT, "DATASETS", "human-eval.jsonl")
HUMAN_EVAL_MODIFIED = os.path.join(ROOT, "DATASETS", "human-eval-modified.jsonl")
HUMAN_EVAL_PROMPTS = os.path.join(ROOT, "PROMPTS", "human-eval-prompts.jsonl")

def modify_test(test):
    # Initialize the total number of tests and the number of passed tests after the function signature "check(candidate):"
    pattern = r"assert.*candidate"
    matches = re.findall(pattern, test)
    insertion = f"""
    total_tests_xyz = {len(matches)}
    passed_tests_xyz = 0
    """
    pattern = r"(def check\(candidate\):)"
    replacement = r"\1" + insertion
    test = re.sub(pattern, replacement, test)

    # Replace all assert (True|False) statements with always-true statements
    test = re.sub(r"assert\s+True.*\n", "True==True\n", test)

    assert_statement_pattern = r"assert.*candidate.*?(?=assert.*candidate|$)"
    assert_statments = re.findall(assert_statement_pattern, test, re.DOTALL)
    quoted_str_pattern = r",\s+\".*\".*"
    for assert_statement in assert_statments:
        new_assert_statement = re.sub(r"assert", r"passed_tests_xyz+=", assert_statement)
        new_assert_statement = re.sub(quoted_str_pattern, "", new_assert_statement)
        test = re.sub(re.escape(assert_statement), new_assert_statement, test)  

    test += "\n    return passed_tests_xyz / total_tests_xyz"
    return test

def eval_Human_eval_modify():
    with open(HUMAN_EVAL, 'r') as f, open(HUMAN_EVAL_MODIFIED, 'w') as new_f:
        for line in f:
            if any(not x.isspace() for x in line):
                problem = json.loads(line)
                problem['test'] = modify_test(problem['test'])
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
