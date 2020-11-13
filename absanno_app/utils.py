import json
from django.http import JsonResponse, HttpResponse
from django.middleware.csrf import get_token
from django.core.exceptions import ValidationError
from django.utils import timezone
from absanno_app.models import Mission, Message, Users, Reception
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
