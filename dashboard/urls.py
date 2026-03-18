from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home, name='home'),
    path('reports/', views.reports, name='reports'),
    path('reports/export/', views.export_excel, name='export_excel'),
    path('reports/print/', views.print_report, name='print_report'),
    path('reports/submission/<int:pk>/delete/', views.delete_submission, name='delete_submission'),
]
