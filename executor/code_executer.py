import subprocess
import textwrap
from typing import Union
from data.dataset_handler import stream_jsonl
from data.const import HUMAN_EVAL_MODIFIED_PATH, APPS_PATH


def validate_executer(dataset_path: str):
    if dataset_path == HUMAN_EVAL_MODIFIED_PATH:
        for task in stream_jsonl(dataset_path):
            check_program = f"{task['prompt']}\n{task['canonical_solution']}\n{task['test']}\nprint(check({task['entry_point']}))"
            test_pass_rate = evaluate_code(prog_lang="python", code=check_program, test_cases=None)
            print(f"{task['task_id']}: {test_pass_rate}")

    elif dataset_path == APPS_PATH:
        for i, task in enumerate(stream_jsonl(dataset_path)):
                code = task['canonical_solution']
                code = textwrap.indent(code, '    ')
                check_program = f"def solve():\n{code}\nsolve()"
                test_pass_rate = evaluate_code(prog_lang="python", code=check_program, test_cases=task['test'])
                print(f"{task['task_id']}: {test_pass_rate}")


def run_python_code(code, input_str=None) ->Union[Exception, str]: 
    try:
        result = subprocess.run(
            ['python3', '-c', code],
            input=input_str,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except Exception as e:
        return e

def run_java_code(code, input_str=None) -> Union[Exception, str]:
    try:
        with open('code.java', 'w', encoding='utf-8') as file:
            file.write(code)

        compile_result = subprocess.run(
                ['javac', 'code.java'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                text=True,
                check=True
            )
        
        run_result = subprocess.run(
                ['java', 'code'],
                input=input_str,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                text=True,
                check=True
            )
        
        return run_result.stdout.strip()
    except Exception as e:
        return e
    
def evaluate_code(prog_lang, code, test_cases=None):
    language_runners = {
        'python': run_python_code,
        'java': run_java_code
    }

    run_code = language_runners.get(prog_lang.lower())
    if run_code is None:
        print(f"Unsupported language: {prog_lang}")
        return 0
    
    if test_cases:
        tests_passed = 0
        num_tests = len(test_cases['inputs'])

        for input_str, output_str in zip(test_cases['inputs'], test_cases['outputs']):
            try:
                input_str = input_str.strip()
                output_str = output_str.strip()
            except:
                num_tests -= 1
                continue

            output = run_code(code, input_str)
            if isinstance(output, str):
                tests_passed += (output == output_str)
            elif isinstance(output, subprocess.TimeoutExpired):
                # num_tests -= 1
                continue
            elif isinstance(output, Exception):
                # print(f"Error: {output}")                
                continue

        test_pass_rate = (tests_passed / num_tests) * 100 if num_tests != 0 else 0
        return test_pass_rate 
    
    else: 
        output = run_code(code, None)
        if isinstance(output, str):
            return 100 * float(output)
        elif isinstance(output, Exception):
            return 0
        return  0
    