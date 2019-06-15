from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('projects/', views.projects_list, name='projects'),
    path('projects/<slug:slug>/', views.project_detail, name='project_detail'),
    path('skills/', views.skills_view, name='skills'),
    path('experience/', views.experience_view, name='experience'),
    path('contact/', views.contact, name='contact'),
    path('api/ai-chat/', views.ai_chat, name='ai_chat'),
    path('api/refuconnect-demo/', views.refuconnect_demo, name='refuconnect_demo'),
]