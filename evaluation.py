import json
import subprocess
import tqdm
from chatgpt_api import generate_codes
from data import stream_jsonl, HUMAN_EVAL

for problem in stream_jsonl(HUMAN_EVAL):
    prompt = problem['prompt']
    codes = generate_codes(prompt=prompt)
    for code in codes:
        check_program = f"{problem['prompt']}{code}\n{problem['test']}\ncheck({problem['entry_point']})"
        try:
            result = subprocess.run(['python3', '-c', check_program], stderr=subprocess.PIPE)
            if result.returncode == 0:
                print(f"[{problem['task_id']}] Correct")
            else:
                print(f"[{problem['task_id']}] Incorrect")
                err = result.stderr.decode('utf-8')
                # print('Error:', err)
        except Exception as e:
            print('Error:', e)
