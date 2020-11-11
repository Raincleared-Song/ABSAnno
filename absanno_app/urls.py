from django.urls import path
from . import views, tests
from django.conf.urls import url
from django.conf import settings
from django.views.static import serve

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
    path('usepower', views.power_use, name='power_use'),
    path('powerup', views.power_upgrade, name='power_up'),
    path('repshow', views.rep_show, name="rep_show"),
    path('applyshow', views.apply_show, name='apply_show'),
    path('sendapply', views.send_apply, name='send_apply'),
    path('receive', views.book_cancel_mission, name='book_mission'),
    path('result', views.download, name='download'),
    url(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    path('check', views.check_result, name='check_result'),
    path('interest', views.interests, name='personal_interest'),
    path('endmission', views.end_mission, name='end_mission'),
    path('info', views.change_info, name='change_info'),
    path('changepw', views.change_password, name='change_password'),
    path('changeavatar', views.change_avatar, name='change_avatar'),
    path('message', views.message_page, name='message_page')

]
