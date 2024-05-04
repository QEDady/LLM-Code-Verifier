
def fizz_buzz(n: int):
    """Return the number of times the digit 7 appears in integers less than n which are divisible by 11 or 13.
    >>> fizz_buzz(50)
    0
    >>> fizz_buzz(78)
    2
    >>> fizz_buzz(79)
    3
    """
    count = 0
    for i in range(1, n):
        if i % 11 == 0 or i % 13 == 0:
            if '7' in str(i):
                count += 1
    return count

def check(candidate):
    total_tests_xyz = 8
    passed_tests_xyz = 0
    
    
    try:
        passed_tests_xyz+= candidate(50) == 0
    
    except:
        pass

    try:
        passed_tests_xyz+= candidate(78) == 2
    
    except:
        pass

    try:
        passed_tests_xyz+= candidate(79) == 3
    
    except:
        pass

    try:
        passed_tests_xyz+= candidate(100) == 3
    
    except:
        pass

    try:
        passed_tests_xyz+= candidate(200) == 6
    
    except:
        pass

    try:
        passed_tests_xyz+= candidate(4000) == 192
    
    except:
        pass

    try:
        passed_tests_xyz+= candidate(10000) == 639
    
    except:
        pass

    try:
        passed_tests_xyz+= candidate(100000) == 8026

    except:
        pass


    return passed_tests_xyz / total_tests_xyz

print(check(fizz_buzz))