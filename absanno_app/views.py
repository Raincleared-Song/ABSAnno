from django.http import JsonResponse, HttpResponse
import json
from .models import Users, Mission, Question, History
from django.core.exceptions import ValidationError
from django.db.models import Q


def hello_world(request):
    return HttpResponse("Hello Absanno!")


# 有关用户的登录与注册
# request.body为json
# 其中内容为：
# name, password, method, email
# name为必须，password在method为LogIn和SignIn时为必须，为LogOut时非必须
# email留作扩展功能时期实现
# 出错返回可以参考下面的代码


def gen_response(code: int, data: object):  # 是否成功，成功为201，失败为400
    return JsonResponse({
        'code': code,
        'data': str(data)
    }, status=code)


def log_in(request):
    if request.method == 'POST':

        try:
            message = request.body
            js = json.loads(message)
        except json.decoder.JSONDecodeError:
            return gen_response(400, "Request Json Error")

        name = js['name'] if 'name' in js else ''
        password = js['password'] if 'password' in js else ''
        method = js['method'] if 'method' in js else ''
        # email = js['email'] if 'email' in js else ''

        # 安全性验证
        # TODO

        if name == '' or password == '':
            return gen_response(400, "Request Body Error")

        if method == "LogIn":
            user = Users.objects.filter(name=name).first()
            if not user:
                return gen_response(400, "This User Is Not Here")
            if password != user.password:
                return gen_response(400, "Password Is Error")
            if user.is_banned == 1:
                return gen_response(400, "User Is Banned")
            return gen_response(201, {
                'id': user.id,
                'name': user.name
            }
                                )

    return gen_response(400, "Log In Error")


def sign_in(request):
    if request.method == 'POST':

        try:
            message = request.body
            js = json.loads(message)
        except json.decoder.JSONDecodeError:
            return gen_response(400, "Request Json Error")

        name = js['name'] if 'name' in js else ''
        password = js['password'] if 'password' in js else ''
        method = js['method'] if 'method' in js else ''
        email = js['email'] if 'email' in js else ''

        # 安全性验证
        # TODO

        if not name or not password:
            return gen_response(400, "Request Body Error")

        if method == "SignIn":
            if '\t' in name or '\n' in name or ' ' in name or ',' in name or '.' in name:  # 禁止名字中特定字符
                return gen_response(400, "User Name Error")
            if len(password) < 6 or len(password) > 20:
                return gen_response(400, "Password Length Error")
            gen_user = Users.objects.filter(name=name).first()
            if gen_user:
                return gen_response(400, "User Name Has Existed")
            # user = Users(name=name, password=password, email=email)
            user = Users(name=name, password=password)
            try:
                user.full_clean()
                user.save()
            except ValidationError:
                return gen_response(400, "Sign In Form Error")
            return gen_response(201, {
                'id': user.id,
                'name': user.name
            }
                                )

    return gen_response(400, "Sign In Error")


def log_out(request):
    if request.method == 'POST':

        try:
            message = request.body
            js = json.loads(message)
        except json.decoder.JSONDecodeError:
            return gen_response(400, "Request Json Error")

        name = js['name'] if 'name' in js else ''
        password = js['password'] if 'password' in js else ''
        method = js['method'] if 'method' in js else ''
        email = js['email'] if 'email' in js else ''

        # 安全性验证
        # TODO

        if method == "LogOut":
            return gen_response(201, "Log Out Finish")

    return gen_response(400, "Log Out Error")


# 每次前端问题广场需要申请一次获取问题列表GET，然后获得问题
# 包括第一次进入问题广场
# request.body为json
# 其中内容为
# id，num，id表示当前用户id，num表示目前显示给用户的任务的数字，默认为0，之后可以使用后端getNum传给前端的num
# 每次传输的任务数量为 本次返回的getNum-本次传入的num


def user_show(request):
    if request.method == 'GET':

        # 安全性验证
        # TODO

        id_ = request.GET.get('id')
        num_ = request.GET.get('num')

        if not id_.isdigit():
            return gen_response(400, "ID Is Not Digit")
        if not num_.isdigit():
            return gen_response(400, "Num Is Not Digit")
        id, num = int(id_), int(num_)
        if id < 0 or id > len(Users.objects.all()):
            return gen_response(400, "ID Error")
        if num < 0 or num >= len(Mission.objects.filter(to_ans=1)):
            return gen_response(400, "Num Error")

        # 参考id获取用户画像，进而实现分发算法，目前使用id来进行排序
        # TODO

        mission_list = Mission.objects.filter(Q(to_ans=1) & ~Q(user_id=id))
        showNum = 12  # 设计一次更新获得的任务数
        getNum = min(num + showNum, len(mission_list))  # 本次更新获得的任务数

        return gen_response(201, {'ret': getNum,
                                  'total': len(Mission.objects.filter(Q(to_ans=1) & ~Q(user_id=id))),
                                  "question_list":
                                      [
                                          {
                                              'id': ret.id,
                                              'name': ret.name,
                                              'user': ret.user.name,
                                              'questionNum': ret.question_num,
                                              'questionForm': ret.question_form
                                          }
                                          for ret in Mission.objects.filter(
                                          Q(to_ans=1) & ~Q(user_id=id)).order_by('id')[num: getNum]
                                      ]}
                            )
    return gen_response(400, "User Show Error")


# 打开任务后存在GET和POST两种方式

# GET为用户切换题目时使用的方式
# 其request.body为一个json文件，组成为：
# id, num，step
# 其中id为目前所做任务的编号，num表示题号，默认为0，之后使用返回的getNum，step为1或者-1，表示下一题和上一题

# POST为用户提交本次传递题目
# 其request.body为一个json文件，组成为：
# user_id, mission_id, [{ans}]
# 其中user_id为当前答题用户，用于统计其用户信息，如score，mission_id为当前任务的id，表示目前用户回答的任务的id，ans为用户的答案，目前仅支持判断题

def mission_show(request):
    if request.method == 'GET':

        # 安全性验证
        # TODO

        id_ = request.GET.get('id')
        num_ = request.GET.get('num')
        step_ = request.GET.get('step')

        if not id_.isdigit() or not num_.isdigit() or not step_.isdigit():
            return gen_response(400, "Not Digit Error")
        id = int(id_)
        num = int(num_)
        step = int(step_)
        if id <= 0 or id > len(Mission.objects.all()):
            return gen_response(400, "ID Error")
        if num < 0 or num >= len(Mission.objects.get(id=id).father_mission.all()):
            return gen_response(400, "Num Error")
        if step != -1 and step != 1 and step != 0:
            return gen_response(400, "Step Error")

        getNum = num + step
        if getNum < 0 or getNum >= len(Mission.objects.get(id=id).father_mission.all()):
            return gen_response(400, "Runtime Error")

        ret = Mission.objects.get(id=id).father_mission.all().order_by('id')[getNum]

        if Mission.objects.get(id=id).question_form == "judgement":  # 题目型式为判断题的情况
            return gen_response(201, {
                'total': len(Mission.objects.get(id=id).father_mission.all()),
                'ret': getNum,
                'word': ret.word,
            })

        # 题目为选择题型式之后实现
        # TODO

        return gen_response(400, "Change Question Error")

    elif request.method == 'POST':

        # 安全性验证
        # TODO

        try:
            message = request.body
            js = json.loads(message)
        except json.decoder.JSONDecodeError:
            return gen_response(400, "Request Json Error")

        user_id_ = js['user_id'] if 'user_id' in js else '-1'
        mission_id_ = js['mission_id'] if 'mission_id' in js else '-1'
        ans_list = js['ans'] if 'ans' in js else []

        if not user_id_.isdigit() or not mission_id_.isdigit() or not isinstance(ans_list, list):
            return gen_response(400, "Not Digit Or Not List Error")

        user_id = int(user_id_)
        mission_id = int(mission_id_)
        if user_id <= 0 or user_id > len(Users.objects.all()):
            return gen_response(400, "User ID Error")
        if mission_id <= 0 or mission_id > len(Mission.objects.all()):
            return gen_response(400, "Mission ID Error")

        user = Users.objects.get(id=user_id)
        mission = Mission.objects.get(id=mission_id)
        if len(ans_list) != len(mission.father_mission.all()):
            return gen_response(400, "Ans List Error")

        # 开始结算
        # 判断题
        if mission.question_form == "judgement":
            user.score += len(mission.father_mission.all())
            user.fin_num += 1
            flag = True
            for i in range(0, len(ans_list)):
                if mission.father_mission.all().order_by('id')[i].pre_ans != "" and \
                        mission.father_mission.all().order_by('id')[i].pre_ans != ans_list[i]:
                    user.score -= 5
                    flag = False
            if flag:
                user.weight += 1
                for i in range(0, len(ans_list)):
                    now_question = mission.father_mission.all().order_by('id')[i]
                    if ans_list[i] == 'T':
                        now_question.T_num += 1
                    elif ans_list[i] == 'F':
                        now_question.F_num += 1
                    if now_question.F_num > now_question.T_num:
                        now_question.matched_ans = 0
                    else:
                        now_question.matched_ans = 1
                mission.now_num += 1
                if mission.now_num >= mission.total:
                    mission.to_ans = 0
            else:
                user.weight -= 10
                user.score -= len(ans_list)
            if user.weight <= 0:
                user.is_banned = 1

            history = History(user=user, mission=mission)
            history.save()

        # 选择题
        # TODO

        # 之后需要优化weight等内容

        return gen_response(201, "Answer Pushed")
    return gen_response(400, 'Mission Show Error')


# upload关于上传任务

def upload(request):
    if request.method == 'POST':

        try:
            message = request.body
            js = json.loads(message)
        except json.decoder.JSONDecodeError:
            return gen_response(400, "Request Json Error")

        name = js['name'] if 'name' in js else ''
        question_form = js['question_form'] if 'question_form' in js else ''
        question_num_ = js['question_num'] if 'question_num' in js else ''
        user_id_ = js['user_id'] if 'user_id' in js else ''
        total_ = js['total'] if 'total' in js else ''
        if not question_num_.isdigit() or name == '' or question_form == '' or not user_id_.isdigit() or not total_.isdigit():
            return gen_response(400, "Upload Contains Error")
        question_num = int(question_num_)
        user_id = int(user_id_)
        total = int(total_)

        try:
            mission = Mission(name=name, question_form=question_form, question_num=question_num, total=total,
                              user=Users.objects.filter(pk=user_id).first())
            mission.full_clean()
            mission.save()
        except ValidationError:
            return gen_response(400, "Upload Form Error")

        question_list = js['question_list'] if 'question_list' in js else []
        if not isinstance(question_list, list):
            return gen_response(400, "Question_list Is Not A List")
        if len(question_list) != question_num:
            return gen_response(400, "Question_list Length Error")

        # 判断题限定ver.

        if mission.question_form == "judgement":
            for i in question_list:
                contains = i['contains'] if 'contains' in i else ''
                ans = i['ans'] if 'ans' in i else ''
                if contains == '':
                    return gen_response(400, "Question Contains is Null")
                try:
                    question = Question(word=contains, mission=mission)
                    if ans == 'T' or ans == 'F' or ans == '':
                        question.pre_ans = ans
                        if ans != '':
                            question.has_pre_ans = 1
                    else:
                        return gen_response(400, "Ans Set Error")
                    question.full_clean()
                    question.save()
                except ValidationError:
                    return gen_response(400, "Question Form Error")
            return gen_response(201, "Judgement Upload Success")

    return gen_response(400, "Upload Error")


def about_me(request):
    if request.method == 'GET':

        id_ = request.GET.get('id') if 'id' in request.GET else ''
        if not id_.isdigit():
            return gen_response(400, "ID Is Not Digit")
        id = int(id_)
        if id <= 0 or id > len(Users.objects.all()):
            return gen_response(400, "ID Is Illegal")
        method = request.GET.get('method') if 'method' in request.GET else ''

        ret = Users.objects.get(id=id)

        if method == 'user':
            return gen_response(201, {
                'id': ret.id,
                'name': ret.name,
                'score': ret.score,
                'weight': ret.weight,
                'num': ret.fin_num
            })
        elif method == 'mission':
            return gen_response(201, {
                'total_num': len(ret.promulgator.all()),
                'mission_list':
                    [
                        {
                            'id': mission_ret.id,
                            'name': mission_ret.name,
                            'total': mission_ret.total,
                            'num': mission_ret.now_num,
                            'question_num': mission_ret.question_num,
                            'question_form': mission_ret.question_form
                        }
                        for mission_ret in ret.promulgator.all().order_by('id')
                    ]
            })
        elif method == 'history':
            return gen_response(201, {
                'total_num': len(ret.history.all()),
                'mission_list':
                    [
                        {
                            'id': mission_ret.mission.id,
                            'name': mission_ret.mission.name,
                            'user': mission_ret.mission.user.name,
                            'question_num': mission_ret.mission.question_num,
                            'question_form': mission_ret.mission.question_form,
                            'ret_time': mission_ret.pub_time
                        }
                        for mission_ret in ret.history.all().order_by('pub_time')
                    ]
            })
        else:
            return gen_response(400, "Method Is Illegal")
    return gen_response(400, "About Me Error")


def show_my_mission(request):
    if request.method == 'GET':

        user_id_ = request.GET.get('user_id') if 'user_id' in request.GET else ''
        mission_id_ = request.GET.get('mission_id') if 'mission_id' in request.GET else ''

        if not user_id_.isdigit():
            return gen_response(400, "User_ID is not digit")
        if not mission_id_.isdigit():
            return gen_response(400, "Mission_ID is not digit")
        user_id, mission_id = int(user_id_), int(mission_id_)

        if user_id <= 0 or user_id > len(Users.objects.all()):
            return gen_response(400, "User_ID is Illegal")
        if mission_id <= 0 or mission_id > len(Mission.objects.all()):
            return gen_response(400, "Mission_ID is Illegal")
        if user_id != Mission.objects.get(id=mission_id).user.id:
            return gen_response(400, "The ID Is Wrong")
        mission = Mission.objects.get(id=mission_id)

        # 判断题模式

        if mission.question_form == "judgement":
            return gen_response(201, {
                'mission_name': mission.name,
                'question_form': mission.question_form,
                'question_num': mission.question_num,
                'total': mission.total,
                'now_num': mission.now_num,
                'question_list':
                    [
                        {
                            'word': ret.word,
                            'T_num': ret.T_num,
                            'F_num': ret.F_num,
                            'pre_ans': ret.pre_ans,
                            'ans': ret.matched_ans
                        }
                        for ret in mission.father_mission.all()
                    ]
            })
    return gen_response(400, "My Mission Error")
