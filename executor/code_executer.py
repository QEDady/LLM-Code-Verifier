import subprocess
import textwrap
from typing import Tuple, Union
import ast
import numpy as np
from data.dataset_handler import stream_jsonl
from data.const import HUMAN_EVAL_MODIFIED_PATH, APPS_FILTERED_PATH, APPS_PATH

def validate_executer(dataset_path: str):
    if dataset_path == HUMAN_EVAL_MODIFIED_PATH:
        for task in stream_jsonl(dataset_path):
            check_program = f"{task['prompt']}\n{task['canonical_solution']}\n{task['test']}\nprint(check({task['entry_point']}))"
            test_pass_rate = evaluate_code(code_id=0, prog_lang="python", code=check_program, test_cases=None)
            print(f"{task['task_id']}: {test_pass_rate}")
    elif dataset_path in [APPS_FILTERED_PATH, APPS_PATH]:
        for i, task in enumerate(stream_jsonl(dataset_path)):
            # if i in [100]:
                code = task['canonical_solution']
                code = textwrap.indent(code, '    ')
                check_program = f"def solve():\n{code}\nsolve()"
                _, test_pass_rate = evaluate_code(code_id=0, prog_lang="python", code=check_program, test_cases=task['test'])
                print(f"{task['task_id']}: {test_pass_rate}")
                # if (i >= 100):
                #     break

def compare_outputs(expected_output: str, captured_output: str) -> bool:
    """
    Compare the captured output of a program with the expected output.

    This function performs multiple checks to ensure that the captured output matches the expected output.
    It handles various data types and formats, including strings, lists, dictionaries, and floating-point numbers.
    The comparison includes exact matches, custom comparison logic for specific cases, and tolerance for floating-point differences.

    Args:
        expected_output (str): The expected output as a string.
        captured_output (str): The captured output from the program as a string.

    Returns:
        bool: True if the outputs match according to any of the comparison criteria, otherwise False.
    """
    def custom_compare_(output, expected):
        # Custom comparison logic for specific cases
        try:
            output_float = [float(e) for e in output]
            gt_float = [float(e) for e in expected]
            if (len(output_float) == len(gt_float)) and np.allclose(output_float, gt_float):
                return True
        except Exception:
            pass
        try:
            if isinstance(output[0], list):
                output_float = [float(e) for e in output[0]]
                gt_float = [float(e) for e in expected[0]]
                if (len(output_float) == len(gt_float)) and np.allclose(output_float, gt_float):
                    return True
        except Exception:
            pass
        return False

    tmp_result = False

    # Exact match check
    if captured_output == expected_output:
        return True

    # Custom comparison logic
    if custom_compare_(captured_output.split(), expected_output.split()):
        return True

    # Convert tuples to lists
    if isinstance(captured_output, tuple):
        captured_output = list(captured_output)

    try:
        tmp_result = (captured_output == [expected_output])
        if isinstance(expected_output, list):
            tmp_result = tmp_result or (captured_output == expected_output)
            if isinstance(captured_output[0], str):
                tmp_result = tmp_result or ([e.strip() for e in captured_output] == expected_output)
    except Exception as e:
        pass

    if tmp_result == True:  
        return True

    # Try one more time without \n
    if isinstance(expected_output, list):
        for tmp_index, i in enumerate(expected_output):
            expected_output[tmp_index] = i.split("\n")
            expected_output[tmp_index] = [x.strip() for x in expected_output[tmp_index] if x]
    else:
        expected_output = expected_output.split("\n")
        expected_output = list(filter(len, expected_output))
        expected_output = list(map(lambda x:x.strip(), expected_output))

    try:
        tmp_result = (captured_output == [expected_output])
        if isinstance(expected_output, list):
            tmp_result = tmp_result or (captured_output == expected_output)
    except Exception as e:
        pass

    if tmp_result == True:
        return True

    # Try by converting the captured output into a split-up list too
    if isinstance(captured_output, list):
        captured_output = list(filter(len, captured_output))

    if tmp_result == True:
        return True

    try:
        tmp_result = (captured_output == [expected_output])
        if isinstance(expected_output, list):
            tmp_result = tmp_result or (captured_output == expected_output)
    except Exception as e:
        pass

    try:
        output_float = [float(e) for e in captured_output.split()]
        gt_float = [float(e) for e in expected_output.split()]
        tmp_result = tmp_result or ((len(output_float) == len(gt_float)) and np.allclose(output_float, gt_float))
    except Exception as e:
        pass
    try:
        if isinstance(captured_output[0], list):
            output_float = [float(e) for e in captured_output[0]]
            gt_float = [float(e) for e in expected_output[0]]
            tmp_result = tmp_result or ((len(output_float) == len(gt_float)) and np.allclose(output_float, gt_float))
    except Exception as e:
        pass

    if tmp_result == True:
        return True

    # Try by converting the stuff into split-up list
    if isinstance(expected_output, list):
        for tmp_index, i in enumerate(expected_output):
            expected_output[tmp_index] = set(i.split())
    else:
        expected_output = set(expected_output.split())

    try:
        tmp_result = (captured_output == expected_output)
    except Exception as e:
        pass

    if tmp_result == True:
        return True

    # Try by converting the captured output into a split-up list too
    if isinstance(captured_output, list):
        for tmp_index, i in enumerate(captured_output):
            captured_output[tmp_index] = i.split()
        captured_output = list(filter(len, captured_output))
        for tmp_index, i in enumerate(captured_output):
            captured_output[tmp_index] = set(i)    
    else:
        captured_output = captured_output.split()
        captured_output = list(filter(len, captured_output))
        captured_output = set(captured_output)

    try:
        tmp_result = (set(frozenset(s) for s in captured_output) == set(frozenset(s) for s in expected_output))
    except Exception as e:
        pass

    # If they are all numbers, round so that similar numbers are treated as identical
    try:
        tmp_result = tmp_result or (set(frozenset(round(float(t),3) for t in s) for s in captured_output) ==\
            set(frozenset(round(float(t),3) for t in s) for s in expected_output))
    except Exception as e:
        pass    
    
    return tmp_result

def convert_string_to_data_structure(data_str: str):
    try:
        return ast.literal_eval(data_str)
    except (ValueError, SyntaxError):
        return data_str

def compare_and_match(str1: str, str2: str) -> bool:
    data1 = convert_string_to_data_structure(str1)
    data2 = convert_string_to_data_structure(str2)
    if data1 != data2:
        print(f"Expected: {data2}")
        print(f"captured_output: {data1}")
    return data1 == data2

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

        subprocess.run(
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
    
def evaluate_code(code_id, prog_lang, code, test_cases=None) -> Tuple[int, float]:
    language_runners = {
        'python': run_python_code,
        'java': run_java_code
    }

    run_code = language_runners.get(prog_lang.lower())
    if run_code is None:
        print(f"Unsupported language: {prog_lang}")
        return code_id, 0
    
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

            captured_output = run_code(code, input_str)
            if isinstance(captured_output, str):
                # captured_output = [line.strip() for line in captured_output.split("\n")]
                # output_str = [line.strip() for line in output_str.split("\n")]

                if compare_outputs(captured_output, output_str):
                    tests_passed += 1
                # else:
                #     print(f'captured_output: {captured_output}')
                #     print(f'Expected output: {output_str}')
                #     # break
                # tests_passed += (captured_output == output_str)
            elif isinstance(captured_output, subprocess.TimeoutExpired):
                # num_tests -= 1
                continue
            elif isinstance(captured_output, Exception):
                # print(f"Error: {captured_output}")                
                continue

        test_pass_rate = (tests_passed / num_tests) * 100 if num_tests != 0 else 0
        return code_id, test_pass_rate 
    
    else: 
        captured_output = run_code(code, None)
        if isinstance(captured_output, str):
            return code_id, 100 * float(captured_output)
        elif isinstance(captured_output, Exception):
            return code_id, 0
        return  code_id, 0
    
    