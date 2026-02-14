from django.urls import path
from . import views_admin

urlpatterns = [

    # existing admin training list
    path("training/", views_admin.admin_training_list, name="admin_training_list"),

    # NEW PAGES
    path("training/<int:training_id>/modules/", views_admin.training_modules_admin, name="training_modules_admin"),
    path("training/<int:training_id>/students/", views_admin.training_students_admin, name="training_students_admin"),
    path("training/<int:training_id>/progress/", views_admin.training_progress_admin, name="training_progress_admin"),
]
