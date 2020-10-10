# GIT使用规范

by zyz 

### 如有错误尽早指出

### 所有的PUSH都是到远端的同名仓库！这样是最简洁的！

## DEV分支设置

```
$ git branch dev // 在本地创建新分支dev
$ git checkout dev // 在本地切换到dev分支
// 上述两条指令可以通过 git checkout -b dev 一条指令完成
// 在dev分支下
$ git push --set-upstream origin dev // 将本地dev分支推送到远程dev分支（本地dev和远程dev同步）
```

### 不要在dev上直接工作！不要在dev上直接工作！不要在dev上直接工作！

### DEV分支是所有人共用的，所以需要维护好！

## 个人DEV分支设置

### 规范格式：所有dev特性分支叫做dev-xxx，xxx表示你当前分支开发的功能。

```
$ git checkout -b dev-xxx
// 在dev-xxx分支下
$ git --set-upstream origin dev-xxx
```



## 工作流程（检验通过）

完成上述建立分支并且和远程仓库连接。

首先确认：

### 本地应该有且仅有两/三个分支！（除非你在同时开发多个特性）

```
$ git branch -a
（输出：
master
dev
dev-xxx）
// 可能没有dev-xxx分支，因为之前的特性分支可能已经结束了生命周期
```
### 每一次工作之前，必须走以下流程！

```
// 准备阶段：从dev拿到现在最新的dev分支内容，然后在此基础上进行开发。
$ git checkout dev // 
$ git pull
// 如果没有dev-xxx分支，就-b新建一个（并且切换到该分支），否则直接checkout
$ git checkout -b dev-xxx
$ git merge dev --no-ff // 这里可能会弹窗让你写merge信息；这一段的目的是从dev拿到最新的内容，可以这么写
$ git push // 这里如果出现提示set-upstream，照做，git push --set-upstream origin dev-xxx即可，dev-xxx最好与当前分支同名

$ git checkout dev-xxx // 在自己的分支上开发！

// 进行你的工作

// 工作完成！把自己的工作推到dev-xxx分支上
$ git checkout dev-xxx // 在自己的特性分支上！
$ git add .
$ git commit -m "这是你的commit信息"
$ git push // 这里如果出现提示set-upstream，照做，git push --set-upstream origin dev-xxx即可，dev-xxx最好与当前分支同名


// 收尾阶段：待你准备将dev-xxx分支下的内容merge进dev（merge进master同理）
$ git checkout dev
$ git pull // 这里必然要更新，因为有可能已经有人在你之前更新了dev
$ git merge dev-xxx // 注意！这里没有--no-ff参数，因为dev-xxx的声明周期到此为止，在dev-xxx上可以稳定工作的内容放到了dev分支上，dev-xxx没有存在的必要了。
$ git push // 同理，这里如果出现提示set-upstream，照做，但是一定要将origin/<branch>中的branch和你的当前分支，即dev同名
$ git checkout dev 
$ git branch -d dev-xxx // 删除当前特性分支（本地），因为分支已经不再需要。
$ git push origin --delete dev-xxx // 删除当前特性分支（对应的远端），因为分支已经不再需要。


// 如果想要把dev中的内容merge进master，首先要拿到master上最新内容，然后更新dev分支的内容
// 下面五行几乎不会用到！（对于咱们的开发来说）下方是在拿master中的内容，更新dev
$ git checkout master
$ git pull
$ git checkout dev
$ git merge master --no-ff
$ git push
// 以下内容是肯定要用的，merge进master（先更新dev，之后在master分支下merge）
$ git checkout dev
$ git pull
$ git checkout master
$ git merge dev --no-ff
$ git push
```


