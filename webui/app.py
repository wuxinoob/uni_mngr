# app.py
from flask import Flask, render_template, Response, request, jsonify
from terminal_manager import manager # 导入我们的管理器单例
import time

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/terminals', methods=['GET'])
def list_terminals():
    """获取所有终端的列表"""
    return jsonify(manager.list_terminals())

@app.route('/api/terminals', methods=['POST'])
def create_terminal():
    """启动一个新终端"""
    data = request.get_json()
    command = data.get('command')
    if not command:
        return jsonify({'error': 'Command not provided'}), 400
    
    terminal_instance = manager.start_terminal(command)
    return jsonify(terminal_instance.to_dict()), 201

@app.route('/stream/<terminal_id>')
def stream(terminal_id):
    """为指定终端ID创建SSE流"""
    terminal_instance = manager.get_terminal(terminal_id)
    if not terminal_instance:
        return Response("Terminal not found.", status=404)

    def generate():
        for output_line in terminal_instance.get_output_generator():
            # SSE格式: "data: <content>\n\n"
            yield f"data: {output_line}\n\n"
            time.sleep(0.01) # 防止CPU空转

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    # threaded=True 对于开发服务器处理并发后台线程是必需的
    app.run(debug=True, threaded=True, host='0.0.0.0')