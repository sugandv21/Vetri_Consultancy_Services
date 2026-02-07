import os
import re
from openai import OpenAI, OpenAIError

# READ-ONLY IMPORTS
from jobs.utils import visible_jobs_for_user
from django.db.models import Q


# -------------------------------------------------
# FORMAT AI RESPONSE INTO CLEAN STEP FORMAT
# -------------------------------------------------
def format_ai_response(text: str) -> str:
    """
    Convert messy AI paragraph into clean readable steps.
    Does NOT change meaning — only formatting.
    Works even if model outputs bad numbering.
    """

    if not text:
        return text

    # Remove common intro phrases
    text = re.sub(
        r"(?i)(here are the steps|follow these steps|steps to apply|steps:)",
        "",
        text
    )

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # -------------------------------------------------
    # CASE 1: Detect numbered steps (1 2 3 or 1.)
    # -------------------------------------------------
    numbered_parts = re.split(r"\s(?=\d+[\.\)])", text)

    if len(numbered_parts) > 1:
        lines = []
        for part in numbered_parts:
            part = part.strip()
            if part:
                # ensure proper format "1. "
                part = re.sub(r"^(\d+)[\)]?\s*", r"\1. ", part)
                lines.append(part)
        return "\n".join(lines)

    # -------------------------------------------------
    # CASE 2: Convert sentences to numbered steps
    # -------------------------------------------------
    sentences = re.split(r"\.\s+", text)

    if len(sentences) > 1:
        lines = []
        for i, s in enumerate(sentences, 1):
            s = s.strip().rstrip(".")
            if s:
                lines.append(f"{i}. {s}")
        return "\n".join(lines)

    # fallback
    return text


# -------------------------------------------------
# MAIN AI FUNCTION
# -------------------------------------------------
def get_ai_help(user, question, page=None):
    try:
        profile = getattr(user, "profile", None)
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

        if profile and any(k in question_lower for k in apply_keywords):
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
- Profile completion: {profile.completion_percentage() if profile else 0}%
- Page: {page}

Give clear, step-by-step guidance.

Rules:
- Maximum 5 steps
- Each step must be on a new line
- Plain text only
- No markdown
- No emojis
- No paragraphs
- Direct answer only
"""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": context},
                {"role": "user", "content": question},
            ],
            temperature=0.3,
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
            "jobs for me",
            "profile matching jobs",
            "find jobs"
        ]

        if profile and any(k in question_lower for k in keywords):
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
# import re
# from openai import OpenAI, OpenAIError

# # READ-ONLY IMPORTS
# from jobs.utils import visible_jobs_for_user
# from django.db.models import Q


# # -------------------------------------------------
# # FORMAT AI RESPONSE INTO CLEAN STEP FORMAT
# # -------------------------------------------------
# def format_ai_response(text: str) -> str:
#     """
#     Convert messy LLM paragraph into structured steps.
#     Does NOT change meaning — only formatting.
#     """

#     if not text:
#         return text

#     # Remove intro phrases models usually generate
#     text = re.sub(
#         r"(?i)(to .*?follow these steps:|follow these steps:|here are the steps:|steps:)",
#         "",
#         text
#     )

#     # Extract numbered steps
#     steps = re.findall(r"\d+\.\s*[^0-9]+", text)

#     if steps:
#         cleaned = "Steps:\n"
#         for step in steps:
#             cleaned += step.strip() + "\n"
#         return cleaned.strip()

#     # fallback formatting
#     text = re.sub(r"\s*(\d+)\.\s*", r"\n\1. ", text)
#     text = re.sub(r"\n+", "\n", text).strip()

#     return text


# # -------------------------------------------------
# # MAIN AI FUNCTION
# # -------------------------------------------------
# def get_ai_help(user, question, page=None):
#     try:
#         profile = user.profile
#         question_lower = question.lower()

#         # -------------------------------------------------
#         # REAL BUSINESS RULE (NO AI) — APPLY JOB BLOCK
#         # -------------------------------------------------
#         apply_keywords = [
#             "can't apply",
#             "cannot apply",
#             "cant apply",
#             "why cant i apply",
#             "why can't i apply",
#             "not able to apply",
#             "unable to apply"
#         ]

#         if any(k in question_lower for k in apply_keywords):
#             percent = profile.completion_percentage()

#             if percent < 100:
#                 return f"You cannot apply because your profile is {percent}% complete. Please complete your profile to 100% before applying."
#             else:
#                 return "You can apply for jobs. If you still cannot apply, the job may be restricted or expired."

#         # -------------------------------------------------
#         # NORMAL AI FLOW
#         # -------------------------------------------------
#         api_key = os.getenv("OPENAI_API_KEY")
#         base_url = os.getenv("OPENAI_BASE_URL")
#         model = os.getenv("AI_MODEL", "llama-3.1-8b-instant")

#         if not api_key or not base_url:
#             return "⚠️ AI service is not configured."

#         client = OpenAI(
#             api_key=api_key,
#             base_url=base_url,
#         )

#         context = f"""
# You are an AI assistant inside a job portal web application.

# User details:
# - Email: {user.email}
# - Role: {"Admin" if user.is_staff else "Candidate"}
# - Profile completion: {profile.completion_percentage()}%
# - Page: {page}

# Give clear, step-by-step guidance.
# Be concise and helpful.
# Rules:
# - Keep answers short
# - Maximum 5 steps
# - Plain text only
# - No markdown or emojis
# - Answer directly
# """

#         response = client.chat.completions.create(
#             model=model,
#             messages=[
#                 {"role": "system", "content": context},
#                 {"role": "user", "content": question},
#             ],
#             temperature=0.4,
#             max_tokens=200,
#         )

#         # Clean formatted output
#         ai_text = format_ai_response(response.choices[0].message.content)

#         # -------------------------------------------------
#         # ADD REAL MATCHING JOBS (same logic as search_jobs)
#         # -------------------------------------------------
#         keywords = [
#             "match",
#             "matching job",
#             "recommended job",
#             "suggest job",
#             "suitable job",
#             "jobs for me"
#         ]

#         if any(k in question_lower for k in keywords):
#             try:
#                 jobs = visible_jobs_for_user(user)

#                 if profile.skills:
#                     skills_list = [s.strip() for s in profile.skills.split(",") if s.strip()]

#                     query = Q()
#                     for skill in skills_list:
#                         query |= Q(skills__icontains=skill) | Q(title__icontains=skill)

#                     jobs = jobs.filter(query).order_by("-created_at")[:5]

#                     if jobs.exists():
#                         job_lines = "\n".join(
#                             [f"• {job.title} — {job.location}" for job in jobs]
#                         )

#                         ai_text = ai_text.strip() + "\n\nRecommended jobs:\n" + job_lines
#                     else:
#                         ai_text += "\n\nNo matching jobs found yet. Try adding more skills to your profile."

#             except Exception as e:
#                 print("AI JOB MATCH ERROR:", e)

#         return ai_text

#     except OpenAIError as e:
#         print("AI ERROR:", e)
#         return "⚠️ AI assistant is temporarily unavailable."
