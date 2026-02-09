import os
import re
from openai import OpenAI, OpenAIError
from jobs.utils import visible_jobs_for_user
from django.db.models import Q
from jobs.models import Job


# -------------------------------------------------
# FORMAT RESPONSE
# -------------------------------------------------
def format_ai_response(text: str) -> str:
    if not text:
        return text

    text = re.sub(r"\s+", " ", text).strip()

    numbered_parts = re.split(r"\s(?=\d+[\.\)])", text)

    if len(numbered_parts) > 1:
        lines = []
        for part in numbered_parts:
            part = re.sub(r"^(\d+)[\)]?\s*", r"\1. ", part.strip())
            lines.append(part)
        return "\n".join(lines)

    sentences = re.split(r"\.\s+", text)
    if len(sentences) > 1:
        return "\n".join(f"{i+1}. {s.strip()}" for i, s in enumerate(sentences) if s.strip())

    return text


# -------------------------------------------------
# DYNAMIC LOCATION DETECTOR (DB BASED)
# -------------------------------------------------
def extract_location_from_db(question: str):
    q = question.lower()

    locations = (
        Job.objects
        .filter(status="PUBLISHED")
        .values_list("location", flat=True)
        .distinct()
    )

    for loc in locations:
        if loc and loc.lower() in q:
            return loc

    return None


# -------------------------------------------------
# SIMPLE INTENT ROUTER (NO KEYWORD LISTS)
# -------------------------------------------------
def detect_intent(question: str):
    q = question.lower()

    if extract_location_from_db(q):
        return "location_search"

    if "match" in q or "recommended" in q or "suggest job" in q:
        return "job_match"

    if "how" in q or "where" in q or "apply" in q or "upload" in q:
        return "guide"

    return "knowledge"
    

# -------------------------------------------------
# MAIN FUNCTION
# -------------------------------------------------
def get_ai_help(user, question, page=None):
    try:
        profile = getattr(user, "profile", None)
        question_lower = question.lower()

        # -------------------------------------------------
        # BUSINESS RULE — APPLY BLOCK
        # -------------------------------------------------
        apply_keywords = [
            "can't apply", "cannot apply", "cant apply",
            "why cant i apply", "why can't i apply",
            "not able to apply", "unable to apply"
        ]

        if profile and any(k in question_lower for k in apply_keywords):
            percent = profile.completion_percentage()
            if percent < 100:
                return f"You cannot apply because your profile is {percent}% complete. Please complete your profile to 100% before applying."
            return "You can apply for jobs. If the button is disabled, the job may be expired or restricted."

        # -------------------------------------------------
        # LOCATION JOB SEARCH (NO AI)
        # -------------------------------------------------
       
        try:
            location = extract_location_from_db(question_lower)

            # profile based location queries
            if not location and profile and profile.location:
                if any(x in question_lower for x in [
                    "my location", "near me", "nearby",
                    "around me", "based on my location"
                ]):
                    location = profile.location

            if location:
                jobs = visible_jobs_for_user(user).filter(location__icontains=location)[:10]

                if jobs.exists():
                    job_lines = "\n".join([f"• {job.title} — {job.location}" for job in jobs])
                    return f"Here are jobs available in {location}:\n\n{job_lines}"
                else:
                    return f"No jobs found in {location}."

        except Exception as e:
            print("LOCATION SEARCH ERROR:", e)
            
        # -------------------------------------------------
        # SKILL JOB SEARCH (PRIORITY AFTER LOCATION)
        # -------------------------------------------------
        if profile and profile.skills:
            if any(x in question_lower for x in [
                "based on my skill",
                "based on my skills",
                "according to my skill",
                "according to my skills",
                "matching my skills",
                "jobs for my skills"
            ]):
                try:
                    skills_list = [s.strip() for s in profile.skills.split(",") if s.strip()]

                    query = Q()
                    for skill in skills_list:
                        query |= Q(skills__icontains=skill) | Q(title__icontains=skill)

                    jobs = visible_jobs_for_user(user).filter(query).order_by("-created_at")[:5]

                    if jobs.exists():
                        job_lines = "\n".join([f"• {job.title} — {job.location}" for job in jobs])
                        return f"Jobs matching your skills:\n\n{job_lines}"
                    else:
                        return "No matching jobs found. Try adding more skills to your profile."

                except Exception as e:
                    print("SKILL SEARCH ERROR:", e)



        # -------------------------------------------------
        # AI CONFIG
        # -------------------------------------------------
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        model = os.getenv("AI_MODEL", "llama-3.1-8b-instant")

        if not api_key or not base_url:
            return "⚠️ AI service is not configured."

        client = OpenAI(api_key=api_key, base_url=base_url)

        # -------------------------------------------------
        # INTENT ROUTING
        # -------------------------------------------------
        intent = detect_intent(question)

        if intent == "guide":
            system_prompt = f"""
You are a job portal website assistant.

User role: {"Admin" if user.is_staff else "Candidate"}
Profile completion: {profile.completion_percentage() if profile else 0}%
Page: {page}

Provide navigation help only.

Rules:
- Maximum 5 steps
- Each step new line
- No explanations
"""

        elif intent == "job_match":
            system_prompt = """
You are a job portal assistant.

Explain how to view matching jobs.
Do NOT suggest careers or job titles.
System will display real jobs separately.

Rules:
- Maximum 5 steps
- Navigation only
"""

        else:  # KNOWLEDGE MODE (default)
            system_prompt = """
You are a technical knowledge assistant.

Answer user questions clearly.
If they ask interview questions, provide a list.
Do not give website navigation.
Plain text only.
"""

        # -------------------------------------------------
        # AI CALL
        # -------------------------------------------------
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            temperature=0.3,
            max_tokens=300,
        )

        ai_text = format_ai_response(response.choices[0].message.content)

        # -------------------------------------------------
        # MATCHING JOBS ADD REAL DB DATA
        # -------------------------------------------------
        if intent == "job_match" and profile:
            try:
                jobs = visible_jobs_for_user(user)

                if profile.skills:
                    skills_list = [s.strip() for s in profile.skills.split(",") if s.strip()]

                    query = Q()
                    for skill in skills_list:
                        query |= Q(skills__icontains=skill) | Q(title__icontains=skill)

                    jobs = jobs.filter(query).order_by("-created_at")[:5]

                    if jobs.exists():
                        job_lines = "\n".join([f"• {job.title} — {job.location}" for job in jobs])
                        ai_text += "\n\nRecommended jobs:\n" + job_lines
                    else:
                        ai_text += "\n\nNo matching jobs found. Add more skills to your profile."

            except Exception as e:
                print("AI JOB MATCH ERROR:", e)

        return ai_text

    except OpenAIError as e:
        print("AI ERROR:", e)
        return "⚠️ AI assistant is temporarily unavailable."
