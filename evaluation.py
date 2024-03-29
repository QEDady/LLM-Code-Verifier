import json
import subprocess
import tqdm
from chatgpt_api import generate_codes
from data import stream_jsonl, modify_Human_eval
from data import HUMAN_EVAL, HUMAN_EVAL_MODIFIED, HUMAN_EVAL_PROMPTS
import re

def eval_Human_eval():
    pass_rate_dict = {}
    err_dict = {}
    pass_rate = 0
    err = None
    for problem in stream_jsonl(HUMAN_EVAL_MODIFIED):
        if problem['task_id'] == 'HumanEval/41':
            print(problem['prompt'])
            codes = generate_codes(prompt=problem['prompt'], model="gpt-3.5-turbo", t_refrence=0, t_samples=1.5, n=5)
            for i, code in enumerate(codes):
                print(f"[{problem['task_id']}_{i}]--------------------------------------------------------")
                check_program = f"{code}\n{problem['test']}\nprint(check({problem['entry_point']}))"
                print(check_program)
                result = subprocess.run(['python3', '-c', check_program], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode != 0:
                    # print(f"[{problem['task_id']}_{i}] Error {result.stderr.decode()}")
                    err = result.stderr.decode()
                    pass_rate = 0
                else:
                    pass_rate = float(result.stdout.decode())
                    err = None
                # print(f"[{problem['task_id']} - {i}] Pass rate: ", pass_rate*100)
                pass_rate_dict[f"{problem['task_id']}_{i}"] = pass_rate*100
                err_dict[f"{problem['task_id']}_{i}"] = err
            print('\n---------------------------------------------------------------\n')   
    print(pass_rate_dict)
    print(err_dict)
                
if __name__ == '__main__':
    eval_Human_eval()
    # modify_Human_eval()
