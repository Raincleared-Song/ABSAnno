import datetime
import json
import os
import csv
from zipfile import ZipFile, BadZipFile
import random
from django.core.exceptions import ValidationError
from django.http import FileResponse
from .groundPic import generate_pic
from django.core.files.base import File
from io import BytesIO
from .models import Mission, Question, Users
from .utils import check_token, gen_response, find_user_by_token, get_lst, get_csv_rows, abc_to_int, int_to_abc, \
    integrate_mission, parse_json, JSON_ERROR, invalidate_mission, UPLOAD_ERROR, LACK_POWER_ERROR, CACHE_SLASH, \
    CACHE_DIR, json_default, not_digit, is_blank, is_demander, illegal_mission_id


# 静态类，负责图片的打乱操作
class PicRandom:
    # 静态成员
    pic_index = 0
    pic_queue = list(range(1, 18))
    random.shuffle(pic_queue)

    @staticmethod
    def next_pic():
        res = PicRandom.pic_queue[PicRandom.pic_index]
        if PicRandom.pic_index == 6:
            PicRandom.pic_index = 0
            random.shuffle(PicRandom.pic_queue)
        else:
            PicRandom.pic_index += 1
        return res


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
                return gen_response(400, UPLOAD_ERROR)
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
                    return gen_response(400, UPLOAD_ERROR)
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
            js = parse_json(request.POST.get('info'))
            if js is None:
                return gen_response(400, JSON_ERROR)

            name = js['name'] if 'name' in js else ''
            question_num_ = js['question_num'] if 'question_num' in js else ''
            if not question_num_.isdigit() or name == '':
                return gen_response(400, UPLOAD_ERROR)
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
            js = parse_json(request.body)
            if js is None:
                return gen_response(400, JSON_ERROR)

        dic = {'name': '', 'question_form': '', 'question_num': '', 'total': '', 'reward': '100',
               'deadline': '2022-6-30', 'retrieve_time': '', 'check_way': 'auto', 'info': '',
               'mission_tags': [], 'template': '0'}
        name, question_form, question_num_, total_, reward_, deadline_, retrieve_time_, check_way, info, tags_, \
            template_ = json_default(js, dic)
        to_be_check = 0 if check_way == 'auto' else 1

        if len(Mission.objects.filter(name=name)) > 0:
            return gen_response(400, "Mission Name Has Been Used")

        if isinstance(tags_, str):
            tags_ = get_lst(tags_)

        spl_str = '||'
        tags = spl_str.join(tags_)
        tags = tags.lower()
        if not_digit([question_num_, total_, reward_, retrieve_time_, template_]) or is_blank([name, question_form]):
            return gen_response(400, UPLOAD_ERROR)
        question_num = int(question_num_)
        total = int(total_)
        reward = int(reward_)
        d_list = deadline_.split('-')
        y, m, d = int(d_list[0]), int(d_list[1]), int(d_list[2])
        deadline = datetime.date(y, m, d)
        retrieve_time = int(retrieve_time_)
        template = int(template_)

        if file is None and 'question_list' in js:
            question_list = js['question_list']
        if not isinstance(question_list, list):
            return gen_response(400, "Question_list Is Not A List")
        if len(question_list) != question_num:
            return gen_response(400, "Question_list Length Error")
        pre_ans_flag = 0
        for q in question_list:
            if 'ans' in q and q['ans'] != '':
                pre_ans_flag = 1
        if (pre_ans_flag == 0) and (check_way == 'auto'):
            return gen_response(400, "Auto Without Any Pre Ans")
        if (pre_ans_flag == 1) and (check_way != 'auto'):
            return gen_response(400, "You Dont Need To Set Pre_Ans Now")

        if len(Mission.objects.filter(name=name)) > 0:
            return gen_response(400, 'Mission Name Already Used')

        path_base = 'image/_mission_bg' if has_bg else 'pics'
        image_base = f'{name}_bg.png' if has_bg else f'{PicRandom.next_pic()}.jpg'
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
                              deadline=deadline, retrieve_time=retrieve_time, sub_mission_num=sub_mission_num,
                              sub_mission_scale=sub_mission_scale, to_be_check=to_be_check, template=template)
            mission.full_clean()
            mission.save()
        except ValidationError:
            clean_image_when_fail()
            return gen_response(400, UPLOAD_ERROR)

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
                question = Question(word=contains, mission=mission, grand_mission=mission, choices=choices, pre_ans=ans)
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
            father_name = name
            assert len(q_list) > -1
            for i in range(1, sub_mission_num + 1):
                try:
                    name = f'{father_name}_{i}'
                    sub_mis = Mission(name=name, question_form=question_form, total=total, user=user, tags=tags,
                                      reward=reward, check_way=check_way, info=info, deadline=deadline,
                                      retrieve_time=retrieve_time, sub_mission_num=1, template=template)
                    sub_mis.is_sub = i
                    sub_mis.f_mission = mission
                    sub_mis.full_clean()
                    sub_mis.save()
                except ValidationError:
                    clean_image_when_fail()
                    return gen_response(400, "Sub Mission Upload Form Error")
                if i < sub_mission_num:
                    for j in range((i - 1) * sub_mission_scale, i * sub_mission_scale):
                        sub_q = Question.objects.get(id=q_list[j].id)
                        sub_q.mission = sub_mis
                        sub_q.grand_mission = mission
                        sub_q.save()
                else:
                    for j in range((i - 1) * sub_mission_scale, len(q_list)):
                        sub_q = Question.objects.get(id=q_list[j].id)
                        sub_q.mission = sub_mis
                        sub_q.grand_mission = mission
                        sub_q.save()
                sub_mis.question_num = len(sub_mis.father_mission.all())
                sub_mis.sub_mission_scale = len(sub_mis.father_mission.all())
                sub_mis.save()

                path_base = 'image/_mission_bg' if has_bg else 'pics'
                image_base = f'{name}_bg.png' if has_bg else f'{PicRandom.next_pic()}.jpg'
                generate_pic(path_base, image_base, sub_mis.name, sub_mis.question_num,
                             sub_mis.reward, sub_mis.deadline.strftime('%Y-%m-%d'))

        if file is not None:
            file.close()

        return gen_response(201, "Upload Success")

    return gen_response(400, UPLOAD_ERROR)


def download_result(request):
    """需求方导出结果文件"""
    code, data = check_token(request)
    if code == 400:
        return gen_response(code, data)

    user_id = request.session['user_id']
    if not is_demander(user_id):
        return gen_response(400, LACK_POWER_ERROR)

    mission_id_ = request.GET.get('mission_id') if 'mission_id' in request.GET else ''

    if not_digit([mission_id_]):
        return gen_response(400, 'Mission ID Is Not Digit')

    mission_id = int(mission_id_)

    if illegal_mission_id(mission_id):
        return gen_response(400, 'Mission ID Illegal')

    mission = Mission.objects.get(id=mission_id)

    if mission.user.id != user_id:
        return gen_response(400, 'User ID Is Wrong')

    if not os.path.exists(CACHE_DIR):
        os.mkdir(CACHE_DIR)
    else:  # 文件数过多时清楚缓存
        file_list = os.listdir(CACHE_DIR)
        if len(file_list) > 20:
            file_list.sort(key=lambda x: os.path.getmtime(CACHE_SLASH + x))
            os.remove(CACHE_SLASH + file_list[0])

    file_name = 'result-%d.csv' % mission_id
    file = open(CACHE_SLASH + file_name, 'w', encoding='gbk', newline='')
    response = get_csv_rows(mission)
    if response['code'] != 201:
        return gen_response(response['code'], response['data'])
    rows = response['rows']
    writer = csv.writer(file)
    writer.writerows(rows)
    file.close()
    file = open(CACHE_SLASH + file_name, 'rb')
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
        if not is_demander(user_id):
            return gen_response(400, LACK_POWER_ERROR)

        mission_id = request.GET.get("mission_id") if 'mission_id' in request.GET else '0'
        if not mission_id.isdigit():
            return gen_response(400, "mission_id Is Not Digit")

        mission_id = int(mission_id)
        if illegal_mission_id(mission_id):
            return gen_response(400, "Mission ID Error")

        mission = Mission.objects.get(id=mission_id)
        if mission.user.id != user_id:
            return gen_response(400, "Mission Not Published by You")

        return integrate_mission(mission)

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
        if not is_demander(user_id):
            return gen_response(400, 'Lack of Permission')

        mission_id_ = request.GET.get('mission_id') if 'mission_id' in request.GET else '1'

        if not mission_id_.isdigit():
            return gen_response(400, "Mission_ID is not digit")
        mission_id = int(mission_id_)

        if illegal_mission_id(mission_id):
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
        if not is_demander(user_id):
            return gen_response(400, LACK_POWER_ERROR)

        js = parse_json(request.body)
        if js is None:
            return gen_response(400, JSON_ERROR)

        mission_id = js["mission_id"] if 'mission_id' in js else '0'
        if not mission_id.isdigit():
            return gen_response(400, "mission_id Is Not Digit")
        mission_id = int(mission_id)

        if illegal_mission_id(mission_id):
            return gen_response(400, "Mission ID Error")

        mission = Mission.objects.get(id=mission_id)
        if mission.user.id != user_id:
            return gen_response(400, "Mission Not Published by You")

        integrate_mission(mission)

        if mission.sub_mission_num == 1:
            if mission.to_be_check == 1:
                invalidate_mission(mission)
        else:
            for mis in mission.sub_mission.all():
                if mis.to_be_check == 1:
                    invalidate_mission(mis)

        return gen_response(201, 'Mission End Success')

    return gen_response(400, 'End Mission Error')
