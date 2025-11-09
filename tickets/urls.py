from django.urls import path

from tickets import views

urlpatterns = [
    path('', views.dashboard, name="index"),
    # path('test', views.test_page, name="testpage"),
    path('api/chat/', views.chat_api, name='gemini-chat'),

    path('all-tickets/', views.all_tickets, name="all_tickets"),
    path('dashboard/', views.dashboard, name="dashboard")
]