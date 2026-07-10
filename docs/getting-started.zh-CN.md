# Repo Confidence 中文上手指南

## 先记住一句话

**Repo Confidence 不是一个需要运行的命令行程序。**

它是安装在 Codex 里的能力包。安装一次后，你只需要在想了解的目标仓库中
新建一个 Codex 任务，并在需求里写出 `$repository-onboarding-coach`。

## 你现在怎么马上体验

如果 Skill 已经安装完成，只做下面三步：

1. 用 Codex 打开你真正想了解的仓库，例如你的业务项目或一个开源项目；
2. 在这个仓库里**新建一个 Codex 任务**；
3. 复制下面这句话发送：

```text
使用 $repository-onboarding-coach，请全程用中文帮我快速接手当前仓库。
先只读分析，不修改代码。先给我一页项目总览，再告诉我最重要的 5 条业务链路、
数据和缓存在哪里、哪些地方风险最高，以及我下一步应该先学什么。
```

你不需要先选择模式，不需要运行 Python，也不需要创建文档目录。

预期会得到：

```text
项目是做什么的
→ 核心模块和业务名词
→ 5 条关键链路
→ 数据库、缓存和外部服务
→ 高风险区域
→ 已确认、推断和未知内容
→ 建议的学习顺序
```

> 如果输入 `$repository-onboarding-coach` 时没有出现在 Skill 候选中，请新建
> Codex 任务或重新打开 Codex。安装前已经存在的长任务可能不会重新加载 Skill。

## 它实际是怎么工作的

Repo Confidence 当前最直接的使用方式，是把
`repository-onboarding-coach` 安装成 Codex Skill，然后像平时一样在目标
仓库中向 AI 提需求。

它不会自动常驻后台，也不会替换 IDE、Git、CodeGraph 或现有开发流程。
你可以显式输入 `$repository-onboarding-coach`，让 Codex 在正常工作的同时
补充项目理解、改动影响、风险和验证证据。

## 其他用户第一次安装

### 让 Codex 安装

在 Codex 中直接说：

```text
从 GitHub 仓库 LM20230311/repo-confidence 的
skills/repository-onboarding-coach 路径安装这个 Skill。
```

安装后，从下一条任务开始可以使用。

### 从本地仓库安装

如果已经克隆本项目：

```bash
cp -R skills/repository-onboarding-coach \
  "${CODEX_HOME:-$HOME/.codex}/skills/"
```

安装位置通常是：

```text
~/.codex/skills/repository-onboarding-coach
```

## 在目标仓库打开 Codex

进入你真正要了解或维护的仓库，不需要在 Repo Confidence 项目目录里运行。

例如：

```bash
cd /path/to/your-project
```

然后正常打开一个 Codex 任务。Skill 会分析当前工作区中的仓库。

## 熟悉以后再按场景使用

### 场景一：第一次进入陌生仓库

使用 `bootstrap`：

```text
使用 $repository-onboarding-coach 帮我快速接手当前仓库。
先只读分析，不修改业务代码，也不要立即生成大量文档。
给我项目护照、核心实体、5～8 条关键链路、状态与缓存地图、
高风险区域和已知未知，并标明 Verified、Inferred、Unknown。
```

你会先得到一张全局地图。只有当你明确说“写入仓库”时，才需要生成
`docs/project-atlas/`。

### 场景二：日常让 AI 修改需求

使用默认的 `ambient` 模式：

```text
使用 $repository-onboarding-coach，以 ambient 模式完成这个需求：
给订单查询接口增加支付状态筛选。
保持原有开发流程；低风险直接继续，只简要告诉我影响链路、数据/缓存影响、
风险和验证方式。高风险或缺少关键产品决策时再暂停。
```

预期体验仍然是：

```text
提需求 → AI 修改 → 运行测试 → 提交
```

Skill 只在旁边补充：

```text
影响预测 → 风险提示 → Diff 对照 → 验证证据
```

### 场景三：深入理解一条业务链路

使用 `learn`：

```text
使用 $repository-onboarding-coach 带我理解退款链路。
说明正常路径、失败与补偿、数据库和缓存变化、权限、幂等、不变量、
测试与观测点，最后给我一个真实需求和一个故障场景做推演。
```

这个模式适合你真正想把知识装进脑子，而不只是让 AI 给答案。

### 场景四：修改高风险功能前先分析

使用 `change-prep`：

```text
使用 $repository-onboarding-coach，先不要改代码。
为“增加 API Key 专属计费倍率”生成 Change Brief，核实入口、完整调用链、
数据库、缓存、异步任务、计费快照、测试、灰度和回滚影响。
区分事实、推断和阻塞决策。
```

确认影响后再说：

```text
按照这份 Change Brief 实施，完成后对照预测范围和实际 Diff。
```

### 场景五：代码更新后刷新项目地图

使用 `refresh`：

```text
使用 $repository-onboarding-coach，把现有 Project Atlas 从上次验证提交
增量刷新到当前 HEAD。只更新受影响页面，不要重写整个知识库。
```

### 场景六：判断新人能接什么需求

使用 `readiness`：

```text
使用 $repository-onboarding-coach，根据我对当前项目的讲解、需求预测、
真实改动和故障推演，按业务域评估维护能力。
不要根据自信程度评分，告诉我已验证能力、安全边界和下一个练习需求。
```

## 用 New API 案例学习

如果你想先体验成品，不需要重新分析 New API，可以按这个顺序阅读：

1. [Project Atlas 中文总览](../examples/new-api/project-atlas/index.zh-CN.md)
2. [架构地图](../examples/new-api/project-atlas/architecture.md)
3. [同步模型转发链路](../examples/new-api/project-atlas/flows/relay-request.md)
4. [计费生命周期](../examples/new-api/project-atlas/flows/billing-lifecycle.md)
5. [计费维护者指南](../examples/new-api/project-atlas/learning/billing-maintainer-guide.md)
6. [Token 倍率 Change Brief](../examples/new-api/project-atlas/change-briefs/token-billing-multiplier.md)

也可以在 Repo Confidence 仓库中说：

```text
基于 examples/new-api/project-atlas，带我用中文学习 New API 的计费链路。
先讲五分钟心智模型，再逐步提问我，不要一次输出全部内容。
```

## 团队和公司仓库怎么用

默认建议：

- 先只读分析，不自动写业务仓库；
- 不安装 Git Hooks，不增加 CI 门禁；
- 不把私有源码、密钥或客户数据写入公开案例；
- Project Atlas 可以先保存在个人工作区，团队认可后再提交；
- 普通需求使用 `ambient`，核心计费、权限、迁移再使用详细 Change Brief；
- 每完成几个真实需求，只沉淀新发现的不变量、风险和链路。

使用外部 AI 或 CodeGraph 服务分析公司代码前，应先确认公司的代码、数据和
模型使用政策。

## 当前能力边界

当前版本可以：

- 在一次 Codex 任务中分析仓库和需求；
- 生成 Project Atlas、Flow Card 和 Change Brief；
- 让分析绑定代码证据和 Git 提交；
- 结合真实需求进行维护训练；
- 在不改变开发流程的情况下提供旁路风险提示。

当前版本还不能：

- 跨所有 IDE 永久在线；
- 自动感知每一次文件变化；
- 自动维护跨会话的个人能力档案；
- 保证所有业务行为都已被证明正确；
- 在无人参与判断的情况下产生真实维护信心。

因此最有效的使用方式不是“运行一次生成报告”，而是让它伴随真实需求持续
执行：理解、预测、修改、验证和增量沉淀。
