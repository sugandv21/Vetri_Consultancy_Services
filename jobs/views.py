from django.shortcuts import render, redirect
from django.contrib import messages
from accounts.decorators import staff_required, admin_required
from django.contrib.auth.decorators import login_required
from .models import Job, SavedJob, JobApplication
from django.shortcuts import get_object_or_404
from jobs.utils import visible_jobs_for_user, can_user_apply
from jobs.services.quota import can_apply_quota



@staff_required
def create_job(request):
    if request.method == "POST":

        exp_min = request.POST.get("exp_min")
        exp_max = request.POST.get("exp_max")

        if not exp_min or not exp_max:
            messages.error(request, "Experience range is required.")
            return redirect("create_job")

        try:
            exp_min = int(exp_min)
            exp_max = int(exp_max)
        except ValueError:
            messages.error(request, "Experience must be numeric.")
            return redirect("create_job")

        Job.objects.create(
            title=request.POST.get("title"),
            company_name=request.POST.get("company"),
            location=request.POST.get("location"),
            experience_min=exp_min,
            experience_max=exp_max,
            job_type=request.POST.get("job_type"),
            description=request.POST.get("description"),
            skills=request.POST.get("skills"),
            deadline=request.POST.get("deadline"),
            tag_fresher=bool(request.POST.get("fresher")),
            visibility=request.POST.get("visibility"),
            created_by=request.user,
            status="PENDING" if not request.user.is_superuser else "PUBLISHED"
        )

        messages.success(
            request,
            "Job submitted for approval." if not request.user.is_superuser else "Job published."
        )
        return redirect("active_jobs")

    return render(request, "jobs/create_job.html")



@admin_required
def review_jobs(request):
    jobs = Job.objects.filter(status="PENDING")
    return render(request, "jobs/review_jobs.html", {"jobs": jobs})


@admin_required
def approve_job(request, job_id):
    job = Job.objects.get(id=job_id)
    job.status = "PUBLISHED"
    job.save()
    messages.success(request, "Job approved and published.")
    return redirect("review_jobs")

from accounts.decorators import staff_required
from .models import Job

@staff_required
def active_jobs(request):
    jobs = Job.objects.filter(status="PUBLISHED").order_by("-created_at")
    return render(request, "jobs/active_jobs.html", {"jobs": jobs})



@admin_required
def reject_job(request, job_id):
    job = Job.objects.get(id=job_id)
    job.status = "REJECTED"
    job.save()
    messages.error(request, "Job rejected.")
    return redirect("review_jobs")

#candidate search job
from django.core.paginator import Paginator

from .utils import visible_jobs_for_user, can_user_apply

from django.db.models import Q

@login_required
def search_jobs(request):
    user = request.user
    profile = getattr(user, "profile", None)   # safe profile access

    # show all published jobs (no hiding)
    jobs = visible_jobs_for_user(user)

    # Matching jobs
    if request.GET.get("match") == "1" and profile and profile.skills:
        skills_list = [s.strip() for s in profile.skills.split(",")]

        query = Q()
        for skill in skills_list:
            query |= Q(skills__icontains=skill) | Q(title__icontains=skill)

        jobs = jobs.filter(query)

    # filters
    location = request.GET.get("location")
    job_type = request.GET.get("job_type")
    exp = request.GET.get("exp")

    if location:
        jobs = jobs.filter(location__icontains=location)

    if job_type:
        jobs = jobs.filter(job_type=job_type)

    if exp:
        jobs = jobs.filter(
            experience_min__lte=exp,
            experience_max__gte=exp
        )

    paginator = Paginator(jobs.order_by("-created_at"), 6)
    page_obj = paginator.get_page(request.GET.get("page"))

    # 🔹 Attach permission to each job
    job_list = list(page_obj.object_list)
    for job in job_list:
        job.can_apply = can_user_apply(user, job)

        # determine upgrade target
        if job.visibility == "FREE":
            job.required_plan = None
        elif job.visibility == "PRO":
            job.required_plan = "PRO"
        elif job.visibility == "PROPLUS":
            job.required_plan = "PROPLUS"


    page_obj.object_list = job_list

    return render(
        request,
        "jobs/search_jobs.html",
        {
            "jobs": page_obj,
            "is_matching": request.GET.get("match") == "1"
        }
    )


from .utils import can_user_apply
from .models import Job

@login_required
def job_detail(request, job_id):
    # allow viewing any published job
    job = get_object_or_404(Job, id=job_id, status="PUBLISHED")
    can_apply = can_user_apply(request.user, job)

    required_plan = None
    if not can_apply:
        required_plan = job.visibility

    return render(request, "jobs/job_detail.html", {
        "job": job,
        "can_apply": can_apply,
        "required_plan": required_plan
    })

#save job
@login_required
def save_job(request, job_id):
    job = get_object_or_404(visible_jobs_for_user(request.user), id=job_id)

    SavedJob.objects.get_or_create(user=request.user, job=job)
    messages.success(request, "Job saved.")
    return redirect("search_jobs")


#saved job page
@login_required
def saved_jobs(request):
    jobs = SavedJob.objects.filter(user=request.user)
    return render(request, "jobs/saved_jobs.html", {"jobs": jobs})

from accounts.models import Notification

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

from jobs.models import Job, JobApplication, SavedJob
from accounts.models import Notification


@login_required
def apply_job(request, job_id):

    profile = request.user.profile

    # 1️⃣ PROFILE COMPLETION CHECK
    if profile.completion_percentage() < 100:
        messages.warning(
            request,
            "Please complete your profile (100%) before applying for jobs."
        )
        return redirect("my_profile")

    # 2️⃣ MONTHLY QUOTA CHECK
    allowed, used, limit = can_apply_quota(request.user)

    if not allowed:
        messages.error(
            request,
            f"Monthly application limit reached ({limit}). Upgrade your plan to continue applying."
        )
        return redirect("settings")

    # 3️⃣ GET JOB
    job = get_object_or_404(Job, id=job_id)

    # 4️⃣ APPLY (PREVENT DUPLICATE APPLICATIONS)
    application, created = JobApplication.objects.get_or_create(
        user=request.user,
        job=job
    )

    if not created:
        messages.info(request, "You have already applied for this job.")
        return redirect("applications")

    # 5️⃣ ADMIN ALERT (ONLY FIRST TIME APPLY)
    Notification.objects.create(
        user=None,  # admin alert
        title="New Job Application",
        message=f"{request.user.full_name} applied for {job.title}"
    )

    # 6️⃣ REMOVE FROM SAVED JOBS (IF EXISTS)
    SavedJob.objects.filter(
        user=request.user,
        job=job
    ).delete()

    # 7️⃣ SUCCESS MESSAGE
    messages.success(request, "Application submitted successfully.")
    return redirect("applications")



#application page
@login_required
def applications(request):
    applications = JobApplication.objects.filter(user=request.user)
    return render(request, "jobs/applications.html", {"applications": applications})
