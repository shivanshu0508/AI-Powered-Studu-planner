
from gemini_service import get_gemini_client

try:
    client = get_gemini_client()

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Reply with exactly: Gemini connection works."
    )

    print("Gemini API test successful!")
    print(response.text)

except Exception as error:
    print("Gemini API test failed:")
    print(error)
