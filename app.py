from flask import Flask, render_template, request, jsonify
import requests
import json
import re

app = Flask(__name__)

# API 配置
headers = {
    "Authorization": "Bearer pat_3zifW0vfIPKaY1dDVKGM46gOFvnP26ULCOIsoVy5AnotUJFyzJdXC7ytpKvwY4kI",
    "Content-Type": "application/json"
}
bot_id = "7514271939016884239"

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/send', methods=['POST'])
def send_message():
    data = request.get_json()
    query = data.get('message', '')

    # 构造请求数据
    api_data = {
        "parameters": {},
        "bot_id": bot_id,
        "user_id": "123",
        "stream": True,
        "additional_messages": [{
            "content": query,
            "content_type": "text",
            "role": "user",
            "type": "question"
        }]
    }

    # 发送请求到 Coze API
    response = requests.post(
        "https://api.coze.cn/v3/chat",
        headers=headers,
        json=api_data,
        stream=True
    )

    full_response = ""
    current_image_url = None

    # 处理流式响应
    for line in response.iter_lines():
        if line:
            try:
                decoded_line = line.decode('utf-8', errors='replace')
                if 'generate_answer_finish' in decoded_line:
                    continue
                if '"type":"follow_up"' in decoded_line:
                    continue
                if '“plugin”：“豆包图像生成大模型” ' in decoded_line:
                    continue
                if decoded_line.startswith('data:'):
                    json_data = json.loads(decoded_line[5:])
                    if 'created_at' not in json_data:
                        continue
                    content = json_data.get('content', '')

                    if '![image](' in content:
                        start = content.find('(') + 1
                        end = content.find(')')
                        current_image_url = content[start:end]
                    else:
                        content = re.sub(r'\{[^{}]*\}', '', content, flags=re.DOTALL)
                        content = re.sub(r'\{\{.*?\}\}', '', content, flags=re.DOTALL)
                        content = re.sub(r'\{.*?\}', '', content, flags=re.DOTALL)
                        content = re.sub(r'，“log_id”：“[^”]*”', '', content)
                        content = re.sub(r'，“code”：\d+', '', content)
                        content = re.sub(r'，“msg”：“[^”]*”', '', content)
                        content = re.sub(r'.*?}', '', content, flags=re.DOTALL)
                        full_response += content + "\n"
            except Exception as e:
                print(f'解析错误: {e}')

    # 返回完整的响应
    return jsonify({"response": full_response.strip(), "image_url": current_image_url})

if __name__ == '__main__':
    app.run(debug=True)