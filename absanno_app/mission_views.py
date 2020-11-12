from django.db.models import Q
from .utils import *


# 广场页面
def square_show(request):
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
            tag_flag, kw_flag, sub_flag = 0, 0, 1
            if (len(mis.sub_mission.all()) != 0) and (mis.is_sub == 0):
                sub_flag = 0
            if sub_flag == 1:
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
                                              'image_url': ret.mission_image_url(),
                                              'is_sub': ret.is_sub
                                          }
                                          for ret in mission_list[num: get_num]
                                      ]}
                            )
    return gen_response(400, "User Show Error")


# 广场右边栏兴趣栏
def interest_show(request):
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
            mission_list_base = Mission.objects.filter(Q(is_banned=0) & Q(to_ans=1) &
                                                       ((Q(is_sub=0) & Q(sub_mission_num=1)) | ~Q(is_sub=0))
                                                       ).order_by('-id')

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
                                              'image_url': ret.mission_image_url(),
                                              'is_sub': ret.is_sub
                                          }
                                          for ret in mission_list[num: get_num]
                                      ]}
                            )
    return gen_response(400, "User Show Error")


# 展示任务具体内容
def mission_show(request):
    if request.method == 'GET':

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

        js = parse_json(request.body)
        if js is None:
            return gen_response(400, JSON_ERROR)

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