#!/usr/bin/env python3
"""
OpenClaw Bus - 跨实例实时通讯
双通道：Redis + Telegram Group

自动从 OpenClaw 配置文件读取 Telegram Bot Token
"""
import redis
import requests
import json
import os
import time
from datetime import datetime

# 配置
REDIS_URL = os.environ.get('UPSTASH_REDIS_URL', '')
GROUP_ID = os.environ.get('TELEGRAM_GROUP_ID', '-4882522885')

# OpenClaw 配置文件路径
OPENCLAW_CONFIG = os.path.expanduser('~/.openclaw/openclaw.json')

def get_redis():
    """获取 Redis 连接"""
    if REDIS_URL:
        return redis.from_url(REDIS_URL, decode_responses=True)
    # 尝试从配置文件读取
    config_file = os.path.expanduser('~/.openclaw-bus-config.json')
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
            return redis.from_url(config.get('redis_url', ''), decode_responses=True)
    return None

def get_telegram_token():
    """从 OpenClaw 配置文件读取 Telegram Bot Token"""
    if os.path.exists(OPENCLAW_CONFIG):
        with open(OPENCLAW_CONFIG, 'r') as f:
            config = json.load(f)
            return config.get('channels', {}).get('telegram', {}).get('botToken', '')
    return ''

def get_group_id():
    """获取 Telegram Group ID"""
    if GROUP_ID and GROUP_ID != '-4882522885':
        return GROUP_ID
    # 尝试从配置文件读取
    config_file = os.path.expanduser('~/.openclaw-bus-config.json')
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
            return config.get('telegram_group_id', GROUP_ID)
    return GROUP_ID

# Redis 连接
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
    
    # 2. 发送到 Telegram Group（使用配置文件中的 Token）
    telegram_ok = False
    token = get_telegram_token()
    group_id = get_group_id()
    
    if token and group_id:
        try:
            emoji = {"elon": "🦞", "buffett": "💰", "musk": "🚀"}.get(agent.lower(), "🤖")
            resp = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={
                    "chat_id": group_id,
                    "text": f"{emoji} **{agent}**: {text}",
                    "parse_mode": "Markdown"
                },
                timeout=10
            )
            telegram_ok = resp.status_code == 200
            if not telegram_ok:
                print(f"Telegram error: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"Telegram error: {e}")
    else:
        print(f"Telegram skipped: token={bool(token)}, group_id={group_id}")
    
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
    
    # 显示配置信息
    print("📋 配置信息:")
    print(f"  Telegram Token: {'✅ 已配置' if get_telegram_token() else '❌ 未配置'}")
    print(f"  Group ID: {get_group_id()}")
    print(f"  Redis: {'✅ 已连接' if r else '❌ 未连接'}")
    print()
    
    if len(sys.argv) >= 3:
        agent = sys.argv[1]
        text = ' '.join(sys.argv[2:])
        result = send(agent, text)
        print(json.dumps(result))
    elif len(sys.argv) == 2 and sys.argv[1] == 'config':
        # 只显示配置
        pass
    else:
        print("Usage: python3 bus.py <agent> <message>")
        print("       python3 bus.py config  # 显示配置信息")
