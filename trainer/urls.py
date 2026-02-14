from django.urls import path
from . import views

urlpatterns = [

    path("dashboard/", views.trainer_dashboard, name="trainer_dashboard"),

    # sessions
    path("sessions/today/", views.sessions_today, name="trainer_sessions_today"),
    path("session/<int:session_id>/attend/", views.attend_session, name="trainer_attend_session"),
    path("session/<int:session_id>/feedback/", views.submit_feedback, name="trainer_submit_feedback"),

    
    path("sessions/upcoming/", views.sessions_upcoming, name="trainer_sessions_upcoming"),
    path("sessions/completed/", views.sessions_completed, name="trainer_sessions_completed"),

    # training
    path("modules/", views.module_progress, name="trainer_module_progress"),
    path("module/<int:progress_id>/complete/", views.trainer_mark_module_complete, name="trainer_mark_module_complete"),


    # mock
   # mock interviews
    path("mock/", views.trainer_mock_list, name="trainer_mock_list"),
    path("mock/<int:pk>/join/", views.trainer_join_mock, name="trainer_join_mock"),
    path("mock/<int:pk>/feedback/", views.trainer_mock_feedback, name="trainer_mock_feedback"),
    path("mock/<int:pk>/report/", views.trainer_mock_report, name="trainer_mock_report"),


    # escalations
    path("escalations/", views.escalations, name="trainer_escalations"),
    
    path("trainings/", views.trainer_training_students, name="trainer_training_students"),
    path("trainings/<int:enrollment_id>/", views.trainer_student_progress, name="trainer_student_progress"),


    

]
