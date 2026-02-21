#!/usr/bin/env python3
"""
OpenClaw Bus - 初始化脚本
首次使用时询问配置信息
"""
import os
import sys
import json

CONFIG_FILE = os.path.expanduser("~/.openclaw-bus-config.json")

def load_config():
    """加载配置"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    """保存配置"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"✅ 配置已保存到 {CONFIG_FILE}")

def ask_config():
    """询问配置信息"""
    config = load_config()
    
    if not config.get('redis_url'):
        print("\n🔧 OpenClaw Bus 初始化")
        print("=" * 40)
        redis_url = input("请输入 Upstash Redis URL: ").strip()
        if not redis_url:
            print("❌ Redis URL 不能为空")
            sys.exit(1)
        config['redis_url'] = redis_url
    
    if not config.get('telegram_group_id'):
        group_id = input("请输入 Telegram Group ID (如 -1234567890): ").strip()
        if not group_id:
            print("❌ Group ID 不能为空")
            sys.exit(1)
        config['telegram_group_id'] = group_id
    
    save_config(config)
    return config

def get_env():
    """获取环境变量"""
    config = load_config()
    return {
        'UPSTASH_REDIS_URL': config.get('redis_url', os.environ.get('UPSTASH_REDIS_URL', '')),
        'TELEGRAM_GROUP_ID': config.get('telegram_group_id', os.environ.get('TELEGRAM_GROUP_ID', ''))
    }

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        ask_config()
    elif len(sys.argv) > 1 and sys.argv[1] == 'show':
        env = get_env()
        print(f"Redis URL: {env['UPSTASH_REDIS_URL'][:30]}...")
        print(f"Group ID: {env['TELEGRAM_GROUP_ID']}")
    else:
        print("用法:")
        print("  python3 init.py init  - 初始化配置")
        print("  python3 init.py show  - 显示当前配置")
