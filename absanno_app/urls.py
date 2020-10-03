from django.urls import path
from . import views

urlpatterns = [

    path('', views.hello_world, name='hello_world'),
    path('login', views.logIn, name='log_in'),
    path('logout', views.logOut, name='log_out'),
    path('square', views.userShow, name='square_show'),
    path('mission', views.missionShow, name='mission_show'),
    path('upload', views.upload, name='upload_mission')

]
