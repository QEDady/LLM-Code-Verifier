import json
import gzip
import random
from typing import List, Dict, Iterable, Union
import os
import csv

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

def reservoir_sample(dataset_path: str, sample_size: int) -> List[Dict]:    
    sample = []
    
    for i, entry in enumerate(stream_jsonl(dataset_path)):
        if i < sample_size:
            sample.append(entry)
        else:
            j = random.randint(0, i)
            if j < sample_size:
                sample[j] = entry
    print(f"Sampled {len(sample)} entries from {dataset_path}")
    return sample

def extract_task_ids_from_file(file_path: str) -> List[str]:
    if not os.path.exists(file_path):
        return []

    if file_path.endswith(".jsonl"):
        return [task['task_id'] for task in stream_jsonl(file_path)]
    
    if file_path.endswith(".csv"):
        with open(file_path, mode='r', encoding="utf-8") as file:
            reader = csv.DictReader(file, quoting=csv.QUOTE_ALL)
            return [row["task_id"] for row in reader]
        
    return []

# TODO: Implement the range function
# def get_dataset_range(dataset_path: str, limits_config: Dict) -> List[str]:
#     if limits_config['task_ids']:
#         task_ids = limits_config['task_ids']
#     elif limits_config['start_id'] and limits_config['end_id']:
#         task_ids = []
#         for task in stream_jsonl(dataset_path):
#             if task['task_id'] >= limits_config['start_id'] and task['task_id'] <= limits_config['end_id']:
#                 task_ids.append(task['task_id'])

def load_dataset(dataset_path: str, random_config: Dict) -> Union[Iterable[Dict], List[Dict]]:
    if not os.path.exists(dataset_path):
        return []
    if random_config['enabled']:
        return reservoir_sample(dataset_path, random_config['sample_size'])
    else:
        return stream_jsonl(dataset_path)
