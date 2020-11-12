from .utils import *
from zipfile import ZipFile, BadZipFile
import random
from .groundPic import generate_pic
from django.core.files.base import File
from io import BytesIO


def upload_mission(request):
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

        sub_mission_num = 1
        sub_mission_scale = question_num
        if question_num > 10:
            sub_mission_num = int(question_num / 10)
            sub_mission_scale = int(question_num / sub_mission_num)

        cost = reward * total * sub_mission_num
        if user.coin < cost:
            clean_image_when_fail()
            return gen_response(400, "You Dont Have Enough Coin")
        user.coin -= cost
        user.save()

        try:
            mission = Mission(name=name, question_form=question_form, question_num=question_num, total=total,
                              user=user, tags=tags, reward=reward, check_way=check_way, info=info,
                              deadline=deadline, retrieve_time=retrieve_time,
                              sub_mission_num=sub_mission_num, sub_mission_scale=sub_mission_scale)
            mission.full_clean()
            mission.save()
        except ValidationError:
            clean_image_when_fail()
            return gen_response(400, "Upload Form Error")

        for k, i in enumerate(question_list):
            contains = i['contains'] if 'contains' in i else ''
            ans = i['ans'] if 'ans' in i else ''
            choices = i['choices'] if 'choices' in i else ''
            if (contains == '') and (not mission.question_form.endswith('-image')):
                clean_image_when_fail()
                return gen_response(400, "Question Contains is Null")
            if (choices == '') and (mission.question_form.startswith('chosen')):
                clean_image_when_fail()
                return gen_response(400, "There Is No Choice In a Chosen-Mission")
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
        if sub_mission_num > 1:
            q_list = mission.father_mission.all().order_by('id')
            for i in range(1, sub_mission_num + 1):
                try:
                    sub_mis = Mission(name=name, question_form=question_form, total=total, user=user, tags=tags,
                                      reward=reward, check_way=check_way, info=info, deadline=deadline,
                                      retrieve_time=retrieve_time, sub_mission_num=1)
                    sub_mis.is_sub = i
                    sub_mis.f_mission = mission
                    sub_mis.full_clean()
                    sub_mis.save()
                except ValidationError:
                    clean_image_when_fail()
                    return gen_response(400, "Sub Mission Upload Form Error")
                if i < sub_mission_num:
                    for j in range((i-1)*sub_mission_scale, i*sub_mission_scale):
                        sub_q = q_list[j]
                        sub_q.pk = None
                        sub_q.mission = sub_mis
                        sub_q.save()
                else:
                    for j in range((i-1)*sub_mission_scale, len(q_list)):
                        sub_q = q_list[j]
                        sub_q.pk = None
                        sub_q.mission = sub_mis
                        sub_q.save()
                sub_mis.question_num = len(sub_mis.father_mission.all())
                sub_mis.sub_mission_scale = len(sub_mis.father_mission.all())
                sub_mis.save()

        if file is not None:
            file.close()

        return gen_response(201, "Upload Success")

    return gen_response(400, "Upload Error")


def download_result(request):
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

        js = parse_json(request.body)
        if js is None:
            return gen_response(400, JSON_ERROR)

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
