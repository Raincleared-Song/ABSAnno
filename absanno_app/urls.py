from django.urls import path
from . import tests, basic_views, admin_views, demander_views, mission_views, utils
from django.conf.urls import url
from django.conf import settings
from django.views.static import serve

urlpatterns = [

    path('', utils.hello_world, name='hello_world'),
    path('csrf', utils.get_csrf, name='csrf'),
    path('test', tests.cookie_test_view, name='test'),
    url(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),

    path('login', basic_views.log_in, name='log_in'),
    path('signin', basic_views.sign_in, name='sign_in'),
    path('logout', basic_views.log_out, name='log_out'),
    path('user', basic_views.about_me, name='user_main'),
    path('sendapply', basic_views.send_apply, name='send_apply'),
    path('receive', basic_views.book_cancel_mission, name='book_mission'),
    path('info', basic_views.change_info, name='change_info'),
    path('changepw', basic_views.change_password, name='change_password'),
    path('changeavatar', basic_views.change_avatar, name='change_avatar'),

    path('square', mission_views.square_show, name='square_show'),
    path('mission', mission_views.mission_show, name='mission_show'),
    path('repshow', mission_views.rep_show, name="rep_show"),
    path('interest', mission_views.interest_show, name='personal_interest'),

    path('upload', demander_views.upload_mission, name='upload_mission'),
    path('mymission', demander_views.show_my_mission, name='my_mission'),
    path('result', demander_views.download_result, name='download'),
    path('check', demander_views.check_result, name='check_result'),
    path('endmission', demander_views.end_mission, name='end_mission'),

    path('alluser', admin_views.show_all_user, name='show_users'),
    path('usepower', admin_views.ban_page, name='power_use'),
    path('powerup', admin_views.upgrade_examine, name='power_up'),
    path('applyshow', admin_views.apply_show, name='apply_show'),
    path('message', admin_views.message_page, name='message_page'),

]
