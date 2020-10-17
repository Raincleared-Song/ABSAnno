# 后端CHECK/TODO

zyztowjw：在用户界面我需要得到该用户的身份状态（管理员、发布者or普通用户）

# ！！！！任何向后端的请求都要带上TOKEN！！！！！

# 更新：

### 广场页面分类搜索

传送参数：
```
'id': id
'token': token 
'num': num
'type': [string](字符串列表，表示题目类型，比如判断/选择/etc) 'total'/'judge'/'choice'
'theme': [string]（字符串列表，表示题目标签，比如食物/交通/etc，目前阶段应该不用，可以当作空列表）
```
返回参数：同之前，一次12个。
```
'ret': int
'total': int
'question_list':[
    {'name': string, ...}
    ]
```


### 广场页面搜索

传送参数：
```
'id': id
'token': token
'num': num
'keyword':string
```
返回参数：同之前，多于12个则一次返回12个。
```
'ret': int
'total': int
'question_list':[
    {'name': string, ...}
    ]
```

### 广场页面删除
传送参数：
```
'user_id': int(user_id)
'token': string(user_token)
'question_id': int(要删除的题目id)
```
返回参数：暂时感觉不需要额外的返回。
** 这之后前端将直接调用一次广场题目页面刷新 **

### 登录 & 注册：
返回参数：
```
'id': number
'name': string
'token': string
'identity': number (0为普通用户，1为发布者，2为管理员)
```
token一小时有效我觉得就行，每次登录/注册时产生一个新的值，任何向后端的访问都带上这个字段，后端检查无误后进行操作。

另：token可以放在cookie里传过来。

（来自xyq）

# 有关用户的登录与注册

\# request.body为json

\# 其中内容为：

\# name, password, method, email

\# name为必须，password在method为LogIn和SignIn时为必须，为LogOut时非必须

\# email留作扩展功能时期实现

\# 出错返回可以参考下面的代码

```
'name': 用户名
'password': 密码
'method': 方式，三种可选："LogIn""SignIn""LogOut"
若为LogOut方法的话password可为空
'email': 这一项目前传递空字段即可
```





# 每次前端问题广场需要申请一次获取问题列表GET，然后获得问题

\# 包括第一次进入问题广场

\# request.body为json

\# 其中内容为

\# id，num，id表示当前用户id，num表示目前显示给用户的任务是从任务列表中的第几个开始的，默认为0，之后可以使用后端getNum传给前端的num

\# 每次传输的任务数量为 本次返回的getNum-本次传入的num

```json
'id': id
'num': num
```



返回内容

```json
        return gen_response(201, {'ret': getNum,
                            'total': len(Mission.objects.filter(Q(to_ans=1) & ~Q(user_id=id))), # 当前任务总数
                            "question_list":
                            [
                                {
                                    'id': ret.id,
                                    'name': ret.name,
                                    'user': ret.user.name,
                                    'questionNum': ret.question_num,
                                    'questionForm': ret.question_form
                                }
                                for ret in Mission.objects.filter(Q(to_ans=1) & ~Q(user_id=id)).order_by('id')[num: getNum]
                            ]}
                            )
```





# 打开任务后存在GET和POST两种方式



\# GET为用户切换题目时使用的方式

\# 其request.body为一个json文件，组成为：

\# id, num，step

\# 其中id为目前所做任务的编号，num表示题号，默认为0，之后使用返回的getNum，step为1或者-1，表示下一题和上一题，更新step为0情况，为实现题目的跳转·功能，此时num为需要跳转的题号-1

```json
'id': id
'num': num
'step': step
```

返回格式

```json
        if Mission.objects.get(id).question_form == "judgement": # 题目型式为判断题的情况
            return gen_response(201, {
                'total': len(Mission.objects.get(id=id).father_mission.all()), # 目前任务中题目总数
                'ret': getNum,
                'word': ret.word,
                ('options': []) # 选择题的选项
            })
```



\# POST为用户提交本次传递题目

\# 其request.body为一个json文件，组成为：

\# user_id, mission_id, [{ans}]

\# 其中user_id为当前答题用户，用于统计其用户信息，如score，mission_id为当前任务的id，表示目前用户回答的任务的id

\# ans为用户的答案，目前仅支持判断题

```json
'user_id': user_id
'mission_id': mission_id
'ans': ans
```

ljj：对于选择题，关于ans格式的一种提议
```json
'ans': [
    ['op1', 'op2', ...]
]
```

# 上传题目格式

```json
'name': 任务名称
'question_form': 目前仅支持judgement一种格式
'question_num': 题目数量
'user_id': 上传题目的用户id
'total': 任务需要被标注的次数
[
    {
        'contains': 题干
        ('ans': 预先设计的答案) 可以没有
        ('options': [] 选择题的选项)
    }
]
```





# 用户界面的传入与传出格式

传入使用GET方法

格式为：

```json
'id': 用户id
'method': 可以为 'user' 'history' 'mission' 分别表示所需要获取的内容
```

'user'表示需要返回基本的用户界面

```json
                'id': ret.id, # 用户的id
				'name': ret.name, # 用户的名称
                'score': ret.score, # 用户的得分
                'weight': ret.weight, # 用户的权重/信誉度
				'num': ret.fin_num # 用户完成的任务数
```

'history'表示展示用户的答题历史

```json
                'total_num': len(ret.history.all()), # 完成的任务总数
                'mission_list': # 完成的任务的json列表
                    [
                        {
                            'id': mission_ret.mission.id, # 任务的id
                            'name': mission_ret.mission.name, # 任务名
                            'user': mission_ret.mission.user.name, # 任务发布者的名称
                            'question_num': mission_ret.mission.question_num, # 任务中题目的数量
                            'question_form': mission_ret.mission.question_form, # 任务中的题型，目前仅支持"judgement"，为判断题
                            'ret_time': mission_ret.pub_time # 任务的发布时间，为datetime
                        }
                        for mission_ret in ret.history.all().order_by('pub_time')
                    ]

```

'mission'表示用户发布的任务

```json
                'total_num': len(ret.promulgator.all()), # 目前发布的任务的总数
                'mission_list': # 发布的任务的列表
                    [
                        {
                            'id': mission_ret.id, # 发布的任务的id
                            'name': mission_ret.name, # 发布的任务的名称
                            'total': mission_ret.total, # 发布的任务需要被标记的总次数
                            'num': mission_ret.now_num, # 目前被标记的次数
                            'question_num': mission_ret.question_num, # 发布的任务的问题数量
                            'question_form': mission_ret.question_form # 发布的任务的题型
                        }
                        for mission_ret in ret.promulgator.all().order_by('id')
                    ]

```





# 展示我的任务被标注的情况

目前仅完成判断题情况

采用GET方法传递信息

传递内容

```json
'user_id': 用户id
'mission_id': 任务id
```

返回内容

```json
                'mission_name': mission.name, # 任务的名称
                'question_form': mission.question_form, # 任务的题型，目前仅完成"judgement"
                'question_num': mission.question_num, # 任务的题目数量
                'total': mission.total, # 任务需要被标注的总数
                'now_num': mission.now_num, # 任务目前被标注的次数
                'question_list': # 题目列表
                    [
                        {
                            'word': ret.word, # 题目内容
                            'T_num': ret.T_num, # 被判断为对的次数
                            'F_num': ret.F_num, # 被判断为错的次数
                            'pre_ans': ret.pre_ans, # 判断题的预设答案""表示没有，"T"表示预设答案为真，"F"表示预设答案为假
                            'ans': ret.matched_ans # 被标注的答案，1表示被标注为T，0表示被标注为F
                        }
                        for ret in mission.father_mission.all()
                    ]

```





# 所有返回的格式

```
'code' : 400为出错返回，正常情况下201代表无误
'data' : 返回的具体内容
```





# url约定

login/	登录

signin/	注册

square/	广场

user/	用户界面

mission/	回答任务界面

info/	网站规定

upload/	上传任务

user/	用户界面

mymission/	查看我发布的任务