from flask import Flask, request, jsonify
import time

app = Flask(__name__)

@app.route('/post-endpoint', methods=['POST'])
def handle_post():
    print("POST 요청을 받았습니다.")
    time.sleep(90)  # 90초 대기
    return "Hello", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)