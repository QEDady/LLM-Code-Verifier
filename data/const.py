import os

current_dir = os.path.dirname(os.path.abspath(__file__))

ROOT = os.path.dirname(current_dir)

DATASETS_DIR = os.path.join(ROOT, "data", "datasets")
RESULTS_DIR = os.path.join(ROOT, "RESULTS")

APPS_PATH = os.path.join(DATASETS_DIR, "apps", "apps.jsonl")
APPS_TEST_PATH = os.path.join(DATASETS_DIR, "apps", "APPS", "data_split", "test.json")
APPS_TRAIN_PATH = os.path.join(DATASETS_DIR, "apps", "APPS", "data_split", "train.json")
HUMAN_EVAL_PATH = os.path.join(DATASETS_DIR, "human_eval", "human-eval.jsonl")
HUMAN_EVAL_MODIFIED_PATH = os.path.join(DATASETS_DIR, "human_eval", "human-eval-modified.jsonl")
RESULTS = RESULTS_DIR

APPS = "apps"
HUMAN_EVAL = "human_eval"