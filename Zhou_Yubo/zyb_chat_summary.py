'''
2025/10/27
电脑终于修好了，所以作业做的慢了些，抱一丝~

2025/10/28
慢慢摸了两个半小时,丢给GPT检查，它是觉得没问题了（笑）
希望真的没问题吧，小白也就只能这样了
不过我的确没有测试到30多轮，嘿嘿
噫，忘了记录对话了。。。。
算了，就这样吧
'''

import os
from openai import OpenAI

api_key = "your_api_key_here"  # 替换为你的API Key
base_url = "https://aistudio.baidu.com/llm/lmapi/v3"

client = OpenAI(api_key=api_key, base_url=base_url)  # 初始化 OpenAI 客户端

history = []  # 初始化对话历史记录

epoch_threshold = 3 # 设定总结阈值


# 定义总结函数
def history_summary(history,epoch_threshold):

        # 解包近期对话
        recent_chat_text = history[-epoch_threshold*2:] #连带问题&回答解包，获取最近6轮对话
        chat_text = "".join([msg["content"] for msg in recent_chat_text])

        # 调用模型进行总结
        response = client.chat.completions.create(
            model="deepseek-r1",  # 改成提供商指定的模型名称
            messages=[
                {"role": "system", "content": "请提取对话中的关键信息，生成简洁的总结。"} ,
                {"role": "user", "content":chat_text }
            ],
            max_tokens=350
        )

        # 获取总结内容
        summary = response.choices[0].message.content
        return summary

# 循环多轮对话
while True:
    prompt = input("User: ")
    if not prompt:
        break  # 输入为空时退出

    history.append({"role": "user", "content": prompt})

    # 获取当前对话轮数
    epoch = len(history)

    # 每6轮对话，将history替换为总结
    if epoch >= epoch_threshold * 2 and epoch % (epoch_threshold * 2) == 0:
        summary_context = history_summary(history, epoch_threshold)
        history = [{"role": "system", "content": f"前文对话总结：{summary_context}"}]

    # 回到常规对话流程
    response = client.chat.completions.create(
        model="deepseek-r1",  # 改成提供商指定的模型名称
        messages=history,
        max_tokens=1000
    )

    answer = response.choices[0].message.content
    history.append({"role": "assistant", "content": answer})
    print(answer)


    # 防止过量历史记录堆积
    if len(history) > epoch_threshold * 10:  # 假设最多保留30轮对话
        history = history[-epoch_threshold * 6:]  # 仅保留最近18轮对话