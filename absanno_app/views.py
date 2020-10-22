from django.http import JsonResponse, HttpResponse
import json
from .models import Users, Mission, Question, History
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.middleware.csrf import get_token
from zipfile import ZipFile, BadZipFile


def hello_world(request):
    return HttpResponse("Hello Absanno!")


def get_csrf(request):
    return HttpResponse(get_token(request))


def find_user_by_token(request):
    return Users.objects.get(id=request.session['user_id'])


def check_is_banned(request):
    """return True iff user not exist or user is banned"""
    user = find_user_by_token(request)
    return user is None or user.is_banned == 1


def check_token(request):
    if not request.COOKIES.get('token'):
        return 400, "No Token Found in Cookie"
    if 'is_login' not in request.session:
        return 400, "Invalid Token or Have Not Login"
    return 201, 'Valid'


def gen_response(code: int, data: object):  # 是否成功，成功为201，失败为400
    return JsonResponse({
        'code': code,
        'data': str(data)
    }, status=code)


# 有关用户的登录与注册
# request.body为json
# 其中内容为：
# name, password
# email留作扩展功能时期实现
# 出错返回可以参考下面的代码


def log_in(request):
    if request.method == 'POST':

        try:
            js = json.loads(request.body)
        except json.decoder.JSONDecodeError:
            return gen_response(400, "Request Json Error")

        name = js['name'] if 'name' in js else ''
        password = js['password'] if 'password' in js else ''
        # email = js['email'] if 'email' in js else ''

        # 安全性验证
        # TODO

        if not name or not password:
            return gen_response(400, "Request Body Error")

        user = Users.objects.filter(name=name).first()
        if not user:
            return gen_response(400, "This User Is Not Here")
        if password != user.password:
            return gen_response(400, "Password Is Error")
        if user.is_banned == 1:
            return gen_response(400, "User Is Banned")

        request.session['user_id'] = user.id
        request.session['is_login'] = True
        request.session.save()

        return gen_response(201, {
            'name': user.name,
            'power': user.power
        })

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
        tags = js['tags'] if 'tags' in js else ''
        # email = js['email'] if 'email' in js else ''

        # 安全性验证
        # TODO

        if not name or not password:
            return gen_response(400, "Request Body Error")

        if '\t' in name or '\n' in name or ' ' in name or ',' in name or '.' in name:  # 禁止名字中特定字符
            return gen_response(400, "User Name Error")
        if len(password) < 6 or len(password) > 20:
            return gen_response(400, "Password Length Error")
        gen_user = Users.objects.filter(name=name).first()
        if gen_user:
            return gen_response(400, "User Name Has Existed")

        # user = Users(name=name, password=password, email=email)
        user = Users(name=name, password=password, tags=tags)

        try:
            user.full_clean()
            user.save()
        except ValidationError:
            return gen_response(400, "Sign In Form Error")

        request.session['user_id'] = user.id
        request.session['is_login'] = True
        request.session.save()

        return gen_response(201, {
            'name': user.name,
            'power': user.power
        })

    return gen_response(400, "Sign In Error")


def log_out(request):
    if request.method == 'POST':

        # 安全性验证
        # TODO

        code, data = check_token(request)
        if code == 400:
            return gen_response(201, "Log Out Finish Without Token")

        if request.session['is_login']:
            request.session['is_login'] = False
        request.session.flush()  # remove the token
        return gen_response(201, "Log Out Finish With Token")

    return gen_response(400, "Log Out Error")


# 每次前端问题广场需要申请一次获取问题列表GET，然后获得问题
# 包括第一次进入问题广场
# request.body为json
# 其中内容为
# num，num表示目前显示给用户的任务的数字，默认为0，之后可以使用后端getNum传给前端的num
# 每次传输的任务数量为 本次返回的getNum-本次传入的num


def user_show(request):
    if request.method == 'GET':

        # 安全性验证
        # TODO

        user_id = request.session['user_id'] if check_token(request)[0] == 201 else 0
        # user_id = request.GET.get('user_id')

        num_ = request.GET.get('num')
        type__ = request.GET.get('type') if 'type' in request.GET else ""
        theme__ = request.GET.get('theme') if 'theme' in request.GET else ""
        kw = request.GET.get('kw') if 'kw' in request.GET else ""

        if not num_:
            num_ = "0"
        if type__ != "":
            type_ = type__.split(",")
        else:
            type_ = []
        if theme__ != "":
            theme_ = theme__.split(",")
        else:
            theme_ = []

        if not num_.isdigit():
            return gen_response(400, "Num Is Not Digit")
        num = int(num_)
        if num < 0 or num >= len(Mission.objects.filter(to_ans=1)):
            return gen_response(400, "Num Error")

        # 参考id获取用户画像，进而实现分发算法，目前使用id来进行排序
        # TODO

        user = Users.objects.filter(id=user_id).first()

        if user:
            mission_list_temp = Mission.objects.filter(Q(to_ans=1) & Q(is_banned=0)).order_by('id')
            mission_list_base = []
            for mission in mission_list_temp:
                if user.history.filter(mission__id=mission.id).first() is None:
                    mission_list_base.append(mission)
        else:
            mission_list_base = Mission.objects.all().order_by('id')

        mission_list = []
        for mis in mission_list_base:
            tag_flag, kw_flag = 0, 0
            if ('total' in type_) or (type_ == []) or (mis.question_form in type_):
                if ('total' in theme_) or (theme_ == []):
                    tag_flag = 1
                else:
                    for t in theme_:
                        if t in mis.tags:
                            tag_flag = 1
                if tag_flag == 1:
                    if kw == "":
                        kw_flag = 1
                    else:
                        if (kw in mis.name) or (kw in mis.user.name) or (kw in mis.tags):
                            kw_flag = 1
                        for qs in mis.father_mission.all():
                            if kw in qs.word:
                                kw_flag = 1
                    if kw_flag == 1:
                        mission_list.append(mis)

        show_num = 12  # 设计一次更新获得的任务数
        get_num = min(num + show_num, len(mission_list))  # 本次更新获得的任务数

        return gen_response(201, {'ret': get_num,
                                  'total': len(mission_list),
                                  "question_list":
                                      [
                                          {
                                              'id': ret.id,
                                              'name': ret.name,
                                              'user': ret.user.name,
                                              'questionNum': ret.question_num,
                                              'questionForm': ret.question_form,
                                              'is_banned': ret.is_banned,
                                              'full': ret.to_ans,
                                              'total_ans': ret.total,
                                              'ans_num': ret.now_num,
                                              'deadline': '',
                                              'cash': '',
                                              'tags': ret.tags.split(",")
                                          }
                                          for ret in mission_list[num: get_num]
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
# mission_id, [{ans}]
# mission_id为当前任务的id，表示目前用户回答的任务的id，ans为用户的答案，目前仅支持判断题

def mission_show(request):
    if request.method == 'GET':

        # 安全性验证
        # TODO

        code, data = check_token(request)
        if code == 400:
            return gen_response(code, data)

        if check_is_banned(request):
            return gen_response(400, 'User is Banned')

        id_ = request.GET.get('id')
        num_ = request.GET.get('num')
        step_ = request.GET.get('step')

        if not id_.isdigit() or not num_.isdigit() or not step_.isdigit():
            return gen_response(400, "Not Digit Error")
        mission_id = int(id_)
        num = int(num_)
        step = int(step_)
        if mission_id <= 0 or mission_id > len(Mission.objects.all()):
            return gen_response(400, "ID Error")
        if num < 0 or num >= len(Mission.objects.get(id=mission_id).father_mission.all()):
            return gen_response(400, "Num Error")
        if step != -1 and step != 1 and step != 0:
            return gen_response(400, "Step Error")
        if Mission.objects.get(id=mission_id).is_banned == 1:
            return gen_response(400, "This Mission Is Banned")

        get_num = num + step
        if get_num < 0 or get_num >= len(Mission.objects.get(id=mission_id).father_mission.all()):
            return gen_response(400, "Runtime Error")

        ret = Mission.objects.get(id=mission_id).father_mission.all().order_by('id')[get_num]

        if Mission.objects.get(id=mission_id).question_form == "judgement":  # 题目型式为判断题的情况
            return gen_response(201, {
                'total': len(Mission.objects.get(id=mission_id).father_mission.all()),
                'ret': get_num,
                'word': ret.word,
            })

        # 题目为选择题型式之后实现
        # TODO

        return gen_response(400, "Change Question Error")

    elif request.method == 'POST':

        # 安全性验证
        # TODO

        code, data = check_token(request)
        if code == 400:
            return gen_response(code, data)

        if check_is_banned(request):
            return gen_response(400, 'User is Banned')

        try:
            message = request.body
            js = json.loads(message)
        except json.decoder.JSONDecodeError:
            return gen_response(400, "Request Json Error")

        mission_id_ = js['mission_id'] if 'mission_id' in js else '-1'
        ans_list = js['ans'] if 'ans' in js else []

        if not mission_id_.isdigit() or not isinstance(ans_list, list):
            return gen_response(400, "Not Digit Or Not List Error")

        mission_id = int(mission_id_)
        if mission_id <= 0 or mission_id > len(Mission.objects.all()):
            return gen_response(400, "Mission ID Error")

        user = find_user_by_token(request)
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
                    now_question.save()
                mission.now_num += 1
                if mission.now_num >= mission.total:
                    mission.to_ans = 0
                mission.save()
            else:
                user.weight -= 10
                user.score -= len(ans_list)
            if user.weight <= 0:
                user.is_banned = 1
            user.save()

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

        code, data = check_token(request)
        if code == 400:
            return gen_response(code, data)

        user = find_user_by_token(request)
        if user.is_banned:
            return gen_response(400, 'User is Banned')
        if user.power < 1:
            return gen_response(400, "Lack of Permission")

        file = request.FILES.get('zip')
        question_list = []
        if file is not None:
            # upload a zip file
            try:
                file = ZipFile(file, mode='r')
                basic = file.open('basic.json', mode='r')
                js = json.load(basic)
                basic.close()
            except BadZipFile:
                return gen_response(400, 'Zip File Error (Not Zip File)')
            except KeyError:
                return gen_response(400, 'Zip File Error (basic.json Not Found)')
            except json.JSONDecodeError:
                return gen_response(400, 'Zip File Error (basic.json Json Error)')
            if 'question_path' not in js:
                return gen_response(400, 'Zip File Error (Question Path Not Found)')
            path = js['question_path']
            try:
                q_list = file.open(path, mode='r')
            except KeyError:
                return gen_response(400, 'Zip File Error (Question Path Invalid)')
            for line in q_list.readlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    question_list.append(json.loads(line))
                except json.JSONDecodeError:
                    return gen_response(400, 'Zip File Error (questions.json Json Error)')
            q_list.close()
            file.close()
        # normal POST
        else:
            try:
                js = json.loads(request.body)
            except json.decoder.JSONDecodeError:
                return gen_response(400, "Request Json Error")

        name = js['name'] if 'name' in js else ''
        question_form = js['question_form'] if 'question_form' in js else ''
        question_num_ = js['question_num'] if 'question_num' in js else ''
        total_ = js['total'] if 'total' in js else ''
        tags = js['mission_tags'] if 'mission_tags' in js else ''
        if not question_num_.isdigit() or name == '' or question_form == '' or not total_.isdigit():
            return gen_response(400, "Upload Contains Error")
        question_num = int(question_num_)
        total = int(total_)

        try:
            mission = Mission(name=name, question_form=question_form, question_num=question_num, total=total,
                              user=user, tags=tags)
            mission.full_clean()
            mission.save()
        except ValidationError:
            return gen_response(400, "Upload Form Error")

        if file is None and 'question_list' in js:
            question_list = js['question_list']
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

        code, data = check_token(request)
        if code == 400:
            return gen_response(code, data)

        method = request.GET.get('method') if 'method' in request.GET else ''

        ret = find_user_by_token(request)
        if ret.is_banned:
            return gen_response(400, 'User is Banned')

        if method == 'user':
            return gen_response(201, {
                'name': ret.name,
                'score': ret.score,
                'weight': ret.weight,
                'num': ret.fin_num,
                'tags': ret.tags.split(",")
            })
        elif method == 'mission':
            if ret.power < 1:
                return gen_response(400, "Lack of Permission")
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
                            'ret_time': int(mission_ret.pub_time.timestamp() * 1000)
                        }
                        for mission_ret in ret.history.all().order_by('pub_time')
                    ]
            })
        else:
            return gen_response(400, "Method Is Illegal")
    return gen_response(400, "About Me Error")


def show_my_mission(request):
    if request.method == 'GET':

        code, data = check_token(request)
        if code == 400:
            return gen_response(code, data)
        user_id = request.session['user_id']

        user = Users.objects.get(id=user_id)
        if user.is_banned:
            return gen_response(400, 'User is Banned')
        if user.power < 1:
            return gen_response(400, 'Lack of Permission')

        mission_id_ = request.GET.get('mission_id') if 'mission_id' in request.GET else '1'

        if not mission_id_.isdigit():
            return gen_response(400, "Mission_ID is not digit")
        mission_id = int(mission_id_)

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
                'is_banned': mission.is_banned,
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


# 权限升级
def power_upgrade(request):
    if request.method == 'POST':

        code, data = check_token(request)
        if code == 400:
            return gen_response(code, data)

        user_id = request.session['user_id']

        if user_id < 1 or user_id > len(Users.objects.all()):
            return gen_response(400, "User_ID Error")

        # 目前仅限获取发题权限，无法进一步上升为管理员
        if Users.objects.get(id=user_id).power == 2:
            return gen_response(400, "Are You Kidding Me?")
        obj = Users.objects.get(id=user_id)
        obj.power = 1
        obj.save()
        return gen_response(201, "Upgrade Success")

    return gen_response(400, "Upgrade Failed")


# 封禁用户
def power_use(request):
    if request.method == 'POST':

        code, data = check_token(request)
        if code == 400:
            return gen_response(code, data)

        user_id = request.session['user_id']
        if Users.objects.get(id=user_id).power != 2:
            return gen_response(400, "Dont Have Power")

        try:
            js = json.loads(request.body)
        except json.decoder.JSONDecodeError:
            return gen_response(400, "Json Error")

        id_ = js['id'] if 'id' in js else '*'
        method = js['method'] if 'method' in js else 'null'
        if not id_.isdigit():
            return gen_response(400, "ID Error")
        power_id = int(id_)
        if method == 'null':
            return gen_response(400, "No Method")

        if method == 'user_ban':
            if power_id < 1 or power_id > len(Users.objects.all()):
                return gen_response(400, "Ban User ID Error")
            if Users.objects.get(id=power_id).power != 2:
                obj = Users.objects.get(id=power_id)
                obj.is_banned = 1
                obj.save()
                return gen_response(201, "Ban User Success")
        elif method == 'mission_ban':
            if power_id < 1 or power_id > len(Mission.objects.all()):
                return gen_response(400, "Ban Mission ID Error")
            obj = Mission.objects.get(id=power_id)
            obj.is_banned = 1
            obj.save()
            return gen_response(201, "Ban Mission Success")
        elif method == 'user_free':
            if power_id < 1 or power_id > len(Users.objects.all()):
                return gen_response(400, "Free User ID Error")
            obj = Users.objects.get(id=power_id)
            obj.is_banned = 0
            obj.save()
            return gen_response(201, "Free User Success")
        elif method == 'mission_free':
            if power_id < 1 or power_id > len(Mission.objects.all()):
                return gen_response(400, "Free Mission ID Error")
            obj = Mission.objects.get(id=power_id)
            obj.is_banned = 0
            obj.save()
            return gen_response(201, "Free Mission Success")

    return gen_response(400, "Ban_User Failed")


# 向管理员展示所有用户
def power_user_show_user(request):
    if request.method == 'GET':

        code, data = check_token(request)
        if code == 400:
            return gen_response(code, data)

        user_id = request.session['user_id']
        if Users.objects.get(id=user_id).power != 2:
            return gen_response(400, "Dont Have Power")

        now_num_ = request.GET.get('now_num') if 'now_num' in request.GET else '0'
        if not now_num_.isdigit():
            return gen_response(400, "Now_Num Is Not Digit")
        now_num = int(now_num_)
        total = len(Users.objects.filter(Q(power=0) | Q(power=1)))
        if now_num < 0 or now_num >= total:
            return gen_response(400, "Now_Num Error")

        num = min(len(Users.objects.filter(Q(power=0) | Q(power=1))), now_num+20)

        return gen_response(201, {'num': num-now_num,
                                  'total': total,
                                  'user_list': [{
                                      'id': ret.id,
                                      'name': ret.name,
                                      'power': ret.power,
                                      'is_banned': ret.is_banned,
                                      'score': ret.score,
                                      'weight': ret.weight,
                                      'fin_num': ret.fin_num,
                                  } for ret in Users.objects.filter(Q(power=0) | Q(power=1))[now_num: num]
                                  ]})

    return gen_response(400, "Show All Users Failed")
