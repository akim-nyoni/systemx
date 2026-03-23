from django.urls import path
from . import views

app_name = 'stock'

urlpatterns = [
    # Admin outlet overview
    path('',                                views.stock_dashboard,        name='dashboard'),
    path('outlet/<int:outlet_pk>/',         views.stock_outlet_detail,    name='outlet_detail'),
    # PAR
    path('par/',                            views.par_report,             name='par_report'),
    # Items
    path('items/',                          views.item_list,              name='item_list'),
    path('items/add/',                      views.item_create,            name='item_create'),
    path('items/<int:pk>/',                 views.item_detail,            name='item_detail'),
    path('items/<int:pk>/edit/',            views.item_edit,              name='item_edit'),
    # Counts
    path('counts/',                         views.count_list,             name='count_list'),
    path('counts/start/',                   views.count_create,           name='count_create'),
    path('counts/<int:pk>/',                views.count_detail,           name='count_detail'),
    path('counts/<int:pk>/fill/',           views.count_fill,             name='count_fill'),
    path('counts/<int:pk>/complete/',       views.count_complete,         name='count_complete'),
    path('counts/<int:count_pk>/save-line/',views.save_count_line,        name='save_count_line'),
    # Movements
    path('movements/',                      views.movement_list,          name='movement_list'),
    path('movements/add/',                  views.movement_create,        name='movement_create'),
    path('movements/add/<int:item_pk>/',    views.movement_create,        name='movement_create_item'),
    # Categories
    path('categories/',                     views.category_list,          name='category_list'),
    path('categories/add/',                 views.category_create,        name='category_create'),
    path('categories/<int:pk>/edit/',       views.category_edit,          name='category_edit'),
    path('categories/<int:pk>/delete/',     views.category_delete,        name='category_delete'),
    # Locations
    path('locations/',                      views.location_list,          name='location_list'),
    path('locations/add/',                  views.location_create,        name='location_create'),
    path('locations/<int:pk>/edit/',        views.location_edit,          name='location_edit'),
    path('locations/<int:pk>/delete/',      views.location_delete,        name='location_delete'),
]
