# Linkding 前向验证报告

> 状态：已完成第二个真实仓库前向验证
> 上游提交：[`30510d3463237f0653ea8c1cdbd889c070062566`](https://github.com/sissbruecker/linkding/tree/30510d3463237f0653ea8c1cdbd889c070062566)
> 验证日期：2026-07-11
> 上游许可：[MIT License](https://github.com/sissbruecker/linkding/blob/30510d3463237f0653ea8c1cdbd889c070062566/LICENSE.txt)
> 用途：验证 Repo Confidence 的跨技术栈适用性，不生成第二本代码百科

## 为什么选择 Linkding

[Linkding](https://github.com/sissbruecker/linkding) 是一个可自托管的书签管理
产品。检查时约有 10,826 个 GitHub Stars，主技术栈是 Python/Django，仓库
持续活跃，提供 Docker 部署、数据库迁移、后台任务和较完整的自动化测试。

它适合作为第二个案例，因为：

- 与 New API 的 Go 网关架构明显不同；
- 是一个完整业务产品，不是框架、SDK 或演示项目；
- 438 个文件，规模足以暴露工具问题，但不会再次形成超大型分析工程；
- 包含 REST API、页面路由、Django ORM、Huey 后台任务、SQLite/PostgreSQL、OIDC 和 Auth Proxy；
- MIT 许可清晰，适合作为公开验证材料。

## 本次验证目标

这次没有为 Linkding 生成完整 Project Atlas，而是验证当前仓库盘点器能否：

1. 在 Python/Django 项目中找到结构入口；
2. 控制测试和迁移列表带来的上下文噪声；
3. 区分源码测试与测试资源文件；
4. 为后续核心链路发现提供足够候选；
5. 在不修改目标仓库的情况下完成分析。

## 初始盘点暴露的问题

旧版 `repo_inventory.py` 在 Linkding 上得到：

- 438 个仓库文件；
- 81 个“测试文件”，其中包含 PNG、HTML 等测试资源；
- 55 个迁移文件和 39 个文档候选被完整展开；
- 只识别 `manage.py` 和前端 `index.js`；
- 没有单独指出 Django 路由、后台任务和 ORM 模型。

这些结果虽然没有错到无法使用，但会消耗 AI 上下文，也不足以帮助新人快速
找到业务入口。

## 根据真实反馈完成的改进

### 1. 摘要模式

新增：

```bash
python3 repo_inventory.py /path/to/repository --summary --max-items 12
```

摘要模式保留每类完整计数，只截断展示列表，并通过 `truncated_lists` 明确说明
显示数量和实际总数。

### 2. 结构候选分类

新增三类只读路径提示：

- `route_candidates`：路由和 URL 注册入口；
- `worker_candidates`：任务、Job、Worker 和 Consumer；
- `persistence_candidates`：ORM Model 和 Schema。

在 Linkding 上成功识别：

```text
路由：
- bookmarks/api/routes.py
- bookmarks/urls.py

后台任务：
- bookmarks/services/tasks.py
- bookmarks/tasks.py

持久化：
- bookmarks/models.py
```

### 3. 测试资源过滤

测试目录中只有源码和脚本后缀会进入 `test_files`。PNG、HTML 等 Fixture 资源
不再被误认为测试程序。

Linkding 的测试文件计数从 81 个修正为 78 个。

## 改进后的 Linkding 摘要

| 类别 | 总数 | 摘要展示 |
|---|---:|---:|
| 构建与依赖文件 | 5 | 5 |
| 执行入口 | 2 | 2 |
| 路由候选 | 2 | 2 |
| 后台任务候选 | 2 | 2 |
| 持久化候选 | 1 | 1 |
| 测试源码 | 78 | 12 |
| 数据库迁移 | 55 | 12 |
| 文档候选 | 39 | 12 |

## Evidence Manifest 前向验证

在结构盘点之后，继续运行：

```bash
python3 evidence_manifest.py /path/to/linkding --summary --max-items 12
```

脚本在固定提交上提取到：

| 语义证据 | 数量 |
|---|---:|
| Django / DRF 路由注册 | 58 |
| Huey 风格任务注册 | 10 |
| Django ORM Model | 9 |
| 待核实链路候选 | 77 |

其中包括：

- `bookmarks/urls.py` 中的页面、API、认证、Feed 和管理路由；
- `bookmarks/api/routes.py` 中的 `BookmarkViewSet` 等 Router 注册；
- `bookmarks/services/tasks.py` 中的 favicon、preview、metadata 和快照任务；
- `bookmarks/models.py` 中的 `Bookmark`、`BookmarkAsset`、`UserProfile` 等状态实体；
- 与上述入口按包路径和符号相似度关联的测试、迁移候选。

所有输出仍标记为候选：静态注册不等于完整调用链，测试和迁移关系也只是
启发式关联。下一步由 Skill、CodeGraph 或人工阅读继续验证业务编排、失败
路径和不变量。

## 执行的上游验证

按照上游 [`README`](https://github.com/sissbruecker/linkding/blob/30510d3463237f0653ea8c1cdbd889c070062566/README.md)
和 [`Makefile`](https://github.com/sissbruecker/linkding/blob/30510d3463237f0653ea8c1cdbd889c070062566/Makefile)
安装锁定依赖，并执行三组代表性测试：

```bash
uv sync --frozen
mkdir -p data/assets data/favicons data/previews
uv run pytest \
  bookmarks/tests/test_auth_api.py \
  bookmarks/tests/test_bookmarks_service.py \
  bookmarks/tests/test_bookmarks_tasks.py \
  -q
```

结果：

```text
119 passed in 17.72s
```

第一次直接运行测试时，Huey 因缺少 `data/` 目录而无法初始化 SQLite。上游
`make init` 会创建这些目录；补齐官方前置目录后测试通过。这说明 Project
Passport 必须记录运行命令背后的环境初始化，而不能只复制测试命令。

## 已验证和未验证边界

### 已验证

- 当前盘点器可以用于 Python/Django 单体仓库；
- 摘要模式显著减少大列表输出；
- 路由、后台任务和 ORM 候选识别有效；
- 过滤测试资源后计数更准确；
- 鉴权 API、书签服务和后台任务代表性测试通过；
- 分析和测试没有修改 Linkding 的受 Git 跟踪文件。

### 尚未验证

- 没有生成完整 Linkding Project Atlas；
- 没有运行全部 pytest、Playwright E2E 或性能测试；
- 没有验证 PostgreSQL、OIDC、Auth Proxy 和 Docker 生产部署；
- 路径候选只能帮助定位，不能证明真实调用链；
- 当前语义提取只覆盖 Python 中一组常见注册方式，尚未覆盖动态注册和其他语言；
- Evidence Manifest 只给出调查起点，尚不能自动证明完整业务链路；
- 尚未验证 77 个候选中哪些最具业务中心性，需要结合代码和真实使用排序。

## 对 Repo Confidence 的结论

第二个仓库验证没有证明整个 Skill 已经通用，但证明了正确的迭代方式：

```text
选择不同技术栈的真实仓库
→ 使用现有工具
→ 记录具体失败和噪声
→ 修复通用能力
→ 在原仓库重新验证
```

本轮已经把路径候选推进为标准化 Evidence Manifest。下一步不应扩写
Linkding 百科，而应增加第三种技术栈的语义适配，并验证候选排序能否稳定
帮助新人选出真正值得先学的五到八条链路。
