from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_user, name='login'),
    path('register/', views.register_user, name='register'),
    path('logout/', views.logout_user, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    path("admin-panel/dashboard/", views.admin_dashboard, name="admin_dashboard"),

    path('profile/setup/', views.profile_wizard, name='profile_wizard'),
    path('profile/', views.my_profile, name='my_profile'),
    path('settings/', views.settings_view, name='settings'),

    path('admin-panel/candidates/', views.candidate_list, name='candidate_list'),
    path('admin-panel/candidates/<int:user_id>/', views.candidate_detail, name='candidate_detail'),

    path(
        "admin-panel/applications/<int:app_id>/update-status/",
        views.update_application_status,
        name="update_application_status"
    ),

    path("ai-chat/", views.ai_chat_page, name="ai_chat_page"),
    path("ai-help/", views.ai_chatbot, name="ai_chatbot"),

    path("payment/", views.payment, name="payment"),
    path("upgrade/pro/", views.upgrade_to_pro, name="upgrade_to_pro"),
]


# from django.urls import path
# from . import views
# from .views import ai_chat_page

# urlpatterns = [
#     path('login/', views.login_user, name='login'),
#     path('register/', views.register_user, name='register'),
#     path('logout/', views.logout_user, name='logout'),
#     path('dashboard/', views.dashboard_view, name='dashboard'),
#     path("admin-panel/dashboard/", views.admin_dashboard, name="admin_dashboard"),
#     # path("resume/", views.resume_view, name="resume"),
#     path('profile/setup/', views.profile_wizard, name='profile_wizard'),
#     path('profile/', views.my_profile, name='my_profile'),
#     path('settings/', views.settings_view, name='settings'),
#     path('admin-panel/candidates/', views.candidate_list, name='candidate_list'),
#     path('admin-/candidates/<int:user_id>/', views.candidate_detail, name='candidate_detail'),
#     path("admin-panel/applications/<int:app_id>/update-status/", views.update_application_status,
#     name="update_application_status"),
#     path("ai-chat/", ai_chat_page, name="ai_chat_page"),
#     path("ai-help/", views.ai_chatbot, name="ai_chatbot"),
#     path("ai-chat/", views.ai_chat_page, name="ai_chat_page"),
#     path("payment/", views.payment, name="payment"),
#     path("upgrade/pro/", views.upgrade_to_pro, name="upgrade_to_pro"),




# ]
