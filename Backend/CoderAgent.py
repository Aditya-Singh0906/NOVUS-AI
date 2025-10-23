import os
import re
import subprocess
import tempfile
import traceback
from dotenv import dotenv_values
from openai import OpenAI
import sys
from Backend.Utils import resource_path


class CoderAgent:
    def __init__(self):
        # Load environment vars
        env_path = resource_path(".env")
        env_vars = dotenv_values(env_path)  

        # Dedicated API key (falls back to main key if not set)
        self.api_key = env_vars.get("CODER_API_KEY", env_vars.get("OPENAI_API_KEY"))

        # Model routing (default fallback is gpt-4.1)
        self.model_fast = env_vars.get("CODER_MODEL_FAST", "gpt-4o")     # for code generation
        self.model_strict = env_vars.get("CODER_MODEL_STRICT", "gpt-4.1")  # for review/debug

        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key)

    # -------------------- Language Detection -------------------- #
    def detect_language(self, code: str) -> str:
        """Basic language detection using keywords and syntax."""
        if "import " in code or "def " in code:
            return "python"
        if "#include" in code or "int main" in code:
            return "c/c++"
        if "public static void main" in code:
            return "java"
        if "function " in code or "console.log" in code:
            return "javascript"
        if "<html" in code and "</html>" in code:
            return "html"
        return "unknown"

    # -------------------- Code Review -------------------- #
    def review_code(self, code: str) -> str:
        prompt = f"""
        You are a senior software engineer. Review the following code thoroughly:
        - Identify bugs or logical issues
        - Suggest performance optimizations
        - Recommend readability/clean coding improvements
        - Highlight potential security issues

        Code:
        ```\n{code}\n```
        """
        return self._ask_model(prompt, mode="strict")

    # -------------------- Code Debugging -------------------- #
    def debug_code(self, code: str) -> str:
        prompt = f"""
        You are an expert debugger. Analyze the following code:
        - Identify syntax or runtime issues
        - Suggest corrected version
        - Explain the fixes clearly

        Code:
        ```\n{code}\n```
        """
        return self._ask_model(prompt, mode="strict")

    # -------------------- Code Writing -------------------- #
    def write_code(self, request: str, lang: str = "python") -> str:
        prompt = f"""
        Write clean, well-documented {lang} code for the following request:

        {request}

        - Use best practices
        - Add minimal but clear comments
        - After the code, explain the solution briefly
        """
        return self._ask_model(prompt, mode="fast")

    # -------------------- Code Execution -------------------- #
    def execute_code(self, code: str, lang: str = "python") -> str:
        if lang != "python":
            return "⚠️ Execution is only supported for Python right now."

        try:
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".py") as tmp:
                tmp.write(code)
                tmp.flush()
                result = subprocess.run(
                    [sys.executable, tmp.name],
                    capture_output=True, text=True, timeout=10
                )
            os.unlink(tmp.name)

            if result.returncode == 0:
                return f"✅ Execution successful:\n```\n{result.stdout.strip()}\n```"
            else:
                return f"❌ Error:\n```\n{result.stderr.strip()}\n```"
        except Exception as e:
            return f"[Execution ERROR] {e}\n{traceback.format_exc()}"

    # -------------------- Handle Query -------------------- #
    def handle(self, query: str) -> str:
        query_lower = query.lower()

        # Extract code blocks (```...```)
        code_match = re.search(r"```(.*?)```", query, re.DOTALL)
        code = code_match.group(1).strip() if code_match else None

        if "review" in query_lower and code:
            return self.review_code(code)
        elif "debug" in query_lower and code:
            return self.debug_code(code)
        elif "write" in query_lower or "generate" in query_lower:
            return self.write_code(query)
        elif "run" in query_lower and code:
            lang = self.detect_language(code)
            return self.execute_code(code, lang)
        else:
            return "⚠️ Please specify whether to *review*, *debug*, *write*, or *run* code, and include your code or request."

    # -------------------- Model Caller -------------------- #
    def _ask_model(self, prompt: str, mode: str = "fast") -> str:
        try:
            model_to_use = self.model_fast if mode == "fast" else self.model_strict
            response = self.client.chat.completions.create(
                model=model_to_use,
                messages=[
                    {"role": "system", "content": "You are a professional AI coding assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[CoderAgent ERROR] {e}\n{traceback.format_exc()}"
