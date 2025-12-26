from flask import Flask, request, jsonify
import sys
import io
import contextlib

app = Flask(__name__)

@app.route('/api/exec', methods=['POST'])
def execute_code():
    data = request.json
    # 获取 LLM 生成的代码
    code_to_run = data.get('code', '')
    
    # 准备捕获输出 (print 的内容)
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    try:
        # 使用 contextlib 劫持 stdout 和 stderr
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            # ==============================
            # 危险动作：直接运行字符串代码
            # ==============================
            exec(code_to_run, {'__name__': '__main__'})
            
        return jsonify({
            "status": "success",
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "stdout": stdout_capture.getvalue() # 即使报错也返回之前打印的内容
        }), 400

@app.route('/api/exec', methods=['GET'])
def test_get():
    return "test for api"

if __name__ == '__main__':
    app.run()
