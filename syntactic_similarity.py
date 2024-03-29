from difflib import SequenceMatcher

from nltk.metrics import edit_distance, jaccard_distance
from nltk.tokenize import word_tokenize
from nltk.util import ngrams

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import f1_score

from scipy.spatial.distance import hamming

def syntactic_similarity(func1: str, func2: str, n_grams=2) -> float:
    # Calculate sequence similarity
    seq_matcher = SequenceMatcher(None, func1, func2, autojunk=False)
    sequence_similarity = seq_matcher.ratio()

    # Normalize the sequence similarity score
    sequence_similarity = (1 + sequence_similarity) / 2

    # Calculate the LCS similarity
    lcs = seq_matcher.find_longest_match(0, len(func1), 0, len(func2))
    lcs_similarity = lcs.size / max(len(func1), len(func2))

    # Calculate edit distance
    edit_distance_raw = edit_distance(func1, func2)
    edit_distance_score = 1 - edit_distance_raw / max(len(func1), len(func2))

    # Tokenize the code into words
    tokens1 = word_tokenize(func1)
    tokens2 = word_tokenize(func2)

    # Calculate Jaccard similarity
    jaccard_similarity = 1 - jaccard_distance(set(tokens1), set(tokens2))

    # Generate ngrams
    n_grams1 = [' '.join(n_gram) for n_gram in ngrams(tokens1, n_grams)]
    n_grams2 = [' '.join(n_gram) for n_gram in ngrams(tokens2, n_grams)]

    # Combine the ngrams into single strings
    ng_text1 = ' '.join(n_grams1)
    ng_text2 = ' '.join(n_grams2)

    # Calculate TF-IDF vectors
    vectorizer = TfidfVectorizer().fit([ng_text1, ng_text2])
    tfidf1 = vectorizer.transform([ng_text1])
    tfidf2 = vectorizer.transform([ng_text2])

    # Calculate cosine similarity
    cosine_similarity_score = cosine_similarity(tfidf1, tfidf2)[0, 0]

    # padding the codes for calculating Hamming Distance & Sørensen–Dice coefficient
    max_len = max(len(func1), len(func2))
    padded_func1 = func1.ljust(max_len)
    padded_func2 = func2.ljust(max_len)

    # Calculate Hamming distance - Regular
    hamming_distance = hamming(list(padded_func1), list(padded_func2))
    hamming_distance_score = 1 - hamming_distance

    # Calculate Hamming distance - Sorted
    hamming_distance_sorted = hamming(sorted(padded_func1), sorted(padded_func2))
    hamming_distance_score_sorted = 1 - hamming_distance_sorted

    # Calculate Sørensen–Dice coefficient (F1 score) - Need to binarize the padded strings
    binarized_func1 = [1 if char in padded_func2 else 0 for char in padded_func1]
    binarized_func2 = [1 if char in padded_func1 else 0 for char in padded_func2]
    sorensen_dice_coefficient = f1_score(binarized_func1, binarized_func2)
    
    # Calculate n-gram similarity
    ngrams1 = set(ngrams(tokens1, n_grams))
    ngrams2 = set(ngrams(tokens2, n_grams))
    ngram_similarity = 1 - jaccard_distance(ngrams1, ngrams2)

    # Return an aggregate similarity score and the scores for each metric
    scores = {
        "sequence_similarity": sequence_similarity,
        "edit_distance_score": edit_distance_score,
        "jaccard_similarity": jaccard_similarity,
        "cosine_similarity_score": cosine_similarity_score,
        "sorensen_dice_coefficient": sorensen_dice_coefficient,
        "hamming_distance_score": hamming_distance_score,
        "hamming_distance_score_sorted": hamming_distance_score_sorted,
        "ngram_similarity": ngram_similarity,
    }

    return sum(scores.values()) / len(scores), scores


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