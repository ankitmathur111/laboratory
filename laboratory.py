"""
PIP installations before beiginning:
1. pip install google-genai (Since October/November 2024)
2. pip install google-generativeai (Older version of google-genai, not recommended). It was part of Commit 1 & 2
The installations come from Python Package Index (PyPI) and pip tool delivers the package to the system.
"""
import os
from google import genai

#Configuring API key
"""
The client gets the API key from the environment variable `GEMINI_API_KEY`.
However we are using variable name `aistudio_key_laboratory` to store the API key, 
so we need to pass it to the client. This is because the client is looking for the environment variable `GEMINI_API_KEY` by default, but we are using a different variable name to store the API key. 
By passing the API key. Its optional argument to the function if we have not changed the environment variable name. 
We can simply use the client without passing the API key and 
keep name of original envionment variable as `GEMINI_API_KEY`.
"""
api_key_aistudio_key_laboratory=os.getenv("aistudio_key_laboratory")
client = genai.Client(api_key=api_key_aistudio_key_laboratory)

response = client.models.generate_content(
    model="gemini-3-flash-preview", contents="Explain what python lists are in simple terms and in few words"
)
print(response.text)