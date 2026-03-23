from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('',                                          views.home,                  name='home'),
    # Outlet drill-down (admin)
    path('outlet/<int:outlet_pk>/',                   views.outlet_detail,         name='outlet_detail'),
    path('outlet/<int:outlet_pk>/dept/<int:dept_pk>/',views.outlet_dept_reports,   name='outlet_dept_reports'),
    # Reports
    path('reports/',                                  views.reports,               name='reports'),
    path('reports/export/',                           views.export_excel,          name='export_excel'),
    path('reports/print/',                            views.print_report,          name='print_report'),
    path('reports/submission/<int:pk>/delete/',       views.delete_submission,     name='delete_submission'),
]
