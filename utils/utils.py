import gzip
import json
import os
import csv
import glob
from typing import Any, Dict, Iterable
import yaml

from data.const import RESULTS

def stream_jsonl(file_path: str) -> Iterable[Dict]:

    if file_path.endswith(".gz"):
        with open(file_path, "rb") as gzfp:
            with gzip.open(gzfp, 'rt') as fp:
                for line in fp:
                    if isinstance(line, str) and any(not x.isspace() for x in line):
                        yield json.loads(line)
    else:
        with open(file_path, "r", encoding="utf-8") as fp:
            for line in fp:
                if isinstance(line, str) and any(not x.isspace() for x in line):
                    yield json.loads(line)

def write_jsonl(file_path: str, data: Iterable[Dict], append: bool = False):
    if append:
        mode = 'ab'
    else:
        mode = 'wb'
    file_path = os.path.expanduser(file_path)
    if file_path.endswith(".gz"):
        with open(file_path, mode) as fp:
            with gzip.GzipFile(fileobj=fp, mode='wb') as gzfp:
                for x in data:
                    gzfp.write((json.dumps(x) + "\n").encode('utf-8'))
    else:
        with open(file_path, mode) as fp:
            for x in data:
                fp.write((json.dumps(x) + "\n").encode('utf-8'))  
                
def generate_results_csv_filename(dataset, model, n, t_refrence, t_samples, trial):
    filename = f'dataset_{dataset}_model_{model}_n_{n}_tempr_{t_refrence}_temps_{t_samples}_trial_{trial}.csv'
    return os.path.join(RESULTS, filename)

def create_results_csv_file(dataset, model_config: Dict, trial):
    model = model_config['name']
    n = model_config['samples_n']
    t_reference = model_config['base_temperature']
    t_samples = model_config['samples_temperature']
    
    file_name = generate_results_csv_filename(dataset, model, n, t_reference, t_samples, trial)
    fieldnames = ["task_id", "prompt"] + [f"code_{i}" for i in range(n+1)] + [f"pass_rate_{i}" for i in range(n+1)]

    if not os.path.exists(file_name):
        with open(file_name, mode='w', newline='', encoding='utf-8') as csv_f:
            writer = csv.DictWriter(csv_f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()

    return file_name, fieldnames

def clean_repo():
    for ext in ['java', 'class']:
        for file in glob.glob(f'*.{ext}'):
            os.remove(file)

def load_config(config_file: str) -> Dict[str, Any]:
    with open(config_file, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def validate_config(config):
    # Validate dataset
    dataset = config.get('dataset', {})
    dataset_options = config.get('dataset_options', [])
    dataset_name = dataset.get('name')
    prog_lang = dataset.get('prog_lang')
    random = dataset.get('random')
    range = dataset.get('range')
    from_file = dataset.get('from_file')

    if not dataset_name or dataset_name not in dataset_options:
        raise ValueError(f"Invalid or missing dataset name. Must be one of {dataset_options}.")
    if not prog_lang:
        raise ValueError("Missing required field: dataset.prog_lang")
    
    # Validate random sampling
    if random["enabled"] and (not isinstance(random['sample_size'], int) or random['sample_size'] <= 0):
        raise ValueError("Field 'random.sample_size' must be an integer more than zero.")

    # Validate range sampling
    if range["enabled"]:
        if range["task_ids"] is not None:
            if not isinstance(range["task_ids"], list) or not all(isinstance(task_id, int) and task_id >= 0 for task_id in range["task_ids"]):
                raise ValueError("Field 'range.task_ids' must be a list of integers more than or equal to zero.")
        else:
            if range["start_id"] is None and range["end_id"] is None:
                raise ValueError("Either 'range.task_ids' must be provided as a list of integers, or 'range.start_id' and/or 'range.end_id' must be specified.")
            
            if range["start_id"] is not None and not isinstance(range["start_id"], int):
                raise ValueError("Field 'range.start_id' must be an integer.")
            
            if range["end_id"] is not None and not isinstance(range["end_id"], int):
                raise ValueError("Field 'range.end_id' must be an integer.")
            
            if range["start_id"] is not None and range["start_id"] < 0:
                raise ValueError("Field 'range.start_id' must be greater than or equal to zero.")
            
            if range["end_id"] is not None and range["end_id"] < 0:
                raise ValueError("Field 'range.end_id' must be greater than or equal to zero.")
            
            if range["start_id"] is not None and range["end_id"] is not None:
                if range["start_id"] > range["end_id"]:
                    raise ValueError("Field 'range.start_id' must be less than or equal to 'range.end_id'.")
    
    # Validate from_file sampling
    if from_file["enabled"] and not os.path.exists(from_file["file_path"]):
        raise ValueError(f"File '{from_file['file_path']}' does not exist.")

    # Validate model
    model = config.get('model', {})
    model_options = config.get('model_options', [])
    model_name = model.get('name')
    base_temperature = model.get('base_temperature')
    samples_temperature = model.get('samples_temperature')
    samples_n = model.get('samples_n')

    if not model_name or model_name not in model_options:
        raise ValueError(f"Invalid or missing model name. Must be one of {model_options}.")
    if base_temperature is None:
        raise ValueError("Missing required field: model.base_temperature")
    if samples_temperature is None:
        raise ValueError("Missing required field: model.samples_temperature")
    if samples_n is None:
        raise ValueError("Missing required field: model.samples_n")

    # Validate trial (optional, default to 100)
    trial = config.get('trial', 100)
    if not isinstance(trial, int):
        raise ValueError("Field 'trial' must be an integer.")

    # Return validated and possibly modified config
    return {
        'dataset': dataset,
        'model': model,
        'trial': trial
    }
