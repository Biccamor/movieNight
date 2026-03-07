from engine.prompts import AGENT_SYSTEM_PROMPT
from openai import AsyncOpenAI


client = AsyncOpenAI(
    base_url='http://localhost:11434/v1',
    api_key='ollama'
)

async def llm_response(AGENT_USER_PROMPT: str):
    
    response = await client.chat.completions.create(
        model='llama3.1',
        messages=[
            {"role": "system",
            "content": AGENT_SYSTEM_PROMPT},
            {"role": 'user',
            "content": AGENT_USER_PROMPT}
        ]
    )

    return response[0].choices.message.content