# minagent — 从零实现的最小可用 Agent

一个不依赖任何 Agent 框架（langgraph / openhands / openclaw）的最小可用 Agent Runtime。
核心 Agent Runtime 自行实现，LLM 通过标准库直连 OpenAI-compatible 接口（可配置任意端点）。

- 语言：Python（>=3.9，零第三方依赖，仅标准库）

---

## 一、运行方式

### 1. 配置（必须）

复制 `.env.example` 为 `.env` 并填入真实值（`.env` 已在 `.gitignore` 中，**不会上传 GitHub**）：

```bash
# 或直接设置环境变量

# Linux / macOS
export MINAGENT_API_KEY="你的密钥"

# Windows PowerShell
$env:MINAGENT_API_KEY="你的密钥"
```

可选配置（均有默认值，见 `.env.example`）：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `MINAGENT_API_KEY` | — | API 密钥（必填，放在 `.env` 或环境变量，勿硬编码） |
| `MINAGENT_BASE_URL` | `https://note3-prev-api.askdiandian.com/v1` | OpenAI-compatible 端点 |
| `MINAGENT_MODEL` | `dots3-note-prev` | 模型名 |
| `MINAGENT_AUTH_HEADER` | `api-key` | 认证请求头名 |
| `MINAGENT_AUTH_PREFIX` | 空 | 认证值前缀（如 `Bearer `），本接口留空 |
| `MINAGENT_MAX_TOKENS` | `0` | 0 表示不限制；>0 时限制最大生成 token |
| `MINAGENT_MAX_STEPS` | `10` | 单轮回合内最大工具调用轮次 |
| `MINAGENT_MAX_CONTEXT_MESSAGES` | `20` | 消息数超过该阈值触发压缩 |
| `MINAGENT_KEEP_RECENT_MESSAGES` | `6` | 压缩时保留最近原文条数 |
| `MINAGENT_TIMEOUT` | `60` | HTTP 超时秒数 |

### 2. 安装

无第三方依赖，Python 3.9+ 即可：

```bash
# 无需 pip install，直接运行
```

### 3. 启动交互式对话

```bash
python -m minagent
```

交互命令：

- 直接输入消息开始对话
- `/new` — 新建一个 session 并切换过去
- `/list` — 列出所有 session
- `/switch <id>` — 切换回指定 session 继续聊
- `/exit` — 退出

### 4. 运行测试

```bash
python -m unittest discover -s tests -v
```

---

## 二、系统设计

### 整体架构

```
CLI (__main__.py)
        │
        ▼
┌─────────────────────────────────────────┐
│  Agent (agent.py)  —— ReAct 主循环        │
│    run(session, user_input) -> str        │
└───────┬──────────────────────┬───────────┘
        │                      │
        ▼                      ▼
┌───────────────┐      ┌──────────────────────┐
│ LLMClient      │      │ ToolRegistry          │
│ (llm.py)       │      │ (tools/registry.py)   │
│ 直连 LLM API   │      │ calculator/search/todo │
└───────────────┘      └──────────────────────┘
        │
        ▼
┌─────────────────────────────────────────┐
│ Session (session.py)  —— 消息历史 + 工具状态 │
│ SessionManager —— 多窗口隔离               │
│ memory.py —— token 估算 + 对话压缩          │
└─────────────────────────────────────────┘
```

### 核心循环（要求 2）

完全按题目要求实现四步 Loop：

1. **接收用户输入**：`session.add_user(input)`
2. **判断直接回复还是调用工具**：交给 LLM，解析其返回的 `tool_calls` 或 `content`
3. **调用工具**：按 `tool_calls` 执行对应工具，结果以 `role=tool` 回填
4. **判断继续 loop 还是返回**：有 `tool_calls` 则继续循环，有最终 `content` 则返回给用户；超过 `max_steps` 抛 `MaxStepsExceeded`

### 工具注册机制

每个工具包含：`name` / `description` / `parameters`（JSON Schema）/ `func`。

- `ToolRegistry.register()` 注册，重复注册抛错
- `ToolRegistry.to_openai_list()` 生成 OpenAI-compatible 的 `tools` 参数
- `ToolRegistry.execute(name, arguments, session)` 执行，参数不匹配抛 `ToolError`
- LLM 基于 Schema 自主决策是否调用、调用哪个工具

内置三个工具：

| 工具 | 说明 |
|---|---|
| `calculator` | AST 安全求值，无 `eval` 注入风险，支持 `+ - * / // % **` |
| `search` | mock 实现，返回模拟搜索结果 |
| `todo` | 有状态工具，`add/list/done/remove`，状态按 session 隔离 |

### LLM 输出解析

`parse_step()` 从一轮响应中提取三种候选：

- `reasoning_content`（思考过程）— 仅部分推理模型返回
- `tool_calls`（工具调用）— 非法 JSON arguments 降级为空 dict
- `content`（最终答案）

解析后由主循环决定是执行工具还是结束。

### session 管理（要求 2）

- `Session` 持有独立的消息历史与工具状态 `state`
- `SessionManager` 按 `session_id` 隔离，用户 A 的窗口 1（加日历）与窗口 2（加联系人）互不影响，可随时 `/switch` 回去继续聊
- 有状态工具（todo）把数据写在 `session.state` 中，天然按窗口隔离

### context 有效管理（要求 2）

- **最大轮次限制**：`max_steps` 限制单次输入内的工具循环上限，防止死循环
- **记住之前的状态**：完整消息历史 + 工具状态常驻 session，天然支持追问（纯对话追问、带工具追问）
- **哪些信息塞入 context**：system prompt（角色/工具介绍）、用户输入、assistant 回复、工具调用参数与工具执行结果；思考过程 `reasoning_content` 不塞回 context（省 token），仅写入日志
- **基础压缩**：当消息数超过 `max_context_messages`，保留 system 与最近 `keep_recent_messages` 条原文，中间部分由 LLM 压缩成一条 `[早期对话摘要]`，摘要失败回退为原文

---

## 三、memory 的召回时机与放置方式说明

### 当前实现（基础版）

**放置方式（写入时机）**：

1. **对话历史**：每轮用户/助手/工具消息即时追加进 `session.messages`
2. **工具状态**：有状态工具（todo）在执行时写入 `session.state`，随 session 生命周期保留
3. **早期摘要**：当消息数超过阈值触发压缩，把旧对话写成一条 system 消息 `[早期对话摘要]`，放在 system prompt 之后、最近原文之前

**召回时机（放置位置）**：

- 短对话：全量在 context 内，无需召回
- 长对话：超过阈值才触发压缩，把"需要保留的早期信息"以摘要形式常驻 context，配合最近原文，保证后续对话能延续上下文
- 有状态工具数据：不占 context，但通过 `session.state` 在工具执行时可读可写

### 后续可扩展方向（对应架构设计题模块二）

当前为基础版（滚动摘要 + 工具状态），可在此基础上扩展为三层 memory：

```
短期（上下文内原文）
  ▲ 超过阈值滚动压缩
中期（滚动摘要，常驻 context）
  ▲ 结构化抽取
长期（结构化事实/用户画像 → 向量库，按需检索召回）
```

即：**写入时**抽取用户偏好/事实存储 + 滚动摘要；**召回时**根据当前 query 做语义/关键词混合检索，只注入 top-k 相关记忆，而非全量塞入。详见 `架构设计题答案.md` 模块二。

---

## 四、目录结构

```
minagent/
  __init__.py
  __main__.py      # CLI 入口
  config.py        # 环境变量配置
  models.py        # ToolCall / Step 数据模型
  llm.py           # LLMClient + parse_step 输出解析
  agent.py         # ReAct 主循环（核心 Runtime）
  session.py       # Session + SessionManager
  memory.py        # token 估算 + 对话压缩
  tools/
    __init__.py
    base.py        # Tool 抽象 + ToolError
    registry.py    # 工具注册表
    calculator.py  # AST 安全计算器
    search.py      # mock 搜索
    todo.py        # 有状态待办
tests/             # 47 个单元测试（mock LLM，无需真实 API）
```