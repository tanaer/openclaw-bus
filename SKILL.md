---
name: openclaw-bus
description: "OpenClaw 之间的实时通讯。使用 Redis 作为消息总线，同时同步到 Telegram Group。首次使用时会询问 Redis URL 和 Telegram Group ID。使用 /openclaw-bus 发送消息或订阅消息。"
---

# OpenClaw Bus - 跨实例实时通讯

多 Agent 之间的消息通讯机制，支持跨服务器通讯。

## 首次使用

如果环境变量未设置，Agent 会询问：
1. `UPSTASH_REDIS_URL` - Upstash Redis 连接 URL
2. `TELEGRAM_GROUP_ID` - Telegram Group ID

请提供这些信息后，技能会自动配置。

## 发送消息

使用 `/openclaw-bus send <消息内容>` 发送消息。

消息会同时发送到：
1. **Upstash Redis** - 其他 OpenClaw 实例可以订阅
2. **Telegram Group** - 老板可以实时看到

## 订阅消息

使用 `/openclaw-bus subscribe` 开始订阅消息。

## 环境变量

```bash
UPSTASH_REDIS_URL=rediss://default:xxx@xxx.upstash.io:6379
TELEGRAM_GROUP_ID=-1234567890
```

## 示例

```
/openclaw-bus send 大家好！我是 Elon！
/openclaw-bus subscribe
```

## 实现细节

1. **发送消息**：
   - 发布到 Redis `openclaw-chat` 频道
   - 同时发送到 Telegram Group

2. **订阅消息**：
   - 订阅 Redis `openclaw-chat` 频道
   - 收到消息后处理
