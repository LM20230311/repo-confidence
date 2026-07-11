# Roadmap

Repo Confidence 的路线图围绕三个目标展开：建立项目地图、训练维护能力、持续校准信心。

## Phase 0：理念与最小可用工具

- [x] 定义 Ownership Gap 和维护信心模型；
- [x] 定义 Project Atlas、Flow Card、Change Brief、Confidence Loop；
- [x] 创建 `repository-onboarding-coach` Skill；
- [x] 创建通用 Project Atlas 模板；
- [x] 创建只读仓库盘点脚本；
- [x] 定义 L1～L4 维护能力等级。

## Phase 1：真实仓库可用

- [ ] 使用三个不同技术栈的公开仓库进行前向验证；
- [x] 完成第二个 Python/Django 仓库前向验证，并根据结果修复盘点噪声；
- [ ] 改进对后端、前端、CLI、数据项目和 Monorepo 的识别；
- [x] 增加基于显式注册的核心链路初步候选发现（当前优先支持 Python）；
- [x] 增加测试、迁移与入口之间的启发式关联提示；
- [x] 输出标准化 Evidence Manifest；
- [x] 提供一个完整的公开 Project Atlas 示例（New API）。

## Phase 2：增量刷新

- [x] 根据验证提交和显式证据路径计算初步知识影响范围；
- [ ] 检测关键符号、路由、表和配置变化；
- [x] 标记证据文件发生变化、可能需要复核的 Flow Card；
- [ ] 提供 CI 检查和 Pull Request 提示；
- [ ] 支持人工确认后更新验证提交。

## Phase 3：交互式维护训练

- [ ] 根据仓库自动生成 Teach Back 问题；
- [ ] 生成需求推演和故障演练；
- [ ] 记录个人能力矩阵，但避免提交个人隐私；
- [ ] 根据真实任务更新 L1～L4 能力判断；
- [ ] 提供团队 onboarding 路径建议。

## Phase 4：生态扩展

- [ ] 支持更多 AI Agent；
- [ ] 提供 IDE 集成；
- [ ] 提供 GitHub/GitLab Pull Request 集成；
- [ ] 为主流语言和框架提供专项参考包；
- [ ] 建立可复现的 onboarding 评测基准；
- [ ] 发布团队级 dashboard。

## 近期优先事项

1. 在真实陌生仓库中验证 Skill 是否能形成准确、可用的 Atlas；
2. 验证新人使用 Atlas 后是否更能预测真实需求影响；
3. 找出哪些内容应该自动生成，哪些必须人工确认；
4. 让增量刷新足够轻量，避免知识库成为新的维护负担；
5. 收集 AI 修改成功但人仍然不放心的真实案例。

## 非目标

当前阶段不计划：

- 替代 IDE、CodeGraph 或代码搜索工具；
- 自动证明所有代码行为正确；
- 为仓库生成完整逐文件百科；
- 用考试分数替代真实维护能力；
- 强制所有团队采用同一种文档结构；
- 在未授权的情况下把私有代码上传到外部服务。
