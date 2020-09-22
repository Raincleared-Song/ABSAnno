# 数据库字段

每个数据表都以自带的 `_id` 为主键

### 用户数据表

|          字段名          |          字段类型          |
| :----------------------: | :------------------------: |
|          同户名          |         CharField          |
|       密码（编码）       | IntegerField / StringField |
|           头像           |     CharFiled（地址）      |
| 用户类别（含是否被 ban） |        IntegerField        |
|   信誉度（平均正确率）   |         FloatField         |
|        获得总奖励        |        IntegerField        |
|       已完成任务数       |        IntegerFiled        |

### 任务总表

|      字段名      |                  字段类型                   |
| :--------------: | :-----------------------------------------: |
|      任务名      |                  CharFiled                  |
|     创建时间     |                DateTimeFiled                |
|   创建人用户名   |                  CharFiled                  |
|    所属需求者    |                外键，用户类                 |
|   任务最高奖励   |                IntergerFiled                |
| 任务完成时间估计 | IntegerField（default：$\sum$ 题数 * 时限） |
|     任务说明     |                  CharFiled                  |
|       题数       |                IntegerFiled                 |
| 任务类别标签列表 |              CharFiled（json）              |

### 题目总表

|      字段名      |                    字段类型                     |
| :--------------: | :---------------------------------------------: |
|       题面       |                    CharField                    |
|     题目类型     |                  IntegerFiled                   |
| 题目选项（三种） | 选择（选项 json 串）/填空（""）/ 图片题（地址） |
|     时间限制     |                  IntegerFiled                   |
| 题目奖励（答对） |                  IntergerFiled                  |
| 题目奖励（答错） |                  IntegerFiled                   |
|     预设答案     |                    CharFiled                    |
|     所属任务     |                  外键，任务类                   |

### 答题记录表

|        字段名        |      字段类型      |
| :------------------: | :----------------: |
|       是否有效       |    BooleanField    |
|       答题时间       |   DateTimeField    |
|        答题者        |     外键，用户     |
|       所属任务       |     外键，任务     |
|       获得奖励       |    IntegerField    |
|       答案列表       | CharFiled，json 串 |
| 已有标签抽检的正确率 |     FloatField     |

