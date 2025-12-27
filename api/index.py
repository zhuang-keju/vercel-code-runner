from flask import Flask, request, jsonify
import sys
import io
import contextlib
import os
import unittest
import traceback

app = Flask(__name__)

API_KEY = os.environ.get("API_KEY")

@app.route('/api/exec', methods=['POST'])
def execute_code():

    if not API_KEY:
         return jsonify({"error": "Server configuration error: Token not set"}), 500

    auth_header = request.headers.get('Authorization')
    if auth_header != f"Bearer {API_KEY}":
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    # 获取 LLM 生成的代码
    code_to_run = data.get('code', '')
    test_code = data.get('test', '') # 新增字段
    
    # 准备捕获输出 (print 的内容)
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    execution_success = False
    test_result_summary = "No tests found or execution failed."

    try:
        # 使用 contextlib 劫持 stdout 和 stderr
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            # ==============================
            # 危险动作：直接运行字符串代码
            # ==============================
            exec_globals = {'__name__': 'dify_lib', 'unittest': unittest}
            
            # === 执行核心 ===
            exec(code_to_run, exec_globals)
            if test_code:
                exec(test_code, exec_globals)

            #如果有testcase，会出现在exec_globals

            test_loader = unittest.TestLoader()
            suite = unittest.TestSuite()
            
            has_tests = False
            for name, obj in exec_globals.items():
                if isinstance(obj, type) and issubclass(obj, unittest.TestCase):
                    suite.addTests(test_loader.loadTestsFromTestCase(obj))
                    has_tests = True
            
            if has_tests:
                # 创建一个 TestResult 对象来捕获详细结果
                runner = unittest.TextTestRunner(stream=sys.stderr, verbosity=2) # 结果打到 stderr
                result = runner.run(suite)
                
                execution_success = result.wasSuccessful()
                test_result_summary = f"Run {result.testsRun} tests. Errors: {len(result.errors)}, Failures: {len(result.failures)}"
            else:
                # 如果没有测试类，且代码没报错，就算成功
                execution_success = True
                test_result_summary = "Code executed successfully (No test cases detected)."

        return jsonify({
            "status": "success",
            "is_pass": execution_success, # ✅ 给 Dify 的直接判断依据
            "summary": test_result_summary,
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue() # unittest 的详细报错通常在这里
        })

    except Exception as e:
        # 捕获语法错误或运行时崩溃
        return jsonify({
            "status": "error",
            "is_pass": False,
            "summary": "Runtime Error / Syntax Error",
            "error": traceback.format_exc(),
            "stdout": stdout_capture.getvalue()
        }), 200 # 返回 200 让 Dify 处理逻辑，而不是直接红灯报错




    #     return jsonify({
    #         "status": "success",
    #         "stdout": stdout_capture.getvalue(),
    #         "stderr": stderr_capture.getvalue()
    #     })
        
    # except Exception as e:
    #     return jsonify({
    #         "status": "error",
    #         "error": str(e),
    #         "stdout": stdout_capture.getvalue() # 即使报错也返回之前打印的内容
    #     }), 400

@app.route('/api/exec', methods=['GET'])
def test_get():
    return "test for api"

if __name__ == '__main__':
    app.run()
