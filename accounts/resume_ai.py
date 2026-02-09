import os

import re
from openai import OpenAI


def generate_resume_suggestions(profile, resume_text=None):

    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("AI_MODEL", "llama-3.1-8b-instant")

    client = OpenAI(api_key=api_key, base_url=base_url)

    # Decide Level 
    years = profile.experience or 0
    if years <= 1:
        level = "fresher"
    elif years <= 3:
        level = "junior"
    elif years <= 6:
        level = "mid-level"
    else:
        level = "senior"

    content = f"""
Candidate Level: {level}
Experience: {years} years
Skills: {profile.skills}
"""

    if resume_text:
        content += f"\nResume Content:\n{resume_text[:5000]}"

    prompt = f"""
You are an expert technical recruiter.

Analyze this candidate and give resume improvement suggestions.

Rules:
- Bullet points only
- Practical suggestions
- No explanation paragraphs
- Max 8 points

{content}
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You review resumes."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=400,
    )

    raw = response.choices[0].message.content
    return clean_ai_text(raw)




def clean_ai_text(text: str) -> str:
    if not text:
        return text

    # Remove markdown bold **
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)

    # Remove stray single *
    text = text.replace("* ", "• ")

    return text.strip()
