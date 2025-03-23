from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    # path('', views.IndexView.as_view(), name='index'),
    path('', views.dashboard_view, name='index'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),

    # User URLs
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserFormView.as_view(), name='user_create'),
    path('users/<int:pk>/update/', views.UserFormView.as_view(), name='user_update'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('projects//<int:pk>', views.ProjectDetailView.as_view(), name='project_detail'),
    path('projects/create/', views.ProjectFormView.as_view(), name='project_create'),
    path('projects/<int:pk>/update/', views.ProjectFormView.as_view(), name='project_update'),
    path('projects/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),

    path('tasks/', views.TaskListView.as_view(), name='task_list'),
]

handler403 = 'projects.views.custom_403'
handler404 = 'projects.views.custom_404'
handler500 = 'projects.views.custom_500'
