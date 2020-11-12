from django.db.models import Q
from .models import Apply, Users, Message, Mission
from .utils import check_token, gen_response, parse_json, JSON_ERROR, print_msg_error, gen_message, get_lst, \
    MESSAGE_FROM_ADMIN, LACK_POWER_ERROR


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
                        'user_fin_num': ret.user.fin_num,
                        'user_avatar': ret.user.user_avatar_url()
                    }
                    for ret in apply_list
                ]
        })

    return gen_response(400, "Apply Show Failed")


# 权限升级管理员审批
def upgrade_examine(request):
    if request.method == 'POST':

        code, data = check_token(request)
        if code == 400:
            return gen_response(code, data)

        now_id = request.session['user_id']
        if Users.objects.get(id=now_id).power < 2:
            return gen_response(400, LACK_POWER_ERROR)

        js = parse_json(request.body)
        if js is None:
            return gen_response(400, JSON_ERROR)

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
def ban_user(request):
    if request.method == 'POST':

        code, data = check_token(request)
        if code == 400:
            return gen_response(code, data)

        user_id = request.session['user_id']
        if Users.objects.get(id=user_id).power != 2:
            return gen_response(400, LACK_POWER_ERROR)

        js = parse_json(request.body)
        if js is None:
            return gen_response(400, JSON_ERROR)

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
def show_all_user(request):
    if request.method == 'GET':

        code, data = check_token(request)
        if code == 400:
            return gen_response(code, data)

        user_id = request.session['user_id']
        if Users.objects.get(id=user_id).power != 2:
            return gen_response(400, LACK_POWER_ERROR)

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
                                      'tags': get_lst(ret.tags),
                                      'avatar': ret.user_avatar_url()
                                  } for ret in Users.objects.filter(Q(power=0) | Q(power=1))[now_num: num]
                                  ]})

    return gen_response(400, "Show All Users Failed")


def message_page(request):
    if request.method == "POST":
        code, data = check_token(request)
        if code == 400:
            return gen_response(400, data)

        user_id = request.session['user_id']
        user = Users.objects.get(id=user_id)

        if user.power < 2:
            return gen_response(400, LACK_POWER_ERROR)

        js = parse_json(request.body)
        if js is None:
            return gen_response(400, JSON_ERROR)

        msg = js['msg'] if 'msg' in js else ''
        user_list = js['user'] if 'user' in js else ''
        if msg == '':
            return gen_response(400, 'Message is blank?!')
        if len(user_list) == 0 or user_list[0] == '':
            return gen_response(400, "You didnt specify receivers")

        user_list_tmp = []
        for i in range(len(user_list)):
            user_list_tmp.append(user_list[i].lower())
        user_list = set(user_list_tmp)

        if 'all' in user_list:
            receivers = Users.objects.all()
            for receiver in receivers:
                gen_message(MESSAGE_FROM_ADMIN, msg, user, receiver)

            return gen_response(201, "Successfully send message to all users")


        for target_user in user_list:
            if target_user == 'admin':
                receivers = Users.objects.filter(Q(power=2))
                for receiver in receivers:
                    m = gen_message(MESSAGE_FROM_ADMIN, msg, user, receiver)
                    if m == 400:
                        print_msg_error(msg, receiver)
            if target_user == 'vip':
                receivers = Users.objects.filter(Q(power=1))
                for receiver in receivers:
                    m = gen_message(MESSAGE_FROM_ADMIN, msg, user, receiver)
                    if m == 400:
                        print_msg_error(msg, receiver)
            if target_user == 'normal':
                receivers = Users.objects.filter(Q(power=0))
                for receiver in receivers:
                    m = gen_message(MESSAGE_FROM_ADMIN, msg, user, receiver)
                    if m == 400:
                        print_msg_error(msg, receiver)


        return gen_response(201, f"Successfully send message to target users: {sorted(list(user_list))}")

    if request.method == "GET":
        code, data = check_token(request)
        if code == 400:
            return gen_response(400, data)

        user_id = request.session['user_id']
        user = Users.objects.get(id=user_id)

        message_list = list(Message.objects.filter(receiver=user))
        message_list.sort(key=lambda x: x.pub_time, reverse=True)
        length = min(10, len(message_list))
        if length == 0:
            return gen_response(201, "No message to show!")
        return gen_response(201, {
            'message_num': length,
            'message_list': [
                {
                    'title': message.title,
                    'content': message.content,
                    'time': int(message.pub_time.timestamp() * 1000),
                    'sender': message.sender.name
                }
                for message in message_list
            ]
        })
    return gen_response(400, "Use POST or GET, other methods not supported")
