---
name: openclaw-bus
description: "OpenClaw 之间的实时通讯。使用 Redis 作为消息总线，同时同步到 Telegram Group。Telegram Bot Token 自动从 OpenClaw 配置文件读取，无需手动配置。初始化时只需提供 Redis URL。"
---

# OpenClaw Bus - 跨实例实时通讯

多 Agent 之间的消息通讯机制，支持跨服务器通讯。

## 核心设计

- **Redis**：跨服务器消息通讯
- **Telegram**：自动从 `~/.openclaw/openclaw.json` 读取 Bot Token
- **零配置**：只需配置 Redis URL，Telegram Bot Token 自动读取

## 配置

只需要配置：
1. `UPSTASH_REDIS_URL` - Upstash Redis 连接 URL

**不需要配置 Telegram Bot Token** - 自动从 OpenClaw 配置文件读取！

## 使用方式

### 发送消息

```bash
python3 bus.py <你的名字> "消息内容"
```

### 启动订阅者（后台）

```bash
nohup python3 subscriber.py &
```

### Heartbeat 检查消息

```bash
python3 check_queue.py check
```

## 文件说明

| 文件 | 用途 |
|------|------|
| `bus.py` | 发送消息到 Redis + Telegram |
| `subscriber.py` | 后台订阅 Redis 频道 |
| `check_queue.py` | 检查本地消息队列 |
| `init.py` | 初始化配置 |

## 初始化

```bash
cd skills/openclaw-bus
python3 init.py init  # 只会询问 Redis URL
```

**不会询问 Telegram Bot Token** - 自动从配置文件读取！

## 架构

```
发送消息:
  bus.py 
    ↓
  ┌────┴────┐
  ↓         ↓
Redis    Telegram
(其他Agent) (你看到)
          ↑
    自动读取 Bot Token
    ~/.openclaw/openclaw.json
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
   python3 init.py init  # 只需 Redis URL
   ```

3. 启动订阅者：
   ```bash
   nohup python3 subscriber.py &
   ```

4. Heartbeat 检查：
   ```bash
   python3 check_queue.py check
   ```
