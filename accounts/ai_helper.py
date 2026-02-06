import os
import re
from openai import OpenAI, OpenAIError

from jobs.utils import visible_jobs_for_user
from django.db.models import Q


# -------------------------------------------------
# FORMAT AI RESPONSE INTO CLEAN STEP FORMAT
# -------------------------------------------------
def format_ai_response(text: str) -> str:
    """
    Convert messy LLM paragraph into structured steps.
    Does NOT change meaning — only formatting.
    """

    if not text:
        return text

    # Remove intro phrases models usually generate
    text = re.sub(
        r"(?i)(to .*?follow these steps:|follow these steps:|here are the steps:|steps:)",
        "",
        text
    )

    # Extract numbered steps
    steps = re.findall(r"\d+\.\s*[^0-9]+", text)

    if steps:
        cleaned = "Steps:\n"
        for step in steps:
            cleaned += step.strip() + "\n"
        return cleaned.strip()

    # fallback formatting
    text = re.sub(r"\s*(\d+)\.\s*", r"\n\1. ", text)
    text = re.sub(r"\n+", "\n", text).strip()

    return text


# -------------------------------------------------
# MAIN AI FUNCTION
# -------------------------------------------------
def get_ai_help(user, question, page=None):
    try:
        profile = user.profile
        question_lower = question.lower()

        # -------------------------------------------------
        # REAL BUSINESS RULE (NO AI) — APPLY JOB BLOCK
        # -------------------------------------------------
        apply_keywords = [
            "can't apply",
            "cannot apply",
            "cant apply",
            "why cant i apply",
            "why can't i apply",
            "not able to apply",
            "unable to apply"
        ]

        if any(k in question_lower for k in apply_keywords):
            percent = profile.completion_percentage()

            if percent < 100:
                return f"You cannot apply because your profile is {percent}% complete. Please complete your profile to 100% before applying."
            else:
                return "You can apply for jobs. If you still cannot apply, the job may be restricted or expired."

        # -------------------------------------------------
        # NORMAL AI FLOW
        # -------------------------------------------------
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        model = os.getenv("AI_MODEL", "llama-3.1-8b-instant")

        if not api_key or not base_url:
            return "⚠️ AI service is not configured."

        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        context = f"""
You are an AI assistant inside a job portal web application.

User details:
- Email: {user.email}
- Role: {"Admin" if user.is_staff else "Candidate"}
- Profile completion: {profile.completion_percentage()}%
- Page: {page}

Give clear, step-by-step guidance.
Be concise and helpful.
Rules:
- Keep answers short
- Maximum 5 steps
- Plain text only
- No markdown or emojis
- Answer directly
"""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": question},
            ],
            temperature=0.4,
            max_tokens=200,
        )

        # Clean formatted output
        ai_text = format_ai_response(response.choices[0].message.content)

        # -------------------------------------------------
        # ADD REAL MATCHING JOBS (same logic as search_jobs)
        # -------------------------------------------------
        keywords = [
            "match",
            "matching job",
            "recommended job",
            "suggest job",
            "suitable job",
            "jobs for me"
        ]

        if any(k in question_lower for k in keywords):
            try:
                jobs = visible_jobs_for_user(user)

                if profile.skills:
                    skills_list = [s.strip() for s in profile.skills.split(",") if s.strip()]

                    query = Q()
                    for skill in skills_list:
                        query |= Q(skills__icontains=skill) | Q(title__icontains=skill)

                    jobs = jobs.filter(query).order_by("-created_at")[:5]

                    if jobs.exists():
                        job_lines = "\n".join(
                            [f"• {job.title} — {job.location}" for job in jobs]
                        )

                        ai_text = ai_text.strip() + "\n\nRecommended jobs:\n" + job_lines
                    else:
                        ai_text += "\n\nNo matching jobs found yet. Try adding more skills to your profile."

            except Exception as e:
                print("AI JOB MATCH ERROR:", e)

        return ai_text

    except OpenAIError as e:
        print("AI ERROR:", e)
        return "⚠️ AI assistant is temporarily unavailable."




# import os
# from openai import OpenAI, OpenAIError


# def get_ai_help(user, question, page=None):
#     try:
#         api_key = os.getenv("OPENAI_API_KEY")
#         base_url = os.getenv("OPENAI_BASE_URL")
#         model = os.getenv("AI_MODEL", "llama-3.1-8b-instant")

#         if not api_key or not base_url:
#             return "⚠️ AI service is not configured."

#         client = OpenAI(
#             api_key=api_key,
#             base_url=base_url,
#         )

#         profile = user.profile

#         context = f"""
# You are an AI assistant inside a job portal web application.

# User details:
# - Email: {user.email}
# - Role: {"Admin" if user.is_staff else "Candidate"}
# - Profile completion: {profile.completion_percentage()}%
# - Page: {page}

# Give clear, step-by-step guidance.
# Be concise and helpful.
# """

#         response = client.chat.completions.create(
#             model=model,
#             messages=[
#                 {"role": "system", "content": context},
#                 {"role": "user", "content": question},
#             ],
#             temperature=0.4,
#         )

#         return response.choices[0].message.content

#     except OpenAIError as e:
#         print("AI ERROR:", e)
#         return "⚠️ AI assistant is temporarily unavailable."


