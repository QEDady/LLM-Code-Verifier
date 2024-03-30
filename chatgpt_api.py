# -*- coding: utf-8 -*-
"""ChatGPT API.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1iqdPX2wnsbAfBCHeoS-_5SuFMUQV9cjv
"""

#!pip install --upgrade openai

import requests
import json
import pprint


def parse_response(choice):
    code = choice['message']['content'].replace('`', "")
    if code[:6] == "python":
      code = code.replace("python", "", 1)
    elif code[:6] == "Python":
      code = code.replace("Python", "", 1)
    code = code.replace("markdown", "")
    return code


# n: number of samples to generate other than the refrence response
# The function returns an array of n+1 codes where the first the refrence code and the others are the candidates.
def generate_codes(model="gpt-4-turbo-preview", n=5, t_refrence=0, t_samples=1, prompt=None):
    URL = "https://api.openai.com/v1/chat/completions"
    api_key = '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'
    if prompt is None:
        raise ValueError("prompt is not specifid")
    else:
        prompt = "Write a Python function in markdown that does the following:\n" + prompt + \
            ". \nReturn the code of the function only without any other text." + \
            "\nAlso, include all the needed imports."

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # refrence request
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a programming assistant, skilled in writing complex programming concepts with creative syntax."},
            {"role": "user", "content": prompt}],
        "temperature": t_refrence,
        "top_p": 1.0,
        "n": 1,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 0,
    }

    refrence_response = requests.post(
        URL, headers=headers, json=payload, stream=False).content.strip().decode("utf-8")
    response_dict = json.loads(refrence_response)
    generated_codes = []
    for choice in response_dict['choices']:
        generated_codes.append(parse_response(choice))

    # sampled responses
    payload["temperature"] = t_samples
    payload["n"] = n
    samples_response = requests.post(
        URL, headers=headers, json=payload, stream=False).content.strip().decode("utf-8")
    response_dict = json.loads(samples_response)
    # print(response_dict)
    for choice in response_dict['choices']:
        generated_codes.append(parse_response(choice))

    return generated_codes


# if __name__=="__main__":
#   prompt = " Write a Python function in markdown that takes a sequence of numbers and determines whether all the numbers are different from each other. Return the code of the function only without any other text."
#   print(generate_codes(prompt=prompt))
