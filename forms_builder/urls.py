from django.urls import path
from . import views

app_name = 'forms_builder'

urlpatterns = [
    # Manager-facing
    path('', views.my_forms, name='my_forms'),
    path('fill/<int:pk>/', views.fill_form, name='fill_form'),
    path('submission/<int:submission_pk>/save/', views.save_response, name='save_response'),
    path('submission/<int:submission_pk>/submit/', views.submit_form, name='submit_form'),
    path('submission/<int:pk>/', views.submission_detail, name='submission_detail'),
    # Admin template builder
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<int:pk>/edit/', views.template_edit, name='template_edit'),
    path('templates/<int:pk>/builder/', views.template_builder, name='template_builder'),
    # AJAX
    path('templates/<int:form_pk>/sections/', views.section_create, name='section_create'),
    path('sections/<int:pk>/delete/', views.section_delete, name='section_delete'),
    path('sections/<int:section_pk>/items/', views.item_create, name='item_create'),
    path('items/<int:pk>/delete/', views.item_delete, name='item_delete'),
]
