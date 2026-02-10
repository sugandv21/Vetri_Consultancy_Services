from django.urls import path
from . import views

urlpatterns = [

    # -------------------------
    # CANDIDATE PAGES
    # -------------------------
    path("schedule/", views.schedule_mock, name="schedule_mock"),
    path("my/", views.my_mock_interviews, name="my_mock_interviews"),
    path("join/<int:pk>/", views.join_mock, name="join_mock"),
    path("report/<int:pk>/", views.mock_report, name="mock_report"),

    # -------------------------
    # WEBSITE ADMIN DASHBOARD
    # -------------------------
    path("manage/", views.admin_mock_list, name="admin_mock_list"),
    path("manage/<int:pk>/", views.admin_mock_update, name="admin_mock_update"),
    path("feedback/<int:pk>/", views.mock_feedback, name="mock_feedback"),
]
