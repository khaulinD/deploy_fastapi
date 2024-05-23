from core.config import settings
from openai import OpenAI
# Upload a file for fine-tuning
client = OpenAI(api_key=settings.openai_api_key)


async def generate_note(messages, role="user", model='gpt-4'):
    try:
        response = client.chat.completions.create(
            model=model,
            # prompt=messages,
            messages=[{
                "role": role,
                "content": messages
            }],
            max_tokens=1024,  # It's better to specify max_tokens, None could lead to unexpectedly long outputs.
            n=1,
            stop=None,
            temperature=0.7,
        )
        # Properly accessing the response object's content
        response_message = response.choices[0].message.content
        # response_message = response.choices[0].text.strip()
        print(response_message)
        return response_message
    except Exception as e:
        return f"Error: {e}"
