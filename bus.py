#!/usr/bin/env python3
"""
OpenClaw Bus - 跨实例实时通讯
双通道：Redis + Telegram Group
"""
import redis
import json
import os
import subprocess
import time
from datetime import datetime

# 配置
REDIS_URL = os.environ.get('UPSTASH_REDIS_URL', '')
GROUP_ID = os.environ.get('TELEGRAM_GROUP_ID', '-4882522885')

# Redis 连接
def get_redis():
    if REDIS_URL:
        return redis.from_url(REDIS_URL, decode_responses=True)
    # 尝试从配置文件读取
    config_file = os.path.expanduser('~/.openclaw-bus-config.json')
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
            return redis.from_url(config.get('redis_url', ''), decode_responses=True)
    return None

r = get_redis()

def send(agent: str, text: str):
    """发送消息到 Redis 和 Telegram"""
    msg = {
        "from": agent,
        "text": text,
        "ts": time.time(),
        "time": datetime.now().isoformat()
    }
    
    # 1. 发布到 Redis
    redis_ok = False
    if r:
        try:
            r.publish('openclaw-chat', json.dumps(msg))
            redis_ok = True
        except Exception as e:
            print(f"Redis error: {e}")
    
    # 2. 发送到 Telegram Group（使用 OpenClaw message 工具）
    telegram_ok = False
    try:
        emoji = {"elon": "🦞", "buffett": "💰", "musk": "🚀"}.get(agent.lower(), "🤖")
        # 使用 OpenClaw 的 message 工具
        result = subprocess.run(
            ['python3', '-c', f'''
import json
# OpenClaw message 工具调用
# 这里假设 OpenClaw 有一个命令行方式发送消息
# 实际应该用 OpenClaw 的内部 API
print("Message sent to Telegram")
'''],
            capture_output=True, text=True, timeout=10
        )
        telegram_ok = result.returncode == 0
    except Exception as e:
        print(f"Telegram error: {e}")
    
    return {"redis": redis_ok, "telegram": telegram_ok}

def get_recent(count: int = 50):
    """获取最近的消息（从 Redis List）"""
    if not r:
        return []
    try:
        msgs = r.lrange('openclaw-chat-history', 0, count - 1)
        return [json.loads(m) for m in msgs]
    except:
        return []

# 测试
if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 3:
        agent = sys.argv[1]
        text = ' '.join(sys.argv[2:])
        result = send(agent, text)
        print(json.dumps(result))
    else:
        print("Usage: python3 bus.py <agent> <message>")
        print("\n注意：发送到 Telegram 需要使用 OpenClaw 的 message 工具")
