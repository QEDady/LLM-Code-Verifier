import pycode_similar

# The code is written with the help of https://github.com/CodeHero0/Nondeterminism-of-ChatGPT-in-Code-Generation?tab=readme-ov-file

def compute_similarity(func_ast_diff_list):
    total_plagiarism_count = sum(func_diff_info.plagiarism_count for func_diff_info in func_ast_diff_list)
    total_count = sum(func_diff_info.total_count for func_diff_info in func_ast_diff_list)
    if total_count == 0:
        similarity_percent = 0
    else:
        similarity_percent = total_plagiarism_count / float(total_count)
    return similarity_percent


def add_function_name(code):
    prefix = 'def main():\n'
    tab = '    '
    code_list = code.split('\n')
    code_list = [tab + x for x in code_list]
    res_0 = '\n'.join(x for x in code_list)
    sufix = '\n\nif __name__ == "__main__":\n' + tab + 'main()'
    res = prefix + res_0 + sufix
    return res


def structual_similarity(generated_codes, mode=pycode_similar.UnifiedDiff):
    try:
        res = pycode_similar.detect(generated_codes,
                                    diff_method=mode,
                                    keep_prints=True,
                                    module_level=False)
    except pycode_similar.NoFuncException:
        for i in range(len(generated_codes)):
            if "__main__" not in generated_codes[i]:
                generated_codes[i] = add_function_name(generated_codes[i])
        try:
            res = pycode_similar.detect(generated_codes,
                                        diff_method=mode,
                                        keep_prints=True,
                                        module_level=False)
        except Exception as e:
            #TODO(amer): maybe return negative numbers
            raise Exception("f'Could not compute the {mode} structural similarity", e)
    except Exception as e:
            #TODO(amer): maybe return negative numbers
            raise Exception("f'Could not compute the {mode} structural similarity", e)
    
    similarity_scores = {}
    for i, func_ast_diff_list in res:
        score = compute_similarity(func_ast_diff_list)
        similarity_scores[f'res_code_{i}'] = score
    return similarity_scores  


def structual_similarity_driver(codes):
    scores = {}

    res_unified= structual_similarity(codes, pycode_similar.UnifiedDiff)
    res_tree = structual_similarity(codes, pycode_similar.TreeDiff)
    
    for key in res_unified:
        metrics = {
            "UnifiedDiff" : res_unified[key],
            "TreeDiff":res_tree[key],
        }

        aggregate_score = sum(metrics.values()) / len(metrics)
        scores[key] = {
            "aggregate_score": aggregate_score,
            "metrics": metrics
        }
    
    return scores

# if __name__=="__main__": 
#     # generated_codes = ['\ndef all_unique(seq):\n    return len(seq) == len(set(seq))\n', '\ndef all_different(sequence):\n    return len(sequence) == len(set(sequence))\n', '\ndef all_different(seq):\n    return len(seq) == len(set(seq))+1\n', '\ndef are_all_numbers_unique(sequence):\n    return len(sequence) == len(set(sequence))\n', '\ndef are_all_numbers_different(sequence):\n    return len(sequence) == len(set(sequence))\n', '\ndef are_all_numbers_different(sequence):\n    return len(sequence) == len(set(sequence))\n']
#     generated_codes = [
#         '\ndef find_divisors(num):\n    divisors = []\n    for i in range(1, n + 1):\n        if n % i == 0:\n            divisors.append(i)\n    return divisors\n',
#         '\ndef find_divisors(num):\n    divisors = []\n    for j in range(1, num + 1, 1):\n        if num % j == 0:\n            divisors.append(j)\n    return divisors\n',
#         '\ndef find_divisors(num):\n    something = set()\n    for index in range(1, int(weird**0.5) + 1):\n        if not (weird % index != 0):\n            something.add(index)\n            something.add(weird // index)\n    return sorted(something)\n'
#     ]

#     print(structual_similarity_driver(generated_codes))
