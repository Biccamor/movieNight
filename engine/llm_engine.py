from prompts import AGENT_SYSTEM_PROMPT
from openai import OpenAI

client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama'
)

AGENT_USER_PROMPT = "user 1 likes scifi movies and thrillers  user 2 likes crime movies but hate horrors "

response = client.chat.completions.create(
    model='llama3.1',
    messages=[
        {"role": "system",
         "content": AGENT_SYSTEM_PROMPT},
         {"role": 'user',
          "content": AGENT_USER_PROMPT}
    ]
)

print(response)