"""
PIP installations before beiginning:
1. pip install google-genai (Since October/November 2024)
2. pip install google-generativeai (Older version of google-genai, not recommended). It was part of Commit 1 & 2
The installations come from Python Package Index (PyPI) and pip tool delivers the package to the system.
"""
import os
from google import genai
from google.genai import types

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

chat = client.chats.create(model="gemini-2.5-flash",
                           config=types.GenerateContentConfig(
                               system_instruction="You are professional, polite, happy, peaceful and friendly William Shakespeare. Respond only in poetic manner and instead of word 'Hark' please use its better synoyms. Dont respond for any controversial topics, sexual content, initimate content, violent content, arms or ammunitions related content, slang content, abusive content",
                               temperature=1.0
                      ))

print("Please respond with 'stop' when you want to close this conversation. Else, sit back and enjoy the conversation with the model. \nWarning & Note: To be used for professional, educational and ethical purposes only. If your thoughts differ then please don't proceed as its completely user's responsibility.\nLets begin...")
print("May I take your name?")
name = input()
print("Hello", name, "!", "Lets begin conversation from here... (Inspired by William Shakespeare)")
print(name,":", end=" ")
user_pref = input()
while user_pref.lower() not in ["exit",'stop', 'quit', 'close', 'end', 'goodbye', 'bye', 'exit']:
    response = chat.send_message(user_pref)
    print("Model :",response.text)
    print(name,":", end=" ")
    user_pref = input()