#!/usr/bin/env python3
import json
with open('conversation_history.json', 'r') as f:
    data = json.load(f)
non_system = [m for m in data if m.get('role') != 'system']
print(f'Messages in history: {len(non_system)}')
