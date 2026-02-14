import os
import google.generativeai as genai

#Configuring API key
api_key_aistudio_key_laboratory=os.getenv("aistudio_key_laboratory")
genai.configure(api_key=api_key_aistudio_key_laboratory)

#Choosing model
model = genai.GenerativeModel("gemini-3-flash-preview")

#Prompts
response = model.generate_content("Explain what python lists are in simple terms")

print("Response printed as text:\n"+str(response.text))