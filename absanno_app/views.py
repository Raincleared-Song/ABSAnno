from django.http import JsonResponse, HttpResponse, FileResponse
import json
from .models import Users, Mission, Question, History, Apply, Reception
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.middleware.csrf import get_token
from zipfile import ZipFile, BadZipFile
from django.utils import timezone
import datetime
import random
from .groundPic import generate_pic

from django.core.files.base import File
from io import BytesIO
import os

from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_job


def hello_world(request):
    return HttpResponse("Hello Absanno!")


def int_to_abc(a: int):
    return chr(a + ord('A'))


def abc_to_int(c: str):
    return ord(c) - ord('A')


def get_lst(ans: str):
    raw_ret = ans.split('||')
    ret = []
    for r in raw_ret:
        if r != '':
            ret.append(r)
    return ret


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

        num_ = request.GET.get('num')
        type__ = request.GET.get('type') if 'type' in request.GET else ""
        theme__ = request.GET.get('theme') if 'theme' in request.GET else ""
        kw = request.GET.get('kw') if 'kw' in request.GET else ""

        if not num_:
            num_ = "0"
        if type__ != "":
            type_ = get_lst(type__)
        else:
            type_ = []
        if theme__ != "":
            theme_ = get_lst(theme__)
        else:
            theme_ = []

        if not num_.isdigit():
            return gen_response(400, "Num Is Not Digit")
        num = int(num_)
        if num < 0 or num >= len(Mission.objects.filter(to_ans=1)):
            return gen_response(400, "Num Error in Square")

        # 参考id获取用户画像，进而实现分发算法，目前使用id来进行排序
        # TODO

        user = Users.objects.filter(id=user_id).first()

        receive_set = None
        if user:
            mission_list_temp = Mission.objects.filter(Q(to_ans=1) & Q(is_banned=0)).order_by('-id')
            mission_list_base = []
            for mission in mission_list_temp:
                # 做过的和已经接完的单不显示
                if user.history.filter(mission__id=mission.id).first() is None \
                        and mission.reception_num < mission.total:
                    mission_list_base.append(mission)
            rec_list = user.user_reception.all()
            receive_set = set([r.mission.id for r in rec_list])
        else:
            mission_list_base = Mission.objects.filter(Q(is_banned=0) & Q(to_ans=1)).order_by('-id')

        def get_mission_rec_status(m):
            if receive_set is None:
                return ''
            else:
                return 'T' if m.id in receive_set else 'F'

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
                    if kw_flag == 1 and (mis.reception_num < mis.total) and (mis.deadline > timezone.now()):
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
                                              'deadline': int(ret.deadline.timestamp() * 1000),
                                              'cash': ret.reward,
                                              'info': ret.info,
                                              'tags': get_lst(ret.tags),
                                              'received': get_mission_rec_status(ret),
                                              'image_url': ret.mission_image_url()
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
            return gen_response(400, "Num Error in Mission Show")
        if step != -1 and step != 1 and step != 0:
            return gen_response(400, "Step Error")
        mission = Mission.objects.get(id=mission_id)
        if mission.is_banned == 1:
            return gen_response(400, "This Mission Is Banned")

        user = find_user_by_token(request)
        rec = Reception.objects.filter(user__id=user.id, mission__id=mission_id).first()
        if rec is None:
            return gen_response(400, 'Have Not Received Yet')
        if not rec.can_do:
            return gen_response(400, 'Cannot Do Reception')

        get_num = num + step
        if get_num < 0 or get_num >= len(mission.father_mission.all()):
            return gen_response(400, "Runtime Error")
        if mission.deadline <= timezone.now():
            return gen_response(400, "After The Deadline")

        ret = mission.father_mission.all().order_by('id')[get_num]

        return gen_response(201, {
            'total': len(mission.father_mission.all()),
            'type': mission.question_form,
            'ret': get_num,
            'word': ret.word,
            'choices': ret.choices,
            'image_url': ret.picture_url() if mission.question_form.endswith('-image') else ""
        })

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
        ans = js['ans'] if 'ans' in js else ''

        if not mission_id_.isdigit():
            return gen_response(400, "Not Digit Or Not List Error")

        mission_id = int(mission_id_)
        if mission_id <= 0 or mission_id > len(Mission.objects.all()):
            return gen_response(400, "Mission ID Error")

        user = find_user_by_token(request)
        mission = Mission.objects.get(id=mission_id)

        rec = Reception.objects.filter(user__id=user.id, mission__id=mission_id).first()
        if rec is None:
            return gen_response(400, 'Have Not Received Yet')
        if not rec.can_do:
            return gen_response(400, 'Cannot Do Reception')

        flag = 1
        tot, g = 0, 0

        if mission.question_form.startswith('chosen'):
            ans_list = get_lst(ans)
            q_list = mission.father_mission.all()
            if len(ans_list) != len(q_list):
                return gen_response(400, 'Answer List Length Error')
            for i in range(len(ans_list)):
                if q_list[i].pre_ans != '':
                    tot += 1
                    if q_list[i].pre_ans == ans_list[i]:
                        g += 1
            if tot != 0 and (g * 100 / tot < 60):
                flag = 0
            # 基于做题时间的反作弊
            if timezone.now() - rec.pub_time < datetime.timedelta(seconds=mission.question_num):
                flag = 0
            if flag == 1:
                user.weight += 5
                if user.weight > 100:
                    user.weight = 100
                user.coin += mission.reward
                user.fin_num += 1
                user.save()
                mission.now_num += 1
                if mission.now_num == mission.total:
                    mission.to_ans = 0
                mission.save()
                rec.can_do = False  # 接单不可做
                rec.save()
                history = History(user=user, mission=mission, ans=ans, ans_weight=user.weight)
                history.save()
                return gen_response(201, "Answer Pushed")
            else:
                user.weight -= 5
                if user.weight < 0:
                    user.weight = 0
                    user.is_banned = 1
                user.save()
                return gen_response(201, "Did Not Pass The Test")

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

        file = request.FILES.get('zip', None)
        image_list = request.FILES.getlist('img_list', None)
        img_bg = request.FILES.get('mission_image', None)
        question_list = []
        has_bg = False
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

            name = js['name'] if 'name' in js else ''
            question_form = js['question_form'] if 'question_form' in js else ''
            question_num_ = js['question_num'] if 'question_num' in js else ''
            if not question_num_.isdigit() or question_form == '' or name == '':
                return gen_response(400, "Upload Contains Error")
            question_num = int(question_num_)
            if 'question_list' in js:
                question_list = js['question_list']
            if not isinstance(question_list, list):
                return gen_response(400, "Question_list Is Not A List")
            if len(question_list) != question_num:
                return gen_response(400, "Question_list Length Error")

            image_path = js['mission_image_path'] if 'mission_image_path' in js else ''
            if len(image_path) > 0:
                has_bg = True
                bg_img = file.open(image_path)
                save_img = open(os.path.join('image', '_mission_bg', name + '_bg.png'), 'wb')
                save_img.write(bg_img.read())
                bg_img.close()
                save_img.close()

            if question_form.endswith('-image'):
                # 上传的是图片题
                image_path = js['image_path'] if 'image_path' in js else ''
                if image_path == '':
                    return gen_response(400, "Upload Contains Error")
                image_list = []
                for question in question_list:
                    if 'image_name' not in question:
                        return gen_response(400, 'Question Image Unspecified')
                    image_name = question['image_name']
                    image_file_path = '/'.join((image_path, image_name))
                    try:
                        image_file = file.open(image_file_path)
                        image_list.append(image_file)
                    except KeyError:
                        return gen_response(400, 'File %s Do Not Exist' % image_file_path)

        # image post
        elif (image_list is not None and len(image_list) > 0) or img_bg is not None:
            try:
                js = json.loads(request.POST.get('info'))
            except json.JSONDecodeError:
                return gen_response(400, "Request Json Error")
            name = js['name'] if 'name' in js else ''
            question_num_ = js['question_num'] if 'question_num' in js else ''
            if not question_num_.isdigit() or name == '':
                return gen_response(400, "Upload Contains Error")
            question_num = int(question_num_)
            if image_list is not None and 0 < len(image_list) != question_num:
                return gen_response(400, "ImageList Length Error")
            if img_bg is not None:
                has_bg = True
                save_img = open(os.path.join('image', '_mission_bg', name + '_bg.png'), 'wb')
                save_img.write(img_bg.read())
                img_bg.close()
                save_img.close()

        # normal POST
        else:
            try:
                js = json.loads(request.body)
            except json.JSONDecodeError:
                return gen_response(400, "Request Json Error")

        name = js['name'] if 'name' in js else ''
        question_form = js['question_form'] if 'question_form' in js else ''
        question_num_ = js['question_num'] if 'question_num' in js else ''
        total_ = js['total'] if 'total' in js else ''
        reward_ = js['reward'] if 'reward' in js else '100'
        deadline_ = js['deadline'] if 'deadline' in js else '2022-6-30'
        retrieve_time_ = js['retrieve_time'] if 'retrieve_time' in js else ''
        check_way = js['check_way'] if 'check_way' in js else 'auto'
        info = js['info'] if 'info' in js else ''

        if 'mission_tags' not in js:
            tags_ = []
        else:
            tags_ = js['mission_tags']
            if isinstance(tags_, str):
                tags_ = get_lst(tags_)

        spl_str = '||'
        tags = spl_str.join(tags_)
        tags = tags.lower()
        if not question_num_.isdigit() or name == '' or question_form == '' or \
                not total_.isdigit() or not reward_.isdigit() or not retrieve_time_.isdigit():
            return gen_response(400, "Upload Contains Error")
        question_num = int(question_num_)
        total = int(total_)
        reward = int(reward_)
        d_list = deadline_.split('-')
        y, m, d = int(d_list[0]), int(d_list[1]), int(d_list[2])
        deadline = datetime.date(y, m, d)
        retrieve_time = int(retrieve_time_)

        if file is None and 'question_list' in js:
            question_list = js['question_list']
        if not isinstance(question_list, list):
            return gen_response(400, "Question_list Is Not A List")
        if len(question_list) != question_num:
            return gen_response(400, "Question_list Length Error")

        if len(Mission.objects.filter(name=name)) > 0:
            return gen_response(400, 'Mission Name Already Used')

        path_base = 'image/_mission_bg' if has_bg else 'pics'
        image_base = f'{name}_bg.png' if has_bg else f'{random.randint(1, 7)}.jpg'
        generate_pic(path_base, image_base, name, question_num, reward, deadline.strftime('%Y-%m-%d'))

        def clean_image_when_fail():
            if os.path.exists(os.path.join('image', '_mission_bg', name + '_bg.png')):
                os.remove(os.path.join('image', '_mission_bg', name + '_bg.png'))
            if os.path.exists(os.path.join('image', '_mission_bg', name + '.png')):
                os.remove(os.path.join('image', '_mission_bg', name + '.png'))

        try:
            mission = Mission(name=name, question_form=question_form, question_num=question_num, total=total,
                              user=user, tags=tags, reward=reward, check_way=check_way,
                              info=info, deadline=deadline, retrieve_time=retrieve_time)
            mission.full_clean()
            mission.save()
        except ValidationError:
            clean_image_when_fail()
            return gen_response(400, "Upload Form Error")

        for k, i in enumerate(question_list):
            contains = i['contains'] if 'contains' in i else ''
            ans = i['ans'] if 'ans' in i else ''
            choices = i['choices'] if 'choices' in i else ''
            if contains == '':
                clean_image_when_fail()
                return gen_response(400, "Question Contains is Null")
            if choices == '':
                clean_image_when_fail()
                return gen_response(400, "There Is No Choice")
            try:
                question = Question(word=contains, mission=mission, choices=choices, pre_ans=ans)
                if question_form.endswith('-image'):
                    if image_list is None or len(image_list) == 0:
                        return gen_response(400, 'Images Expected')
                    image_file = image_list[k]
                    file_name = image_file.name.split('/').pop()
                    question.picture.save(file_name, File(BytesIO(image_file.read())))
                    image_file.close()
                question.full_clean()
                question.save()
            except ValidationError:
                clean_image_when_fail()
                return gen_response(400, "Question Form Error")

        if file is not None:
            file.close()

        cost = reward * total
        if user.coin < cost:
            clean_image_when_fail()
            return gen_response(400, "You Dont Have Enough Coin")
        user.coin -= cost
        user.save()

        return gen_response(201, "Chosen Upload Success")

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
                'coin': ret.coin,
                'weight': ret.weight,
                'num': ret.fin_num,
                'tags': get_lst(ret.tags),
                'power': ret.power
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
                            'question_form': mission_ret.question_form,
                            'to_ans': mission_ret.to_ans,
                            'reward': mission_ret.reward,
                            'deadline': int(mission_ret.deadline.timestamp() * 1000),
                            'info': mission_ret.info,
                            'check_way': mission_ret.check_way,
                            'is_banned': mission_ret.is_banned
                        }
                        for mission_ret in ret.promulgator.all().order_by('-id')
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
                            'reward': mission_ret.mission.reward,
                            'info': mission_ret.mission.info,
                            'ret_time': int(mission_ret.pub_time.timestamp() * 1000)
                        }
                        for mission_ret in ret.history.all().order_by('-pub_time')
                    ]
            })
        elif method == 'apply':
            return gen_response(201, {
                'total_num': len(ret.user_apply.all()),
                'apply_list':
                    [
                        {
                            'type': apply_ret.type,
                            'pub_time': int(apply_ret.pub_time.timestamp() * 1000),
                            'accept': apply_ret.accept
                        }
                        for apply_ret in ret.user_apply.all().order_by('pub_time')
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

        return integrate_mission(mission)

    return gen_response(400, "My Mission Error")


def integrate_mission(mission):
    # 选择题模式
    if mission.question_form.startswith('chosen'):

        question_list = mission.father_mission.all()
        history_list = mission.ans_history.all()
        if len(history_list) == 0:
            return gen_response(400, 'No Answer History Yet')

        for i in range(len(question_list)):
            weight_list = []
            ans, tot_weight = 0, 0
            q = question_list[i]
            c_lst = get_lst(q.choices)
            c_num = len(c_lst)
            for j in range(c_num):
                weight_list.append(0)
            for his in history_list:
                a_lst = get_lst(his.ans)
                weight_list[abc_to_int(a_lst[i])] += his.ans_weight
                tot_weight += his.ans_weight
            for j in range(c_num):
                if weight_list[j] > weight_list[ans]:
                    ans = j
            q.ans = int_to_abc(ans)
            q.ans_weight = weight_list[ans] / tot_weight
            q.save()

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
                        'pre_ans': ret.pre_ans,
                        'ans': ret.ans,
                        'ans_weight': ret.ans_weight,
                    }
                    for ret in mission.father_mission.all()
                ]
        })
    return gen_response(400, "My Mission Error")


# 申请
def send_apply(request):
    if request.method == 'POST':

        code, data = check_token(request)
        if code == 400:
            return gen_response(code, data)

        user_id = request.session['user_id']
        user = Users.objects.get(id=user_id)

        try:
            js = json.loads(request.body)
        except json.decoder.JSONDecodeError:
            return gen_response(400, "Json Error")

        type_ = js['type'] if 'type' in js else ''
        if type_ == '':
            return gen_response(400, "No Type Send")

        try:
            apply = Apply(user=user, type=type_)
            apply.full_clean()
            apply.save()
        except ValidationError:
            return gen_response(400, "Apply Form Error")

        return gen_response(201, "Send Success")

    return gen_response(400, "Send Failed")


# 接单与取消接单
def book_cancel_mission(request):
    if request.method == 'POST':

        code, data = check_token(request)
        if code == 400:
            return gen_response(code, data)

        user_id = request.session['user_id']

        try:
            js = json.loads(request.body)
        except json.decoder.JSONDecodeError:
            return gen_response(400, "Json Error")

        mission_id_ = js['mission_id'] if 'mission_id' in js else '0'
        if not mission_id_.isdigit():
            return gen_response(400, "Mission ID Is Not Digit")
        mission_id = int(mission_id_)

        if mission_id < 1 or mission_id > len(Mission.objects.all()):
            return gen_response(400, "Mission ID Error")
        if user_id < 1 or user_id > len(Users.objects.all()):
            return gen_response(400, "User ID Error")
        user = Users.objects.get(id=user_id)
        mission = Mission.objects.get(id=mission_id)

        reception = Reception.objects.filter(user__id=user_id, mission__id=mission_id).first()
        if reception is None:
            # 接单
            mission.reception_num += 1
            mission.save()

            try:
                rep = Reception(user=user, mission=mission)
                rep.deadline = timezone.now() + datetime.timedelta(hours=mission.retrieve_time)
                rep.full_clean()
                rep.save()
            except ValidationError:
                return gen_response(400, "Form Error")
            return gen_response(201, "Book Success")
        else:
            # 取消接单
            if mission.reception_num == 0:
                return gen_response(400, 'No Reception Yet')
            mission.reception_num -= 1
            mission.save()
            reception.delete()
            return gen_response(201, "Cancel Book Success")

    return gen_response(400, "Book Failed")


# 展示申请，对管理员
def apply_show(request):
    if request.method == 'GET':

        code, data = check_token(request)
        if code == 400:
            return gen_response(code, data)

        user_id = request.session['user_id']
        if user_id < 1 or user_id > len(Users.objects.all()):
            return gen_response(400, "User ID Error")
        user = Users.objects.get(id=user_id)

        if user.power == 2:
            apply_list = Apply.objects.filter(accept=0).order_by('pub_time')
        else:
            apply_list = Apply.objects.filter(user=user).order_by('pub_time')

        return gen_response(201, {
            'apply_num': len(apply_list),
            'apply_list':
            [
                {
                    'id': ret.user.id,
                    'app_id': ret.id,
                    'user_name': ret.user.name,
                    'pub_time': int(ret.pub_time.timestamp() * 1000),
                    'type': ret.type,
                    'accept': ret.accept,
                    'user_weight': ret.user.weight,
                    'user_coin': ret.user.coin,
                    'user_fin_num': ret.user.fin_num
                }
                for ret in apply_list
            ]
        })

    return gen_response(400, "Apply Show Failed")


# # 操作apply
# @Deprecated
def admin_apply(request):
    pass
#     if request.method == 'POST':
#
#         code, data = check_token(request)
#         if code == 400:
#             return gen_response(code, data)
#
#         try:
#             js = json.loads(request.body)
#         except json.decoder.JSONDecodeError:
#             return gen_response(400, "Json Error")
#
#         method = js['method'] if 'method' in js else ''
#         apply_id_ = js['apply_id'] if 'apply_id' in js else '0'
#
#         if not apply_id_.isdigit():
#             return gen_response(400, "Apply ID Is Not Digit")
#
#         apply_id = int(apply_id_)
#         if apply_id < 1 or apply_id > len(Apply.objects.all()):
#             return gen_response(400, "Apply ID Error")
#         apply = Apply.objects.get(id=apply_id)
#
#         user_id = request.session['user_id']
#         if user_id < 1 or user_id > len(Users.objects.all()):
#             return gen_response(400, "User ID Error")
#         user = Users.objects.get(id=user_id)
#         if user.power != 2:
#             return gen_response(400, "Dont Have Power")
#
#         if method == 'Accept':
#             apply.accept = 1
#         else:
#             apply.accept = 2
#         apply.save()
#         return gen_response(400, "Admin Success")
#
#     return gen_response(400, "Admin Error")


# 展示我的接单内容
def rep_show(request):
    if request.method == 'GET':

        code, data = check_token(request)
        if code == 400:
            return gen_response(code, data)

        user_id = request.session['user_id']
        if user_id < 1 or user_id > len(Users.objects.all()):
            return gen_response(400, "User ID Error")
        user = Users.objects.get(id=user_id)

        rep_list = Reception.objects.filter(Q(user=user) & Q(can_do=True)).order_by('pub_time')

        return gen_response(201, {
            'total_num': len(rep_list),
            'user_name': user.name,
            'rep_list':
                [
                    {
                        'pub_time': int(ret.pub_time.timestamp() * 1000),
                        'deadline': int(ret.deadline.timestamp() * 1000),
                        'mission_id': ret.mission.id,
                        'mission_name': ret.mission.name,
                        'mission_info': ret.mission.info,
                        'mission_deadline': int(ret.mission.deadline.timestamp() * 1000),
                        'mission_reward': ret.mission.reward,
                        'mission_tag': get_lst(ret.mission.tags),
                        'question_form': ret.mission.question_form,
                        'question_num': ret.mission.question_num
                    }
                    for ret in rep_list
                ]
        })

    return gen_response(400, "Rep Show Failed")


# 权限升级管理员审批
def power_upgrade(request):
    if request.method == 'POST':

        code, data = check_token(request)
        if code == 400:
            return gen_response(code, data)

        now_id = request.session['user_id']
        if Users.objects.get(id=now_id).power < 2:
            return gen_response(400, "You Dont Have Power")

        try:
            js = json.loads(request.body)
        except json.decoder.JSONDecodeError:
            return gen_response(400, "Json Error")

        user_id_ = js['p_id'] if 'p_id' in js else '0'
        if not user_id_.isdigit():
            return gen_response(400, "UserID Error")
        user_id = int(user_id_)

        if user_id < 1 or user_id > len(Users.objects.all()):
            return gen_response(400, "User_ID Error")

        method_ = js['method'] if 'method' in js else 'Reject'

        # 目前仅限获取发题权限，无法进一步上升为管理员
        if Users.objects.get(id=user_id).power == 2:
            return gen_response(400, "Are You Kidding Me?")
        obj = Users.objects.get(id=user_id)

        if Users.objects.get(id=user_id).power == 1:
            return gen_response(400, "You are already publisher!")

        if method_.lower() == "accept":
            obj.power = 1
            obj.save()
            apply = Apply.objects.filter(user=obj)

            for app in apply:
                app.accept = 1
                app.save()
            return gen_response(201, "Upgrade Success")
        else:
            apply = Apply.objects.filter(user=obj)
            for app in apply:
                app.accept = 2
                app.save()
            return gen_response(201, "Upgrade Rejected")

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

        num = min(len(Users.objects.filter(Q(power=0) | Q(power=1))), now_num + 20)

        return gen_response(201, {'num': num - now_num,
                                  'total': total,
                                  'user_list': [{
                                      'id': ret.id,
                                      'name': ret.name,
                                      'power': ret.power,
                                      'is_banned': ret.is_banned,
                                      'coin': ret.coin,
                                      'weight': ret.weight,
                                      'fin_num': ret.fin_num,
                                      'tags': get_lst(ret.tags)
                                  } for ret in Users.objects.filter(Q(power=0) | Q(power=1))[now_num: num]
                                  ]})

    return gen_response(400, "Show All Users Failed")


def get_answer_dict(mission: Mission) -> dict:
    """获取指定任务的导出答案列表"""
    res = {'name': mission.name, 'form': mission.question_form, 'question_num': mission.question_num,
           'total': mission.total, 'now_num': mission.now_num,
           'word': [], 'pre_ans': [], 'ans': [], 'weight': []}
    response = integrate_mission(mission)
    if response.status_code == 400:
        return json.loads(response.content)
    for question in mission.father_mission.all():
        res['word'].append(question.word)
        res['pre_ans'].append(question.pre_ans)
        res['ans'].append(question.ans)
        res['weight'].append(question.ans_weight)
    return res


def download(request):
    """需求方导出结果文件"""
    code, data = check_token(request)
    if code == 400:
        return gen_response(code, data)

    user_id = request.session['user_id']
    if Users.objects.get(id=user_id).power < 1:
        return gen_response(400, "Dont Have Power")

    mission_id_ = request.GET.get('mission_id') if 'mission_id' in request.GET else ''

    if not mission_id_.isdigit():
        return gen_response(400, 'Mission ID Is Not Digit')

    mission_id = int(mission_id_)

    if mission_id <= 0 or mission_id > len(Mission.objects.all()):
        return gen_response(400, 'Mission ID Illegal')

    mission = Mission.objects.get(id=mission_id)

    if mission.user.id != user_id:
        return gen_response(400, 'User ID Is Wrong')

    if not os.path.exists('cache'):
        os.mkdir('cache')
    else:  # 文件数过多时清楚缓存
        file_list = os.listdir('cache')
        if len(file_list) > 20:
            file_list.sort(key=lambda x: os.path.getmtime('cache/' + x))
            os.remove('cache/' + file_list[0])

    file_name = 'result-%d.json' % mission_id
    file = open('cache/' + file_name, 'w')
    ans_dict = get_answer_dict(mission)
    if 'name' not in ans_dict:
        return gen_response(400, ans_dict['data'])
    json.dump(get_answer_dict(mission), file)
    file.close()
    file = open('cache/' + file_name, 'rb')
    response = FileResponse(file, status=201)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="%s"' % file_name
    return response


# 验收内容，GET
def check_result(request):
    if request.method == "GET":
        code, data = check_token(request)
        if code == 400:
            return gen_response(400, data)

        user_id = request.session['user_id']
        if Users.objects.get(id=user_id).power < 1:
            return gen_response(400, "Dont Have Power")

        mission_id = request.GET.get("mission_id") if 'mission_id' in request.GET else '0'
        if not mission_id.isdigit():
            return gen_response(400, "mission_id Is Not Digit")

        mission_id = int(mission_id)
        if user_id < 1 or user_id > len(Users.objects.all()):
            return gen_response(400, "User ID Error")
        if mission_id < 1 or mission_id > len(Mission.objects.all()):
            return gen_response(400, "Mission ID Error")

        mission = Mission.objects.get(id=mission_id)
        # print(mission.user.id, user_id)
        if mission.user.id != user_id:
            return gen_response(400, "Mission Not Published by You")

        if mission.question_form.endswith("chosen"):

            for i in range(len(mission.father_mission.all())):
                weight_list = []
                ans, tot_weight = 0, 0
                q = mission.father_mission.all()[i]
                c_lst = get_lst(q.choices)
                c_num = len(c_lst)
                for j in range(c_num):
                    weight_list.append(0)
                for his in mission.ans_history.all():
                    a_lst = get_lst(his.ans)
                    weight_list[abc_to_int(a_lst[i])] += his.ans_weight
                    tot_weight += his.ans_weight
                for j in range(c_num):
                    if weight_list[j] > weight_list[ans]:
                        ans = j
                q.ans = int_to_abc(ans)
                q.ans_weight = weight_list[ans] / tot_weight
                q.save()

            return gen_response(201, {
                'question_list':
                    [
                        {
                            'word': ret.word,
                            'pre_ans': ret.pre_ans,
                            'ans': ret.ans,
                            'ans_weight': ret.ans_weight,
                        }
                        for ret in mission.father_mission.all()
                    ]
            })
        return gen_response(400, "Check Mission Error, Chosen Expected")
    return gen_response(400, "Check Mission Error, Use GET Instead")


def sort_mission_list_by_interest(mission_list, user):
    if not user:
        # print("not login, sort by tag numbers")
        mission_list.sort(key=lambda x: len(x.tags.split('||')))
        return mission_list
    else:
        # print("logged in, sort by same tag numbers")
        user_tag = user.tags.split('||')
        user_tag = [s.lower() for s in user_tag]
        # print(user_tag)
        mission_list.sort(key=lambda x: len(set(user_tag) & set(x.tags.split('||'))), reverse=True)
        # print(mission_list)
        return mission_list


def interests(request):
    if request.method == 'GET':

        # 安全性验证
        # TODO
        user_id = request.session['user_id'] if check_token(request)[0] == 201 else 0

        num_ = request.GET.get('page')

        if not num_:
            num_ = "0"

        if not num_.isdigit():
            return gen_response(400, "Num Is Not Digit")
        num = int(num_)
        if num < 0 or num >= len(Mission.objects.filter(to_ans=1)):
            return gen_response(400, "Num Error in Interest")

        user = Users.objects.filter(id=user_id).first()
        receive_set = None
        if user:
            mission_list_temp = Mission.objects.filter(Q(to_ans=1) & Q(is_banned=0)).order_by('-id')
            mission_list_base = []
            for mission in mission_list_temp:
                if user.history.filter(mission__id=mission.id).first() is None \
                        and mission.reception_num < mission.total:
                    mission_list_base.append(mission)
            rec_list = user.user_reception.all()
            receive_set = set([r.mission.id for r in rec_list])
        else:
            mission_list_base = Mission.objects.filter(Q(is_banned=0) & Q(to_ans=1)).order_by('-id')

        def get_mission_rec_status(m):
            if receive_set is None:
                return ''
            else:
                return 'T' if m.id in receive_set else 'F'

        mission_list = sort_mission_list_by_interest(list(mission_list_base), user)

        show_num = 5  # 设计一次更新获得的任务数
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
                                              'deadline': int(ret.deadline.timestamp() * 1000),
                                              'cash': ret.reward,
                                              'info': ret.info,
                                              'tags': get_lst(ret.tags),
                                              'received': get_mission_rec_status(ret),
                                              'image_url': ret.mission_image_url()
                                          }
                                          for ret in mission_list[num: get_num]
                                      ]}
                            )
    return gen_response(400, "User Show Error")


# def modify_personal_info(request):
#     if request.method == "POST":
#         pass
#     return gen_response(400, "Please Use Post Method")


def end_mission(request):
    if request.method == 'POST':

        code, data = check_token(request)
        if code == 400:
            return gen_response(400, data)

        user_id = request.session['user_id']
        if Users.objects.get(id=user_id).power < 1:
            return gen_response(400, "Dont Have Power")
        if user_id < 1 or user_id > len(Users.objects.all()):
            return gen_response(400, "User ID Error")

        try:
            js = json.loads(request.body)
        except json.JSONDecodeError:
            return gen_response(400, 'Request Json Error')

        mission_id = js["mission_id"] if 'mission_id' in js else '0'
        if not mission_id.isdigit():
            return gen_response(400, "mission_id Is Not Digit")
        mission_id = int(mission_id)
        if mission_id < 1 or mission_id > len(Mission.objects.all()):
            return gen_response(400, "Mission ID Error")

        mission = Mission.objects.get(id=mission_id)
        if mission.user.id != user_id:
            return gen_response(400, "Mission Not Published by You")

        if mission.to_ans == 1:
            invalidate_mission(mission)
        return gen_response(201, 'Mission End Success')

    return gen_response(400, 'End Mission Error')


def invalidate_mission(mission: Mission):
    mission.to_ans = 0
    if mission.now_num < mission.total:
        user = mission.user
        user.coin += mission.reward * (mission.total - mission.now_num)
        user.save()
    for rec in mission.mission_reception.all():
        rec.can_do = False
        rec.save()
    mission.save()


# 用户修改密码
def change_password(request):
    if request.method == "POST":
        code, data = check_token(request)
        if code == 400:
            return gen_response(400, data)

        user_id = request.session['user_id']
        user = Users.objects.get(id=user_id)

        try:
            js = json.loads(request.body)
        except json.decoder.JSONDecodeError:
            return gen_response(400, "Json Error")

        old_password = js['old_password'] if 'old_password' in js else ''
        new_password_1 = js['new_password_1'] if 'new_password_1' in js else ''
        new_password_2 = js['new_password_2'] if 'new_password_2' in js else ''
        if old_password != user.password:
            return gen_response(400, "Old Password Error")
        if new_password_1 == '' or new_password_2 == '':
            return gen_response(400, "Didnt Input New Password")
        if new_password_1 != new_password_2:
            return gen_response(400, "New Password Is Not Equal")
        if len(new_password_1) < 6 or len(new_password_2) > 20:
            return gen_response(400, "Password Length Error")

        user.password = new_password_1
        user.save()

    return gen_response(400, "You Change Your Password Failed")


# 用户修改个人信息
def change_info(request):
    return gen_response(400, "You Change Your Info Failed")


# 开启检查线程
scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore())
try:
    # jobs that should be executed periodically
    @register_job(scheduler, 'interval', hours=1, id='check', replace_existing=True)
    def check_deadline():
        mission_list = Mission.objects.all()
        for mission in mission_list:
            if mission.to_ans == 1 and timezone.now() > mission.deadline:
                invalidate_mission(mission)
        rec_list = Reception.objects.all()
        for rec in rec_list:
            if rec.can_do and timezone.now() > rec.deadline:
                rec.can_do = False
                rec.save()
                rec.mission.reception_num -= 1
                rec.mission.save()  # 接单过期，原任务接单数减一

    scheduler.start()
except Exception as e:
    print(e)
    if scheduler.state > 0:  # is running or paused
        scheduler.shutdown()
