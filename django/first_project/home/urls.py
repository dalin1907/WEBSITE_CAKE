from django.urls import path
from . import views

app_name = "home"

urlpatterns = [
    path("", views.index, name="index"),
    path("resume/", views.resume, name="resume"),
    path("contact/", views.contact, name="contact"),
    path("portfolio/", views.portfolio, name="portfolio"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("user/", views.user, name="user"),

]
