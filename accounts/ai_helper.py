import os
from openai import OpenAI, OpenAIError


def get_ai_help(user, question, page=None):
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        model = os.getenv("AI_MODEL", "llama-3.1-8b-instant")

        if not api_key or not base_url:
            return "⚠️ AI service is not configured."

        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        profile = user.profile

        context = f"""
You are an AI assistant inside a job portal web application.

User details:
- Email: {user.email}
- Role: {"Admin" if user.is_staff else "Candidate"}
- Profile completion: {profile.completion_percentage()}%
- Page: {page}

Give clear, step-by-step guidance.
Be concise and helpful.
"""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": question},
            ],
            temperature=0.4,
        )

        return response.choices[0].message.content

    except OpenAIError as e:
        print("AI ERROR:", e)
        return "⚠️ AI assistant is temporarily unavailable."
