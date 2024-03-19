import pycode_similar

"""
human eval entry
{"task_id": "HumanEval/84", 
"prompt": "\ndef solve(N):\n    \"\"\"Given a positive integer N, return the total sum of its digits in binary.\n    \n    Example\n        For N = 1000, the sum of digits will be 1 the output should be \"1\".\n        For N = 150, the sum of digits will be 6 the output should be \"110\".\n        For N = 147, the sum of digits will be 12 the output should be \"1100\".\n    \n    Variables:\n        @N integer\n             Constraints: 0 \u2264 N \u2264 10000.\n    Output:\n         a string of binary number\n    \"\"\"\n", 
"entry_point": "solve", 
"canonical_solution": "    return bin(sum(int(i) for i in str(N)))[2:]\n", 
"test": "def check(candidate):\n\n    # Check some simple cases\n    assert True, \"This prints if this assert fails 1 (good for debugging!)\"\n    assert candidate(1000) == \"1\", \"Error\"\n    assert candidate(150) == \"110\", \"Error\"\n    assert candidate(147) == \"1100\", \"Error\"\n\n    # Check some edge cases that are easy to work out by hand.\n    assert True, \"This prints if this assert fails 2 (also good for debugging!)\"\n    assert candidate(333) == \"1001\", \"Error\"\n    assert candidate(963) == \"10010\", \"Error\"\n\n"}

"""
s1 = """
def solve(N):
    return bin(sum(int(digit) for digit in str(N)))[2:]
    """

s2 = """
def solve(N):
    binary_sum = sum(int(digit) for digit in bin(N)[2:])
    return bin(binary_sum)[2:]"""

s3 = """
def solve(N):
    return bin(sum(int(digit) for digit in str(N)))[2:]
    """

res = pycode_similar.detect([s1, s2, s3], diff_method=pycode_similar.UnifiedDiff, keep_prints=False, module_level=False)
print(res[0][1][0])
print(res[1][1][0])

res_tree = pycode_similar.detect([s1, s2, s3], diff_method=pycode_similar.TreeDiff, keep_prints=False, module_level=False)
print(res_tree[0][1][0])
print(res_tree[1][1][0])