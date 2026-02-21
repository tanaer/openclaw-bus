#!/usr/bin/env python3
"""
OpenClaw Bus - 跨实例实时通讯
双通道：Redis + Telegram Group
"""
import redis
import requests
import json
import os
import time
from datetime import datetime

# 配置
REDIS_URL = os.environ.get('UPSTASH_REDIS_URL', 'rediss://default:AZKoAAIncDEzYzYyMDI3OWFjMjA0ZTE4OGFjZGY4MWU1MDA2ZDEwMnAxMzc1NDQ@literate-herring-37544.upstash.io:6379')
GROUP_ID = os.environ.get('TELEGRAM_GROUP_ID', '-4882522885')
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')

# Redis 连接
r = redis.from_url(REDIS_URL, decode_responses=True)

def send(agent: str, text: str, silent: bool = False):
    """发送消息到 Redis 和 Telegram"""
    msg = {
        "from": agent,
        "text": text,
        "ts": time.time(),
        "time": datetime.now().isoformat()
    }
    
    # 1. 发布到 Redis
    try:
        r.publish('openclaw-chat', json.dumps(msg))
        redis_ok = True
    except Exception as e:
        print(f"Redis error: {e}")
        redis_ok = False
    
    # 2. 发送到 Telegram Group
    telegram_ok = False
    if BOT_TOKEN and not silent:
        try:
            emoji = {"elon": "🦞", "buffett": "💰", "musk": "🚀"}.get(agent.lower(), "🤖")
            resp = requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": GROUP_ID,
                    "text": f"{emoji} **{agent}**: {text}",
                    "parse_mode": "Markdown"
                },
                timeout=10
            )
            telegram_ok = resp.status_code == 200
        except Exception as e:
            print(f"Telegram error: {e}")
    
    return {"redis": redis_ok, "telegram": telegram_ok}

def get_recent(count: int = 50):
    """获取最近的消息（从 Redis List）"""
    try:
        msgs = r.lrange('openclaw-chat-history', 0, count - 1)
        return [json.loads(m) for m in msgs]
    except:
        return []

def save_to_history(msg: dict):
    """保存消息到历史记录"""
    try:
        r.lpush('openclaw-chat-history', json.dumps(msg))
        r.ltrim('openclaw-chat-history', 0, 999)  # 保留最近1000条
    except:
        pass

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
