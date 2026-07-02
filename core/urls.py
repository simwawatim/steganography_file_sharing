from core.Views.Users.UsersView import (ProfileDetailView, ProfilePictureUpdateView, ProfileUpdateView, SignupView, LoginView)
from django.urls import path

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("profile/", ProfileDetailView.as_view(), name="profile-detail"),
    path("profile/update/", ProfileUpdateView.as_view(), name="profile-update"),
    path("profile/picture/", ProfilePictureUpdateView.as_view(), name="profile-picture"),
]