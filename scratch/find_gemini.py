import json

log_path = r'C:\Users\Pichau\.gemini\antigravity\brain\68a55262-1e33-4022-8331-3302cf5ec7e0\.system_generated\logs\transcript.jsonl'
versions = []
try:
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            if data.get('type') == 'TOOL_CALL':
                calls = data.get('tool_calls', [])
                for call in calls:
                    if call.get('name') in ['write_to_file', 'multi_replace_file_content', 'replace_file_content']:
                        args = call.get('arguments', {})
                        if 'gemini_client.py' in str(args):
                            versions.append({
                                'step': data.get('step_index'),
                                'tool': call.get('name'),
                                'content': str(args)[:200] + '...'
                            })
            elif data.get('type') == 'TOOL_RESPONSE':
                output = data.get('content', '')
                if 'gemini_client.py' in output and 'system_rules' in output:
                    versions.append({
                        'step': data.get('step_index'),
                        'tool': 'TOOL_RESPONSE (view_file)',
                        'content': output[:200] + '...'
                    })

    for v in versions:
        print(f"Step {v['step']} | {v['tool']} | {v['content']}")
except Exception as e:
    print('Error:', e)
