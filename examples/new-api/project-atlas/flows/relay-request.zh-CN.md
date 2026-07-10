# 链路：同步模型转发

> 状态：部分验证
> 最近验证提交：[`4e570389`](https://github.com/QuantumNous/new-api/tree/4e570389dd433a717373ce9c9b822b59f5ed3d5d)
> 证据：[E2、E5～E11](../evidence.md)
> 尚未验证：没有调用真实供应商，也没有执行端到端流式请求
>
> [English version](relay-request.md)

## 核心心智模型

转发控制器负责一次请求的完整事务：校验客户端协议、预估用量和价格、预扣
额度、尝试一个或多个渠道、让选中的 Adaptor 转换协议并调用供应商、按实际
Usage 结算，最后返回与客户端协议兼容的响应。

## 入口

- OpenAI 兼容：`/v1/chat/completions`、`/v1/responses`、Embedding、图片、音频、Rerank 和 Realtime。
- Claude 兼容：`/v1/messages`。
- Gemini 兼容：`/v1beta/models/*path`。
- 路由链：性能检查 → `TokenAuth` → 模型限流 → `Distributor` → `controller.Relay`。

## 正常路径

1. `Distributor` 提取请求模型，校验 Token 的模型限制并选择初始渠道。
2. `controller.Relay` 校验对应协议的请求结构。
3. `RelayInfo` 保存用户、Token、分组、模型、重试和请求元数据。
4. 按配置执行敏感词检查和 Token 预估。
5. `ModelPriceHelper` 冻结价格输入并计算预扣额度。
6. `BillingSession` 预扣 Token 额度以及钱包或订阅额度。
7. 控制器进入有限次数的重试循环，每次重新设置选中渠道的上下文。
8. 协议 Helper 创建供应商 Adaptor，映射模型和请求字段并发送上游请求。
9. Adaptor 把响应和 Usage 归一化。
10. 文本、音频或图片结算逻辑计算实际额度、更新账务并写消费日志。

## 状态变化

| 状态 | 变化 |
|---|---|
| 钱包或订阅 | 预扣，然后按差额结算或退款 |
| Token 额度 | 预扣，然后按差额结算或退款 |
| 渠道健康 | 错误可能异步禁用单个 Key 或整个渠道 |
| 用量与日志 | 写消费或错误记录，并更新聚合计数 |
| 渠道亲和性 | 成功渠道可能被缓存，供相关请求继续使用 |

## 失败路径

- 参数校验、计价和权限错误会标记为不可重试。
- 请求体会被保存，以便每次重试重新读取；过大的请求体返回 HTTP 413。
- 供应商错误会先归一化，再根据配置的状态码判断是否重试。
- 预扣后失败会调用 `BillingSession.Refund`，除非会话已经完成结算。
- 错误日志包含请求和渠道元数据；敏感字段会脱敏或只对管理员显示。

## 流式边界

代码中存在流状态跟踪和供应商专用的流解析器，但当前案例没有证明所有供应商
在第一个 Chunk 已经发送给客户端之后都能安全处理失败。因此，修改“输出后
重试”和流式 Usage 提取属于高风险变更。

## 不变量

- 同一个请求体必须能在多次重试中重复读取。
- 价格和资金来源必须在调用上游前确定。
- 实际 Usage 必须使用当前请求开始时的计费快照结算。
- 失败请求不能残留未结算的预扣额度，除非明确收取违规费用。
- 客户端看到的协议格式必须与请求的转发格式一致。

## 测试边界

已执行的 `relay`、`relay/common`、`relay/helper`、`service` 和
`pkg/billingexpr` 测试通过。OpenAI、Claude、Gemini、AWS、Moonshot、
MiniMax、Ollama 和任务适配器存在专项测试，但本案例没有执行所有供应商包。
