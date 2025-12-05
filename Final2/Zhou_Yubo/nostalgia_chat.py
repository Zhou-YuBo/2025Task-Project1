import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, filedialog
from datetime import datetime
import json, csv, os
import markdown2
import re
from openai import OpenAI

# ======================
# 识别时间/日期
# ======================
def get_datetime_answer(user_text):
    text = user_text.lower()
    now = datetime.now()
    if any(k in text for k in ["时间", "几点"]):
        return f"现在时间是 {now.strftime('%H:%M:%S')}"
    elif any(k in text for k in ["日期", "几号", "今天"]):
        return f"今天是 {now.strftime('%Y-%m-%d')}"
    elif any(k in text for k in ["星期", "星期几", "周几"]):
        week_map = ["星期一","星期二","星期三","星期四","星期五","星期六","星期日"]
        return f"今天是 {week_map[now.weekday()]}"
    else:
        return None

# ======================
# 初始化窗口并询问 API Key 和 Base URL
# ======================
root = tk.Tk()
root.withdraw() # 隐藏主窗口

api_key = simpledialog.askstring("API Key", "请输入你的 API Key：")
if not api_key:
    messagebox.showerror("错误", "API Key 不能为空")
    exit()

base_url = simpledialog.askstring("Base URL", "请输入你的 Base URL（API地址）：")
if not base_url:
    messagebox.showerror("错误", "Base URL 不能为空")
    exit()

root.deiconify()
root.title("怀旧chat 1.0")

user_name = simpledialog.askstring("昵称", "请输入你的昵称（默认“你”）：") or "你"
assistant_name = simpledialog.askstring("助手昵称", "请输入助手昵称（默认“助手”）：") or "助手"
model_name = simpledialog.askstring("模型名称", "请输入调用模型名称（默认“deepseek-v3”）：") or "deepseek-v3"

# ======================
# 初始化 OpenAI 客户端
# ======================
client = OpenAI(api_key=api_key, base_url=base_url)

history = []
important_memory = []
knowledge_base = []

# ======================
# 聊天显示函数
# ======================
def append_chat(speaker, text, color):
    chat_window.config(state='normal')
    chat_window.insert(tk.END, f"{speaker}：", "color")
    chat_window.insert(tk.END, f"{text}\n\n")
    chat_window.tag_config("color", foreground=color)
    chat_window.see(tk.END)
    chat_window.config(state='disabled')

# ======================
# 助手自我介绍
# ======================
def introduce_features():
    intro_text = (
        f"你好，我是{assistant_name}！\n"
        f"我可以帮你：\n"
        f"1. 回答各种问题，并记住会话中的重要信息。\n"
        f"2. 获取当前的日期、时间和星期。\n"
        f"3. （高级功能）可以导入外部知识库，为你提供更专业的回答。\n"
        f"外部知识库仅支持 CSV 和 JSON，并且必须带 tag 和 content！\n"
    )
    append_chat(assistant_name, intro_text, "#34A853")
    history.append({"role":"assistant","content":intro_text})

# ======================
# 开启新对话
# ======================
def reset_chat():
    chat_window.config(state='normal')
    chat_window.delete("1.0", tk.END)
    chat_window.config(state='disabled')
    history.clear()
    important_memory.clear()
    introduce_features()

# ======================
# 导入知识库
# ======================
def import_knowledge_base():
    file_path = filedialog.askopenfilename(filetypes=[("CSV文件","*.csv"), ("JSON文件","*.json")])
    if not file_path:
        return
    ext = os.path.splitext(file_path)[1].lower()
    imported_count = 0
    skipped_count = 0
    try:
        if ext == ".csv":
            with open(file_path,newline='',encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    tag = row.get("tag","").strip()
                    content = row.get("content","").strip()
                    if not tag or not content:
                        skipped_count += 1
                        continue
                    knowledge_base.append({"tag": tag, "content": content})
                    imported_count += 1
        elif ext == ".json":
            with open(file_path,encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    tag = item.get("tag","").strip()
                    content = item.get("content","").strip()
                    if not tag or not content:
                        skipped_count += 1
                        continue
                    knowledge_base.append({"tag": tag, "content": content})
                    imported_count += 1
        else:
            messagebox.showwarning("文件错误","请选择 CSV 或 JSON 文件")
            return
    except Exception as e:
        messagebox.showerror("导入错误", str(e))
        return

    messagebox.showinfo("导入完成", f"已成功导入 {imported_count} 条知识库，{skipped_count} 条跳过。")
    append_chat(assistant_name, f"已成功导入 {imported_count} 条知识库，{skipped_count} 条跳过。", "#34A853")

# ======================
# 发送消息逻辑
# ======================
def send_message():
    user_text = input_box.get().strip()
    if not user_text:
        return
    
    # 1. 显示用户消息并添加到历史记录
    append_chat(user_name, user_text, "#1A73E8")
    input_box.delete(0, tk.END)
    history.append({"role":"user","content":user_text})

    # 2. 识别时间/日期命令
    datetime_answer = get_datetime_answer(user_text)
    if datetime_answer:
        append_chat(assistant_name, datetime_answer, "#34A853")
        return

    # 3. 准备消息结构 (知识库/记忆/历史)
    matched_kb = []
    for item in knowledge_base:
        if item["tag"].lower() in user_text.lower():
            matched_kb.append(f"[{item['tag']}] {item['content']}")
            
    kb_prompt = "请参考以下知识库内容回答用户问题：\n" + "\n".join(matched_kb) if matched_kb else ""

    messages = []
    if kb_prompt:
        messages.append({"role":"system","content":kb_prompt})
    if important_memory:
        memory_prompt = "助手请记住以下信息，在回答问题时参考：\n" + "\n".join(important_memory)
        messages.append({"role":"system","content":memory_prompt})
    messages += history

    try:
        # 4. 调用主模型获取回答
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=5000
        )
        answer = response.choices[0].message.content
        html = markdown2.markdown(answer)
        clean_text = re.sub(r"<.*?>","",html)

        # 5. 短期记忆判断（成功获取回答后才执行）
        memory_check = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role":"system","content":"请从以下用户消息中判断哪些信息值得记忆，只输出一句或几个重点，不需要解释，如果没有特别重要的内容，可以不记忆："},
                {"role":"user","content":answer}
            ],
            max_tokens=60
        )
        memory_text = memory_check.choices[0].message.content.strip()
        if memory_text:
            important_memory.append(memory_text)

        # 6. 将成功获取的回答添加到历史记录，并显示在聊天窗口 (移入 try 块)
        history.append({"role":"assistant","content":answer})
        append_chat(assistant_name, clean_text, "#34A853")


    except Exception as e:
        # 7. 捕获错误并显示给用户
        error_text = f"[错误] API 调用失败或发生其他异常：{str(e)}"
        append_chat(assistant_name, error_text, "red")


# ======================
# GUI 布局
# ======================
chat_window = scrolledtext.ScrolledText(root, width=60, height=20, state='disabled')
chat_window.tag_config("user", foreground="blue")
chat_window.tag_config("bot", foreground="green")
chat_window.pack(padx=10, pady=10)

input_box = tk.Entry(root, width=50)
input_box.pack(side=tk.LEFT, padx=10, pady=10)
# 禁用回车发送 (用户原有代码)
# input_box.bind("<Return>", lambda e: send_message())

send_button = tk.Button(root, text="发送", command=send_message)
send_button.pack(side=tk.LEFT, padx=5)

# 功能按钮：新对话 & 导入知识库
reset_button = tk.Button(root, text="开启新对话", command=reset_chat)
reset_button.pack(side=tk.LEFT, padx=5)

import_button = tk.Button(root, text="导入知识库", command=import_knowledge_base)
import_button.pack(side=tk.LEFT, padx=5)

introduce_features()
root.mainloop()


"""
备注：
这是简单chat 的。。。
简陋版？阉割版？刻意反人类版？？（笑
"""

# 课题一（暂为旁听）
# 周宇博