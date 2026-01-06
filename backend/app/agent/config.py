import os

# DashScope API Configuration
# 优先从环境变量获取，如果不存在则使用空字符串或抛出错误
# 警告：请勿在代码中硬编码真实的 API Key
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

# 模型名称配置
# 可选: qwen-turbo, qwen-plus, qwen-max
DASHSCOPE_MODEL_NAME = "qwen-max"

# 生成参数
GENERATE_ARGS = {
    "temperature": 0.5,
    "stream": False
}
