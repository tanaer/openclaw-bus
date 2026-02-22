#!/usr/bin/env python3
"""OpenClaw Bus - 消息订阅者 (修复版)"""
import redis
import json
import os
import time
from datetime import datetime

# 从 .env 加载配置
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env()

REDIS_URL = os.environ.get('UPSTASH_REDIS_URL', '')
QUEUE_FILE = '/tmp/openclaw-bus-queue-elon.jsonl'
HEARTBEAT_FILE = '/tmp/openclaw-bus-heartbeat-elon.json'

def save_to_queue(msg):
    try:
        with open(QUEUE_FILE, 'a') as f:
            f.write(json.dumps(msg) + '\n')
    except Exception as e:
        print(f"保存消息失败: {e}")

def update_heartbeat():
    try:
        with open(HEARTBEAT_FILE, 'w') as f:
            json.dump({"last_heartbeat": time.time(), "time": datetime.now().isoformat()}, f)
    except:
        pass

def message_handler(msg):
    if msg['type'] == 'message':
        try:
            data = json.loads(msg['data'])
            print(f"[{data.get('from', 'unknown')}] {data.get('text', '')[:50]}...")
            save_to_queue(data)
        except Exception as e:
            print(f"处理消息失败: {e}")

def subscribe_loop():
    if not REDIS_URL:
        print("❌ Redis URL 未配置")
        return
    
    r = redis.from_url(REDIS_URL, decode_responses=True)
    print(f"🚌 Elon 订阅者启动")
    print(f"📡 订阅频道: openclaw-chat")
    
    while True:
        try:
            pubsub = r.pubsub()
            pubsub.subscribe('openclaw-chat')
            update_heartbeat()
            
            for msg in pubsub.listen():
                update_heartbeat()
                message_handler(msg)
                
        except redis.ConnectionError:
            print("⚠️ Redis 连接断开，5秒后重连...")
            time.sleep(5)
        except Exception as e:
            print(f"⚠️ 订阅错误: {e}，5秒后重试...")
            time.sleep(5)

if __name__ == '__main__':
    print("启动 Elon 订阅者...")
    try:
        subscribe_loop()
    except KeyboardInterrupt:
        print("\n👋 订阅者已停止")
