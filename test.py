
def solve():
    x = int(input())
    sum_digits = lambda n: sum(int(d) for d in str(n))
    max_sum = 0
    result = 1

    for i in range(1, min(x, 82)):
        if x - i < 10 or sum_digits(x - i) > max_sum:
            max_sum = sum_digits(x - i)
            result = x - i

    print(result)

solve()
