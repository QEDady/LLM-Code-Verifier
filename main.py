from typing import Dict
from utils.utils import load_config, validate_config
from data.evaluate_dataset import evaluate_dataset
from dotenv import load_dotenv

def main(config: Dict):
    dataset_config = config['dataset']
    model_config = config['model']
    trial = config['trial']
    evaluate_dataset(dataset_config, model_config, trial)

if __name__ == '__main__':
    load_dotenv()
    config = load_config('config.yaml')
    try:
        config = validate_config(config)
        print("Configuration is valid.")
    except ValueError as e:
        print(f"Configuration error: {e}")
    
    main(config)
    