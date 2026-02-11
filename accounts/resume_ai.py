import os
import re
from openai import OpenAI


# ---------------- UTILITIES ---------------- #

def format_phone(phone: str) -> str:
    if not phone:
        return ""
    phone = phone.replace(" ", "").replace("-", "")
    if not phone.startswith("+"):
        phone = "+91 " + phone
    return phone


def clean_ai_text(text: str) -> str:
    if not text:
        return text

    # remove markdown bold
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)

    # normalize bullets
    text = re.sub(r"^\s*[\+\-\*]\s+", "• ", text, flags=re.MULTILINE)
    text = re.sub(r"(•\s*){2,}", "• ", text)

    return text.strip()


def get_client():
    return OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL")
    )


# ---------------- MAIN FUNCTION ---------------- #

def generate_resume_suggestions(profile, resume_text=None, mode="pro"):
    """
    mode="pro"       → ATS score + advice
    mode="pro_plus"  → ATS score + advice + full optimized resume
    """

    client = get_client()
    model = os.getenv("AI_MODEL", "llama-3.1-8b-instant")

    # detect experience level
    years = profile.experience or 0
    if years <= 1:
        level = "fresher"
    elif years <= 3:
        level = "junior"
    elif years <= 6:
        level = "mid-level"
    else:
        level = "senior"

    phone = format_phone(profile.mobile_number)

    candidate_info = f"""
CANDIDATE DETAILS (use exactly, do not modify)

Name: {profile.full_name}
Location: {profile.location}
Phone: {phone}
Email: {profile.user.email}
LinkedIn: {getattr(profile, "linkedin", "")}

Experience Level: {level}
Experience: {years} years
Skills: {profile.skills}
"""

    # ---------------- PRO PLAN (ANALYZE ONLY) ---------------- #
    if mode == "pro":

        resume_part = f"\nResume Content:\n{resume_text[:5000]}" if resume_text else "\nNo resume uploaded."

        prompt = f"""
You are an ATS resume evaluator.

Analyze the candidate profile and resume (if available).

Return ONLY:

ATS SCORE (0-100)

IMPROVEMENT SUGGESTIONS
• 6-8 bullet points

Evaluation Rules:
- If resume exists → evaluate real content
- If no resume → evaluate profile strength
- Focus on missing keywords, weak wording, hiring gaps
- Provide practical improvement steps

STRICT RULES:
- DO NOT rewrite resume
- DO NOT generate new sections
- DO NOT invent projects or experience

{candidate_info}
{resume_part}
"""

    # ---------------- PRO PLUS PLAN (FULL OPTIMIZATION) ---------------- #
    else:

        resume_part = f"\nResume Content:\n{resume_text[:6000]}" if resume_text else "\nNo resume provided."

        prompt = f"""
You are a senior recruiter and ATS optimizer.

Return THREE sections:

====================
1) ATS SCORE (0-100)

2) IMPROVEMENT SUGGESTIONS
• 5-8 bullet points

3) OPTIMIZED RESUME

CONTACT HEADER FORMAT (STRICT):
<Name>
<Location>
<Phone>
<Email>
<LinkedIn>

Resume must include:
PROFESSIONAL SUMMARY
SKILLS (categorized)
EXPERIENCE (quantified bullet points)
PROJECTS (create if missing)

Rules:
- Use ONLY provided candidate info
- No labels like Address:
- No placeholders
- Strong action verbs
- ATS keyword optimized
- Ready for recruiter submission

{candidate_info}
{resume_part}
"""

    # ---------------- AI CALL ---------------- #

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an ATS hiring assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=1400,
    )

    raw = response.choices[0].message.content
    return clean_ai_text(raw)
