from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/',  views.login_view,  name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_view, name='change_password'),
    # Users
    path('users/',                  views.user_list_view,         name='user_list'),
    path('users/create/',           views.user_create_view,       name='user_create'),
    path('users/<int:pk>/edit/',    views.user_edit_view,         name='user_edit'),
    path('users/<int:pk>/toggle/',  views.user_toggle_active_view,name='user_toggle'),
    path('users/<int:pk>/delete/',  views.user_delete_view,       name='user_delete'),
    # Roles
    path('roles/',                  views.role_list_view,   name='role_list'),
    path('roles/create/',           views.role_create_view, name='role_create'),
    path('roles/<int:pk>/edit/',    views.role_edit_view,   name='role_edit'),
    path('roles/<int:pk>/delete/',  views.role_delete_view, name='role_delete'),
    # Departments
    path('departments/',                 views.dept_list_view,   name='dept_list'),
    path('departments/create/',          views.dept_create_view, name='dept_create'),
    path('departments/<int:pk>/edit/',   views.dept_edit_view,   name='dept_edit'),
    path('departments/<int:pk>/delete/', views.dept_delete_view, name='dept_delete'),
]
