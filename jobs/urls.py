from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_job, name='create_job'),
    path('review/', views.review_jobs, name='review_jobs'),
    path('approve/<int:job_id>/', views.approve_job, name='approve_job'),
    path('reject/<int:job_id>/', views.reject_job, name='reject_job'),
    path('active/', views.active_jobs, name='active_jobs'),
    path("search/", views.search_jobs, name="search_jobs"),
    path("save/<int:job_id>/", views.save_job, name="save_job"),
    path("saved/", views.saved_jobs, name="saved_jobs"),
    path("apply/<int:job_id>/", views.apply_job, name="apply_job"),
    path("applications/", views.applications, name="applications"),
    path("job/<int:job_id>/", views.job_detail, name="job_detail"),
    

]
