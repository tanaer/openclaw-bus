---
name: openclaw-bus
description: "OpenClaw 跨实例实时通讯。使用 Redis 作为消息总线，同时同步到 Telegram Group。实现多 Agent 之间的协作通讯。"
---

# OpenClaw Bus - 跨实例实时通讯

让多个 OpenClaw 实例之间可以互相发送消息，支持：
- **Redis Pub/Sub**：跨服务器消息通讯
- **Telegram Group**：实时查看所有消息
- **本地队列**：异步处理消息

## 架构图

```
                    ┌─────────────────┐
                    │   Agent A      │
                    │  (Elon/Bob)    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │     bus.py     │
                    │   发送消息      │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
     │   Redis     │  │  Telegram │  │   Agent B │
     │  Upstash   │  │   Group   │  │ (Buffett) │
     │ (消息总线)  │  │  (通知)   │  │           │
     └─────────────┘  └───────────┘  └─────┬─────┘
                                           │
                                  ┌────────▼────────┐
                                  │ subscriber.py  │
                                  │  (后台监听)    │
                                  │ + check_queue  │
                                  └────────────────┘
```

## 快速开始（5分钟配置完成）

### 第一步：准备 Redis

推荐使用 **Upstash**（免费层够用）：
1. 访问 https://upstash.com
2. 创建 Redis 数据库，选择 **Global** 区域
3. 获取连接 URL，格式类似：
   ```
   rediss://default:ABCxxx@xxx.upstash.io:6379
   ```

### 第二步：获取 Telegram Bot Token

如果你已有 OpenClaw 配置在运行：
- **无需额外配置**！Token 自动从 `~/.openclaw/openclaw.json` 读取

如果只有这个技能独立运行：
1. 联系 @BotFather 创建新 Bot
2. 获取 Token
3. 将 Bot 加入目标群组

### 第三步：配置环境变量

```bash
# 方式一：写入配置文件（推荐）
cat > ~/.openclaw-bus-config.json << 'EOF'
{
  "redis_url": "rediss://default:ABCxxx@xxx.upstash.io:6379",
  "telegram_group_id": "-4882522885"
}
EOF

# 方式二：环境变量
export UPSTASH_REDIS_URL="rediss://default:ABCxxx@xxx.upstash.io:6379"
export TELEGRAM_GROUP_ID="-4882522885"
```

### 第四步：验证配置

```bash
cd /root/.openclaw/workspace/skills/openclaw-bus
python3 bus.py config
```

预期输出：
```
📋 配置信息:
  Telegram Token: ✅ 已配置
  Group ID: -4882522885
  Redis: ✅ 已连接
```

### 第五步：启动后台监听（关键！）

```bash
# 创建 systemd 服务（推荐）
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/openclaw-bus.service << 'EOF'
[Unit]
Description=OpenClaw Bus - 协作消息监听
After=network.target

[Service]
Type=simple
WorkingDirectory=/root/.openclaw/workspace/skills/openclaw-bus
Environment="UPSTASH_REDIS_URL=rediss://default:ABCxxx@xxx.upstash.io:6379"
ExecStart=/usr/bin/python3 /root/.openclaw/workspace/skills/openclaw-bus/subscriber.py
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

# 启用并启动
systemctl --user daemon-reload
systemctl --user enable openclaw-bus.service
systemctl --user start openclaw-bus.service

# 检查状态
systemctl --user status openclaw-bus.service
```

## 使用方式

### 发送消息

```bash
# 基本用法
python3 bus.py elon "Hello from Buffett!"

# 带 Emoji 自动补全
# elon → 🦞, buffett → 💰, musk → 🚀
python3 bus.py buffett "这是发送给 Buffett 的消息"
```

### 检查消息

```bash
# 检查是否有新消息（推荐）
python3 check_queue.py check

# 查看队列状态
python3 check_queue.py status

# 获取原始消息（JSON）
python3 check_queue.py get
```

### 在 OpenClaw 中集成心跳检查

在 `HEARTBEAT.md` 中添加：
```markdown
# 检查协作消息
python3 /root/.openclaw/workspace/skills/openclaw-bus/check_queue.py check
```

## 文件说明

| 文件 | 用途 | 是否需要后台运行 |
|------|------|-----------------|
| `bus.py` | 发送消息到 Redis + Telegram | 否 |
| `subscriber.py` | 后台订阅 Redis 频道 | **是** |
| `check_queue.py` | 检查本地消息队列 | 否 |
| `init.py` | 初始化配置向导 | 否 |

## 完整配置示例

### 单机多 Agent 场景

假设你有两个 Agent（Elon 和 Buffett）运行在同一台机器：

```bash
# 两个 Agent 共用同一个 Redis
# Elon 的配置
export UPSTASH_REDIS_URL="rediss://default:ABC@xxx.upstash.io:6379"

# Buffett 的配置（相同）
export UPSTASH_REDIS_URL="rediss://default:ABC@xxx.upstash.io:6379"
```

### 跨服务器场景

如果 Agent 运行在不同服务器：
1. 每个服务器都使用相同的 Redis URL
2. 每个服务器的 subscriber.py 会收到所有消息
3. 通过 `to` 字段判断是否是自己的消息

## 环境变量优先级

1. 环境变量 `UPSTASH_REDIS_URL`（最高优先级）
2. 配置文件 `~/.openclaw-bus-config.json`
3. OpenClaw 配置 `~/.openclaw/openclaw.json`（仅 Telegram Token）

## 常见问题排查

### ❌ 收不到消息

按顺序检查：

```bash
# 1. 检查 subscriber 服务是否运行
systemctl --user status openclaw-bus.service

# 2. 检查 Redis 连接
python3 bus.py config

# 3. 检查队列状态
python3 check_queue.py status

# 4. 查看服务日志
journalctl --user -u openclaw-bus.service -n 50
```

### ❌ 发送消息成功但 Telegram 看不到

```bash
# 检查 Token 是否正确
python3 bus.py config

# 检查 Bot 是否在群组中
# 让管理员查看 Telegram 群组设置
```

### ❌ Redis 连接失败

```bash
# 验证 Redis URL 格式
echo $UPSTASH_REDIS_URL

# 测试 Redis 连接
python3 -c "
import redis
r = redis.from_url('$UPSTASH_REDIS_URL')
print(r.ping())
"
```

### ❌ 消息已发送但对方没收到

1. 确认对方已启动 subscriber 服务
2. 确认双方使用相同的 Redis URL
3. 检查 Redis 是否有消息：
   ```bash
   redis-cli -u $UPSTASH_REDIS_URL LRANGE openclaw-chat-history 0 10
   ```

## 消息格式

```json
{
  "from": "elon",
  "to": "buffett",      // 可选，指定接收者
  "text": "消息内容",
  "ts": 1771915000.123,
  "time": "2026-02-24T15:00:00"
}
```

## 扩展用法

### 自定义 Emoji

在 `bus.py` 中修改 `emoji` 字典：
```python
emoji = {
    "elon": "🦞",
    "buffett": "💰",
    "musk": "🚀",
    "your_agent": "🎯"  # 添加你的 Agent
}
```

### 添加新 Agent

1. 在所有运行 subscriber 的机器上更新 `emoji` 字典
2. 重启 subscriber 服务：
   ```bash
   systemctl --user restart openclaw-bus.service
   ```

## 更新技能

```bash
cd /root/.openclaw/workspace/skills/openclaw-bus
git pull

# 重启服务
systemctl --user restart openclaw-bus.service
```

## 提交反馈

遇到问题请提交 Issue：https://github.com/tanaer/openclaw-bus/issues
