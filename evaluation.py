# import json
# import subprocess
# import tqdm
# from chatgpt_api import generate_codes
# from data import stream_jsonl, HUMAN_EVAL
# import re

# def eval_Human_eval():
#     err_num = 0
#     pr_err_num = 0
#     pr_err_list = []
#     for problem in stream_jsonl(HUMAN_EVAL):
#         if problem['task_id'] == 'HumanEval/158':
#             print(problem['test'])
#             problem_test = problem['test']
#             problem['test'] = modify_test(problem['test'])
#             prompt = problem['prompt']
#             # codes = generate_codes(prompt=prompt)
#             codes = [problem['canonical_solution']]
#             for code in codes:
#                 check_program = f"{problem['prompt']}{code}\n{problem['test']}\nprint(check({problem['entry_point']}))"
#                 print(check_program)
#                 result = subprocess.run(['python3', '-c', check_program], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#                 if result.returncode != 0:
#                     print('\n---------------------------------------------------------------\n')
#                     print(f"[{problem['task_id']}] Error {result.stderr.decode()}")
#                     err_num += 1
#                     continue
#                 pass_rate = float(result.stdout.decode())
#                 print(f"[{problem['task_id']}] Pass rate: ", pass_rate)
#                 pr_err_num += pass_rate!=1.0
#                 # if pass_rate != 1.0:
#                 #     pr_err_list.append(problem['task_id'])
#                 #     print(problem['task_id'])
#                 #     print(problem['test'])

                
#     print(f"Total error: {err_num}\n")  
#     # print(f"Total error pass rate: {pr_err_num}")
#     # print(pr_err_list)



# # def modify_test(test):
# #     pattern = r"assert"
# #     matches = re.findall(pattern, test)
# #     insertion = f"""
# #     total_tests = {len(matches)}
# #     passed_tests = 0
# #     """

# #     pattern = r"(def check\(candidate\):)"
# #     replacement = r"\1" + insertion
# #     test = re.sub(pattern, replacement, test)
# #     pattern = r'assert\s+(.+?)\s+(==|!=|>|<|>=|<=)\s+(.+?)$ '

# #     test = re.sub(pattern, lambda match: f"if {match.group(1)} {match.group(2)} {match.group(3)}:\n            passed_tests += 1\n", test, flags=re.MULTILINE)

# #     # Add a return statement for the pass rate
# #     test += "\n    return passed_tests / total_tests"
# #     return test

# # if __name__ == '__main__':
# #     eval_Human_eval()

# def modify_test(test):
#     # Initialize the total number of tests and the number of passed tests after the function signature "check(candidate):"
#     pattern = r"assert.*candidate"
#     matches = re.findall(pattern, test)
#     insertion = f"""
#     total_tests_xyz = {len(matches)}
#     passed_tests_xyz = 0
#     """
#     pattern = r"(def check\(candidate\):)"
#     replacement = r"\1" + insertion
#     test = re.sub(pattern, replacement, test)

#     # Replace all assert (True|False) statements with always-true statements
#     test = re.sub(r"assert\s+(True|False).*\n", "True==True\n", test)

#     assert_statement_pattern = r"assert.*candidate.*?(?=assert candidate|$)"
#     assert_statments = re.findall(assert_statement_pattern, test, re.DOTALL)
#     quoted_str_pattern = r",\s+\".*\".*"
#     for assert_statement in assert_statments:
#         new_assert_statement = re.sub(r"assert", r"passed_tests_xyz+=", assert_statement)
#         new_assert_statement = re.sub(quoted_str_pattern, "", new_assert_statement)
#         test = re.sub(re.escape(assert_statement), new_assert_statement, test)  

#     test += "\n    return passed_tests_xyz / total_tests_xyz"
#     return test

# if __name__ == '__main__':
#     eval_Human_eval()



# # import re

# # # Your multi-line string
# # s = """
# # assert x == 5
# # assert some_function(
# #     arg1, arg2, arg3
# # ) == expected_result, "Error message"
# # assert some_function(
# #     arg1, arg2, arg2
# # ) == expected_result, "Error message"
# # """

# # # Your pattern
# # pattern = r"assert .*?(?=assert|$)"

# # # Find matches
# # matches = re.findall(pattern, s, re.DOTALL)

# # # Print matches
# # for match in matches:
# #     print(match)

# # print(len(matches))

import re

s = 'assert (candidate(["name", "of", "string"]) == "string"), "t1"'

# Remove return string after "assert" statement
s = re.sub(r'\), ".*"$', '', s)

print(s)