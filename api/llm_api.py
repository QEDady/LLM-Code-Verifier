import json
import os
from typing import List, Optional
from openai import AzureOpenAI
from dotenv import load_dotenv

RETRIALS = 10

def parse_code(prog_lang: str, code: str) -> str:
    replacements = {
        "python": ["python\n", "Python\n"],
        "java": ["java\n", "Java\n"]
    }
    code = code.replace("markdown\n", "")

    for replacement in replacements.get(prog_lang, []):
        code = code.replace(replacement, "", 1)

    return code

def get_response(client: AzureOpenAI, model: str="gpt4-api", n: int=1, temperature: float=0.7, prompt: Optional[str]=None) -> Optional[dict]:
    for _ in range(RETRIALS):
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a programming assistant, skilled in writing complex programming concepts with creative syntax."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            n=n
        )
        response_dict = json.loads(response.to_json())
        if response_dict:
            return response_dict
    return None

def generate_codes(prog_lang: str="python", model: str="gpt4-api", n: int=5, t_reference: float=0.7, t_samples: float=0.7, prompt: Optional[str]=None) -> list:
    if prompt is None:
        raise ValueError("prompt is not specified")

    client = AzureOpenAI(
        azure_endpoint="https://team5-chatgpt-4-api.openai.azure.com/",
        api_version = "2023-05-15",  # Use the latest available version
        api_key = os.getenv("OPENAI_API_KEY"),
    )
    
    if prog_lang == "python":
        prompt = "Write a Python function in markdown that does the following:\n" + prompt + \
            ". \nReturn the code of the function only without any other text." + \
            "\nAlso, include all the needed imports."

    else:
        prompt = prompt.replace(" and function signature solve()", ".")
        prompt = "Write a java function in markdown that does the following:\n" + prompt + \
            ". \nReturn the code of the function only without any other text." + \
            "\nInclude all necessary imports." + \
            "\nName the public class 'code' and provide only the Java code in a single 'main' function without any explanations."
    
    generated_codes: List[str] = []
    reference_response = get_response(client, model, 1, t_reference, prompt)
    if reference_response:
        generated_codes.extend(parse_code(prog_lang, choice['message']['content']).replace('`', "").strip() for choice in reference_response['choices'])

    samples_response = get_response(client, model, n, t_samples, prompt)
    if samples_response:
        generated_codes.extend(parse_code(prog_lang, choice['message']['content']).replace('`', "").strip() for choice in samples_response['choices'])

    return generated_codes