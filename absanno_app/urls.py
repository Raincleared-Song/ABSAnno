from django.urls import path
from . import views, tests

urlpatterns = [

    path('', views.hello_world, name='hello_world'),
    path('csrf', views.get_csrf, name='csrf'),
    path('test', tests.cookie_test_view, name='test'),
    path('login', views.log_in, name='log_in'),
    path('signin', views.sign_in, name='sign_in'),
    path('logout', views.log_out, name='log_out'),
    path('square', views.user_show, name='square_show'),
    path('mission', views.mission_show, name='mission_show'),
    path('upload', views.upload, name='upload_mission'),
    path('user', views.about_me, name='user_main'),
    path('mymission', views.show_my_mission, name='my_mission'),
    path('alluser', views.power_user_show_user, name='show_users'),
    path('usepower', views.power_use, name='power_use')

]
