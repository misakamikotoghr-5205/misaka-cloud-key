# Misaka Cloud Key (`misaka-cloud-key`)

在已登录 Hermes 订阅的云端电脑上签发 OpenAI 兼容格式接入信息，供 **Cursor** 及任意 OpenAI 兼容客户端接入使用。

---

## 目录

- [功能简介](#功能简介)
- [目录结构](#目录结构)
- [环境前提](#环境前提)
- [快速开始](#快速开始)
  - [方式一：作为 Hermes Skill 调用](#方式一作为-hermes-skill-调用)
  - [方式二：命令行直接运行](#方式二命令行直接运行)
- [接入客户端配置（以 Cursor 为例）](#接入客户端配置以-cursor-为例)
- [模型路由与思考强度](#模型路由与思考强度)
- [工具调用机制（Tools & MCP）](#工具调用机制tools--mcp)
- [更多文档](#更多文档)
- [常见问题排查](#常见问题排查)
- [License](#license)

---

## 功能简介

`misaka-cloud-key` 是一个面向 Hermes 环境的 Skill 与命令行工具：

- **本地凭证安全隔离**：模型订阅与登录状态保留在云端电脑本地，不写入签发结果，也不会在终端输出所有者凭证。
- **标准 OpenAI 兼容接口**：自动获取云端公网入口（或本地回环地址）并拼接 `/v1` 路径，返回标准 `openai_base` 与接入标识。
- **多模型家族路由**：支持通过单一接入点按模型前缀调用 `grok`、`gpt`、`claude`、`gemini` 四大模型系列。
- **灵活的思考强度控制**：支持通过请求参数 `reasoning_effort` 或模型名后缀（如 `@high`）指定推理档位。
- **双向工具协同**：支持客户端本地 `tools` 透传执行，也支持无客户端工具时由云端 Hermes 自动接管 MCP 与电脑操作。

---

## 目录结构

```text
misaka-cloud-key/
├── SKILL.md          # Hermes Skill 定义与执行规范说明
├── mint_key.py       # 签发脚本（零第三方依赖，基于 Python 3 标准库）
├── README.md         # 项目主文档
├── docs/
│   └── USAGE.md      # 详细接入指南、调用示例与架构说明
└── LICENSE           # MIT 开源许可证
```

---

## 环境前提

1. **运行位置**：必须在已安装 **Hermes** 的云端电脑本机运行（其他客户端系统仅使用签发结果，不运行本仓库脚本）。
2. **订阅登录**：需要使用的模型订阅已在云端电脑的 Hermes 中完成登录：
   - 若需调用 Gemini 模型，请确保云端 Hermes 环境中已配置 `GEMINI_API_KEY`。
3. **调度服务就绪**：本机 `127.0.0.1:8765` 的云端调度服务处于监听状态，且已完成 MISAKA 一键自动连接（存在所有者配对文件）。
4. **Python 环境**：Python 3.8+（仅使用标准库，无需额外 `pip install`）。

---

## 快速开始

### 方式一：作为 Hermes Skill 调用

将本项目放入 Hermes 的 Skills 目录中：

```bash
cp -r misaka-cloud-key ~/.hermes/skills/
```

随后在对话中直接向 Agent 发送指令，例如：

- “帮我生成一把接入 Cursor 的钥匙”
- “生成中转站 key 和 OpenAI base URL”

### 方式二：命令行直接运行

在云端电脑终端中直接执行 `mint_key.py`（与当前工作目录无关）：

```bash
python3 mint_key.py
```

#### 环境变量说明（可选）

脚本按以下优先级查找主目录：

1. `HERMES_HOME`
2. `MISAKA_HOME`
3. 默认路径 `~/.misaka-agent`

#### 输出示例

执行成功后，脚本会向标准输出（stdout）打印一行 JSON：

```json
{
  "openai_base": "https://your-cloud-endpoint.example.com/v1",
  "key_id": "hk_01J...",
  "api_key": "misaka-key-..."
}
```

> **注意**：每运行一次 `mint_key.py` 都会新签发一组接入凭证；除非手动清理，此前签发的旧凭证依然保持有效。

---

## 接入客户端配置（以 Cursor 为例）

拿到脚本输出的 JSON 后，在 **Cursor** 或其他支持自定义 OpenAI 接口的客户端中按如下方式填写：

| 客户端配置项 | 填写内容 |
| :--- | :--- |
| **OpenAI Base URL** | 填入输出 JSON 中的 `openai_base` 字段 |
| **OpenAI API Key** | 填入输出 JSON 中的 `api_key` 字段（以 `misaka-key-` 开头） |
| **模型名称 (Model)** | 按需填入目标模型名（支持携带 `@档位` 后缀，见下表） |

---

## 模型路由与思考强度

客户端在每次发起请求时可自由指定模型名称与思考强度（Reasoning Effort）：

### 1. 模型前缀与后端路由对应关系

| 模型名前缀 | 路由目标后端 | 示例模型名称 |
| :--- | :--- | :--- |
| `grok` | xAI | `grok-4.7`, `grok-4.7@high` |
| `gpt` | Codex | `gpt-5`, `gpt-5@xhigh` |
| `claude` | Claude | `claude-sonnet-4-5`, `claude-opus-4-5@max` |
| `gemini` | Gemini | `gemini-2.5-pro`, `gemini-2.5-pro@high` |

### 2. 思考强度档位

支持以下 7 个思考强度档位：

`none` · `minimal` · `low` · `medium` · `high` · `xhigh` · `max`

**指定方式（二选一）：**

1. **模型名后缀**：直接在模型名称后追加 `@<档位>`，例如 `grok-4.7@high`。
2. **请求体参数**：在 OpenAI Chat Completions 请求 JSON 中传入 `"reasoning_effort": "high"`。

---

## 工具调用机制（Tools & MCP）

云端调度服务会根据请求体中是否包含 `tools` 自动切换工作模式：

- **客户端带 `tools` 请求**：当客户端（如 Cursor）将本地 MCP 或文件/终端操作放入 OpenAI 请求的 `tools` 字段发送时，云端会将模型生成的 `tool_calls` 原样交回客户端，由客户端在本地执行后再把工具结果发回云端继续推理。
- **客户端不带 `tools` 请求**：当请求中不包含 `tools` 时，MCP 与电脑操作由云端电脑上的 Hermes 直接执行，执行完毕后向客户端返回最终文本响应。

---

## 更多文档

详细的配置步骤、代码调用示例（Python OpenAI SDK / `curl`）以及工作流说明请参阅：

- [详细使用与配置说明 (`docs/USAGE.md`)](./docs/USAGE.md)
- [Skill 规范定义 (`SKILL.md`)](./SKILL.md)

---

## 常见问题排查

| 错误提示 | 原因分析 | 解决方法 |
| :--- | :--- | :--- |
| `这台电脑还没有云端所有者凭证。先在 MISAKA 里完成一键自动连接。` | 主目录下缺少 `pairing/owner-token` 文件 | 先在云端电脑的 MISAKA 客户端完成一键自动连接配对 |
| `本机 8765 上的云端调度没有开，无法签发钥匙。` | 本机 `127.0.0.1:8765` 未监听 | 先启动云端调度服务，确认 8765 端口处于监听状态后再运行脚本 |
| `云端没有返回接入钥匙。` | 调度接口返回格式异常或未包含有效字段 | 检查云端调度服务版本与运行日志是否正常 |
| Gemini 模型调用报错 | 云端 Hermes 缺少 Gemini 凭证 | 在云端 Hermes 环境中配置有效的 `GEMINI_API_KEY` |

---

## License

本项目采用 [MIT License](./LICENSE) 开源。
