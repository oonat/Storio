from django.urls import path
from . import views

app_name = "account"

urlpatterns = [
    path('register/', views.registration_view, name='registration_view'),
    path('logout/', views.logout_view, name='logout_view'),
    path('login/', views.login_view, name='login_view'),
    path('', views.account_view, name='account_view'),
]