import os
import csv
import glob
from typing import Any, Dict
import yaml

from data.const import RESULTS

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

    if not dataset_name or dataset_name not in dataset_options:
        raise ValueError(f"Invalid or missing dataset name. Must be one of {dataset_options}.")
    if not prog_lang:
        raise ValueError("Missing required field: dataset.prog_lang")

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

    # Validate limits (all optional)
    limits = config.get('limits', {})
    task_ids = limits.get('task_ids')
    start_id = limits.get('start_id')
    end_id = limits.get('end_id')

    # Validate trial (optional, default to 100)
    trial = config.get('trial', 100)
    if not isinstance(trial, int):
        raise ValueError("Field 'trial' must be an integer.")

    # Return validated and possibly modified config
    return {
        'dataset': dataset,
        'limits': limits,
        'model': model,
        'trial': trial
    }
