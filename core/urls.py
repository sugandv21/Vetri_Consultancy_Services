from django.urls import path
from . import views
from .views import training_enquiry_chat
from .views_admin import (
    admin_enrollments,
    admin_enquiries,
    add_training,
    admin_training_list,
    edit_training,
    delete_training,
    admin_enquiry_chat,
)
from .views import services_view, pricing_view, about_view, contact_view
from core import views
from core import views_admin


urlpatterns = [

    # PUBLIC
    path("", views.public_home, name="public_home"),

    # ADMIN HOME
    path("admin-panel/", views.admin_home, name="admin_home"),

    # CANDIDATE – TRAINING
    path("training/", views.training_list, name="training_list"),
    path("training/<int:training_id>/enroll/", views.enroll_training, name="enroll_training"),
    path("training/<int:training_id>/enquiry/",
        training_enquiry_chat,
        name="training_enquiry_chat"
    ),

    # ADMIN – TRAINING MANAGEMENT
    path("admin/training/", admin_training_list, name="admin_training_list"),
    path("admin/training/add/", add_training, name="add_training"),
    path("admin/training/<int:training_id>/edit/", edit_training, name="edit_training"),
    path("admin/training/<int:training_id>/delete/", delete_training, name="delete_training"),

    # ADMIN – ENROLLMENTS & ENQUIRIES
    path("admin/training/enrollments/", admin_enrollments, name="admin_enrollments"),
    path("admin/training/enquiries/", admin_enquiries, name="admin_enquiries"),
    path("admin/enquiry/<int:enquiry_id>/", admin_enquiry_chat, name="admin_enquiry_chat"),
    path("training/<int:training_id>/", views.training_detail, name="training_detail"),
    
    # public view 
    path("services/", services_view, name="services"),
    path("pricing/", pricing_view, name="pricing"),
     path("about/", about_view, name="about"),
    path("contact/", contact_view, name="contact"),
    
    # core/urls.py
    path(
    "admin/enrollment/<int:enrollment_id>/edit/",
    views_admin.edit_enrollment,
    name="edit_enrollment"
),


    

]
