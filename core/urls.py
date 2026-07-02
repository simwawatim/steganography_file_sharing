from core.Views.Users.UsersView import (SignupView, LoginView, ProfileView)
from django.urls import path

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("profile/", ProfileView.as_view(), name="profile"),
]