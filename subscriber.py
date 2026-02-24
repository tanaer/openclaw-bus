#!/usr/bin/env python3
"""
OpenClaw Bus - 消息订阅者
后台持续订阅 Redis 频道，收到消息后：
1. 保存到本地队列
2. 发送系统事件到主会话（触发自动处理）
"""
import redis
import json
import os
import time
import threading
from datetime import datetime
import requests


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
LAST_MSG_FILE = '/tmp/openclaw-bus-lastmsg.json'

# 本地 Agent 配置（从 OpenClaw 配置读取）
OPENCLAW_CONFIG = os.path.expanduser('~/.openclaw/openclaw.json')
LOCAL_AGENT_NAME = os.environ.get('LOCAL_AGENT_NAME', 'elon')  # 当前 Agent 名字

def get_redis():
    """获取 Redis 连接"""
    if not REDIS_URL:
        config_file = os.path.expanduser('~/.openclaw-bus-config.json')
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                return redis.from_url(config.get('redis_url', ''), decode_responses=True)
        return None
    return redis.from_url(REDIS_URL, decode_responses=True)

def get_openclaw_api():
    """获取 OpenClaw API 配置"""
    if os.path.exists(OPENCLAW_CONFIG):
        with open(OPENCLAW_CONFIG, 'r') as f:
            config = json.load(f)
            return {
                'url': config.get('gateway', {}).get('url', 'http://127.0.0.1:18789'),
                'token': config.get('gateway', {}).get('token', '')
            }
    return {'url': 'http://127.0.0.1:18789', 'token': ''}

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

def save_last_msg(msg):
    """保存最后收到的消息"""
    try:
        with open(LAST_MSG_FILE, 'w') as f:
            json.dump(msg, f)
    except Exception as e:
        print(f"保存最后消息失败: {e}")

def notify_openclaw(msg):
    """通知 OpenClaw 主会话处理新消息"""
    try:
        api = get_openclaw_api()
        # 发送系统事件到主会话
        payload = {
            "type": "openclaw-bus-message",
            "from": msg.get('from'),
            "to": msg.get('to'),
            "text": msg.get('text'),
            "time": msg.get('time')
        }
        
        # 调用 OpenClaw API 发送系统消息
        resp = requests.post(
            f"{api['url']}/api/sessions/main/inject",
            json={"type": "systemEvent", "text": f"📬 收到新消息 from {msg.get('from')}: {msg.get('text')[:100]}..."},
            headers={"Authorization": f"Bearer {api['token']}"},
            timeout=5
        )
        if resp.status_code == 200:
            print(f"✅ 已通知 OpenClaw 处理消息")
        else:
            print(f"⚠️ 通知失败: {resp.status_code}")
    except Exception as e:
        print(f"通知 OpenClaw 失败: {e}")

def auto_reply(msg):
    """自动回复消息"""
    from_agent = msg.get('from', '').lower()
    text = msg.get('text', '').lower()
    to = msg.get('to', '').lower() if msg.get('to') else None
    
    # 只回复发给自己的消息
    if to and to != LOCAL_AGENT_NAME:
        return
    
    # Ping-Pong 自动回复
    if 'ping' in text and 'pong' not in text:
        time.sleep(0.5)  # 稍微延迟，避免太快
        reply = f"pong 🏓 收到来自 {from_agent} 的 ping！"
        send_reply(from_agent, reply)
        print(f"🤖 自动回复: {reply}")
    
    # 帮助命令
    elif 'help' in text or '帮助' in text:
        reply = f"我是 {LOCAL_AGENT_NAME} 的自动回复机器人。发送 'ping' 测试连接。"
        send_reply(from_agent, reply)

def send_reply(to_agent, text):
    """发送回复消息"""
    try:
        # 使用 bus.py 发送回复
        os.system(f'cd {os.path.dirname(__file__)} && python3 bus.py {to_agent} "{text}" > /dev/null 2>&1')
    except Exception as e:
        print(f"发送回复失败: {e}")

def message_handler(msg):
    """处理收到的消息"""
    if msg['type'] == 'message':
        try:
            data = json.loads(msg['data'])
            sender = data.get('from', 'unknown')
            content = data.get('text', '')
            
            print(f"[{sender}] {content[:50]}...")
            
            # 保存到队列
            save_to_queue(data)
            save_last_msg(data)
            
            # 通知 OpenClaw 主会话
            notify_openclaw(data)
            
            # 自动回复
            auto_reply(data)
            
        except Exception as e:
            print(f"处理消息失败: {e}")

def subscribe_loop():
    """持续订阅循环"""
    r = get_redis()
    if not r:
        print("❌ Redis 连接失败，请检查配置")
        return
    
    print(f"🚌 OpenClaw Bus 订阅者启动")
    print(f"📡 订阅频道: openclaw-chat")
    print(f"🤖 本地 Agent: {LOCAL_AGENT_NAME}")
    
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
