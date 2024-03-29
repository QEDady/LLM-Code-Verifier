import json
import subprocess
import tqdm
from chatgpt_api import generate_codes
from data import stream_jsonl, modify_Human_eval
from data import HUMAN_EVAL, HUMAN_EVAL_MODIFIED, HUMAN_EVAL_PROMPTS
import re

def eval_Human_eval():
    err_num = 0
    for problem in stream_jsonl(HUMAN_EVAL_MODIFIED):
        # if problem['task_id'] == 'HumanEval/41':
            codes = generate_codes(prompt=problem['prompt'])
            for i, code in enumerate(codes):
                check_program = f"{code}\n{problem['test']}\nprint(check({problem['entry_point']}))"
                # print(check_program)
                result = subprocess.run(['python3', '-c', check_program], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode != 0:
                    print('\n---------------------------------------------------------------\n')
                    print(f"[{problem['task_id']}] Error {result.stderr.decode()}")
                    err_num += 1
                    continue
                pass_rate = float(result.stdout.decode())
                print(f"[{problem['task_id']} - {i}] Pass rate: ", pass_rate*100)
                
    # print(f"[{problem['task_id']}] Total error: {err_num}\n")  

if __name__ == '__main__':
    eval_Human_eval()
    # modify_Human_eval()
