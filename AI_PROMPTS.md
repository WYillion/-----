# AI Prompt 与问题解决记录

> 本文件记录开发过程中如何借助 AI 辅助思考（而非代劳），以及遇到的关键问题与解决思路。

## 一、使用的 AI Prompt 思路

开发过程中主要用 AI 做了三件事，每件事都先自己想清目标再提问，AI 输出后自己 review 与验证：

1. **方案选型咨询**
   - "Python 下安全地实现数学表达式求值器、避免 eval 注入，有哪些方案？"
   - 结果：确认 `ast` 白名单静态树遍历是标准做法，据此实现 `calculator`。
   - 自己把关的点：只允许 `Constant + BinOp + UnaryOp` 及明确的白名单运算符，其余节点一律拒绝，并补了注入类测试用例。

2. **协议细节确认**
   - "OpenAI-compatible 的 tool_calls 回填格式、以及 DeepSeek 是否支持 role=tool？"
   - 结果：确认 assistant 消息需带 `tool_calls`、结果用 `role=tool + tool_call_id` 回填，DeepSeek 兼容该格式。
   - 自己把关的点：解析层对非法 JSON arguments、缺失 choices 做了降级和容错。

3. **设计权衡讨论**
   - "有状态工具如何在多 session 之间隔离？把状态放全局还是放 session 里？"
   - 结果：确认状态应归属 session，通过让工具 `run(session, ...)` 接收 session、状态写入 `session.state` 实现隔离。

## 二、问题解决记录

| # | 问题 | 定位过程 | 解决方案 |
|---|---|---|---|
| 1 | 终端 `python --version` 无输出 | Windows 下 `python` 指向 Store stub | 改用 anaconda 完整路径 `C:/Users/nextc/anaconda3/python.exe` |
| 2 | 单元测试报 `TestTodoTool.run() takes 1 positional argument but 2 were given` | 自定义方法 `run` 覆盖了 `unittest.TestCase.run` | 测试辅助方法重命名为 `do` |
| 3 | 计算器 `test_syntax_error` 断言 `1++2` 会报语法错但实际没报 | `1++2` 其实是合法表达式（一元正号），`ast.parse` 能解析 | 改用真正非法表达式 `1+` 作为测试用例 |
| 4 | 上下文压缩测试 `StopIteration` | 压缩时 `_summarize` 也会调用 `llm.chat`，额外消耗了 mock 的 `side_effect` 队列 | 用带分支的 `side_effect` 函数，按是否传 `tools` 区分摘要调用与主循环调用 |
| 5 | 如何防死循环 | 工具执行失败若静默丢弃会让模型反复重试 | 工具异常被捕获后转为 `工具执行错误: ...` 文本回填，让模型知情并收敛；同时 `max_steps` 硬性兜底 |

## 三、关键设计决策

- **零第三方依赖**：LLM 调用用标准库 `urllib` 直连，而非引入 openai SDK，更贴合"从零实现核心 Runtime"。
- **解析与执行解耦**：`parse_step` 只负责把响应转成 `Step`（思考/工具调用/答案），执行决策全部在 `Agent.run` 主循环里，职责清晰、易测试。
- **思考过程不进 context**：`reasoning_content` 只写日志，不回填消息，节省 token 且不干扰后续模型。
- **压缩是"滚动摘要"而非"逐轮重写"**：只在超阈值时把中间部分压成一条摘要，保留最近原文，兼顾连贯性与成本。