import csv
import re
from typing import Dict, List, Iterable, Optional, Union

from utils.utils import create_results_csv_file
from data.dataset_handler import extract_task_ids_from_file, load_dataset
from api.llm_api import generate_codes
from executor.code_executer import evaluate_code
from data.const import HUMAN_EVAL_MODIFIED, APPS

def preprocess_code(code: str, dataset: str, prog_lang: str, task: dict, test_key: str, entry_point_key: str) -> Optional[str]:
    if dataset == "HumanEval":
        if prog_lang.lower() == "python":
            return f"{code}\n{task[test_key]}\nprint(check({task[entry_point_key]}))"
        else:
            print(f"{prog_lang} is not supported for HumanEval dataset")
        
    elif dataset == "APPS":
        if prog_lang.lower() == "python":
            if re.search(r"solve\(\)\s*$", code) is None:
                code += "\nsolve()"
            return code
        elif prog_lang.lower() == "java":
            return code
        else:
            print(f"{prog_lang} is not supported for APPS dataset")
         
    return None

def eval(dataset: str, model: str, n: int, t_reference: float, t_samples: float, trial: int, prog_lang: str, 
                    tasks: Union[Iterable[Dict], List[Dict]], test_key: str, entry_point_key: Optional[str] = None) -> None:
    csv_file_name, fieldnames = create_results_csv_file(dataset=dataset, model=model, n=n, t_reference=t_reference, 
                                                            t_samples=t_samples, trial=trial)
    existing_task_ids = extract_task_ids_from_file(csv_file_name)

    with open(csv_file_name, mode='a', newline='') as csv_f:
        writer = csv.DictWriter(csv_f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)

        for i, task in enumerate(tasks):
            if task['task_id'] in existing_task_ids:
                continue
            
            print(f"\n[{len(existing_task_ids) + i + 1}/{len(tasks)}] Processing {task['task_id']}")
            row = {
                'task_id': task['task_id'],
                'prompt': task['prompt']
            }

            generated_codes = generate_codes(prog_lang=prog_lang, model=model, n=n, t_reference=t_reference, 
                                                t_samples=t_samples, prompt=task['prompt'])

            for code_idx, code in enumerate(generated_codes):
                check_program = preprocess_code(code, dataset, prog_lang, task, test_key, entry_point_key)
                if check_program is None:
                    return
                
                print(f"\tcode {code_idx + 1}/{len(generated_codes)}")
                test_cases = task[test_key] if dataset == "APPS" else None
                test_pass_rate = evaluate_code(prog_lang=prog_lang, code=check_program, test_cases=test_cases)

                row[f"code_{code_idx}"] = code
                row[f"pass_rate_{code_idx}"] = test_pass_rate * 100 if prog_lang == "python" else test_pass_rate

            writer.writerow(row)

def eval_Human_eval(random: bool, sample_size: int, prog_lang: str, model: str="gpt4-api", n: int=5, t_reference: float=0.7, t_samples: float=0.7, trial: int=1) -> None:
    tasks = load_dataset(HUMAN_EVAL_MODIFIED, random=random, sample_size=sample_size)
    eval(dataset="HumanEval", model=model, n=n, t_reference=t_reference, t_samples=t_samples, 
                    trial=trial, prog_lang=prog_lang, tasks=tasks, test_key='test', entry_point_key='entry_point')

def eval_APPS(random: bool, sample_size: int, prog_lang: str, model: str="gpt4-api", n: int=5, t_reference: float=0.7, t_samples: float=0.7, trial: int=1) -> None:
    tasks = load_dataset(dataset_path=APPS, random=random, sample_size=sample_size)
    eval(dataset="APPS", model=model, n=n, t_reference=t_reference, t_samples=t_samples, 
                 trial=trial, prog_lang=prog_lang, tasks=tasks, test_key='test')

def evaluate_dataset(config: Dict) -> None:
    dataset_config = config['dataset']
    dataset = dataset_config['name']
    prog_lang = dataset_config['language']
    random = dataset_config['random']
    sample_size = dataset_config['sample_size']

    limits_config = config['limits']
    task_ids: List = limits_config['task_ids']
    start_id = limits_config['start_id']
    end_id = limits_config['end_id']

    model_config = config['model']
    model = model_config['name']
    t_reference = model_config['base_temperature']
    t_samples = model_config['samples_temperature']
    n = model_config['samples_n']

    trial = config['trial']
    
    if dataset.upper() == "HUMAN_EVAL":
        eval_Human_eval(random=random, sample_size=sample_size, prog_lang=prog_lang ,model=model, n=n, t_reference=t_reference, t_samples=t_samples, trial=trial)
    elif dataset.upper() == "APPS":
            eval_APPS(random=random, sample_size=sample_size, prog_lang=prog_lang, model=model, n=n, t_reference=t_reference, t_samples=t_samples, trial=trial)
    else:
        print(f"{dataset} is not supported")