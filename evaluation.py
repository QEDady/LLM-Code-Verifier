import subprocess
import tqdm
from chatgpt_api import generate_codes
from data import stream_jsonl, modify_Human_eval, create_csv_file
from data import HUMAN_EVAL, HUMAN_EVAL_MODIFIED, HUMAN_EVAL_PROMPTS, RESULTS
from structural_similarity import structual_similarity_driver
from syntactic_similarity import syntactic_similarity_driver
import csv
import pprint
import json

def eval_Human_eval(model="gpt-3.5-turbo", n=5, t_refrence=0, t_samples=1, trial=1):
    pass_rate = 0
    err = None
    row = {}
    csv_file_name, fieldnames, last_task_id_num = create_csv_file(dataset="HumanEval", model=model, n=n, 
                                                 t_refrence=t_refrence, t_samples=t_samples, trial=trial)

    with open(csv_file_name, mode='a', newline='') as csv_f:
        writer = csv.DictWriter(csv_f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        for problem in stream_jsonl(HUMAN_EVAL_MODIFIED):
            if int(problem['task_id'].split('/')[-1]) > last_task_id_num:
                tqdm.tqdm.write(f"Processing {problem['task_id']}")
                row['task_id'] = problem['task_id']
                row['prompt'] = problem['prompt']
                codes = generate_codes(prompt=problem['prompt'], model=model, t_refrence=t_refrence, 
                                       t_samples=t_samples, n=n)
                for i, code in enumerate(codes):
                    row[f"code_{i}"] = code
                    check_program = f"{code}\n{problem['test']}\nprint(check({problem['entry_point']}))"
                    try:
                        result = subprocess.run(['python3', '-c', check_program], stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE, timeout=10)
                    except subprocess.TimeoutExpired:
                        row[f"err_{i}"] = "Timeout"
                        row[f"pass_rate_{i}"] = 0
                        continue
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
                            print(e)
                            print(check_program)
                    row[f"err_{i}"] = err
                    row[f"pass_rate_{i}"] = pass_rate*100
                writer.writerow(row)
                
def parse_csv(csv_file_name):
    codes = []
    with open(csv_file_name, mode='r') as csv_f:
        reader = csv.DictReader(csv_f)
        for row in reader:
            for i in range(6):
                codes.append(row[f'code_{i}'])
    return codes
            

def read_test():
    with open(HUMAN_EVAL_MODIFIED, 'r') as f:
        for line in f:
            problem = json.loads(line)
            if problem['task_id'] == "HumanEval/66":
                print(f"{problem['test']}")
                break


if __name__ == '__main__':
    # eval_Human_eval(model='gpt-3.5-turbo', n=5, t_refrence=0, t_samples=1, trial=1)
    # eval_Human_eval(model='gpt-3.5-turbo', n=3, t_refrence=0, t_samples=1, trial=1)
    # eval_Human_eval(model='gpt-3.5-turbo', n=10, t_refrence=0, t_samples=1, trial=1)
    # eval_Human_eval(model='gpt-3.5-turbo', n=5, t_refrence=1, t_samples=1, trial=1)
    # eval_Human_eval(model='gpt-3.5-turbo', n=5, t_refrence=0, t_samples=1.5, trial=1)

    # eval_Human_eval(model='gpt-4-turbo-preview', n=5, t_refrence=0, t_samples=1, trial=1)
    # eval_Human_eval(model='gpt-4-turbo-preview', n=3, t_refrence=0, t_samples=1, trial=1)
    # eval_Human_eval(model='gpt-4-turbo-preview', n=10, t_refrence=0, t_samples=1, trial=1)
    # eval_Human_eval(model='gpt-4-turbo-preview', n=5, t_refrence=1, t_samples=1, trial=1)
    # eval_Human_eval(model='gpt-4-turbo-preview', n=5, t_refrence=0, t_samples=1.5, trial=1)
    read_test()
    