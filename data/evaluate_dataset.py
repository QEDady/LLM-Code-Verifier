import csv
import re
from typing import Dict, List, Iterable, Optional, Union

from utils.utils import create_results_csv_file
from data.dataset_handler import extract_task_ids_from_file, load_dataset
from api.llm_api import generate_codes
from executor.code_executer import evaluate_code
from data.const import HUMAN_EVAL, HUMAN_EVAL_MODIFIED_PATH, APPS, APPS_PATH

def preprocess_code(code: str, dataset: str, prog_lang: str, task: dict, test_key: str, entry_point_key: Optional[str]) -> Optional[str]:
    if dataset.lower() == HUMAN_EVAL:
        if prog_lang.lower() == "python":
            return f"{code}\n{task[test_key]}\nprint(check({task[entry_point_key]}))"
        else:
            print(f"{prog_lang} is not supported for HumanEval dataset")
        
    elif dataset.lower() == APPS:
        if prog_lang.lower() == "python":
            if re.search(r"solve\(\)\s*$", code) is None:
                code += "\nsolve()"
            return code
        elif prog_lang.lower() == "java":
            return code
        else:
            print(f"{prog_lang} is not supported for APPS dataset")
         
    return None

def evaluate(dataset_config: Dict, model_config: Dict, trial: int, tasks: Union[Iterable[Dict], List[Dict]], test_key: str, entry_point_key: Optional[str]) -> None:
    dataset = dataset_config['name']
    prog_lang = dataset_config['prog_lang']
    
    csv_file_name, fieldnames = create_results_csv_file(dataset=dataset, model_config=model_config, trial=trial)
    existing_task_ids = extract_task_ids_from_file(csv_file_name)

    with open(csv_file_name, mode='a', newline='', encoding='utf-8') as csv_f:
        writer = csv.DictWriter(csv_f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)

        for i, task in enumerate(tasks):
            if task['task_id'] in existing_task_ids:
                continue
            
            print(f"\n[{len(existing_task_ids) + i + 1}] Processing {task['task_id']}")
            row = {
                'task_id': task['task_id'],
                'prompt': task['prompt']
            }

            generated_codes = generate_codes(prog_lang=prog_lang, model_config=model_config, prompt=task['prompt'])

            for code_idx, code in enumerate(generated_codes):
                check_program = preprocess_code(code=code, dataset=dataset, prog_lang=prog_lang, task=task, test_key=test_key, entry_point_key=entry_point_key)
                if check_program is None:
                    return
                
                print(f"\tcode {code_idx + 1}/{len(generated_codes)}")
                test_cases = task[test_key] if dataset.lower() == APPS else None
                test_pass_rate = evaluate_code(prog_lang=prog_lang, code=check_program, test_cases=test_cases)

                row[f"code_{code_idx}"] = code
                row[f"pass_rate_{code_idx}"] = test_pass_rate 
            writer.writerow(row)

def eval_Human_eval(dataset_config: Dict, model_config: Dict, trial: int) -> None:
    tasks = load_dataset(dataset_path=HUMAN_EVAL_MODIFIED_PATH, random_config=dataset_config['random'])
    evaluate(dataset_config, model_config, trial, tasks=tasks, test_key='test', entry_point_key='entry_point')

def eval_APPS(dataset_config: Dict, model_config: Dict, trial: int) -> None:
    tasks = load_dataset(dataset_path=APPS_PATH, random_config=dataset_config['random'])
    evaluate(dataset_config, model_config, trial, tasks=tasks, test_key='test', entry_point_key=None)

def evaluate_dataset(dataset_config: Dict, model_config: Dict, trial: int) -> None:
    """
    This function evaluates the dataset using the specified model and programming language.
    """
    dataset = dataset_config['name']

    if dataset.lower() == HUMAN_EVAL:
        eval_Human_eval(dataset_config, model_config, trial=trial)
    elif dataset.lower() == APPS:
        eval_APPS(dataset_config, model_config, trial=trial)
    else:
        print(f"{dataset} is not supported")
