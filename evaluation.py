import json
import subprocess
import tqdm
from chatgpt_api import generate_codes
from data import stream_jsonl, HUMAN_EVAL, HUMAN_EVAL_MODIFIED, HUMAN_EVAL_PROMPTS
import re

def eval_Human_eval():
    err_num = 0
    pr_err_num = 0
    pr_err_list = []
    for problem in stream_jsonl('./DATASETS/human-eval_modified.jsonl'):
        # if problem['task_id'] == 'HumanEval/51':
            problem_test = problem['test']
            # problem['test'] = modify_test(problem['test'])
            prompt = problem['prompt']
            # codes = generate_codes(prompt=prompt)
            codes = [problem['canonical_solution']]
            for code in codes:
                check_program = f"{problem['prompt']}{code}\n{problem['test']}\nprint(check({problem['entry_point']}))"
                result = subprocess.run(['python3', '-c', check_program], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode != 0:
                    print('\n---------------------------------------------------------------\n')
                    print(f"[{problem['task_id']}] Error {result.stderr.decode()}")
                    err_num += 1
                    continue
                pass_rate = float(result.stdout.decode())
                print(f"[{problem['task_id']}] Pass rate: ", pass_rate)
                pr_err_num += pass_rate!=1.0
                if pass_rate != 1.0:
                    pr_err_list.append(problem['task_id'])
                    print(problem['task_id'])
                    print(problem['test'])

                
    print(f"Total error: {err_num}\n")  
    print(f"Total error pass rate: {pr_err_num}")
    print(pr_err_list)

if __name__ == '__main__':
    eval_Human_eval()
    # eval_Human_eval_modify()
