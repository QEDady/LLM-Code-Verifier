def parse_response(choice):
    code = choice.replace('`', "").strip()
    code = code.replace("markdown\n", "")
    if code.startswith("python\n"):
      code = code.replace("python\n", "", 1)
    elif code.startswith("Python\n"):
      code = code.replace("Python\n", "", 1)

    print(code)



s = """
markdown
python
def solve():
    import sys
    input = sys.stdin.read
    s = input().strip()
    
    # Define mirroring pairs:
    mirror_characters = {
        'A': 'A', 'H': 'H', 'I': 'I', 'M': 'M', 'O': 'O',
        'T': 'T', 'U': 'U', 'V': 'V', 'W': 'W', 'X': 'X',
        'Y': 'Y', 'b': 'd', 'd': 'b', 'o': 'o', 'p': 'q',
        'q': 'p', 'v': 'v', 'w': 'w', 'x': 'x'
    }

    # Check symmetry:
    n = len(s)
    mid = n // 2
    for i in range(mid):
        left_char = s[i]
        right_char = s[n - 1 - i]
        if right_char not in mirror_characters or mirror_characters[right_char] != left_char:
            print(""NIE"")
            return
    
    # If there is a middle character in an odd length string, it must be its own mirror:
    if n % 2 == 1:
        middle_char = s[mid]
        if middle_char not in mirror_characters or mirror_characters[middle_char] != middle_char:
            print(""NIE"")
            return
    
    print(""TAK"")
solve()
"""

parse_response(s)
