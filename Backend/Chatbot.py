import os
from google import genai

from Env import GEMINI_API_KEY

if __name__ == "__main__":
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents="Explain how AI works"
    )
    print(response.text)