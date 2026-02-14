from django.urls import path
from . import views
from . import views_admin


urlpatterns = [
    #user
    path("request/", views.request_session, name="consultant_sessions"),
    path("my/", views.my_sessions, name="my_sessions"),
    # admin
    path("admin/requests/", views_admin.admin_session_requests, name="admin_session_requests"),
    path("admin/scheduled/", views_admin.admin_session_scheduled, name="admin_session_scheduled"),
    path("admin/completed/", views_admin.admin_session_completed, name="admin_session_completed"),
    path("admin/schedule/<int:session_id>/", views_admin.schedule_session, name="schedule_session"),
    path("admin/complete/<int:session_id>/", views_admin.mark_completed, name="mark_completed"),
]
