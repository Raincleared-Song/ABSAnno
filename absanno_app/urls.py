from django.urls import path
from . import views

urlpatterns = [

    path('', views.hello_world, name='hello_world'),
    path('login', views.log_in, name='log_in'),
    path('signin', views.sign_in, name='sign_in'),
    path('logout', views.log_out, name='log_out'),
    path('square', views.user_show, name='square_show'),
    path('mission', views.mission_show, name='mission_show'),
    path('upload', views.upload, name='upload_mission'),
    path('user', views.about_me, name='user_main'),
    path('mymission', views.show_my_mission, name='my_mission')

]
