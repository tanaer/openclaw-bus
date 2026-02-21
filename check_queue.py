#!/usr/bin/env python3
"""
OpenClaw Bus - 检查消息队列
在 heartbeat 时调用，检查是否有新消息
"""
import json
import os
import time

QUEUE_FILE = '/tmp/openclaw-bus-queue.jsonl'
LAST_READ_FILE = '/tmp/openclaw-bus-last-read.json'

def get_last_read():
    """获取上次读取的位置"""
    if os.path.exists(LAST_READ_FILE):
        with open(LAST_READ_FILE, 'r') as f:
            return json.load(f).get('last_read', 0)
    return 0

def set_last_read(pos):
    """设置上次读取的位置"""
    with open(LAST_READ_FILE, 'w') as f:
        json.dump({'last_read': pos}, f)

def get_new_messages():
    """获取新消息（从上次读取位置之后）"""
    if not os.path.exists(QUEUE_FILE):
        return []
    
    last_read = get_last_read()
    messages = []
    
    try:
        with open(QUEUE_FILE, 'r') as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines):
            if i >= last_read:
                try:
                    messages.append(json.loads(line.strip()))
                except:
                    pass
        
        # 更新读取位置
        set_last_read(len(lines))
        
    except Exception as e:
        print(f"读取队列失败: {e}")
    
    return messages

def has_new_messages():
    """检查是否有新消息"""
    if not os.path.exists(QUEUE_FILE):
        return False
    
    last_read = get_last_read()
    
    try:
        with open(QUEUE_FILE, 'r') as f:
            lines = f.readlines()
        return len(lines) > last_read
    except:
        return False

def clear_queue():
    """清空队列"""
    if os.path.exists(QUEUE_FILE):
        os.remove(QUEUE_FILE)
    set_last_read(0)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == 'check':
            # 检查是否有新消息
            if has_new_messages():
                msgs = get_new_messages()
                print(f"📬 有 {len(msgs)} 条新消息:")
                for msg in msgs:
                    print(f"  [{msg.get('from', '?')}] {msg.get('text', '')[:50]}...")
            else:
                print("📭 没有新消息")
        
        elif cmd == 'get':
            # 获取所有新消息（JSON 格式）
            msgs = get_new_messages()
            print(json.dumps(msgs, ensure_ascii=False))
        
        elif cmd == 'clear':
            # 清空队列
            clear_queue()
            print("🗑️ 队列已清空")
        
        elif cmd == 'status':
            # 显示状态
            last_read = get_last_read()
            queue_size = 0
            if os.path.exists(QUEUE_FILE):
                with open(QUEUE_FILE, 'r') as f:
                    queue_size = len(f.readlines())
            print(f"📊 队列状态:")
            print(f"  总消息数: {queue_size}")
            print(f"  已读: {last_read}")
            print(f"  未读: {queue_size - last_read}")
        
        else:
            print("用法:")
            print("  python3 check_queue.py check  - 检查新消息")
            print("  python3 check_queue.py get    - 获取新消息（JSON）")
            print("  python3 check_queue.py clear  - 清空队列")
            print("  python3 check_queue.py status - 显示状态")
    else:
        # 默认：返回是否有新消息（用于 heartbeat）
        if has_new_messages():
            msgs = get_new_messages()
            for msg in msgs:
                print(f"📨 [{msg.get('from', '?')}] {msg.get('text', '')}")
        else:
            print("📭 无新消息")
