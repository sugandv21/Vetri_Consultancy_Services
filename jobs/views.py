from django.shortcuts import render, redirect
from django.contrib import messages
from accounts.decorators import staff_required, admin_required
from django.contrib.auth.decorators import login_required
from .models import Job, SavedJob, JobApplication
from django.shortcuts import get_object_or_404

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
from .utils import visible_jobs_for_user


@login_required
def search_jobs(request):
    user = request.user
    profile = user.profile

    jobs = visible_jobs_for_user(user)

    # Matching jobs button clicked
    if request.GET.get("match") == "1":
        skills = profile.skills
        role = profile.full_name  # optional if you later add role field

        if skills:
            skills_list = [s.strip() for s in skills.split(",")]

            from django.db.models import Q
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

    return render(
        request,
        "jobs/search_jobs.html",
        {
            "jobs": page_obj,
            "is_matching": request.GET.get("match") == "1"
        }
    )



@login_required
def job_detail(request, job_id):
    jobs = visible_jobs_for_user(request.user)
    job = get_object_or_404(jobs, id=job_id)

    return render(request, "jobs/job_detail.html", {"job": job})


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

#apply job
# @login_required
# def apply_job(request, job_id):
#     job = get_object_or_404(visible_jobs_for_user(request.user), id=job_id)

#     JobApplication.objects.get_or_create(user=request.user, job=job)
#     SavedJob.objects.filter(user=request.user, job=job).delete()

#     messages.success(request, "Application submitted.")
#     return redirect("applications")
@login_required
def apply_job(request, job_id):
    profile = request.user.profile

    #  Block apply if profile not 100% complete
    if profile.completion_percentage() < 100:
        messages.warning(
            request,
            "Please complete your profile (100%) before applying for jobs."
        )
        return redirect("profile_wizard")

    job = get_object_or_404(
        visible_jobs_for_user(request.user),
        id=job_id
    )

    JobApplication.objects.get_or_create(
        user=request.user,
        job=job
    )

    # Remove from saved jobs after applying
    SavedJob.objects.filter(
        user=request.user,
        job=job
    ).delete()

    messages.success(request, "Application submitted successfully.")
    return redirect("applications")


#application page
@login_required
def applications(request):
    applications = JobApplication.objects.filter(user=request.user)
    return render(request, "jobs/applications.html", {"applications": applications})
