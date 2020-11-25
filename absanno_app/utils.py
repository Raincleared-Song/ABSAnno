import json
from django.http import JsonResponse, HttpResponse
from django.middleware.csrf import get_token
from django.core.exceptions import ValidationError
from django.utils import timezone
from absanno_app.models import Mission, Message, Users, Reception, History
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_job

all_tags = ['青年', '中年', '老年',
            '学生', '教师', '上班族', '研究者',
            '人脸识别', '图片识别', '文字识别', 'AI写作', '翻译', '文本分析',
            '生活场景', '工作场景', '购物', '运动', '旅游', '动物', '道德准则', '地理', '科学', '心理学']

tags_by_age = all_tags[0:3]
tags_by_profession = all_tags[3:7]
tags_by_target = all_tags[7:13]
tags_by_content = all_tags[13:]
user_power_dict = {'admin': 2, 'vip': 1, 'normal': 0}

JSON_ERROR = "Request Json Error"
UPLOAD_ERROR = "Upload Contains Error"
LACK_POWER_ERROR = "Dont Have Power"

MESSAGE_FROM_ADMIN = "Message from Admin"
CACHE_SLASH = "cache/"
CACHE_DIR = "cache"

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


def json_default(js, dic):
    ret = []
    for w in dic:
        if w in js:
            ret.append(js[w])
        else:
            ret.append(dic[w])
    return ret


def illegal_name(name):
    a = '\t' in name or '\n' in name or ' ' in name or ',' in name or '.' in name
    return a


def illegal_password(password):
    a = len(password) < 6 or len(password) > 20
    return a


def illegal_user_id(user_id):
    a = user_id < 1 or user_id > len(Users.objects.all())
    return a


def illegal_mission_id(mission_id):
    a = mission_id < 1 or mission_id > len(Mission.objects.all()) or not_digit([mission_id])
    return a


def illegal_user_list(user_list: list):
    for target_user in user_list:
        if target_user not in user_power_dict:
            return True
    return False


def not_digit(li: list):
    for i in li:
        if type(i) is int:
            continue
        elif not i.isdigit():
            return True
    return False


def is_blank(li: list):
    for i in li:
        if i == '':
            return True
    return False


def get_csrf(request):
    return HttpResponse(get_token(request))


def find_user_by_token(request):
    return Users.objects.get(id=request.session['user_id'])


def check_is_banned(request):
    """return True iff user not exist or user is banned"""
    user = find_user_by_token(request)
    return user is None or user.is_banned == 1


def is_normal_user(user_id):
    return Users.objects.get(id=user_id).power == 0


def is_demander(user_id):
    return Users.objects.get(id=user_id).power > 0


def is_admin(user_id):
    return Users.objects.get(id=user_id).power > 1


def parse_json(body):
    try:
        js = json.loads(body)
    except json.decoder.JSONDecodeError:
        return None
    return js


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


def gen_message(_title, _content, _sender, _receiver):
    message = Message(title=_title, content=_content,
                      sender=_sender, receiver=_receiver,
                      pub_time=timezone.now())
    try:
        message.full_clean()
        message.save()
    except ValidationError:
        return 400
    return 0


def print_msg_error(m, r):
    print(f"error when sending content: {m} to {r}")


def cal_sub(mission):
    question_list = mission.father_mission.all()
    history_list_base = mission.ans_history.all()
    history_list = []

    for i in history_list_base:
        if check_history(i):
            history_list.append(i)

    if mission.question_form.startswith('chosen'):
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
            if tot_weight != 0:
                q.ans = int_to_abc(ans)
                q.ans_weight = weight_list[ans] / tot_weight
            q.now_num = mission.now_num
            q.save()
    elif mission.question_form.startswith('fill'):
        for i in range(len(mission.father_mission.all())):
            q = mission.father_mission.all()[i]
            ans_lst = []
            for his in mission.ans_history.all():
                a_lst = get_lst(his.ans)
                ans_lst.append(a_lst[i])
            spl_str = '||'
            q.ans = spl_str.join(ans_lst)
            q.now_num = mission.now_num
            q.save()


def integrate_mission(mission):
    for ret in mission.grand_mission.all():
        ret.ans = 'NULL'
        if ret.pre_ans == '':
            ret.pre_ans = 'NULL'
        ret.save()

    if len(mission.sub_mission.all()) == 0:
        cal_sub(mission)
    else:
        for s in mission.sub_mission.all():
            cal_sub(s)

    return gen_response(201, {
        'mission_name': mission.name,
        'question_form': mission.question_form,
        'question_num': mission.question_num,
        'total': mission.total,
        'is_banned': mission.is_banned,
        'question_list':
            [
                {
                    'word': ret.word,
                    'pre_ans': ret.pre_ans if (mission.question_form.startswith('fill') or ret.pre_ans == "NULL")
                    else get_lst(ret.choices)[abc_to_int(ret.pre_ans)],
                    'ans': ret.ans if (mission.question_form.startswith('fill') or ret.ans == "NULL")
                    else get_lst(ret.choices)[abc_to_int(ret.ans)],
                    'ans_weight': ret.ans_weight,
                    'now_num': ret.now_num
                }
                for ret in mission.grand_mission.all()
            ]
    })


def get_csv_rows(mission: Mission) -> dict:
    """获取指定任务的导出答案列表"""
    rows = [('任务名', '题型', '编号', '总题数', '题干', '已标注次数', '需标注次数', '预埋答案', '标注答案', '置信权重')]
    response = json.loads(integrate_mission(mission).content)
    if response['code'] == 400:
        return response
    response = eval(response['data'])
    for i, question in enumerate(response['question_list']):
        rows.append((response['mission_name'], response['question_form'], i, response['question_num'],
                     question['word'], question['now_num'], response['total'], question['pre_ans'],
                     question['ans'], question['ans_weight']))
    return {'code': 201, 'rows': rows}


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


def sort_mission_list_by_interest(mission_list, user):
    if not user or user.tags == '':
        # not login, sort by tag numbers
        mission_list.sort(key=lambda x: len(x.tags.split('||')))
        return mission_list
    else:
        user_tag = user.tags.split('||')
        user_tag = [s.lower() for s in user_tag]
        mission_list.sort(key=lambda x: len(set(user_tag) & set(x.tags.split('||'))), reverse=True)
        return mission_list


def equals(ans, pre_ans, form):
    ret = False
    if pre_ans == '' or pre_ans == 'NULL':
        return False
    if form.startswith('chosen'):
        ret = ans == pre_ans
    elif form.startswith('fill'):
        ret = pre_ans in ans
    return ret


def check_history(history: History):
    flag, tot, g = 1, 0, 0
    ans_list = get_lst(history.ans)
    q_list = history.mission.father_mission.all()
    feature = history.valid

    if history.user.id == history.mission.user.id:
        flag = 0
    for i in range(len(ans_list)):
        if q_list[i].pre_ans != '' and q_list[i].pre_ans != 'NULL':
            tot += 1
            if equals(ans_list[i], q_list[i].pre_ans, history.mission.question_form):
                g += 1
    if tot != 0 and (g * 100 / tot < 60):
        flag = 0
    if flag == 0:
        ret = False
        history.valid = False
    else:
        ret = True
        history.valid = True
    if feature and (not History.valid):
        mission = history.mission
        mission.now_num -= 1
        if mission.now_num != mission.total:
            mission.to_ans = 1
        mission.save()
        if mission.f_mission is not None:
            upgrade_f_m_num(mission)

    history.save()

    return ret


def upgrade_f_m_num(mission: Mission):
    f_m = mission.f_mission
    f_m.now_num = mission.now_num
    for mis in f_m.sub_mission.all():
        f_m.now_num = min(f_m.now_num, mis.now_num)
    if f_m.now_num == f_m.total:
        f_m.to_ans = 0
    else:
        f_m.to_ans = 1
    f_m.save()


def set_reward(history: History):
    mission = history.mission
    user = history.user
    flag = history.valid
    if flag:
        user.weight += 2
        if user.weight > 100:
            user.weight = 100
        user.coin += mission.reward
        user.fin_num += 1
    else:
        user.weight -= 5
        if user.weight < 0:
            user.weight = 0
            user.is_banned = 1
    user.save()

