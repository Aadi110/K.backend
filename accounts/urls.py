from django.urls import path

from .views import signup, login, update_profile

urlpatterns = [
    path("signup/", signup, name="signup"),
    path("login/", login, name="login"),
    path("update-profile/", update_profile, name="update_profile"),
]
