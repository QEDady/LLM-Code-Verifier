import csv
import re
from typing import Counter, Dict, List, Iterable, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils.utils import create_results_csv_file
from data.dataset_handler import extract_task_ids_from_file, load_dataset
from api.llm_api import generate_codes
from executor.code_executer import evaluate_code
from data.const import HUMAN_EVAL, HUMAN_EVAL_PLUS, HUMAN_EVAL_MODIFIED_PATH, HUMAN_EVAL_PLUS_PATH, APPS, APPS_FILTERED_PATH, SET_ENCODING_TEXT

def preprocess_code(code: str, dataset: str, prog_lang: str, task: dict, test_key: str, entry_point_key: Optional[str]) -> Optional[str]:
    if dataset.lower() in [HUMAN_EVAL, HUMAN_EVAL_PLUS]:
        if prog_lang.lower() == "python":
            return SET_ENCODING_TEXT + f"{code}\n{task[test_key]}\nprint(check({task[entry_point_key]}))"
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
    wanted_task_ids = extract_task_ids_from_file(dataset_config['from_file']['file_path']) if dataset_config['from_file']['enabled'] else []
    
    if isinstance(model_config['samples_temperature'], (int, float)):
        model_config['samples_temperature'] = [model_config['samples_temperature']]

    tasks = list(tasks)
    for temp in model_config['samples_temperature']:
        print(f"\nEvaluating dataset: {dataset} with temperature: {temp}")
        model_config_tmp = model_config.copy()
        model_config_tmp['base_temperature'] = temp
        model_config_tmp['samples_temperature'] = temp

        csv_file_name, fieldnames = create_results_csv_file(dataset=dataset, model_config=model_config_tmp, trial=trial)
        existing_task_ids = extract_task_ids_from_file(csv_file_name)
        # print(f"Existing task ids: {existing_task_ids}")
        human_eval_results_file, _ = create_results_csv_file(dataset="human_eval", model_config=model_config_tmp, trial=trial)

        with open(csv_file_name, mode='a', newline='', encoding='utf-8') as csv_f, open(human_eval_results_file, mode='r', encoding='utf-8') as human_eval_f:
            writer = csv.DictWriter(csv_f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            reader = csv.DictReader(human_eval_f, quoting=csv.QUOTE_ALL)

            for i, (task, res_task) in enumerate(zip(tasks, reader)):
                if task['task_id'] in existing_task_ids or (dataset_config['from_file']['enabled'] and task['task_id'] not in wanted_task_ids):
                    continue
                
                print(f"\n[{len(existing_task_ids) + i + 1}] Processing {task['task_id']}")
                row = {
                    'task_id': task['task_id'],
                    'prompt': task['prompt']
                }

                # generated_codes = generate_codes(prog_lang=prog_lang, model_config=model_config_tmp, prompt=task['prompt'])
                generated_codes = [res_task[f"code_{i}"] for i in range(6)]

                with ThreadPoolExecutor(4) as executor:
                    task_id = task['task_id']
                    futures  = []
                    submitted_codes = Counter()

                    print(f"[{task['task_id']}] Submitting codes...")
                    for code_idx, code in enumerate(generated_codes):
                        check_program = preprocess_code(code=code, dataset=dataset, prog_lang=prog_lang, task=task, test_key=test_key, entry_point_key=entry_point_key)
                        if check_program is None:
                            return
                        
                        row[f"code_{code_idx}"] = code                    
                        test_cases = task[test_key] if dataset.lower() == APPS else None
                        args = (code_idx, prog_lang, check_program, test_cases)
                        future = executor.submit(evaluate_code, *args)
                        futures.append(future)
                        submitted_codes [task_id] += 1

                    assert submitted_codes[task_id] == 6, "Some codes are not attempted"
                        
                    print(f"[{task['task_id']}] Evaluating codes...")
                    for idx, future in enumerate(as_completed(futures)):
                        code_idx, test_pass_rate = future.result()
                        print(f"test_pass_rate: {test_pass_rate}")
                        print(f"\t[{idx + 1}/{len(generated_codes)}] code {code_idx} completed")
                        row[f"pass_rate_{code_idx}"] = test_pass_rate
                writer.writerow(row)
                # break

def eval_Human_eval(dataset_config: Dict, model_config: Dict, trial: int) -> None:
    tasks = load_dataset(dataset_path=HUMAN_EVAL_MODIFIED_PATH, random_config=dataset_config['random'])
    evaluate(dataset_config, model_config, trial, tasks=tasks, test_key='test', entry_point_key='entry_point')

def eval_Human_eval_plus(dataset_config: Dict, model_config: Dict, trial: int) -> None:
    tasks = load_dataset(dataset_path=HUMAN_EVAL_PLUS_PATH, random_config=dataset_config['random'])
    evaluate(dataset_config, model_config, trial, tasks=tasks, test_key='test', entry_point_key='entry_point')

def eval_APPS(dataset_config: Dict, model_config: Dict, trial: int) -> None:
    tasks = load_dataset(dataset_path=APPS_FILTERED_PATH, random_config=dataset_config['random'])
    evaluate(dataset_config, model_config, trial, tasks=tasks, test_key='test', entry_point_key=None)

def evaluate_dataset(dataset_config: Dict, model_config: Dict, trial: int) -> None:
    """
    This function evaluates the dataset using the specified model and programming language.
    """
    dataset = dataset_config['name']

    if dataset.lower() == HUMAN_EVAL:
        eval_Human_eval(dataset_config, model_config, trial=trial)
    elif dataset.lower() == HUMAN_EVAL_PLUS:
        eval_Human_eval_plus(dataset_config, model_config, trial=trial)
    elif dataset.lower() == APPS:
        eval_APPS(dataset_config, model_config, trial=trial)
    else:
        print(f"{dataset} is not supported")
