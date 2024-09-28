
import subprocess

def run_python_code(code, input_str=None): 
    try:
        result = subprocess.run(
            ['python3', '-c', code],
            input=input_str,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            text=True
        )
        
        if result.returncode != 0:
            return result.stderr.strip(), None
        
        try:
            output = result.stdout.strip()
            return None, output
        except ValueError as e:
            return str(e), None
        
    except subprocess.TimeoutExpired:
        return "Timeout", None
    except Exception as e:
        return str(e), None

def run_java_code(code, input_str=None):
    try:
        with open('code.java', 'w') as file:
            file.write(code)

        compile_result = subprocess.run(
                ['javac', 'code.java'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                text=True
            )

        if compile_result.returncode != 0:
            return compile_result.stderr.strip(), None
        
        run_result = subprocess.run(
                ['java', 'code'],
                input=input_str,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                text=True
            )
        
        if run_result.returncode != 0:
            return run_result.stderr.strip(), None
        
        return None, run_result.stdout.strip()

    except subprocess.TimeoutExpired:
        return "Timeout", None
    except Exception as e:
        return str(e), None
    
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

            err, res = run_code(code, input_str)

            if res is None or err == 'Timeout':
                num_tests -= 1
                continue
            
            tests_passed += (res == output_str)

        test_pass_rate = (tests_passed / num_tests) * 100 if num_tests != 0 else 0
        return test_pass_rate if test_pass_rate else 0
    
    else: 
        err, test_pass_rate = run_code(code, None)
        return test_pass_rate if test_pass_rate else 0