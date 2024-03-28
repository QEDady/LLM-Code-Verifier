import json
import subprocess
import tqdm
from chatgpt_api import generate_codes
from data import stream_jsonl, HUMAN_EVAL
import re

def eval_Human_eval():
    err_num = 0
    for problem in stream_jsonl(HUMAN_EVAL):
        # if problem['task_id'] == 'HumanEval/66':
            # print(problem['test'])
            problem['test'] = modify_test(problem['test'])
            prompt = problem['prompt']
            # codes = generate_codes(prompt=prompt)
            codes = [problem['canonical_solution']]
            for code in codes:
                check_program = f"{problem['prompt']}{code}\n{problem['test']}\nprint(check({problem['entry_point']}))"
                # print(check_program)
                result = subprocess.run(['python3', '-c', check_program], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode != 0:
                    print(f"[{problem['task_id']}] Error {result.stderr.decode()}")
                    err_num += 1
                    continue
                print(f"[{problem['task_id']}] Pass rate: ", result.stdout.decode())
    print(f"Total error: {err_num}")



def modify_test(test):
    pattern = r"assert"
    matches = re.findall(pattern, test)
    insertion = f"""
    total_tests = {len(matches)}
    passed_tests = 0
    """

    pattern = r"(def check\(candidate\):)"
    replacement = r"\1" + insertion
    test = re.sub(pattern, replacement, test)
    pattern = r'assert\s+(.+?)\s+(==|!=|>|<|>=|<=)\s+(.+?)$'

    test = re.sub(pattern, lambda match: f"if {match.group(1)} {match.group(2)} {match.group(3)}:\n            passed_tests += 1", test, flags=re.MULTILINE)

    # Add a return statement for the pass rate
    test += "\n    return passed_tests / total_tests"
    return test

if __name__ == '__main__':
    eval_Human_eval()
