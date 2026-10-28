# 详细使用与配置指南 (`USAGE.md`)

本文档详细介绍 `misaka-cloud-key` 的工作原理、目录文件约定、各客户端接入方法以及 API 调用示例。

---

## 1. 工作原理与数据流

```text
+-------------------------------------------------------------------+
| 云端电脑 (已登录 Hermes 订阅 + 127.0.0.1:8765 调度服务)           |
|                                                                   |
|  1. 读取 ~/.misaka-agent/pairing/owner-token                      |
|  2. 请求 POST http://127.0.0.1:8765/v1/harness-keys               |
|  3. 读取 ~/.misaka-agent/pairing/public-origin.txt (若存在)       |
|  4. 输出 { openai_base, key_id, api_key }                         |
+-------------------------------------------------------------------+
                                 |
                                 v
+-------------------------------------------------------------------+
| 外部 OpenAI 兼容客户端 (Cursor / OpenAI SDK / 其它客户端)         |
|                                                                   |
|  - Base URL: <openai_base>                                        |
|  - Authorization: Bearer <api_key>                                |
+-------------------------------------------------------------------+
```

### 本地数据目录结构约定

`mint_key.py` 默认读取 `~/.misaka-agent`（可通过环境变量 `HERMES_HOME` 或 `MISAKA_HOME` 覆盖）：

- `<root>/pairing/owner-token`：本机所有者凭证文件（必需）。脚本仅在本地向 `127.0.0.1:8765` 请求签发时读取该文件，**绝不会**将其打印到终端或写入返回结果。
- `<root>/pairing/public-origin.txt`：公网 HTTPS 入口地址文件（可选）。若存在且以 `https://` 开头，脚本会将其拼接 `/v1` 作为 `openai_base`；否则回退为 `http://127.0.0.1:8765/v1`。

---

## 2. 命令行运行与返回格式

在云端电脑上运行：

```bash
python3 /path/to/misaka-cloud-key/mint_key.py
```

标准输出格式如下：

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| `openai_base` | `string` | 供客户端填写的 OpenAI Base URL（已包含 `/v1` 后缀） |
| `key_id` | `string` | 本次签发记录的唯一标识 ID |
| `api_key` | `string` | 供客户端填写的接入凭证（固定以 `misaka-key-` 开头） |

---

## 3. 客户端配置步骤

### 3.1 Cursor 配置

1. 打开 **Cursor Settings** -> **Models**。
2. 添加自定义模型名称（例如 `grok-4.7@high`、`gpt-5@high`、`claude-sonnet-4-5@high` 或 `gemini-2.5-pro`）。
3. 展开 **OpenAI API Key** 与 **Override OpenAI Base URL**：
   - 将 `api_key` 粘贴到 **OpenAI API Key** 输入框。
   - 开启 **Override OpenAI Base URL**，填入 `openai_base`。
4. 点击 **Verify** 或直接在对话面板中选择对应模型即可开始使用。

### 3.2 使用 `curl` 调用示例

```bash
curl -X POST "${OPENAI_BASE}/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${MISAKA_API_KEY}" \
  -d '{
    "model": "grok-4.7@high",
    "messages": [
      {"role": "user", "content": "你好，请介绍一下当前环境。"}
    ]
  }'
```

### 3.3 使用 Python `openai` SDK 调用示例

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://your-cloud-endpoint.example.com/v1",  # 替换为 openai_base
    api_key="misaka-key-...",                               # 替换为 api_key
)

response = client.chat.completions.create(
    model="claude-sonnet-4-5@high",
    messages=[
        {"role": "user", "content": "写一段快速排序的 Python 示例"}
    ],
)

print(response.choices[0].message.content)
```

---

## 4. 思考强度（Reasoning Effort）详解

可以通过以下两种方式控制模型的思考强度：

### 方式 A：模型名后缀（推荐用于 Cursor 等 GUI 客户端）

在模型名后直接添加 `@<档位>`：

- `grok-4.7@none`
- `grok-4.7@minimal`
- `grok-4.7@low`
- `grok-4.7@medium`
- `grok-4.7@high`
- `grok-4.7@xhigh`
- `grok-4.7@max`

### 方式 B：请求参数 `reasoning_effort`（适用于代码调用）

```json
{
  "model": "gpt-5",
  "reasoning_effort": "high",
  "messages": [
    {"role": "user", "content": "分析这段代码的并发安全性"}
  ]
}
```

---

## 5. 工具调用（Tool Calling）行为对比

| 场景 | 请求中是否包含 `tools` | 工具执行方 | 返回内容 |
| :--- | :--- | :--- | :--- |
| **IDE / 客户端本地 Agent 模式**（如 Cursor Agent） | 包含 `tools` | **客户端本地** | 云端返回 `tool_calls`，客户端执行本地工具后将结果发回云端 |
| **纯对话 / 云端托管执行模式** | 不包含 `tools` | **云端 Hermes** | 云端 Hermes 自动执行云端 MCP 与电脑操作，完成后直接返回最终文本 |

---

## 6. 注意事项

1. **不要伪造或截断凭证**：当本机 `127.0.0.1:8765` 未启动或未完成配对时，脚本会以非零状态码退出并输出中文原因，请先启动云端调度服务再重新执行。
2. **多凭证并存**：每次执行 `mint_key.py` 都会生成一把新凭证，旧凭证不会因为生成新凭证而自动失效，便于为不同设备或客户端分配独立的 `key_id`。
