from django.db import models
from django.core.files.storage import FileSystemStorage
import django.utils.timezone as timezone
from django.conf import settings
import datetime
import os


class Users(models.Model):
    # 用户的id使用默认的主键

    name = models.CharField(unique=True, max_length=20)  # 用户名必须唯一，最长长度为20
    # 之后需要考虑在用户名中禁止特定字符，如" ",","等
    password = models.CharField(max_length=20)  # 密码，最大长度20位
    # 之后需要增加最短长度6位，同时保证密码不能仅含数字，以及不能和用户名匹配度过高
    coin = models.IntegerField(default=1000)  # 用户积分，参与答题即可获得积分(金币)，作为答题奖励
    weight = models.IntegerField(default=50)  # 用户权重，有关用户答题质量的评定
    # 用户答题被判断乱答题时会扣除weight， weight被扣到0时用户可能被自动封禁
    # photo = models.ImageField(default="")  # 用户头像，存储图片所在地址，""表示默认头像
    fin_num = models.IntegerField(default=0)  # 已完成任务数量
    is_banned = models.IntegerField(default=0)  # 用户是否被封禁，如为0表示正常运行，如为1表示已被封禁，无法正常登录，需要向管理员申请解封
    power = models.IntegerField(default=0)  # 用户权限，0 为普通用户，1 为发布者，2 为管理员
    # email = models.CharField(max_length=50)  # 用户邮箱，目前可能用不到，之后可以增加与用户邮箱的关联
    # 可以用于注册时对于用户的验证以及用户找回密码
    tags = models.CharField(default="", max_length=1000, blank=True)  # 存储tag，每个tag之间使用||分隔


class Mission(models.Model):
    # 任务的id使用默认的主键

    name = models.CharField(max_length=30, unique=True)  # 发布的任务的名字，必须唯一，因此在显示时可能要显示小的编号
    user = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="promulgator")  # 关联任务的发布用户
    f_mission = models.ForeignKey(to='self', null=True, on_delete=models.DO_NOTHING, related_name="sub_mission")
    # 被分割的子任务
    is_sub = models.IntegerField(default=0)  # 是否为子任务，0表示不是子任务，非0表示为第几个子任务
    total = models.IntegerField()  # 任务需要完成的次数
    now_num = models.IntegerField(default=0)  # 目前已经完成的次数
    question_num = models.IntegerField(default=0)  # 任务中题目的数量，题目最多为20题
    question_form = models.CharField(default="chosen", max_length=20)
    to_ans = models.IntegerField(default=1)  # 当前任务是否需要继续被标注，1表示需要，0表示不需要
    is_banned = models.IntegerField(default=0)  # 是否被封禁，0表示没有被封禁，1表示被封禁
    tags = models.CharField(default="", max_length=1000, blank=True)  # 存储tag，每个tag之间使用||分隔
    reward = models.IntegerField(default=5)  # 当前任务给每个做题用户的报酬
    deadline = models.DateTimeField(default=datetime.date(2021, 6, 30))  # 任务结束时间
    retrieve_time = models.IntegerField(default=24)  # 用户接单后需要在多长时间内完成，以小时为单位
    check_way = models.CharField(default="auto", max_length=10)  # 验收方式，目前为自动验收
    info = models.CharField(default="", max_length=200, blank=True)  # 任务简介
    reception_num = models.IntegerField(default=0)  # 目前接单数
    sub_mission_num = models.IntegerField(default=1)  # 被拆分子任务数
    sub_mission_scale = models.IntegerField(default=0)  # 被拆分任务规模

    def mission_image_url(self):
        default_path = '/'.join(('', 'backend', 'media', '_mission_bg', self.name + '.png'))
        return default_path if os.path.exists(default_path) else '/backend/media/logo/app.png'


def question_image_path(instance, filename):
    return os.path.join(instance.mission.name, filename)


class OverWriteStorage(FileSystemStorage):
    """重写原本的存储类，实现重名覆盖"""
    def get_available_name(self, name, max_length=None):
        # if the filename already exists, remove it
        if self.exists(name):
            os.remove(os.path.join(settings.MEDIA_ROOT, name))
        return name


class Question(models.Model):
    mission = models.ForeignKey(Mission, on_delete=models.DO_NOTHING, related_name="father_mission")  # 关联题目来自的任务
    word = models.CharField(default="", max_length=200, blank=True)  # 文字描述，最多200字
    pre_ans = models.CharField(default="", max_length=10, blank=True)  # 预埋答案，使用 ABCD 表示
    choices = models.CharField(max_length=500)  # 存储选项，不同选项间使用||分隔
    ans = models.CharField(default="NULL", max_length=10, blank=True)  # 统合答案，读取答案利用history读取
    ans_weight = models.FloatField(default=0.0, blank=True)  # 答案的权重

    picture = models.ImageField(upload_to=question_image_path, storage=OverWriteStorage(), blank=True, null=True)

    def picture_url(self):
        if self.picture:
            return '/'.join(('', 'backend', 'media', self.mission.name, self.picture.name.split('/').pop()))
        else:
            return '/backend/media/logo/app.png'


class History(models.Model):
    user = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="history")
    mission = models.ForeignKey(Mission, on_delete=models.DO_NOTHING, related_name="ans_history")
    pub_time = models.DateTimeField(default=timezone.now)
    ans_time = models.IntegerField(default=0)  # 用户答题所花时间
    ans_weight = models.IntegerField(default=50)  # 答题时用户权重
    ans = models.CharField(default="", max_length=1000)  # 存储用户答案，不同题目间使用||分隔


class Apply(models.Model):
    user = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="user_apply")
    type = models.CharField(default="", blank=True, max_length=10)  # 请求的类别
    pub_time = models.DateTimeField(default=timezone.now)
    accept = models.IntegerField(default=0)  # 审批状态，0表示待审批，1表示通过，2表示拒绝


class Reception(models.Model):
    user = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="user_reception")
    mission = models.ForeignKey(Mission, on_delete=models.DO_NOTHING, related_name="mission_reception")
    pub_time = models.DateTimeField(default=timezone.now)
    deadline = models.DateTimeField(default=datetime.date(2021, 6, 30))
    can_do = models.BooleanField(default=True)  # 表示这个接单目前是否可以做


class Message(models.Model):
    title = models.CharField(default="title", max_length=50)
    content = models.CharField(default="content", max_length=500)
    sender = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="send_message")
    receiver = models.ForeignKey(Users, on_delete=models.DO_NOTHING, related_name="receive_message")
    pub_time = models.DateTimeField(default=timezone.now)
