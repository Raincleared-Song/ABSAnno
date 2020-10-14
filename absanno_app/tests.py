from django.test import TestCase
from .models import Users, Mission, Question


class UnitTest(TestCase):
    """class for backend unit test"""

    def setUp(self):
        song = Users.objects.create(name='test', password='test_pw')
        wang = Users.objects.create(name='test_wang', password='test_pw_wang')
        Users.objects.create(name='test3', password='test_pw3', is_banned=1)
        self.user_num = 3

        mission = Mission.objects.create(name='task_test', question_form='judgement',
                                         question_num=2, user=song, total=5)
        Question.objects.create(mission=mission, word='title1', pre_ans='T')
        Question.objects.create(mission=mission, word='title2', pre_ans='F')
        Mission.objects.create(name='task_test2', question_form='judgement',
                               question_num=3, user=wang, total=5)
        self.mission_num = 2

        self.upload_pos_case = {"name": "task", "question_form": "judgement", "question_num": "2", "total": "5",
                                "question_list": [{"contains": "title3", "ans": ""},
                                                  {"contains": "title4", "ans": ""}]}
        self.upload_pos_case2 = {"name": "task", "question_form": "judgement", "question_num": "2", "total": "5",
                                "question_list": [{"contains": "title3", "ans": "T"},
                                                  {"contains": "title4", "ans": "F"}]}
        self.square_pos_case_all = str({'ret': 2, 'total': 2, 'question_list':
            [{'id': 1, 'name': 'task_test',
              'user': 'test', 'questionNum': 2, 'questionForm': 'judgement'},
             {'id': 2, 'name': 'task_test2', 'user': 'test_wang',
              'questionNum': 3, 'questionForm': 'judgement'}]})
        self.square_pos_case1 = str({'ret': 1, 'total': 1, 'question_list':
            [{'id': 2, 'name': 'task_test2', 'user': 'test_wang',
              'questionNum': 3, 'questionForm': 'judgement'}]})
        self.mission_my_pos_case = str(
            {'mission_name': 'task_test', 'question_form': 'judgement', 'question_num': 2, 'total': 5, 'now_num': 0,
             'question_list': [{'word': 'title1', 'T_num': 0, 'F_num': 0, 'pre_ans': 'T', 'ans': 1},
                               {'word': 'title2', 'T_num': 0, 'F_num': 0, 'pre_ans': 'F', 'ans': 1}]})

    def mock_login(self):
        self.client.post('/absanno/login', data={'name': 'test', 'password': 'test_pw'},
                         content_type='application/json')

    def mock_login2(self):
        self.client.post('/absanno/login', data={'name': 'test_wang', 'password': 'test_pw_wang'},
                         content_type='application/json')

    def mock_invalid_token(self):
        self.client.post('/absanno/test')

    def test_hello_world(self):
        res = self.client.get('/absanno')
        self.assertEqual(res.status_code, 301)

    def test_login_pos(self):
        body = {"name": "test", "password": "test_pw"}
        res = self.client.post('/absanno/login', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], str({'name': 'test', 'power': 0}))

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
        self.assertEqual(res.json()['data'], str({'name': 'tests', 'power': 0}))
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
        self.assertEqual(res.json()['data'], 'Judgement Upload Success')

    def test_upload_pos2(self):
        self.mock_login()
        body = self.upload_pos_case2
        res = self.client.post('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], 'Judgement Upload Success')

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

    def test_upload_neg_json_err(self):
        self.mock_login()
        body = '{"name": "task", "question_form": "judgement", "question_num": "2", "total": "5",' + \
               ' [{"contains": "title3", "ans": ""}, {"contains": "title4", "ans": ""}]}'
        res = self.client.post('/absanno/upload', data=body, content_type='application/text')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Request Json Error')

    def test_upload_neg_num_not_digit1(self):
        self.mock_login()
        body = {"name": "task", "question_form": "judgement", "question_num": "a", "total": "5",
                "question_list": [{"contains": "title3", "ans": ""}, {"contains": "title4", "ans": ""}]}
        res = self.client.post('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Upload Contains Error')

    def test_upload_neg_num_not_digit2(self):
        self.mock_login()
        body = {"name": "task", "question_form": "judgement", "question_num": "2", "total": "a",
                "question_list": [{"contains": "title3", "ans": ""}, {"contains": "title4", "ans": ""}]}
        res = self.client.post('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Upload Contains Error')

    def test_upload_neg_name_long(self):
        self.mock_login()
        body = {"name": "task" * 8, "question_form": "judgement", "question_num": "2", "total": "5",
                "question_list": [{"contains": "title3", "ans": ""}, {"contains": "title4", "ans": ""}]}
        res = self.client.post('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Upload Form Error')

    def test_upload_neg_list_type_err(self):
        self.mock_login()
        body = {"name": "task", "question_form": "judgement", "question_num": "2", "total": "5",
                "question_list": {'data': [{"contains": "title3", "ans": ""}, {"contains": "title4", "ans": ""}]}}
        res = self.client.post('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Question_list Is Not A List')

    def test_upload_neg_list_size_err(self):
        self.mock_login()
        body = {"name": "task", "question_form": "judgement", "question_num": "2", "total": "5",
                "question_list": [{"contains": "title3", "ans": ""}]}
        res = self.client.post('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Question_list Length Error')

    def test_upload_neg_que_null(self):
        self.mock_login()
        body = {"name": "task", "question_form": "judgement", "question_num": "2", "total": "5",
                "question_list": [{"contains": "title3", "ans": ""}, {"contains": "", "ans": ""}]}
        res = self.client.post('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Question Contains is Null')

    def test_upload_neg_ans_err(self):
        self.mock_login()
        body = {"name": "task", "question_form": "judgement", "question_num": "2", "total": "5",
                "question_list": [{"contains": "title3", "ans": "A"}, {"contains": "title4", "ans": ""}]}
        res = self.client.post('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Ans Set Error')

    def test_upload_neg_que_word_long(self):
        self.mock_login()
        body = {"name": "task", "question_form": "judgement", "question_num": "2", "total": "5",
                "question_list": [{"contains": "title3" * 40, "ans": ""}, {"contains": "title4", "ans": ""}]}
        res = self.client.post('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Question Form Error')

    def test_upload_neg_request_method_err(self):
        self.mock_login()
        body = {"name": "task", "question_form": "judgement", "question_num": "2", "total": "5",
                "question_list": [{"contains": "title3", "ans": ""}, {"contains": "title4", "ans": ""}]}
        res = self.client.get('/absanno/upload', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Upload Error')

    def test_square_pos1(self):
        self.mock_login()
        param = "?num=0"
        res = self.client.get('/absanno/square' + param)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], self.square_pos_case1)

    def test_square_pos2(self):
        self.mock_login2()
        param = "?num=0"
        res = self.client.get('/absanno/square' + param)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], str({'ret': 1, 'total': 1, 'question_list':
            [{'id': 1, 'name': 'task_test',
              'user': 'test', 'questionNum': 2, 'questionForm': 'judgement'}]}))

    def test_square_pos3(self):
        self.mock_login()
        res = self.client.get('/absanno/square')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], self.square_pos_case1)

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
        self.assertEqual(res.json()['data'], 'Num Error')

    def test_square_request_method_err(self):
        self.mock_login()
        param = {'num': 0}
        res = self.client.post('/absanno/square', data=param, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'User Show Error')

    def test_mission_pos(self):
        self.mock_login()
        param = "?id=1&num=0&step=1"
        res = self.client.get('/absanno/mission' + param)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], str({'total': 2, 'ret': 1, 'word': 'title2'}))

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
        self.assertEqual(res.json()['data'], 'Num Error')

    def test_mission_neg_step_illegal(self):
        self.mock_login()
        param = "?id=1&num=0&step=2"
        res = self.client.get('/absanno/mission' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Step Error')

    def test_mission_neg_out_of_bound(self):
        self.mock_login()
        param = "?id=1&num=%d&step=1" % (self.mission_num - 1)
        res = self.client.get('/absanno/mission' + param)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Runtime Error')

    def test_mission_p_pos(self):
        self.mock_login()
        body = {'mission_id': '1', 'ans': ['T', 'F']}
        res = self.client.post('/absanno/mission', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], 'Answer Pushed')

    def test_mission_p_neg_no_token(self):
        body = {'mission_id': '1', 'ans': ['T', 'F']}
        res = self.client.post('/absanno/mission', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'No Token Found in Cookie')

    def test_mission_p_neg_invalid_token(self):
        self.mock_invalid_token()
        body = {'mission_id': '1', 'ans': ['T', 'F']}
        res = self.client.post('/absanno/mission', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Invalid Token or Have Not Login')

    def test_mission_p_neg_json_err(self):
        self.mock_login()
        body = "{'mission_id': '1', ans: ['T', 'F']}"
        res = self.client.post('/absanno/mission', data=body, content_type='application/text')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Request Json Error')

    def test_mission_p_neg_mid_illegal(self):
        self.mock_login()
        body = {'mission_id': 'a', 'ans': ['T', 'F']}
        res = self.client.post('/absanno/mission', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Not Digit Or Not List Error')

    def test_mission_p_neg_ans_illegal(self):
        self.mock_login()
        body = {'mission_id': '1', 'ans': 'T'}
        res = self.client.post('/absanno/mission', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Not Digit Or Not List Error')

    def test_mission_p_neg_mid_big(self):
        self.mock_login()
        body = {'mission_id': str(self.mission_num + 1), 'ans': ['T', 'F']}
        res = self.client.post('/absanno/mission', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Mission ID Error')

    def test_mission_p_neg_ans_len(self):
        self.mock_login()
        body = {'mission_id': '1', 'ans': ['T', 'F', 'T']}
        res = self.client.post('/absanno/mission', data=body, content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['data'], 'Ans List Error')

    def test_about_pos_user(self):
        self.mock_login()
        param = "?method=user"
        res = self.client.get('/absanno/user' + param)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], str({'name': 'test', 'score': 0, 'weight': 100, 'num': 0}))

    def test_about_pos_mission(self):
        self.mock_login()
        param = "?method=mission"
        res = self.client.get('/absanno/user' + param)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], str(
            {'total_num': 1, 'mission_list': [{'id': 1, 'name': 'task_test', 'total': 5, 'num': 0,
                                               'question_num': 2, 'question_form': 'judgement'}]}))

    def test_about_pos_history(self):
        self.mock_login()
        param = "?method=history"
        res = self.client.get('/absanno/user' + param)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['data'], str({'total_num': 0, 'mission_list': []}))

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
