import os

current_dir = os.path.dirname(os.path.abspath(__file__))

ROOT = os.path.dirname(current_dir)

DATASETS_DIR = os.path.join(ROOT, "data", "datasets")
RESULTS_DIR = os.path.join(ROOT, "RESULTS")

APPS_PATH = os.path.join(DATASETS_DIR, "apps", "apps.jsonl")
APPS_FILTERED_PATH = os.path.join(DATASETS_DIR, "apps", "filtered_apps.jsonl")
APPS_TEST_PATH = os.path.join(DATASETS_DIR, "apps", "APPS", "data_split", "test.json")
APPS_TRAIN_PATH = os.path.join(DATASETS_DIR, "apps", "APPS", "data_split", "train.json")
HUMAN_EVAL_PATH = os.path.join(DATASETS_DIR, "human_eval", "human-eval.jsonl")
HUMAN_EVAL_MODIFIED_PATH = os.path.join(DATASETS_DIR, "human_eval", "human-eval-modified.jsonl")
HUMAN_EVAL_PLUS_PATH = os.path.join(DATASETS_DIR, "human_eval", "human_eval_plus.jsonl")
RESULTS = RESULTS_DIR

APPS = "apps"
HUMAN_EVAL = "human_eval"
HUMAN_EVAL_PLUS = "human_eval_plus"

SET_ENCODING_TEXT = "# -*- coding: utf-8 -*-\n"