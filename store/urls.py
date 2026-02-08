from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.create_bill, name='create_bill'),
    path('bills/', views.bill_history, name='bill_history'),
    path('bill/cancel/<str:bill_no>/', views.cancel_bill, name='cancel_bill'),
    path('bill/pdf/<str:bill_no>/', views.bill_pdf, name='bill_pdf'),
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/edit/<int:product_id>/', views.product_edit, name='product_edit'),

]
