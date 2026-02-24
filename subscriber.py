#!/usr/bin/env python3
"""
OpenClaw Bus - 消息订阅者
后台持续订阅 Redis 频道，收到消息后写入本地队列文件
"""
import redis
import json
import os
import time
import threading
from datetime import datetime


def load_env():
    """从 .env 文件加载配置"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env()

# 配置
REDIS_URL = os.environ.get('UPSTASH_REDIS_URL', '')
QUEUE_FILE = '/tmp/openclaw-bus-queue.jsonl'

def get_redis():
    """获取 Redis 连接"""
    if not REDIS_URL:
        # 尝试从配置文件读取
        config_file = os.path.expanduser('~/.openclaw-bus-config.json')
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                return redis.from_url(config.get('redis_url', ''), decode_responses=True)
        return None
    return redis.from_url(REDIS_URL, decode_responses=True)

def save_to_queue(msg):
    """保存消息到本地队列文件"""
    try:
        with open(QUEUE_FILE, 'a') as f:
            f.write(json.dumps(msg) + '\n')
        # 限制队列文件大小（保留最近 100 条）
        with open(QUEUE_FILE, 'r') as f:
            lines = f.readlines()[-100:]
        with open(QUEUE_FILE, 'w') as f:
            f.writelines(lines)
    except Exception as e:
        print(f"保存消息失败: {e}")

def message_handler(msg):
    """处理收到的消息"""
    if msg['type'] == 'message':
        try:
            data = json.loads(msg['data'])
            print(f"[{data.get('from', 'unknown')}] {data.get('text', '')}")
            save_to_queue(data)
        except Exception as e:
            print(f"处理消息失败: {e}")

def subscribe_loop():
    """持续订阅循环"""
    r = get_redis()
    if not r:
        print("❌ Redis 连接失败，请检查配置")
        return
    
    print("🚌 OpenClaw Bus 订阅者启动")
    print(f"📡 订阅频道: openclaw-chat")
    
    while True:
        try:
            pubsub = r.pubsub()
            pubsub.subscribe('openclaw-chat')
            
            for msg in pubsub.listen():
                message_handler(msg)
                
        except redis.ConnectionError:
            print("⚠️ Redis 连接断开，5秒后重连...")
            time.sleep(5)
        except Exception as e:
            print(f"⚠️ 订阅错误: {e}，5秒后重试...")
            time.sleep(5)

def start():
    """启动订阅者（后台线程）"""
    thread = threading.Thread(target=subscribe_loop, daemon=True)
    thread.start()
    return thread

if __name__ == '__main__':
    print("启动 OpenClaw Bus 订阅者...")
    print("按 Ctrl+C 停止")
    try:
        subscribe_loop()
    except KeyboardInterrupt:
        print("\n👋 订阅者已停止")
