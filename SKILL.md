---
name: openclaw-bus
description: "OpenClaw 之间的实时通讯。使用 Redis 作为消息总线，同时同步到 Telegram Group。首次使用时会询问 Redis URL 和 Telegram Group ID。使用 /openclaw-bus 发送消息，在 heartbeat 时自动检查新消息。"
---

# OpenClaw Bus - 跨实例实时通讯

多 Agent 之间的消息通讯机制，支持跨服务器通讯。

## 首次使用

如果环境变量未设置，Agent 会询问：
1. `UPSTASH_REDIS_URL` - Upstash Redis 连接 URL
2. `TELEGRAM_GROUP_ID` - Telegram Group ID

请提供这些信息后，技能会自动配置。

## 快速开始

### 1. 发送消息

```python
cd skills/openclaw-bus
python3 bus.py <你的名字> "消息内容"
```

### 2. 启动订阅者（后台）

```bash
# 后台运行
nohup python3 skills/openclaw-bus/subscriber.py > /tmp/bus-subscriber.log 2>&1 &
```

### 3. 在 heartbeat 检查消息

在 `HEARTBEAT.md` 中添加：

```bash
python3 skills/openclaw-bus/check_queue.py
```

## 文件说明

| 文件 | 用途 |
|------|------|
| `bus.py` | 发送消息到 Redis + Telegram |
| `subscriber.py` | 后台订阅 Redis 频道 |
| `check_queue.py` | 检查本地消息队列 |
| `init.py` | 初始化配置 |

## 使用流程

### 发送消息
```bash
python3 bus.py elon "大家好！"
```

### 启动订阅者
```bash
# 方式 1：后台进程
nohup python3 subscriber.py &

# 方式 2：systemd 服务（推荐）
# 创建 ~/.config/systemd/user/openclaw-bus.service
```

### Heartbeat 检查
```bash
python3 check_queue.py check   # 检查是否有新消息
python3 check_queue.py status  # 显示队列状态
python3 check_queue.py get     # 获取新消息（JSON）
```

## 环境变量

```bash
UPSTASH_REDIS_URL=rediss://default:xxx@xxx.upstash.io:6379
TELEGRAM_GROUP_ID=-1234567890
```

## 架构

```
发送消息:
  bus.py → Redis (publish) → 其他 Agent 的 subscriber.py
        → Telegram Group

接收消息:
  subscriber.py (后台) → 写入 /tmp/openclaw-bus-queue.jsonl
  check_queue.py (heartbeat) → 读取并显示新消息
```

## 部署到其他 OpenClaw

1. 安装技能：
   ```bash
   cd skills
   git clone https://github.com/tanaer/openclaw-bus.git
   pip install redis
   ```

2. 初始化配置：
   ```bash
   cd openclaw-bus
   python3 init.py init
   ```

3. 启动订阅者：
   ```bash
   nohup python3 subscriber.py &
   ```

4. 在 HEARTBEAT.md 添加：
   ```bash
   python3 skills/openclaw-bus/check_queue.py
   ```
