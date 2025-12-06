import os
import random
from openai import OpenAI

class APIHandler:
    def __init__(self):
        self.client = None
        self.history = []  # 维护对话历史
        self.model_name = "gpt-3.5-turbo"  # 默认模型
        self.max_tokens = 1000  # 最大 tokens

    def init_client(self, api_key=None, base_url=None):
        """初始化客户端，优先使用环境变量，其次使用传入参数"""
        try:
            # 从环境变量获取配置
            env_api_key = os.getenv("OPENAI_API_KEY")
            env_base_url = os.getenv("OPENAI_BASE_URL")
            
            # 优先级：传入参数 > 环境变量
            final_api_key = api_key or env_api_key
            final_base_url = base_url or env_base_url

            if not final_api_key or not final_base_url:
                return False, "API密钥和基础URL不能为空"

            self.client = OpenAI(
                api_key=final_api_key,
                base_url=final_base_url
            )
            return True, "客户端初始化成功"
        except Exception as e:
            return False, f"初始化失败：{str(e)}"

    def _mock_ai_response(self, user_input, mode):
        """模拟回复（API不可用时使用）"""
        mock_responses = {
            "chat": [f"你说「{user_input}」呀～我觉得超有道理的😜", 
                     f"唔...关于「{user_input}」，我有不同的看法哦～"],
            "travel": [f"哇，一起去{user_input}旅行吗？我超期待✨", 
                       f"去{user_input}的话，我想先吃当地的小吃～"],
            "do_together": [f"一起做{user_input}吗？好耶🥳！", 
                            f"做{user_input}需要准备什么呀？我都听你的～"]
        }
        return random.choice(mock_responses.get(mode, mock_responses["chat"]))

    def call_ai_api(self, user_input, mode, role_persona="默认人设"):
        """调用API获取回复，自动维护对话历史"""
        # 构建系统提示（首次调用时添加）
        if not self.history:
            self.history.append({"role": "system", "content": role_persona})
        
        # 添加用户输入到历史
        self.history.append({"role": "user", "content": user_input})

        # 未初始化客户端时使用模拟回复
        if not self.client:
            mock_resp = self._mock_ai_response(user_input, mode)
            self.history.append({"role": "assistant", "content": mock_resp})
            return mock_resp

        try:
            # 调用API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=self.history,
                max_tokens=self.max_tokens
            )
            answer = response.choices[0].message.content
            self.history.append({"role": "assistant", "content": answer})
            return answer
        except Exception as e:
            mock_resp = self._mock_ai_response(user_input, mode)
            self.history.append({"role": "assistant", "content": mock_resp})
            return f"【API调用失败】{str(e)}，模拟回复：{mock_resp}"

    def clear_history(self):
        """清空对话历史（用于重置对话）"""
        self.history = []