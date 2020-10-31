from django.db import models
import django.utils.timezone as timezone
import os


class Users(models.Model):
    # 用户的id使用默认的主键

    name = models.CharField(unique=True, max_length=20)  # 用户名必须唯一，最长长度为20
    # 之后需要考虑在用户名中禁止特定字符，如" ",","等
    password = models.CharField(max_length=20)  # 密码，最大长度20位
    # 之后需要增加最短长度6位，同时保证密码不能仅含数字，以及不能和用户名匹配度过高
    score = models.IntegerField(default=0)  # 用户积分，参与答题即可获得积分(金币)，作为答题奖励
    weight = models.IntegerField(default=100)  # 用户权重，有关用户答题质量的评定
    # 用户答题被判断乱答题时会扣除weight， weight被扣到0时用户可能被自动封禁
    # photo = models.ImageField(default="")  # 用户头像，存储图片所在地址，""表示默认头像
    fin_num = models.IntegerField(default=0)  # 已完成任务数量
    is_banned = models.IntegerField(default=0)  # 用户是否被封禁，如为0表示正常运行，如为1表示已被封禁，无法正常登录，需要向管理员申请解封
    power = models.IntegerField(default=0)  # 用户权限，0 为普通用户，1 为发布者，2 为管理员
    # email = models.CharField(max_length=50)  # 用户邮箱，目前可能用不到，之后可以增加与用户邮箱的关联
    # 可以用于注册时对于用户的验证以及用户找回密码
    tags = models.CharField(default="", max_length=1000, blank=True)  # 存储tag，每个tag之间使用|分隔

    # 接下来为用户画像设计，每个tag表示相关权重，数值为0-100
    tag_science = models.IntegerField(default=0)
    tag_art = models.IntegerField(default=0)
    tag_sports = models.IntegerField(default=0)
    tag_literature = models.IntegerField(default=0)
    tag_food = models.IntegerField(default=0)
    tag_music = models.IntegerField(default=0)
    tag_game = models.IntegerField(default=0)
    tag_daily = models.IntegerField(default=0)
    tag_others = models.IntegerField(default=0)

    # 接下来为相关的函数
    # TODO


class Mission(models.Model):
    # 任务的id使用默认的主键

    name = models.CharField(max_length=30)  # 发布的任务的名字，不是唯一，因此在显示时可能要显示小的编号
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="promulgator")  # 关联任务的发布用户
    total = models.IntegerField()  # 任务需要完成的次数
    now_num = models.IntegerField(default=0)  # 目前已经完成的次数
    question_num = models.IntegerField(default=0)  # 任务中题目的数量，题目最多为20题
    question_form = models.CharField(default="judgement", max_length=20)  # 任务中题目的类型
    to_ans = models.IntegerField(default=1)  # 当前任务是否需要继续被标注，1表示需要，0表示不需要
    is_banned = models.IntegerField(default=0)  # 是否被封禁，0表示没有被封禁，1表示被封禁
    tags = models.CharField(default="", max_length=1000, blank=True)  # 存储tag，每个tag之间使用|分隔

    # 接下来表示的是当前的任务的tag，可以针对用户画像进行发放
    # 总共有3个tag，用0-9表示，0表示无tag，1-9分别对应上方的tag
    tag_1 = models.IntegerField(default=0)
    tag_2 = models.IntegerField(default=0)
    tag_3 = models.IntegerField(default=0)

    # 接下来为需要完成的相关的函数
    # TODO


def question_image_path(instance, filename):
    return os.path.join(instance.mission.name, filename)


class Question(models.Model):  # 判断题和选择题均使用Question存储
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name="father_mission")  # 关联题目来自的任务
    word = models.CharField(default="", max_length=200, blank=True)  # 文字描述，最多200字
    # image = models.ImageField(default="") # 相关图片，""表示无图片
    # 需要对没有文字描述和图片描述的空题目进行判断
    type = models.CharField(default="judgement", max_length=20)  # 题型，默认为判断

    # 判断题内容

    # T_word = models.CharField(default="是") # 对于正选的文字描述
    T_num = models.IntegerField(default=0)  # 正选被选择的次数
    # F_word = models.CharField(default="否") # 对于反选的文字描述
    F_num = models.IntegerField(default=0)  # 反选被选择的次数
    matched_ans = models.IntegerField(default=1)  # 被标注的答案
    # 预设答案，分别有""，"T"，"F"三种存储结果，分别表示无预设答案，预设答案正选，预设答案反选
    pre_ans = models.CharField(default="", max_length=1, blank=True)

    # 选择题内容
    chosen_num = models.IntegerField(default=2)  # 选项的数目，最多为8个
    ans_num = models.IntegerField(default=0)  # 答案的数目，最多为chosen_num
    single = models.IntegerField(default=1)  # 是否作单选题处理，1表示作单选题处理，0表示作不定项选择题处理
    has_pre_ans = models.IntegerField(default=0)  # 是否有预设选项，0表示没有，1表示有

    picture = models.ImageField(upload_to=question_image_path, blank=True, null=True)

    def picture_url(self):
        if self.picture:
            return '/'.join(('', 'backend', 'media', self.mission.name, self.picture.name))
        else:
            return '/backend/media/logo/app.png'

    # 设置选项，分别为选项的文字描述，图片描述和被选择的次数
    # 文字描述长度限制为30字，图片描述中""表示没有图片
    # 选项数最少2项，最多8项


class ChosenAns(models.Model):
    chosen_question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="father_question")  # 关联选项来自的题目
    word = models.CharField(default="", max_length=30, blank=True)  # 选项的文字描述，最长为30个字符
    # image = models.ImageField(default="") # 如果选项用图片表示时存储图片，“”表示无图片
    pre_ans = models.IntegerField(default=0)  # 表示该选项是否为预设的正确答案，0表示不是，1表示是
    chosen_num = models.IntegerField(default=0)  # 目前被选择的次数，涉及结果的判断


class History(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="history")
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name="ans_history")
    pub_time = models.DateTimeField(default=timezone.now)
