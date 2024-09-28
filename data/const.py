import os

current_dir = os.path.dirname(os.path.abspath(__file__))

ROOT = os.path.dirname(current_dir)

DATASETS_DIR = os.path.join(ROOT, "datasets")
RESULTS_DIR = os.path.join(ROOT, "results")

APPS = os.path.join(DATASETS_DIR, "apps", "apps.jsonl")
APPS_TEST = os.path.join(DATASETS_DIR, "apps", "APPS", "data_split", "test.json")
APPS_TRAIN = os.path.join(DATASETS_DIR, "apps", "APPS", "data_split", "train.json")
HUMAN_EVAL = os.path.join(DATASETS_DIR, "human_eval", "human-eval.jsonl")
HUMAN_EVAL_MODIFIED = os.path.join(DATASETS_DIR, "human_eval", "human-eval-modified.jsonl")
RESULTS = RESULTS_DIR
