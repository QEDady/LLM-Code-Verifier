import os
import csv
import glob
import yaml
from typing import Any, Dict

from data.const import RESULTS

def generate_results_csv_filename(dataset, model, n, t_refrence, t_samples, trial):
    filename = f'dataset_{dataset}_model_{model}_n_{n}_tempr_{t_refrence}_temps_{t_samples}_trial_{trial}.csv'
    return os.path.join(RESULTS, filename)

def create_results_csv_file(dataset, model, n, t_reference, t_samples, trial):
    file_name = generate_results_csv_filename(dataset, model, n, t_reference, t_samples, trial)
    fieldnames = ["task_id", "prompt"] + [f"code_{i}" for i in range(n+1)] + [f"pass_rate_{i}" for i in range(n+1)]

    if not os.path.exists(file_name):
        with open(file_name, mode='w', newline='') as csv_f:
            writer = csv.DictWriter(csv_f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()

    return file_name, fieldnames

def clean_repo():
    for ext in ['java', 'class']:
        for file in glob.glob(f'*.{ext}'):
            os.remove(file)

def load_config(config_file: str) -> Dict[str, Any]:
    with open(config_file, 'r') as file:
        return yaml.safe_load(file)