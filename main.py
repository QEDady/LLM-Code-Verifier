from typing import Dict
import pprint
from utils.utils import load_config
from data.evaluate_dataset import evaluate_dataset

def main(config: Dict):
    evaluate_dataset(config)

if __name__ == '__main__':
    config = load_config('config.yaml')
    pprint.pprint(config)
    # main(config)
