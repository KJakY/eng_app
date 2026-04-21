import ollama

MODEL = "gemma3"

def chat(messages: list) -> str:
    response = ollama.chat(model=MODEL, messages=messages)
    return response["message"]["content"]
