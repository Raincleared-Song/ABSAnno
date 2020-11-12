import datetime
from django.test import TestCase
from .models import Users, Mission, Question, Reception, History
from django.http import HttpResponse
from .utils import *
import time
import os
import shutil
import json


def cookie_test_view(request):
    response = HttpResponse("This view is reserved for test!")
    response.set_cookie("token", "test")
    return response


class UnitTest(TestCase):
    """class for backend unit test"""

    def setUp(self):
        self.song = Users.objects.create(name='test', password='test_pw', power=2)
        self.wang = Users.objects.create(name='test_wang', password='test_pw_wang', power=1)
        self.banned_user = Users.objects.create(name='test3', password='test_pw3', is_banned=1)
        self.normal_user = Users.objects.create(name='test4', password='test_pw4', tags='Sports||Plant||Animal')  # user with no power
        self.user_num = 4

        self.mission = Mission.objects.create(name='task_test', question_form='chosen', question_num=2,
                                              user=self.song, total=5, reception_num=1, tags="Sports||Game||Lifestyle".lower())
        Question.objects.create(mission=self.mission, word='title1', pre_ans='A', choices='A||B||C||D')
        Question.objects.create(mission=self.mission, word='title2', pre_ans='C', choices='D||E||F||G')
        History.objects.create(user=self.song, mission=self.mission, ans='A||B', pub_time=datetime.date(2021, 6, 30))
        self.mission2 = Mission.objects.create(name='task_test2', question_form='chosen',
                                               question_num=3, user=self.wang, total=5, tags="Animal||Plant||Space".lower())
        Reception.objects.create(user=self.wang, mission=self.mission)
        self.mission_num = 2
        self.maxDiff = None
        self.default_timestamp = int(datetime.datetime(2021, 6, 30, 0, 0).timestamp() * 1000)
        self.upload_pos_case = {"name": "task", "question_form": "chosen", "question_num": "2", "total": "5",
                                "retrieve_time": "1",
                                "question_list": [{"contains": "title3", "ans": "", "choices": "yes||no"},
                                                  {"contains": "title4", "ans": "", "choices": "A||B||C||D"}]}
        self.upload_pos_case2 = {"name": "task", "question_form": "chosen", "question_num": "2", "total": "5",
                                 "retrieve_time": "1",
                                 "question_list": [{"contains": "title3", "ans": "T", "choices": "yes||no"},
                                                   {"contains": "title4", "ans": "F", "choices": "yes||no"}]}
        self.upload_pos_case3 = '{"name": "test_image", "question_form": "chosen-image", "question_num": "2", ' \
                                '"total": "5", "retrieve_time": "1", "question_list": [{"contains": "title3", ' \
                                '"choices": "A||B||C||D", "ans": ""}, {"contains": "title4", "choices": "E||F||G||H",' \
                                ' "ans": ""}]}'
        self.square_pos_case1 = str({'ret': 2, 'total': 2, 'question_list': [
            {'id': 2, 'name': 'task_test2', 'user': 'test_wang', 'questionNum': 3, 'questionForm': 'chosen', 'is_banned': 0,
             'full': 1, 'total_ans': 5, 'ans_num': 0, 'deadline': 1624982400000, 'cash': 5, 'info': '',
             'tags': ['animal', 'plant', 'space'], 'received': 'F', 'image_url': '/backend/media/logo/app.png', 'is_sub': 0},
            {'id': 1, 'name': 'task_test', 'user': 'test', 'questionNum': 2, 'questionForm': 'chosen', 'is_banned': 0,
             'full': 1, 'total_ans': 5, 'ans_num': 0, 'deadline': 1624982400000, 'cash': 5, 'info': '',
             'tags': ['sports', 'game', 'lifestyle'], 'received': 'T', 'image_url': '/backend/media/logo/app.png', 'is_sub': 0}]})
        self.square_pos_case2 = str({'ret': 1, 'total': 1, 'question_list': [
            {'id': 2, 'name': 'task_test2', 'user': 'test_wang', 'questionNum': 3, 'questionForm': 'chosen', 'is_banned': 0,
             'full': 1, 'total_ans': 5, 'ans_num': 0, 'deadline': 1624982400000, 'cash': 5, 'info': '',
             'tags': ['animal', 'plant', 'space'], 'received': 'F', 'image_url': '/backend/media/logo/app.png', 'is_sub': 0}]})
        self.square_pos_case_all = str({'ret': 2, 'total': 2, 'question_list': [
            {'id': 2, 'name': 'task_test2', 'user': 'test_wang', 'questionNum': 3, 'questionForm': 'chosen', 'is_banned': 0,
             'full': 1, 'total_ans': 5, 'ans_num': 0, 'deadline': 1624982400000, 'cash': 5, 'info': '',
             'tags': ['animal', 'plant', 'space'], 'received': '', 'image_url': '/backend/media/logo/app.png', 'is_sub': 0},
            {'id': 1, 'name': 'task_test', 'user': 'test', 'questionNum': 2, 'questionForm': 'chosen', 'is_banned': 0,
             'full': 1, 'total_ans': 5, 'ans_num': 0, 'deadline': 1624982400000, 'cash': 5, 'info': '',
             'tags': ['sports', 'game', 'lifestyle'], 'received': '', 'image_url': '/backend/media/logo/app.png', 'is_sub': 0}]})
        self.interest_pos_case = str({'ret': 2, 'total': 2, 'question_list': [
            {'id': 2, 'name': 'task_test2', 'user': 'test_wang', 'questionNum': 3, 'questionForm': 'chosen', 'is_banned': 0,
             'full': 1, 'total_ans': 5, 'ans_num': 0, 'deadline': 1624982400000, 'cash': 5, 'info': '',
             'tags': ['animal', 'plant', 'space'], 'received': 'F', 'image_url': '/backend/media/logo/app.png', 'is_sub': 0},
            {'id': 1, 'name': 'task_test', 'user': 'test', 'questionNum': 2, 'questionForm': 'chosen', 'is_banned': 0,
             'full': 1, 'total_ans': 5, 'ans_num': 0, 'deadline': 1624982400000, 'cash': 5, 'info': '',
             'tags': ['sports', 'game', 'lifestyle'], 'received': 'F', 'image_url': '/backend/media/logo/app.png', 'is_sub': 0}]})
        self.mission_my_pos_case = str(
            {'mission_name': 'task_test', 'question_form': 'chosen', 'question_num': 2, 'total': 5, 'now_num': 0,
             'is_banned': 0, 'question_list': [{'word': 'title1', 'pre_ans': 'A', 'ans': 'A', 'ans_weight': 1.0},
                                               {'word': 'title2', 'pre_ans': 'C', 'ans': 'B', 'ans_weight': 1.0}]})
        self.power_user_show = str({'num': 3, 'total': 3, 'user_list': [
            {'id': 2, 'name': 'test_wang', 'power': 1, 'is_banned': 0, 'coin': 1000, 'weight': 50, 'fin_num': 0, 'tags': [], 'avatar': ''},
            {'id': 3, 'name': 'test3', 'power': 0, 'is_banned': 1, 'coin': 1000, 'weight': 50, 'fin_num': 0, 'tags': [], 'avatar': ''},
            {'id': 4, 'name': 'test4', 'power': 0, 'is_banned': 0, 'coin': 1000, 'weight': 50, 'fin_num': 0, 'tags': ['Sports', 'Plant', 'Animal'], 'avatar': ''}]})
        self.about_pos_case = str({'total_num': 1, 'mission_list':
            [{'id': 1, 'name': 'task_test', 'user': 'test', 'question_num': 2, 'question_form': 'chosen',
              'reward': 5, 'info': '', 'ret_time': self.default_timestamp}]})

        if not os.path.exists('image'):
            os.mkdir('image')
        if not os.path.exists(os.path.join('image', '_mission_bg')):
            os.mkdir(os.path.join('image', '_mission_bg'))

    @classmethod
    def tearDownClass(cls):
        bg_path = os.path.join('image', '_mission_bg')
        if os.path.exists(bg_path):
            file_list = os.listdir(bg_path)
            for file in file_list:
                if file.endswith('.png'):
                    os.remove(os.path.join(bg_path, file))
        shutil.rmtree(os.path.join('image', 'test_image'))
        shutil.rmtree(os.path.join('image', 'test_image_zip'))
        shutil.rmtree(os.path.join('image', 'test_zip'))

    def mock_login(self):
        self.client.post('/absanno/login', data={'name': 'test', 'password': 'test_pw'},
                         content_type='application/json')

    def mock_login2(self):
        self.client.post('/absanno/login', data={'name': 'test_wang', 'password': 'test_pw_wang'},
                         content_type='application/json')

    def mock_invalid_token(self):
        self.client.post('/absanno/test')

    def mock_no_power_login(self):
        self.client.post('/absanno/login', data={'name': 'test4', 'password': 'test_pw4'},
                         content_type='application/json')

    def test_csrf(self):
        res = self.client.get('/absanno/csrf')
        token = res.content
        self.assertEqual(res.status_code, 200)
        self.assertIsNot(len(token), 0)

    def mock_banned_login(self):
        self.mock_login()
        self.song.is_banned = 1
        self.song.save()

    def mock_banned_mission(self):
        self.mission.is_banned = 1
        self.mission.save()

    def test_hello_world(self):
        res = self.client.get('/absanno')
        self.assertEqual(res.status_code, 301)

    def test_int_to_ABC(self):
        self.assertEqual('B', int_to_abc(1))

    def test_ABC_to_int(self):
        self.assertEqual(2, abc_to_int("C"))

    def test_login_pos(self):
        body = {"name": "test", "password": "test_pw"}
        res = self.client.post('/absanno/login', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], str({'name': 'test', 'power': 2, 'avatar': ''}))

    def test_login_neg_json_err(self):
        body = '{"name": "test", password: "test_pw"}'
        res = self.client.post('/absanno/login', data=body, content_type='application/text')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Request Json Error')

    def test_login_neg_user_null(self):
        body = {"name": "", "password": "test_pw"}
        res = self.client.post('/absanno/login', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Request Body Error')

    def test_login_neg_user_not_exist(self):
        body = {"name": "test2", "password": "test_pw"}
        res = self.client.post('/absanno/login', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'This User Is Not Here')

    def test_login_neg_invalid_pwd(self):
        body = {"name": "test", "password": "test_pw2"}
        res = self.client.post('/absanno/login', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Password Is Error')

    def test_login_neg_banned_user(self):
        body = {"name": "test3", "password": "test_pw3"}
        res = self.client.post('/absanno/login', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'User Is Banned')

    def test_login_neg_request_method_err(self):
        body = {"name": "test", "password": "test_pw"}
        res = self.client.get('/absanno/login', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Log In Error')

    def test_signin_pos(self):
        body = {"name": "tests", "password": "test_pws"}
        res = self.client.post('/absanno/signin', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], str({'name': 'tests', 'power': 0, 'avatar': ''}))
        find = Users.objects.filter(name='tests').first()
        self.assertIsNotNone(find)
        self.assertEqual(find.name, 'tests')

    def test_signin_neg_json_err(self):
        body = '{"name": "tests", "password": test_pws}'
        res = self.client.post('/absanno/signin', data=body, content_type='application/text')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Request Json Error')

    def test_signin_neg_pwd_null(self):
        body = {"name": "tests2"}
        res = self.client.post('/absanno/signin', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Request Body Error')

    def test_signin_neg_user_name_illegal(self):
        body = {"name": "tests a", "password": "test_pws"}
        res = self.client.post('/absanno/signin', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'User Name Error')

    def test_signin_neg_pwd_illegal(self):
        body = {"name": "tests3", "password": "test_"}
        res = self.client.post('/absanno/signin', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Password Length Error')

    def test_signin_neg_user_exist(self):
        body = {"name": "test", "password": "test_pw"}
        res = self.client.post('/absanno/signin', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'User Name Has Existed')

    def test_signin_neg_user_name_long(self):
        body = {"name": "tests" * 6, "password": "test_pws"}
        res = self.client.post('/absanno/signin', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Sign In Form Error')

    def test_signin_neg_request_method_err(self):
        body = {"name": "tests", "password": "test_pws"}
        res = self.client.get('/absanno/signin', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Sign In Error')

    def test_logout_pos(self):
        self.mock_login()
        res = self.client.post('/absanno/logout')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], 'Log Out Finish With Token')

    def test_logout_upload_pos(self):
        self.mock_login()
        self.client.post('/absanno/logout')  # logout
        body = self.upload_pos_case
        res = self.client.post('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'No Token Found in Cookie')

    def test_logout_neg_no_token(self):
        res = self.client.post('/absanno/logout')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], 'Log Out Finish Without Token')

    def test_logout_neg_invalid_token(self):
        self.mock_invalid_token()
        res = self.client.post('/absanno/logout')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], 'Log Out Finish Without Token')

    def test_logout_neg_request_method_err(self):
        res = self.client.get('/absanno/logout')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Log Out Error')

    def test_upload_pos(self):
        self.mock_login()
        body = self.upload_pos_case
        res = self.client.post('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], 'Upload Success')

    def test_upload_pos2(self):
        self.mock_login2()
        body = self.upload_pos_case2
        res = self.client.post('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], 'Upload Success')

    def test_upload_pos_zip(self):
        self.mock_login()
        file = open('test_data/zip/pos.zip', 'rb')
        res = self.client.post('/absanno/upload', data={'zip': file})
        file.close()
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], 'Upload Success')

    def test_upload_pos_zip_image(self):
        self.mock_login()
        file = open('test_data/zip/pos_img.zip', 'rb')
        res = self.client.post('/absanno/upload', data={'zip': file})
        file.close()
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], 'Upload Success')

    def test_upload_pos_zip_mission_image(self):
        self.mock_login()
        file = open('test_data/zip/pos_mission.zip', 'rb')
        res = self.client.post('/absanno/upload', data={'zip': file})
        file.close()
        # self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], 'Upload Success')

    def test_upload_pos_image_list(self):
        self.mock_login()
        files = [open('test_data/zip/res/app.png', 'rb'), open('test_data/zip/res/app2.png', 'rb')]
        res = self.client.post('/absanno/upload', data={'info': self.upload_pos_case3, 'img_list': files})
        files[0].close()
        files[1].close()
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], 'Upload Success')

    def test_upload_pos_mission_image_list(self):
        self.mock_login()
        files = [open('test_data/zip/res/app.png', 'rb'), open('test_data/zip/res/app2.png', 'rb')]
        mission_pic = open('test_data/zip/res/6.jpg', 'rb')
        res = self.client.post('/absanno/upload', data={'info': self.upload_pos_case3,
                                                        'img_list': files, 'mission_image': mission_pic})
        files[0].close()
        files[1].close()
        mission_pic.close()
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], 'Upload Success')

    def test_upload_neg_zip_not_zip(self):
        self.mock_login()
        file = open('test_data/zip/basic.json', 'rb')
        res = self.client.post('/absanno/upload', data={'zip': file})
        file.close()
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Zip File Error (Not Zip File)')

    def test_upload_neg_zip_basic_json_err(self):
        self.mock_login()
        file = open('test_data/zip/neg_basic_json_err.zip', 'rb')
        res = self.client.post('/absanno/upload', data={'zip': file})
        file.close()
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Zip File Error (basic.json Json Error)')

    def test_upload_neg_zip_no_basic(self):
        self.mock_login()
        file = open('test_data/zip/neg_no_basic.zip', 'rb')
        res = self.client.post('/absanno/upload', data={'zip': file})
        file.close()
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Zip File Error (basic.json Not Found)')

    def test_upload_neg_zip_no_path(self):
        self.mock_login()
        file = open('test_data/zip/neg_no_path.zip', 'rb')
        res = self.client.post('/absanno/upload', data={'zip': file})
        file.close()
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Zip File Error (Question Path Not Found)')

    def test_upload_neg_zip_invalid_path(self):
        self.mock_login()
        file = open('test_data/zip/neg_invalid_path.zip', 'rb')
        res = self.client.post('/absanno/upload', data={'zip': file})
        file.close()
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Zip File Error (Question Path Invalid)')

    def test_upload_neg_zip_question_json_err(self):
        self.mock_login()
        file = open('test_data/zip/neg_question_json_err.zip', 'rb')
        res = self.client.post('/absanno/upload', data={'zip': file})
        file.close()
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Zip File Error (questions.json Json Error)')

    def test_upload_neg_no_token(self):
        body = self.upload_pos_case
        res = self.client.post('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'No Token Found in Cookie')

    def test_upload_neg_invalid_token(self):
        self.mock_invalid_token()
        body = self.upload_pos_case
        res = self.client.post('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Invalid Token or Have Not Login')

    def test_upload_neg_banned(self):
        self.mock_banned_login()
        body = self.upload_pos_case
        res = self.client.post('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'User is Banned')

    def test_upload_neg_no_power(self):
        self.mock_no_power_login()
        body = self.upload_pos_case
        res = self.client.post('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Lack of Permission')

    def test_upload_neg_json_err(self):
        self.mock_login()
        body = '{"name": "task", "question_form": "chosen", "question_num": "2", "total": "5",' + \
               ' [{"contains": "title3", "ans": ""}, {"contains": "title4", "ans": ""}]}'
        res = self.client.post('/absanno/upload', data=body, content_type='application/text')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Request Json Error')

    def test_upload_neg_num_not_digit1(self):
        self.mock_login()
        body = {"name": "task", "question_form": "chosen", "question_num": "a", "total": "5",
                "question_list": [{"contains": "title3", "ans": ""}, {"contains": "title4", "ans": ""}]}
        res = self.client.post('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Upload Contains Error')

    def test_upload_neg_num_not_digit2(self):
        self.mock_login()
        body = {"name": "task", "question_form": "chosen", "question_num": "2", "total": "a",
                "question_list": [{"contains": "title3", "ans": ""}, {"contains": "title4", "ans": ""}]}
        res = self.client.post('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Upload Contains Error')

    def test_upload_neg_name_long(self):
        self.mock_login()
        body = {"name": "task" * 8, "question_form": "chosen", "question_num": "2", "total": "5", "retrieve_time": "1",
                "question_list": [{"contains": "title3", "ans": ""}, {"contains": "title4", "ans": ""}]}
        res = self.client.post('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Upload Form Error')

    def test_upload_neg_list_type_err(self):
        self.mock_login()
        body = {"name": "task", "question_form": "chosen", "question_num": "2", "total": "5", "retrieve_time": "1",
                "question_list": {'data': [{"contains": "title3", "ans": ""}, {"contains": "title4", "ans": ""}]}}
        res = self.client.post('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Question_list Is Not A List')

    def test_upload_neg_list_size_err(self):
        self.mock_login()
        body = {"name": "task", "question_form": "chosen", "question_num": "2", "total": "5",
                "retrieve_time": "1", "question_list": [{"contains": "title3", "ans": ""}]}
        res = self.client.post('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Question_list Length Error')

    def test_upload_neg_que_null(self):
        self.mock_login()
        body = {"name": "task", "question_form": "chosen", "question_num": "2", "total": "5", "retrieve_time": "1",
                "question_list": [{"contains": "title3", "ans": "", "choices": "T||F"},
                                  {"contains": "", "ans": "", "choices": "T||F"}]}
        res = self.client.post('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Question Contains is Null')

    def test_upload_neg_ans_err(self):
        self.mock_login()
        body = {"name": "task", "question_form": "chosen", "question_num": "2", "total": "5", "retrieve_time": "1",
                "question_list": [{"contains": "title3", "ans": "A", "choices": "A||B"},
                                  {"contains": "title4", "ans": "", "choices": "T||F"}]}
        res = self.client.post('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], 'Upload Success')

    def test_upload_neg_que_word_long(self):
        self.mock_login()
        body = {"name": "task", "question_form": "chosen", "question_num": "2", "total": "5", "retrieve_time": "1",
                "question_list": [{"contains": "title3" * 40, "ans": "", "choices": "T||F"},
                                  {"contains": "title4", "ans": "", "choices": "yes||no"}]}
        res = self.client.post('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Question Form Error')

    def test_upload_neg_request_method_err(self):
        self.mock_login()
        body = {"name": "task", "question_form": "chosen", "question_num": "2", "total": "5",
                "question_list": [{"contains": "title3", "ans": ""}, {"contains": "title4", "ans": ""}]}
        res = self.client.get('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Upload Error')

    def test_square_pos1(self):
        self.mock_login()
        param = "?num=0"
        res = self.client.get('/absanno/square' + param)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], self.square_pos_case2)

    def test_square_pos2(self):
        self.mock_login2()
        param = "?num=0"
        res = self.client.get('/absanno/square' + param)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], self.square_pos_case1)

    def test_square_pos3(self):
        self.mock_login()
        res = self.client.get('/absanno/square')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], self.square_pos_case2)

    def test_square_pos_no_token(self):
        param = "?num=0"
        res = self.client.get('/absanno/square' + param)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], self.square_pos_case_all)

    def test_square_pos_invalid_token(self):
        self.mock_invalid_token()
        param = "?num=0"
        res = self.client.get('/absanno/square' + param)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], self.square_pos_case_all)

    def test_square_neg_num_illegal(self):
        self.mock_login()
        param = "?num=a"
        res = self.client.get('/absanno/square' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Num Is Not Digit')

    def test_square_neg_num_big(self):
        self.mock_login()
        param = "?num=%d" % (len(Mission.objects.all()))
        res = self.client.get('/absanno/square' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Num Error in Square')

    def test_square_request_method_err(self):
        self.mock_login()
        param = {'num': 0}
        res = self.client.post('/absanno/square', data=param, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'User Show Error')

    def test_square_search_get_sk2(self):
        self.mock_login()
        param = "?num=0&kw=est2"
        res = self.client.get('/absanno/square' + param)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], self.square_pos_case2)

    def test_login_interest_square_pos(self):
        self.mock_no_power_login()
        res = self.client.get('/absanno/interest')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], self.interest_pos_case)

    def test_visitor_interest_square_neg(self):
        self.mock_invalid_token()
        res = self.client.get('/absanno/interest')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], self.square_pos_case_all)

    def test_mission_pos(self):
        self.mock_login2()
        param = "?id=1&num=0&step=1"
        res = self.client.get('/absanno/mission' + param)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], str({'total': 2, 'type': 'chosen', 'ret': 1,
                                                  'word': 'title2', 'choices': 'D||E||F||G', 'image_url': ''}))

    def test_mission_neg_no_token(self):
        param = "?id=1&num=0&step=1"
        res = self.client.get('/absanno/mission' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'No Token Found in Cookie')

    def test_mission_neg_invalid_token(self):
        self.mock_invalid_token()
        param = "?id=1&num=0&step=1"
        res = self.client.get('/absanno/mission' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Invalid Token or Have Not Login')

    def test_mission_neg_banned(self):
        self.mock_banned_login()
        param = "?id=1&num=0&step=1"
        res = self.client.get('/absanno/mission' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'User is Banned')

    def test_mission_neg_param_illegal1(self):
        self.mock_login()
        param = "?id=a&num=0&step=1"
        res = self.client.get('/absanno/mission' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Not Digit Error')

    def test_mission_neg_param_illegal2(self):
        self.mock_login()
        param = "?id=1&num=a&step=1"
        res = self.client.get('/absanno/mission' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Not Digit Error')

    def test_mission_neg_param_illegal3(self):
        self.mock_login()
        param = "?id=1&num=0&step=a"
        res = self.client.get('/absanno/mission' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Not Digit Error')

    def test_mission_neg_id_big(self):
        self.mock_login()
        param = "?id=%d&num=0&step=1" % (self.mission_num + 1)
        res = self.client.get('/absanno/mission' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'ID Error')

    def test_mission_neg_num_big(self):
        self.mock_login()
        param = "?id=1&num=%d&step=1" % self.mission_num
        res = self.client.get('/absanno/mission' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Num Error in Mission Show')

    def test_mission_neg_step_illegal(self):
        self.mock_login()
        param = "?id=1&num=0&step=2"
        res = self.client.get('/absanno/mission' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Step Error')

    def test_mission_neg_mission_banned(self):
        self.mock_login()
        self.mock_banned_mission()
        param = "?id=1&num=0&step=1"
        res = self.client.get('/absanno/mission' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'This Mission Is Banned')

    def test_mission_neg_out_of_bound(self):
        self.mock_login2()
        param = "?id=1&num=%d&step=1" % (self.mission_num - 1)
        res = self.client.get('/absanno/mission' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Runtime Error')

    def test_mission_p_pos(self):
        self.mock_login2()
        body = {'mission_id': '1', 'ans': 'A||C'}
        time.sleep(2.5)
        res = self.client.post('/absanno/mission', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], 'Answer Pushed')

    def test_mission_p_neg(self):
        self.mock_login2()
        body = {'mission_id': '1', 'ans': 'A||B'}
        res = self.client.post('/absanno/mission', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], 'Did Not Pass The Test')

    def test_mission_p_neg_no_token(self):
        body = {'mission_id': '1', 'ans': 'A||B'}
        res = self.client.post('/absanno/mission', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'No Token Found in Cookie')

    def test_mission_p_neg_invalid_token(self):
        self.mock_invalid_token()
        body = {'mission_id': '1', 'ans': 'A||B'}
        res = self.client.post('/absanno/mission', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Invalid Token or Have Not Login')

    def test_mission_p_neg_banned(self):
        self.mock_banned_login()
        body = {'mission_id': '1', 'ans': 'A||B'}
        res = self.client.post('/absanno/mission', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'User is Banned')

    def test_mission_p_neg_json_err(self):
        self.mock_login()
        body = "{'mission_id': '1', ans: 'A||B'}"
        res = self.client.post('/absanno/mission', data=body, content_type='application/text')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Request Json Error')

    def test_mission_p_neg_mid_illegal(self):
        self.mock_login()
        body = {'mission_id': 'a', 'ans': 'A||B'}
        res = self.client.post('/absanno/mission', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Not Digit Or Not List Error')

    def test_mission_p_neg_ans_illegal(self):
        self.mock_login2()
        body = {'mission_id': '1', 'ans': 'A'}
        res = self.client.post('/absanno/mission', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Answer List Length Error')

    def test_mission_p_neg_mid_big(self):
        self.mock_login()
        body = {'mission_id': str(self.mission_num + 1), 'ans': ['T', 'F']}
        res = self.client.post('/absanno/mission', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Mission ID Error')

    def test_mission_p_neg_ans_len(self):
        self.mock_login2()
        body = {'mission_id': '1', 'ans': 'A||B||C'}
        res = self.client.post('/absanno/mission', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Answer List Length Error')

    def test_about_pos_user(self):
        self.mock_login()
        param = "?method=user"
        res = self.client.get('/absanno/user' + param)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], str({'name': 'test', 'coin': 1000, 'weight': 50, 'num': 0, 'tags': [],
                                                  'power': 2, 'avatar': ''}))

    def test_about_pos_mission(self):
        self.mock_login()
        param = "?method=mission"
        res = self.client.get('/absanno/user' + param)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], str(
            {'total_num': 1, 'mission_list': [{'id': 1, 'name': 'task_test', 'total': 5, 'num': 0,
                                               'question_num': 2, 'question_form': 'chosen',
                                               'to_ans': 1, 'reward': 5,
                                               'deadline': self.default_timestamp,
                                               'info': '', 'check_way': 'auto', 'is_banned': 0}]}))

    def test_about_pos_history(self):
        self.mock_login()
        param = "?method=history"
        res = self.client.get('/absanno/user' + param)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], str(self.about_pos_case))

    def test_about_neg_banned(self):
        self.mock_banned_login()
        param = "?method=user"
        res = self.client.get('/absanno/user' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'User is Banned')

    def test_about_neg_no_power(self):
        self.mock_no_power_login()
        param = "?method=mission"
        res = self.client.get('/absanno/user' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Lack of Permission')

    def test_about_neg_no_token(self):
        param = "?method=user"
        res = self.client.get('/absanno/user' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'No Token Found in Cookie')

    def test_about_neg_invalid_token(self):
        self.mock_invalid_token()
        param = "?method=user"
        res = self.client.get('/absanno/user' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Invalid Token or Have Not Login')

    def test_about_neg_access_method_err(self):
        self.mock_login()
        param = "?method=test"
        res = self.client.get('/absanno/user' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Method Is Illegal')

    def test_about_neg_request_method_err(self):
        self.mock_login()
        body = {'method': 'user'}
        res = self.client.post('/absanno/user', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'About Me Error')

    def test_mission_my_pos(self):
        self.mock_login()
        param = "?mission_id=1"
        res = self.client.get('/absanno/mymission' + param)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], self.mission_my_pos_case)

    def test_mission_my_neg_no_token(self):
        param = "?mission_id=1"
        res = self.client.get('/absanno/mymission' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'No Token Found in Cookie')

    def test_mission_my_neg_invalid_token(self):
        self.mock_invalid_token()
        param = "?mission_id=1"
        res = self.client.get('/absanno/mymission' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Invalid Token or Have Not Login')

    def test_mission_my_neg_banned(self):
        self.mock_banned_login()
        param = "?mission_id=1"
        res = self.client.get('/absanno/mymission' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'User is Banned')

    def test_mission_my_neg_no_power(self):
        self.mock_no_power_login()
        param = "?mission_id=1"
        res = self.client.get('/absanno/mymission' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Lack of Permission')

    def test_mission_my_neg_mid_illegal(self):
        self.mock_login()
        param = "?mission_id=a"
        res = self.client.get('/absanno/mymission' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Mission_ID is not digit')

    def test_mission_my_neg_mid_big(self):
        self.mock_login()
        param = "?mission_id=%d" % (self.mission_num + 1)
        res = self.client.get('/absanno/mymission' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Mission_ID is Illegal')

    def test_mission_my_neg_not_match(self):
        self.mock_login()
        param = "?mission_id=2"
        res = self.client.get('/absanno/mymission' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'The ID Is Wrong')

    def test_mission_my_request_method_err(self):
        self.mock_login()
        body = {'mission_id': '1'}
        res = self.client.post('/absanno/mymission', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'My Mission Error')

    def test_power_user_show_success(self):
        self.mock_login()
        param = "?now_num=0"
        res = self.client.get('/absanno/alluser' + param)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], self.power_user_show)

    def test_power_user_show_no_power(self):
        self.mock_login2()
        param = "?now_num=0"
        res = self.client.get('/absanno/alluser' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], "Dont Have Power")

    def test_power_user_show_now_num_not_digit(self):
        self.mock_login()
        param = "?now_num=a"
        res = self.client.get('/absanno/alluser' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], "Now_Num Is Not Digit")

    def test_power_user_show_now_num_error(self):
        self.mock_login()
        param = "?now_num=999"
        res = self.client.get('/absanno/alluser' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], "Now_Num Error")

    def test_power_user_show_method_error(self):
        self.mock_login()
        body = {'now_num': '0'}
        res = self.client.post('/absanno/alluser', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], "Show All Users Failed")

    def test_power_user_show_no_token(self):
        param = "?now_num=0"
        res = self.client.get('/absanno/alluser' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], "No Token Found in Cookie")

    def test_power_user_show_invalid_token(self):
        self.mock_invalid_token()
        param = "?now_num=0"
        res = self.client.get('/absanno/alluser' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], "Invalid Token or Have Not Login")

    def test_power_upgrade_success(self):
        self.mock_login()  # admin login
        body = {"p_id": "4", 'method': 'Accept'}  # userid of the applicant
        res = self.client.post('/absanno/powerup', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], "Upgrade Success")

    def test_power_upgrade_already_publisher(self):
        self.mock_login()  # admin login
        body = {"p_id": "2", 'method': 'Accept'}  # userid of the applicant
        res = self.client.post('/absanno/powerup', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], "You are already publisher!")

    def test_power_upgrade_rejected(self):
        self.mock_login()  # admin login
        body = {"p_id": "4", 'method': 'Rejected'}  # userid of the applicant
        res = self.client.post('/absanno/powerup', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], "Upgrade Rejected")

    def test_power_upgrade_cannot_more(self):
        self.mock_login()
        body = {"p_id": "1", 'method': 'Accept'}  # userid
        res = self.client.post('/absanno/powerup', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], "Are You Kidding Me?")

    def test_power_upgrade_method_wrong(self):
        self.mock_login()
        param = ""
        res = self.client.get('/absanno/powerup' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], "Upgrade Failed")

    def test_power_upgrade_no_token(self):
        body = {}
        res = self.client.post('/absanno/powerup', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], "No Token Found in Cookie")

    def test_power_upgrade_invalid_token(self):
        self.mock_invalid_token()
        body = {}
        res = self.client.post('/absanno/powerup', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], "Invalid Token or Have Not Login")

    def test_power_use_method_wrong(self):
        self.mock_login()
        param = ""
        res = self.client.get('/absanno/usepower' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], "Ban_User Failed")

    def test_power_use_no_token(self):
        body = {'id': '1', 'method': 'user_ban'}
        res = self.client.post('/absanno/usepower', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], "No Token Found in Cookie")

    def test_power_use_invalid_token(self):
        self.mock_invalid_token()
        body = {'id': '1', 'method': 'user_ban'}
        res = self.client.post('/absanno/usepower', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], "Invalid Token or Have Not Login")

    def test_power_use_dont_have_power(self):
        self.mock_login2()
        body = {'id': '1', 'method': 'user_ban'}
        res = self.client.post('/absanno/usepower', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], "Dont Have Power")

    def test_power_use_json_error(self):
        self.mock_login()
        body = {'id' '1' 'method' 'user_ban'}
        res = self.client.post('/absanno/usepower', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], JSON_ERROR)

    def test_power_use_id_error(self):
        self.mock_login()
        body = {'id': 'a', 'method': 'user_ban'}
        res = self.client.post('/absanno/usepower', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], "ID Error")

    def test_power_use_no_method(self):
        self.mock_login()
        body = {'id': '1'}
        res = self.client.post('/absanno/usepower', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], "No Method")

    def test_power_use_user_ban_success(self):
        self.mock_login()
        body = {'id': '2', 'method': 'user_ban'}
        res = self.client.post('/absanno/usepower', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], "Ban User Success")

    def test_power_use_user_ban_fail(self):
        self.mock_login()
        body = {'id': '0', 'method': 'user_ban'}
        res = self.client.post('/absanno/usepower', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], "Ban User ID Error")

    def test_power_use_mission_ban_success(self):
        self.mock_login()
        body = {'id': '2', 'method': 'mission_ban'}
        res = self.client.post('/absanno/usepower', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], "Ban Mission Success")

    def test_power_use_mission_ban_fail(self):
        self.mock_login()
        body = {'id': '0', 'method': 'mission_ban'}
        res = self.client.post('/absanno/usepower', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], "Ban Mission ID Error")

    def test_power_use_user_free_success(self):
        self.mock_login()
        body = {'id': '2', 'method': 'user_free'}
        res = self.client.post('/absanno/usepower', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], "Free User Success")

    def test_power_use_user_free_fail(self):
        self.mock_login()
        body = {'id': '0', 'method': 'user_free'}
        res = self.client.post('/absanno/usepower', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], "Free User ID Error")

    def test_power_use_mission_free_success(self):
        self.mock_login()
        body = {'id': '2', 'method': 'mission_free'}
        res = self.client.post('/absanno/usepower', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], "Free Mission Success")

    def test_power_use_mission_free_fail(self):
        self.mock_login()
        body = {'id': '0', 'method': 'mission_free'}
        res = self.client.post('/absanno/usepower', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], "Free Mission ID Error")

    def test_result_pos(self):
        self.mock_login()
        param = '?mission_id=1'
        res = self.client.get('/absanno/result' + param)
        self.assertEqual(res.status_code, 201)

    def test_result_neg_no_power(self):
        self.mock_no_power_login()
        param = '?mission_id=1'
        res = self.client.get('/absanno/result' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Dont Have Power')

    def test_result_neg_id_not_digit(self):
        self.mock_login()
        param = '?mission_id=a'
        res = self.client.get('/absanno/result' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Mission ID Is Not Digit')

    def test_result_neg_id_illegal(self):
        self.mock_login()
        param = '?mission_id=%d' % (self.mission_num + 1)
        res = self.client.get('/absanno/result' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Mission ID Illegal')

    def test_result_neg_user_wrong(self):
        self.mock_login()
        param = '?mission_id=2'
        res = self.client.get('/absanno/result' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'User ID Is Wrong')

    def test_receive_pos(self):
        self.mock_login()
        body = {'mission_id': '2'}
        res = self.client.post('/absanno/receive', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], 'Book Success')
        self.assertEqual(len(self.song.user_reception.all()), 1)

    def test_receive_neg_json_err(self):
        self.mock_login()
        body = "{'mission_id' '2'}"
        res = self.client.post('/absanno/receive', data=body, content_type='application/text')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], JSON_ERROR)

    def test_receive_neg_mission_id_not_digit(self):
        self.mock_login()
        body = {'mission_id': 'a'}
        res = self.client.post('/absanno/receive', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Mission ID Is Not Digit')

    def test_receive_neg_mission_id(self):
        self.mock_login()
        body = {'mission_id': '3'}
        res = self.client.post('/absanno/receive', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Mission ID Error')

    def test_receive_pos_cancel(self):
        self.mock_login2()
        body = {'mission_id': '1'}
        res = self.client.post('/absanno/receive', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], 'Cancel Book Success')
        self.assertEqual(len(self.wang.user_reception.all()), 0)

    def test_rep_show_pos(self):
        self.mock_login2()
        res = self.client.get('/absanno/repshow')
        self.assertEqual(res.status_code, 201)
        self.assertTrue(res.json()['data'].find('[{') >= 0)

    def test_check_result_neg_no_power(self):
        self.mock_no_power_login()
        body = {'mission_id': '1'}
        res = self.client.get('/absanno/check', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Dont Have Power')

    def test_check_result_neg_wrong_method(self):
        self.mock_login()
        body = {'mission_id': '1'}
        res = self.client.post('/absanno/check', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Check Mission Error, Use GET Instead')

    def test_check_result_neg_wrong_user(self):
        self.mock_login2()
        body = {'mission_id': '1'}
        res = self.client.get('/absanno/check', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Mission Not Published by You')

    def test_check_result_pos(self):
        self.mock_login()
        body = {'mission_id': '1'}
        res = self.client.get('/absanno/check', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], str({'question_list': [
            {'word': 'title1', 'pre_ans': 'A', 'ans': 'A', 'ans_weight': 1.0},
            {'word': 'title2', 'pre_ans': 'C', 'ans': 'B', 'ans_weight': 1.0}]}))

    def test_end_mission_pos(self):
        self.mock_login()
        body = {'mission_id': '1'}
        res = self.client.post('/absanno/endmission', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], 'Mission End Success')

    def test_end_mission_neg_id_not_digit(self):
        self.mock_login()
        body = {'mission_id': 'a'}
        res = self.client.post('/absanno/endmission', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'mission_id Is Not Digit')

    def test_end_mission_neg_id_error(self):
        self.mock_login()
        body = {'mission_id': '3'}
        res = self.client.post('/absanno/endmission', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Mission ID Error')

    def test_end_mission_neg_user_error(self):
        self.mock_login()
        body = {'mission_id': '2'}
        res = self.client.post('/absanno/endmission', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Mission Not Published by You')

    def test_end_mission_neg_method_error(self):
        self.mock_login()
        body = {'mission_id': '1'}
        res = self.client.get('/absanno/endmission', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'End Mission Error')

    def test_post_change_user_tags_pos(self):
        self.mock_login()
        # body = {'tags': '中年,文字识别,运动'} # 中间无空格，逗号为英文逗号
        body = {'tags': tags_by_age[1]+','+tags_by_target[2]+','+tags_by_content[3]}
        res = self.client.post('/absanno/info', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], "{'tags': ['中年', '文字识别', '运动']}")

    def test_get_change_user_tags_pos(self):
        self.mock_no_power_login()
        res = self.client.get('/absanno/info')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], "{'tags': 'Sports,Plant,Animal'}")

    def test_change_password_pos(self):
        self.mock_login()
        body = {'old_password': 'test_pw', 'new_password_1': 'new_password', 'new_password_2': 'new_password'}
        res = self.client.post('/absanno/changepw', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], "You successfully changed your password!")

    def test_upload_avatar_pos(self):
        self.mock_login()
        file = open('test_data/avatar.jpg', 'rb')
        res = self.client.post('/absanno/changeavatar', data={'avatar': file})
        file.close()
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], 'Successfully changed avatar')
        param = "?method=user"
        res = self.client.get('/absanno/user' + param)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], str({'name': 'test', 'coin': 1000, 'weight': 50, 'num': 0,
                                                  'tags': [], 'power': 2,
                                                  'avatar': '/backend/media/Users/1/avatar.jpg'}))


    def test_admin_post_msg_to_all_pos(self):
        self.mock_login()
        body = {'msg': 'Test Message', 'user': ['all', 'admin']}
        res = self.client.post('/absanno/message', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], 'Successfully send message to all users')


    def test_admin_post_msg_no_msg_neg(self):
        self.mock_login()
        body = {'user': ['all', 'admin']}
        res = self.client.post('/absanno/message', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Message is blank?!')


    def test_admin_post_msg_no_target_neg(self):
        self.mock_login()
        body = {'msg': 'Test Message', 'user': ['']}
        res = self.client.post('/absanno/message', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'You didnt specify receivers')
        body = {'msg': 'Test Message'}
        res = self.client.post('/absanno/message', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'You didnt specify receivers')


    def test_admin_post_msg_to_part_pos(self):
        self.mock_login()
        body = {'msg': 'Test Message', 'user': ['admin', 'vip']}
        res = self.client.post('/absanno/message', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], "Successfully send message to target users: ['admin', 'vip']")


    def test_normal_post_msg_to_all_neg(self):
        self.mock_no_power_login()
        body = {'msg': 'Test Message', 'user': ['all', 'admin']}
        res = self.client.post('/absanno/message', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'You dont have power to send message')


    def test_admin_check_all_msg_pos(self):
        self.mock_login()
        body1 = {'msg': 'Test Message 1', 'user': ['all', 'admin']}
        res = self.client.post('/absanno/message', data=body1, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], 'Successfully send message to all users')
        time.sleep(2)
        body2 = {'msg': 'Test Message 2', 'user': ['all', 'vip']}
        res = self.client.post('/absanno/message', data=body2, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], 'Successfully send message to all users')
        res = self.client.get('/absanno/message')
        self.assertEqual(res.status_code, 201)


