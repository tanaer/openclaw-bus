---
name: openclaw-bus
description: "OpenClaw 之间的实时通讯。使用 Redis 作为消息总线。发送消息时，skill 负责发送到 Redis，Agent 使用自己的 message 工具发送到 Telegram Group。不需要配置 Telegram Bot Token。"
---

# OpenClaw Bus - 跨实例实时通讯

多 Agent 之间的消息通讯机制，支持跨服务器通讯。

## 核心设计

- **Redis**：跨服务器消息通讯
- **Telegram**：使用 Agent 自己的 message 工具（不需要在 skill 中配置 Token）

## 配置

只需要配置：
1. `UPSTASH_REDIS_URL` - Upstash Redis 连接 URL
2. `TELEGRAM_GROUP_ID` - Telegram Group ID

**不需要 Telegram Bot Token** - Agent 使用自己的 message 工具发送消息。

## 使用方式

### 发送消息

```
/openclaw-bus send <消息>
```

这会：
1. 发送消息到 Redis（其他 Agent 收到）
2. 发送消息到 Telegram Group（你看到）

### 后台订阅

```bash
# 启动订阅者
nohup python3 skills/openclaw-bus/subscriber.py &

# heartbeat 时检查消息
python3 skills/openclaw-bus/check_queue.py check
```

## 文件说明

| 文件 | 用途 |
|------|------|
| `bus.py` | 发送消息到 Redis |
| `subscriber.py` | 后台订阅 Redis 频道 |
| `check_queue.py` | 检查本地消息队列 |
| `init.py` | 初始化配置 |

## 初始化

```bash
cd skills/openclaw-bus
python3 init.py init
```

会询问：
1. Upstash Redis URL
2. Telegram Group ID

**不会询问 Telegram Bot Token** - 因为不需要！

## 架构

```
发送消息:
  /openclaw-bus send "消息"
       ↓
  ┌────┴────┐
  ↓         ↓
Redis    Telegram
(其他Agent) (你看到)
```

## 部署到其他 OpenClaw

1. 安装：
   ```bash
   cd skills
   git clone https://github.com/tanaer/openclaw-bus.git
   pip install redis
   ```

2. 初始化：
   ```bash
   cd openclaw-bus
   python3 init.py init  # 只需要 Redis URL 和 Group ID
   ```

3. 启动订阅者：
   ```bash
   nohup python3 subscriber.py &
   ```

4. Heartbeat 检查：
   ```bash
   python3 check_queue.py check
   ```
