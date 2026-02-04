from .models import Job

def visible_jobs_for_user(user):
    jobs = Job.objects.filter(status="PUBLISHED")
    if not user.is_pro:
        jobs = jobs.filter(visibility="FREE")
    return jobs
