from django.urls import path
from . import views

urlpatterns = [

    path('', views.hello_world, name='hello_world'),
    path('absanno/login', views.logIn, name='log_in'),
    path('absanno/logout', views.logOut, name='log_out'),
    path('absanno/square', views.userShow, name='square_show'),
    path('absanno/mission', views.missionShow, name='mission_show'),
    path('absanno/upload', views.upload, name='upload_mission')

]
