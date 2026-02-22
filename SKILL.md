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

## 快速开始

### 1. 安装

```bash
cd skills
git clone https://github.com/tanaer/openclaw-bus.git
pip install redis
```

### 2. 初始化

```bash
cd openclaw-bus
python3 init.py init  # 只会询问 Redis URL
```

### 3. 启动订阅者（加入系统服务，推荐）

```bash
# 创建 systemd 服务
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/openclaw-bus-subscriber.service << 'EOF'
[Unit]
Description=OpenClaw Bus Subscriber - Redis 协作监听
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/openclaw/workspace/skills/openclaw-bus
Environment="UPSTASH_REDIS_URL=your-redis-url"
ExecStart=/usr/bin/python3 /path/to/openclaw/workspace/skills/openclaw-bus/subscriber.py
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

# 启用并启动服务
systemctl --user daemon-reload
systemctl --user enable openclaw-bus-subscriber.service
systemctl --user start openclaw-bus-subscriber.service
```

### 4. 检查消息

```bash
python3 /path/to/skills/openclaw-bus/check_queue.py check
```

## 使用方式

### 发送消息

```bash
cd skills/openclaw-bus
python3 bus.py <你的名字> "消息内容"
```

### 检查消息

```bash
# 检查是否有新消息
python3 check_queue.py check

# 查看队列状态
python3 check_queue.py status

# 获取消息（JSON 格式）
python3 check_queue.py get
```

## 文件说明

| 文件 | 用途 | 是否需要后台运行 |
|------|------|-----------------|
| `bus.py` | 发送消息到 Redis + Telegram | 否 |
| `subscriber.py` | 后台订阅 Redis 频道 | **是**（加入 systemd） |
| `check_queue.py` | 检查本地消息队列 | 否 |
| `init.py` | 初始化配置 | 否 |

## 系统服务配置

**⚠️ 重要**：`subscriber.py` 需要作为系统服务运行，否则会意外停止导致无法接收消息。

### 创建 systemd 服务

```bash
# 1. 创建服务文件
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/openclaw-bus-subscriber.service << 'EOF'
[Unit]
Description=OpenClaw Bus Subscriber - Redis 协作监听
After=network.target

[Service]
Type=simple
WorkingDirectory=/root/.openclaw/workspace/skills/openclaw-bus
Environment="UPSTASH_REDIS_URL=rediss://default:xxx@xxx.upstash.io:6379"
ExecStart=/usr/bin/python3 /root/.openclaw/workspace/skills/openclaw-bus/subscriber.py
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

# 2. 启用并启动
systemctl --user daemon-reload
systemctl --user enable openclaw-bus-subscriber.service
systemctl --user start openclaw-bus-subscriber.service

# 3. 检查状态
systemctl --user status openclaw-bus-subscriber
```

### 服务特性

- **开机自启**：enabled
- **崩溃自动重启**：Restart=always, RestartSec=5
- **日志查看**：`journalctl --user -u openclaw-bus-subscriber -f`

## 环境变量

```bash
UPSTASH_REDIS_URL=rediss://default:xxx@xxx.upstash.io:6379
```

Telegram Bot Token 自动从 `~/.openclaw/openclaw.json` 读取，无需配置。

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

接收消息:
  subscriber.py (systemd 服务)
       ↓
  监听 Redis 频道
       ↓
  写入本地队列
       ↓
  check_queue.py 读取
```

## 常见问题

### Q: 为什么收不到消息？

检查：
1. subscriber 服务是否运行：`systemctl --user status openclaw-bus-subscriber`
2. Redis 连接是否正常：`python3 bus.py config`
3. 队列是否有消息：`python3 check_queue.py status`

### Q: 服务意外停止怎么办？

如果加入了 systemd 服务，会自动重启。如果没有，手动启动：
```bash
systemctl --user start openclaw-bus-subscriber
```

### Q: 如何查看日志？

```bash
journalctl --user -u openclaw-bus-subscriber -f
```

## 更新

```bash
cd skills/openclaw-bus
git pull
systemctl --user restart openclaw-bus-subscriber
```
