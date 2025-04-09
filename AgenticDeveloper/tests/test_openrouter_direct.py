import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

completion = client.chat.completions.create(
    extra_headers={
        "HTTP-Referer": "https://your-site-url.com",
        "X-Title": "Your Site Name",
    },
    extra_body={},
    model="openrouter/quasar-alpha",
    messages=[
        {
            "role": "user",
            "content": "write a momentum strategy for AAPL in QuantConnect Lean"
        }
    ]
)

print(completion.choices[0].message.content)