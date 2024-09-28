import glob
import json
import subprocess
import csv
import os
from openai import AzureOpenAI
from dotenv import load_dotenv

from data import stream_jsonl

def get_existing_task_ids(filename):
    if not os.path.exists(filename):
        return []

    if filename.endswith(".jsonl"):
        return [task['task_id'] for task in stream_jsonl(filename)]
    
    if filename.endswith(".csv"):
        with open(filename, mode='r') as file:
            reader = csv.DictReader(file, quoting=csv.QUOTE_ALL)
            return [row["task_id"] for row in reader]
        
    return []

def parse_code(code):
    return code.replace("java\n", "", 1).replace("Java\n", "", 1)

def generate_java_code(prompt):
    prompt = prompt.replace(" and function signature solve()", ".")
    prompt = "Write a java function in markdown that does the following:\n" + prompt + \
        ". \nReturn the code of the function only without any other text." + \
        "\nAlso, include all the needed imports." + \
        "\nPlease name the public class 'code' and provide only the Java code without any explanations."


    client = AzureOpenAI(
        azure_endpoint="https://team5-chatgpt-4-api.openai.azure.com/",
        api_version = "2023-05-15",  # Use the latest available version
        api_key = os.getenv("OPENAI_API_KEY"),
    )

    response = client.chat.completions.create(
        model="gpt4-api", 
        messages=[
            {"role": "system", "content": "You are a programming assistant, skilled in writing complex programming concepts with creative syntax."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )

    return parse_code(response.choices[0].message.content.replace('`', "").strip())

def run_test_case(code, input_str):
    with open('code.java', 'w') as file:
        file.write(code)

    compile_result = subprocess.run(['javac', 'code.java'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
    if compile_result.returncode != 0:
        print("Error in compilation: ", compile_result.stderr.decode())
        return None
    
    run_result = subprocess.run(['java', 'code'], input=input_str.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
    if run_result.returncode != 0:
        print("Error in running the code: ", run_result.stderr.decode())
        return None
    
    return run_result.stdout.decode().strip()

def evaluate_given_code(code, test_cases):
    tests_passed = 0
    num_tests = len(test_cases['inputs'])
    
    for input_str, output_str in zip(test_cases['inputs'], test_cases['outputs']):
        try:
            input_str = input_str.strip()
            output_str = output_str.strip()
        except:
            print("Error in parsing test cases")
            num_tests -= 1
            continue

        try:
            res = run_test_case(code, input_str)
            if res == output_str:
                tests_passed += 1
        except Exception as e:
            print("Exception in running the test: ", e)
    
    return (tests_passed / num_tests) * 100 if num_tests != 0 else 0
    
def generate_APPS_java(original_dataset, generated_dataset, size=15):
    
    target_task_ids = get_existing_task_ids("RESULTS/dataset_APPS_model_gpt-3.5-turbo_n_5_tempr_1_temps_1_trial_10.csv")[:size]
    # target_task_ids = ["APPS/1728"]

    filtered_tasks = [
        task for task in stream_jsonl(original_dataset) 
        if (
            task['task_id'] in target_task_ids and 
            task['task_id'] not in get_existing_task_ids(generated_dataset)
        )
    ]

    print(f"Generating Java code for {len(filtered_tasks)} tasks")

    with open(generated_dataset, mode='a') as gen_file:
        for i, task in enumerate(filtered_tasks):
            task["canonical_solution"] = generate_java_code(task['prompt'])
            test_pass_rate = evaluate_given_code(task["canonical_solution"], task["test"])

            print(f"[{i + 1}/{len(filtered_tasks)}] {task['task_id']}: {test_pass_rate}")

            if test_pass_rate == 100:
                gen_file.write(json.dumps(task) + '\n')
    
def clean_repo():
    for ext in ['java', 'class']:
        for file in glob.glob(f'*.{ext}'):
            os.remove(file)

if __name__ == "__main__":
    load_dotenv()
    generate_APPS_java("DATASETS/apps.jsonl", "DATASETS/apps_java.jsonl", 100)
    clean_repo()