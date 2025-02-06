import os
from google import genai


if __name__ == "__main__":
    api = os.getenv("GEMINI_API_KEY")
    print(api)
    client = genai.Client(api_key=api)
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents="Explain how AI works"
    )
    print(response.text)