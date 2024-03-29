from difflib import SequenceMatcher
from nltk.metrics import edit_distance, jaccard_distance
from nltk.tokenize import word_tokenize
from nltk.util import ngrams

def syntactic_similarity(func1: str, func2: str, n_grams=2) -> float:
    # Calculate sequence similarity
    seq_matcher = SequenceMatcher(None, func1, func2, autojunk=False)
    sequence_similarity = seq_matcher.ratio()

    # Calculate edit distance
    edit_distance_raw = edit_distance(func1, func2)
    edit_distance_score = (1 - edit_distance_raw) / max(len(func1), len(func2))

    # Tokenize the code into words
    tokens1 = word_tokenize(func1)
    tokens2 = word_tokenize(func2)

    # Calculate Jaccard similarity
    jaccard_similarity = 1 - jaccard_distance(set(tokens1), set(tokens2))

    # Calculate n-gram similarity
    ngrams1 = set(ngrams(tokens1, n_grams))
    ngrams2 = set(ngrams(tokens2, n_grams))
    ngram_similarity = 1 - jaccard_distance(ngrams1, ngrams2)

    # Return an aggregate similarity score and the scores for each metric
    scores = { sequence_similarity, edit_distance_score, jaccard_similarity, ngram_similarity }
    return sum(scores) / len(scores), scores


test_cases = {
    "code_1": '''
        def find_divisors(n):
            divisors = []
            for i in range(1, n + 1):
                if n % i == 0:
                    divisors.append(i)
            return divisors    
    ''',
    "code_2": '''
        def find_divisors(num):
            divisors = []
            for j in range(1, num + 1, 1):
                if num % j == 0:
                    divisors.append(j)
            return divisors
    ''',
    "code_3": '''
       def get_something(weird):
            something = set()
            for index in range(1, int(weird**0.5) + 1):
                if not (weird % index != 0):
                    something.add(index)
                    something.add(weird // index)
            return sorted(something)
    '''
}


if __name__ == "__main__":
    code1 = test_cases["code_1"]
    code2 = test_cases["code_2"]
    code3 = test_cases["code_3"]

    print(syntactic_similarity(code1, code2))
    print(syntactic_similarity(code1, code3))
    print(syntactic_similarity(code2, code3))

    print(syntactic_similarity(code1, code2, n_grams=3))
    print(syntactic_similarity(code1, code3, n_grams=3))
    print(syntactic_similarity(code2, code3, n_grams=3))