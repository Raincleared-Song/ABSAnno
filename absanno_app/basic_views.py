import datetime
from django.core.exceptions import ValidationError
from django.core.files.base import File
from io import BytesIO
from django.utils import timezone
from absanno_app.models import Users, Apply, Mission, Reception
from absanno_app.utils import parse_json, gen_response, JSON_ERROR, check_token, find_user_by_token, get_lst, \
    json_default, illegal_name, illegal_password, illegal_mission_id


def log_in(request):
    if request.method == 'POST':

        js = parse_json(request.body)
        if js is None:
            return gen_response(400, JSON_ERROR)

        dic = {'name': '', 'password': ''}
        name, password = json_default(js, dic)

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
            'power': user.power,
            'avatar': user.user_avatar_url()
        })

    return gen_response(400, "Log In Error")


# 注册
def sign_in(request):
    if request.method == 'POST':

        js = parse_json(request.body)
        if js is None:
            return gen_response(400, JSON_ERROR)

        dic = {'name': '', 'password': '', 'tags': ''}
        name, password, tags = json_default(js, dic)

        if not name or not password:
            return gen_response(400, "Request Body Error")

        if illegal_name(name):  # 禁止名字中特定字符
            return gen_response(400, "User Name Error")
        if illegal_password(password):
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
            'power': user.power,
            'avatar': user.user_avatar_url()
        })

    return gen_response(400, "Sign In Error")


# 登出
def log_out(request):
    if request.method == 'POST':

        code, data = check_token(request)
        if code == 400:
            return gen_response(201, "Log Out Finish Without Token")

        if request.session['is_login']:
            request.session['is_login'] = False
        request.session.flush()  # remove the token
        return gen_response(201, "Log Out Finish With Token")

    return gen_response(400, "Log Out Error")


# 个人信息界面
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
                'power': ret.power,
                'avatar': ret.user_avatar_url()
            })

        elif method == 'mission':
            if ret.power < 1:
                return gen_response(400, "Lack of Permission")
            return gen_response(201, {
                'total_num': len(ret.promulgator.filter(is_sub=0)),
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
                            'is_banned': mission_ret.is_banned,
                            'to_be_check': mission_ret.to_be_check
                        }
                        for mission_ret in ret.promulgator.filter(is_sub=0).order_by('-id')
                    ]
            })
        elif method == 'history':
            return gen_response(201, {
                'total_num': len(ret.history.all()),
                'mission_list':
                    [
                        {
                            'id': mission_ret.mission.id,
                            'name': mission_ret.mission.name if mission_ret.mission.is_sub == 0
                            else mission_ret.mission.name + '-' + str(mission_ret.mission.is_sub),
                            'user': mission_ret.mission.user.name,
                            'question_num': mission_ret.mission.question_num,
                            'question_form': mission_ret.mission.question_form,
                            'reward': mission_ret.mission.reward,
                            'info': mission_ret.mission.info,
                            'ret_time': int(mission_ret.pub_time.timestamp() * 1000),
                            'state': 2 if mission_ret.mission.to_be_check == 1
                            else (1 if mission_ret.valid else 0)
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
        return gen_response(400, "Method Is Illegal")
    return gen_response(400, "About Me Error")


# 向管理员发送申请
def send_apply(request):
    if request.method == 'POST':

        code, data = check_token(request)
        if code == 400:
            return gen_response(code, data)

        user_id = request.session['user_id']
        user = Users.objects.get(id=user_id)

        js = parse_json(request.body)
        if js is None:
            return gen_response(400, JSON_ERROR)

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

        js = parse_json(request.body)
        if js is None:
            return gen_response(400, JSON_ERROR)

        mission_id_ = js['mission_id'] if 'mission_id' in js else '0'
        if not mission_id_.isdigit():
            mission_id_ = '0'
        mission_id = int(mission_id_)

        if illegal_mission_id(mission_id):
            return gen_response(400, "Mission ID Error")
        user = Users.objects.get(id=user_id)
        mission = Mission.objects.get(id=mission_id)

        reception = Reception.objects.filter(user__id=user_id, mission__id=mission_id).first()
        if reception is None:
            # 接单
            if mission.to_ans == 1:

                if mission.reception_num + mission.now_num + 1 == mission.total:
                    mission.to_ans = 0
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
                return gen_response(400, "Rec Conflict!")

        else:
            # 取消接单
            if mission.reception_num == 0:
                return gen_response(400, 'No Reception Yet')
            mission.reception_num -= 1
            if mission.to_ans == 0:
                mission.to_ans = 1
            mission.save()
            reception.delete()
            return gen_response(201, "Cancel Book Success")

    return gen_response(400, "Book Failed")


def change_password(request):
    if request.method == "POST":
        code, data = check_token(request)
        if code == 400:
            return gen_response(400, data)

        user_id = request.session['user_id']
        user = Users.objects.get(id=user_id)

        js = parse_json(request.body)
        if js is None:
            return gen_response(400, JSON_ERROR)

        dic = {'old_password': '', 'new_password_1': '', 'new_password_2': ''}
        old_password, new_password_1, new_password_2 = json_default(js, dic)

        if old_password != user.password:
            return gen_response(400, "Old Password Error")
        if new_password_1 != new_password_2:
            return gen_response(400, "New Password Is Not Equal")
        if illegal_password(new_password_1):
            return gen_response(400, "Password Length Error")

        user.password = new_password_1
        user.save()
        return gen_response(201, "You successfully changed your password!")

    return gen_response(400, "You Change Your Password Failed")


# 用户修改个人信息：TAG
def change_info(request):
    if request.method == "POST":
        code, data = check_token(request)
        if code == 400:
            return gen_response(400, data)

        js = parse_json(request.body)
        if js is None:
            return gen_response(400, JSON_ERROR)

        user_id = request.session['user_id']
        user = Users.objects.get(id=user_id)

        new_tag_str = js['tags'] if 'tags' in js else ''
        new_tag_str = new_tag_str.replace(' ', '')
        new_tags = new_tag_str.split(',')
        while '' in new_tags:
            new_tags.remove('')

        tag = ''
        for t in new_tags:
            tag += t + '||'
        tag = tag[:-2]
        user.tags = tag
        user.save()

        return gen_response(201, {
            'tags': get_lst(user.tags),
        })

    elif request.method == "GET":
        code, data = check_token(request)
        if code == 400:
            return gen_response(400, data)
        user_id = request.session['user_id']
        user = Users.objects.get(id=user_id)
        tag = ''
        for t in get_lst(user.tags):
            tag += t + ','
        tag = tag[:-1]
        return gen_response(201, {
            'tags': tag
        })

    return gen_response(400, "You Change Your Info Failed")


def change_avatar(request):
    if request.method == "POST":
        code, data = check_token(request)
        if code == 400:
            return gen_response(400, data)

        user_id = request.session['user_id']
        user = Users.objects.get(id=user_id)

        file = request.FILES.get('avatar', None)
        if file is None:
            user.avatar = ""
            user.save()
            return gen_response(201, "Successfully changed avatar (to blank)")

        file_name = file.name.split('/').pop()
        user.avatar.save(file_name, File(BytesIO(file.read())))
        file.close()
        user.save()
        return gen_response(201, "Successfully changed avatar")

    return gen_response(400, "Failed to change Avatar")
