---
name: misaka-cloud-key
description: "在已登录 Hermes 订阅的云端电脑上签发一把 OpenAI 格式接入钥匙，供 Cursor 等任意 OpenAI 兼容客户端使用。用户说生成钥匙、中转站 key、OpenAI base URL、接入 Cursor 时使用。"
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [misaka, openai, api-key, relay]
    category: autonomous-ai-agents
    requires_toolsets: [terminal]
---

# Misaka 云端钥匙

## When to Use

在这台云端电脑上签发接入钥匙。别的系统只使用签发结果，不运行本 skill。

## 前提

这台电脑已经装好 Hermes，并且要用的订阅已经在 Hermes 里登录。模型登录留在这台电脑，不写进钥匙。

## Procedure

1. 确认本机 `127.0.0.1:8765` 的调度服务在监听。没有监听时不要编造钥匙，告诉用户先把云端调度打开。
2. 用终端运行本目录里的 `mint_key.py`。工作目录无关。它只读取本机所有者凭证，不会把凭证打印出来。
3. 脚本成功时向标准输出打印一个 JSON 对象，字段是 `openai_base`、`key_id`、`api_key`。
4. 把 `openai_base` 和 `api_key` 交给用户。`api_key` 以 `misaka-key-` 开头。不要改写、截断或另外发明一把钥匙。
5. 告诉用户：在 Cursor 或其他 OpenAI 兼容客户端里，Base URL 填 `openai_base`，API Key 填 `api_key`。模型名和思考强度由客户端在每次请求里选择。`grok` 走 xAI，`gpt` 走 Codex，`claude` 走 Claude，`gemini` 走 Gemini。思考强度用请求里的 `reasoning_effort`，或写在模型名后面，例如 `grok-4.7@high`。档位是 `none`、`minimal`、`low`、`medium`、`high`、`xhigh`、`max`。

## 客户端怎么用这把钥匙

客户端把 MCP、电脑操作放进 OpenAI 的 `tools` 发过来。云端把 `tool_calls` 交回客户端，客户端执行后再把工具结果发回。请求里没有工具时，MCP 和电脑操作由这台云端电脑上的 Hermes 执行，最后返回文字。

## Pitfalls

- 脚本失败时原样转告那句中文原因，不要换成一把假钥匙。
- Gemini 需要这台 Hermes 里已有 `GEMINI_API_KEY`。没有时不要假装已经登录。
- 每运行一次脚本就新签发一把钥匙。旧钥匙仍然有效，除非用户要求只保留最新一把。
