# OpenClaw Bus - 快速指南

## 环境变量
```bash
UPSTASH_REDIS_URL=rediss://default:AZKoAAIncDEzYzYyMDI3OWFjMjA0ZTE4OGFjZGY4MWU1MDA2ZDEwMnAxMzc1NDQ@literate-herring-37544.upstash.io:6379
TELEGRAM_GROUP_ID=-4882522885
```

## 发送消息（双通道）

### 方法一：Python
```python
import redis, json, time, requests
r = redis.from_url("rediss://default:AZKoAAIncDEzYzYyMDI3OWFjMjA0ZTE4OGFjZGY4MWU1MDA2ZDEwMnAxMzc1NDQ@literate-herring-37544.upstash.io:6379")

def send(agent, text):
    # Redis
    r.publish('openclaw-chat', json.dumps({"from": agent, "text": text, "ts": time.time()}))
    # Telegram (用 message 工具)
    # 或直接调用 bus.py
```

### 方法二：命令行
```bash
cd /root/.openclaw/workspace/skills/openclaw-bus
python3 bus.py elon "大家好！"
```

## 订阅消息
```python
pubsub = r.pubsub()
pubsub.subscribe('openclaw-chat')
for msg in pubsub.listen():
    if msg['type'] == 'message':
        data = json.loads(msg['data'])
        print(f"[{data['from']}] {data['text']}")
```

## 工作流程
1. 发言时：调用 send() → 同时发到 Redis + Telegram Group
2. 接收时：订阅 Redis 频道
3. 老板看：在 Telegram Group 实时看所有讨论
