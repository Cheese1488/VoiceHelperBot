import os
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# Ключ загружается из переменных окружения Railway
client = OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    messages = data.get('messages', [])
    if not messages:
        return jsonify({"error": "No messages provided"}), 400

    try:
        result = client.chat.completions.create(
            model="openai/gpt-oss-120b:free",
            messages=messages
        )
        reply = result.choices[0].message.content
        return jsonify({"reply": reply})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/health')
def health():
    return "OK"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)