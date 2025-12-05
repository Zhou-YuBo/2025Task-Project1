"""
需要安装的包：
PyQt6 openai markdown2 requests beautifulsoup4
"""


''' 请忽略下面的版本提醒 '''
''' 因为需要OCR的功能放弃了'''
# # 版本问题：
# # 由于需要调用RapidOCR
# # 所以需要 Python 3.8 ~ 3.12（推荐3.10/3.11）


import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QMessageBox, QDialog, QLabel , 
    QFileDialog , QDoubleSpinBox
)
from PyQt6.QtGui import QFont
from openai import OpenAI

# 获取本地时间信息
from datetime import datetime

# 由于AI过于热衷于md格式，一堆**符号影响阅读，所以————
import markdown2
from PyQt6.QtGui import QTextCursor

# 为了导入外部知识库
import json
import csv
import os

# 为了阅读静态网页
import requests
from bs4 import BeautifulSoup

# # OCR + 截图
# from rapidocr_onnxruntime import RapidOCR   
# import mss
# from PIL import Image

# # 微信窗口控制
# import uiautomation as auto

# import re
# import base64
# from typing import List, Dict, Optional, Tuple
# from dataclasses import dataclass
# from enum import Enum



# ====== 第一级：自定义对话框 ======
class ApiInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("欢迎体验简单chat 2.0")
        self.setMinimumSize(650, 400)  # 和聊天窗口差不多大
        layout = QVBoxLayout(self)

        # 设置用户昵称
        label1 = QLabel("请输入您的用户昵称(默认“你”）：")
        layout.addWidget(label1)
        self.name_input = QLineEdit()
        self.name_input.setFont(QFont("Microsoft YaHei", 12))
        self.name_input.setPlaceholderText("你") # 如果用户没有输入昵称
        layout.addWidget(self.name_input)

        # 设置助手昵称
        label2 = QLabel("请输入助手昵称（默认“助手”）：")
        layout.addWidget(label2)
        self.assistant_input = QLineEdit()
        self.assistant_input.setFont(QFont("Microsoft YaHei", 12))
        self.assistant_input.setPlaceholderText("助手") # 默认助手名称
        layout.addWidget(self.assistant_input)  

        # 设置用户要调用的模型
        label3 = QLabel("请输入要调用的模型（一定要用官方名称）：")
        layout.addWidget(label3)
        self.model_input = QLineEdit()
        self.model_input.setFont(QFont("Microsoft YaHei", 12))
        self.model_input.setPlaceholderText("deepseek-v3") # 默认模型
        layout.addWidget(self.model_input) #自定义模型

        # 设置 API Key 和 Base URL
        label4 = QLabel("请输入你的 API Key:")
        layout.addWidget(label4)
        self.api_input = QLineEdit()
        self.api_input.setFont(QFont("Microsoft YaHei", 12))
        layout.addWidget(self.api_input)

        label5 = QLabel("请输入你的 Base URL（API地址）：")
        layout.addWidget(label5)
        self.url_input = QLineEdit()
        self.url_input.setFont(QFont("Microsoft YaHei", 12))
        self.url_input.setPlaceholderText("https://aistudio.baidu.com/llm/lmapi/v3")
        layout.addWidget(self.url_input)

        # 确定按钮
        self.ok_button = QPushButton("确定")
        self.ok_button.setFont(QFont("Microsoft YaHei", 12))
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)
        self.ok_button.setAutoDefault(True)
        self.ok_button.setDefault(True)

    def get_values(self):
        if self.exec():  # 显示窗口并阻塞，点击确定返回 True
            return (
                self.name_input.text().strip() ,
                self.assistant_input.text().strip() ,
                self.model_input.text().strip() ,
                self.api_input.text().strip(),  
                self.url_input.text().strip(),
                True
            )
            
        else:
            return "", "", "", "", False


# ====== 模型参数调节窗口 ======
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("高级：调整模型参数")
        self.setMinimumSize(400, 350)

        layout = QVBoxLayout(self)

        # 预设模式下拉框
        from PyQt6.QtWidgets import QComboBox
        self.preset_box = QComboBox()
        self.preset_box.addItems([
            "默认模式",
            "创造力模式（高 Temperature）",
            "稳定模式（低 Temperature）",
            "精确答题（Top-p 限制）"
        ])
        self.preset_box.currentIndexChanged.connect(self.apply_preset)
        layout.addWidget(QLabel("预设模式："))
        layout.addWidget(self.preset_box)

        # Temperature
        layout.addWidget(QLabel("Temperature："))
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0, 2)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setValue(parent.temperature)
        layout.addWidget(self.temp_spin)

        # Top-p
        layout.addWidget(QLabel("Top-p："))
        self.top_p_spin = QDoubleSpinBox()
        self.top_p_spin.setRange(0, 1)
        self.top_p_spin.setSingleStep(0.05)
        self.top_p_spin.setValue(parent.top_p)
        layout.addWidget(self.top_p_spin)

        # Max tokens
        layout.addWidget(QLabel("Max tokens："))
        self.max_tokens_spin = QDoubleSpinBox()
        self.max_tokens_spin.setRange(0, 32000)
        self.max_tokens_spin.setValue(parent.max_tokens)
        self.max_tokens_spin.setSingleStep(256)
        layout.addWidget(self.max_tokens_spin)

        # frequency_penalty
        layout.addWidget(QLabel("Frequency Penalty："))
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(0, 2)
        self.freq_spin.setSingleStep(0.1)
        self.freq_spin.setValue(parent.frequency_penalty)
        layout.addWidget(self.freq_spin)

        # presence_penalty
        layout.addWidget(QLabel("Presence Penalty："))
        self.pres_spin = QDoubleSpinBox()
        self.pres_spin.setRange(0, 2)
        self.pres_spin.setSingleStep(0.1)
        self.pres_spin.setValue(parent.presence_penalty)
        layout.addWidget(self.pres_spin)

        # Save button
        self.btn_save = QPushButton("保存")
        self.btn_save.clicked.connect(self.accept)
        layout.addWidget(self.btn_save)

    def apply_preset(self):
        mode = self.preset_box.currentText()
        if mode == "默认模式":
            self.temp_spin.setValue(1.0)
            self.top_p_spin.setValue(1.0)
        elif mode == "创造力模式（高 Temperature）":
            self.temp_spin.setValue(1.5)
            self.top_p_spin.setValue(1.0)
        elif mode == "稳定模式（低 Temperature）":
            self.temp_spin.setValue(0.6)
            self.top_p_spin.setValue(0.9)
        elif mode == "精确答题（Top-p 限制）":
            self.temp_spin.setValue(0.8)
            self.top_p_spin.setValue(0.5)


# ====== URL 和总结问题输入窗口 ======
class UrlInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("网页浏览与总结")
        self.setFixedSize(500, 250)
        layout = QVBoxLayout(self)

        # 网址输入
        layout.addWidget(QLabel("请输入要总结的网址 (URL):"))
        self.url_input = QLineEdit()
        self.url_input.setFont(QFont("Microsoft YaHei", 10))
        self.url_input.setPlaceholderText("https://...")
        layout.addWidget(self.url_input)

        # 总结问题输入
        layout.addWidget(QLabel("请输入总结要求 (可选，默认总结主要内容):"))
        self.query_input = QLineEdit()
        self.query_input.setFont(QFont("Microsoft YaHei", 10))
        self.query_input.setPlaceholderText("例如：找出本文中提到的三个关键技术点")
        layout.addWidget(self.query_input)

        # 确定按钮
        self.ok_button = QPushButton("开始总结")
        self.ok_button.setFont(QFont("Microsoft YaHei", 11))
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)

    def get_values(self):
        if self.exec():  # 显示窗口并阻塞
            url = self.url_input.text().strip()
            query = self.query_input.text().strip()
            return url, query if query else "请总结这篇网页的主要内容", True
        else:
            return "", "", False
        


# ====== 识别时间日期函数 ======
def get_datetime_answer(user_text):
    """
    识别用户是否询问日期、时间或星期
    """
    text = user_text.lower()
    now = datetime.now()

    if any(k in text for k in ["时间", "几点","多少点"]):
        return f"现在时间是 {now.strftime('%H:%M:%S')}"
    elif any(k in text for k in ["日期", "几号", "几日"]):
        return f"今天是 {now.strftime('%Y-%m-%d')}"
    elif any(k in text for k in ["月"]):
        return f"今天是 {now.strftime('%m')} 月份"
    elif any(k in text for k in ["年"]):  
        return f"现在是 {now.strftime('%Y')} 年"
    elif any(k in text for k in ["星期", "星期几", "周几"]):
        week_map = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        return f"今天是 {week_map[now.weekday()]}"
    else:
        return None
    



# ====== 第二级：聊天主窗口 ======
class ChatWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("简单chat 2.0")
        self.setMinimumSize(960,600)

        # ====== 使用自定义对话框输入 用户昵称、助手昵称、API Key 和 Base URL ======
        dialog = ApiInputDialog(self)
        user_name, assistant_name, model_name, api_key, base_url, ok = dialog.get_values()

        if not user_name:
            user_name = "你"
        if not assistant_name:
            assistant_name = "助手"
        if not model_name:
            model_name = "deepseek-v3"
        if not base_url:
            base_url = "https://aistudio.baidu.com/llm/lmapi/v3"
        if not ok or not api_key :
            QMessageBox.critical(self, "错误", "API Key 不能为空")
            sys.exit()

        self.user_name = user_name
        self.assistant_name = assistant_name
        self.model_name = model_name


        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.history = []
        self.important_memory = []  # 用于存放助手认为重要的记忆
        self.knowledge_base = []  # 用于存储导入的外部知识库条目


        # --------- 默认参数 ---------
        self.temperature = 1.0
        self.top_p = 1.0
        self.max_tokens = 2048
        self.frequency_penalty = 0.0
        self.presence_penalty = 0.0



        # ====== UI 主布局 ======
        main_layout = QHBoxLayout(self)


        # ---------左侧：对话区---------
        chat_layout = QVBoxLayout()

        # 聊天记录显示框
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setFont(QFont("Microsoft YaHei", 12))
        self.chat_area.setStyleSheet("""
            QTextEdit {
                background: #FAFAFA;
                border: none;
                padding: 10px;
            }
        """)
        chat_layout.addWidget(self.chat_area)

        # 底部输入区域
        bottom_layout = QHBoxLayout()

        self.input_box = QLineEdit()
        self.input_box.setFont(QFont("Microsoft YaHei", 11))
        self.input_box.setPlaceholderText("输入你的问题...")
        self.input_box.setStyleSheet("""
            QLineEdit {
                border: 2px solid #DDDDDD;
                border-radius: 8px;
                padding: 8px;
            }
            QLineEdit:focus {
                border: 2px solid #4285F4;
            }
        """)
        self.input_box.returnPressed.connect(self.send_message)
        bottom_layout.addWidget(self.input_box)

        self.send_button = QPushButton("发送")
        self.send_button.setFont(QFont("Microsoft YaHei", 11))
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #4285F4;
                color: white;
                padding: 10px 18px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #5A95F5;
            }
            QPushButton:pressed {
                background-color: #2F6DE0;
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        bottom_layout.addWidget(self.send_button)

        chat_layout.addLayout(bottom_layout)
        self.introduce_features() # 调出窗口后立即自我介绍

        # 将左侧对话区加入主布局
        main_layout.addLayout(chat_layout, 3)



        # ----------右侧：功能区----------
        sidebar = QWidget() 
        sidebar.setFixedWidth(220) # 侧边栏宽度
        sidebar_layout = QVBoxLayout() 
        sidebar_layout.setContentsMargins(10, 10, 10, 10) # 边距
        sidebar_layout.setSpacing(12) # 元素间距


        # 增添功能按钮（6号至今仅占位）

        # 按钮1：开启新对话
        self.btn_new_chat = QPushButton("开启新对话")
        self.btn_new_chat.setFont(QFont("Microsoft YaHei", 11))
        sidebar_layout.addWidget(self.btn_new_chat)
        self.btn_new_chat.clicked.connect(self.reset_chat)


        # 按钮2：知识库导入
        self.btn_import_kBase = QPushButton("导入外部知识库")
        self.btn_import_kBase.setFont(QFont("Microsoft YaHei", 11))
        sidebar_layout.addWidget(self.btn_import_kBase)
        self.btn_import_kBase.clicked.connect(self.import_knowledge_base)

        # 按钮3：导出当前对话记录
        self.btn_export_chat = QPushButton("导出当前对话记录")
        self.btn_export_chat.setFont(QFont("Microsoft YaHei", 11))
        sidebar_layout.addWidget(self.btn_export_chat)
        self.btn_export_chat.clicked.connect(self.export_chat)

        # 按钮4：调参
        self.btn_adjust_parameters = QPushButton("高级：调整模型参数")
        self.btn_adjust_parameters.setFont(QFont("Microsoft YaHei", 11))
        sidebar_layout.addWidget(self.btn_adjust_parameters)
        self.btn_adjust_parameters.clicked.connect(self.open_settings_dialog)

        # 按钮5：阅读指定网页
        self.btn_web_summary = QPushButton("🌐 网页自动总结")
        self.btn_web_summary.setFont(QFont("Microsoft YaHei", 11))
        sidebar_layout.addWidget(self.btn_web_summary)
        self.btn_web_summary.clicked.connect(self.open_url_dialog)

        # 按钮6：自动总结微信聊天记录
        self.btn_wechat_summary = QPushButton("🗨️ 总结微信聊天(我是占位的)")
        self.btn_wechat_summary.setFont(QFont("Microsoft YaHei", 11))
        sidebar_layout.addWidget(self.btn_wechat_summary)


        # 拉伸占位，使按钮靠上
        sidebar_layout.addStretch()

        # 设置侧边栏
        sidebar.setLayout(sidebar_layout)
        # 把右侧功能栏加入主布局
        main_layout.addWidget(sidebar, 1)

    # ====== 助手自我介绍 ======
    def introduce_features(self):
        intro_text = ( 
        f"你好，我是<b>{self.assistant_name}</b>！<br>"
        f"我可以帮你：<br>"
        f"1. 回答各种问题，并记住会话中的重要信息。<br>"
        f"2. 获取当前的日期、时间和星期。<br>"
        f"3. 联网阅读指定的静态网页，并为你总结主要内容。<br>"
        f"4. （高级功能）可以导入外部数据库或知识库的信息，为你提供更专业的回答。<br>"
        f"5. （高级功能）可以自定义模型参数。<br><br>"
        f"{self.assistant_name}特别提醒：外部知识库仅支持 csv 和 json 哦~<br>"
        f"目前{self.assistant_name}只懂看简单规整的知识库，而且——<br>"
        f"（划重点！）一定要带上 tag 和 content !<br>"
        f"否则{self.assistant_name}一律跳过！~<br><br>"       
        )

        # 保持HTML格式
        html_intro = markdown2.markdown(intro_text)
        self.append_chat(self.assistant_name, html_intro, color="#34A853")
        # 让助手记住自己的介绍
        self.history.append({"role": "assistant", "content": intro_text})

    # ========== 开启新对话 ==========
    def reset_chat(self):
        self.chat_area.clear()
        self.history = []
        self.important_memory = []
        self.introduce_features()


    # ====== 导入外部知识库 ======
    def import_knowledge_base(self):

        # 1.打开文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择知识库文件",
            "",
            "CSV 文件 (*.csv);;JSON 文件 (*.json)"
        )
        if not file_path:
            return

        ext = os.path.splitext(file_path)[1].lower()
        imported_count = 0 # 统计成功导入条目数量
        skipped_count = 0  # 统计不合规条目数量

        try:
            if ext == ".csv":
                with open(file_path, newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f) 
                    for row in reader:
                        tag = row.get("tag", "").strip()
                        content = row.get("content", "").strip()
                        if not tag or not content:
                            skipped_count += 1
                            continue
                        self.knowledge_base.append({"tag": tag, "content": content})
                        imported_count += 1

            elif ext == ".json":
                with open(file_path, encoding='utf-8') as f:
                    data = json.load(f) 
                    for item in data:
                        tag = item.get("tag", "").strip()
                        content = item.get("content", "").strip()
                        if not tag or not content:
                            skipped_count += 1
                            continue
                        self.knowledge_base.append({"tag": tag, "content": content})
                        imported_count += 1

            else:
                QMessageBox.warning(self, "文件错误", "请选择 CSV 或 JSON 文件")
                return

        except Exception as e:
            QMessageBox.critical(self, "导入错误", str(e))
            return

        # 2. 显示导入结果
        QMessageBox.information(
            self,
            "导入完成",
            f"已成功导入 {imported_count} 条知识，"
            f"{skipped_count} 条不符合规则（缺少 tag 或 content）被跳过。\n"
            f"文件名：{os.path.basename(file_path)}"
        )

        # 3. 同时在聊天区显示
        self.append_chat(
            self.assistant_name,
            f"已成功导入 {imported_count} 条知识库条目，"
            f"{skipped_count} 条不符合规则被跳过。",
            color="#34A853"
        )


    # ====== 导出当前对话记录 ======
    def export_chat(self):
        if not self.history:
            QMessageBox.warning(self, "提示", "当前没有任何对话可以导出！")
            return

        # 让用户选择保存文件路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出聊天记录", "聊天记录.txt", "文本文件 (*.txt)"
        )
        if not file_path:
            return

        import re

        # HTML 标签清理（b/i/u/br 等）
        html_tag_pattern = re.compile(r"<.*?>", flags=re.S)

        # Markdown 清理（**, *, __, _）
        md_bold = re.compile(r"\*\*(.*?)\*\*")
        md_italic = re.compile(r"\*(.*?)\*")
        md_bold2 = re.compile(r"__(.*?)__")
        md_italic2 = re.compile(r"_(.*?)_")

        def clean_text(text):
            # HTML 换行转换
            text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")

            # 去除 HTML 标签
            text = re.sub(html_tag_pattern, "", text)

            # Markdown 简化为普通文本
            text = re.sub(md_bold, r"\1", text)
            text = re.sub(md_italic, r"\1", text)
            text = re.sub(md_bold2, r"\1", text)
            text = re.sub(md_italic2, r"\1", text)

            # 去掉多余空格
            return text.strip()

        output_lines = []

        for item in self.history:
            role = item.get("role", "")
            content = item.get("content", "")

            # 映射自定义昵称
            display_role = self.user_name if role == "user" else self.assistant_name

            clean_content = clean_text(content) 

            # 添加到导出文本
            output_lines.append(f"{display_role}:\n{clean_content}\n")

        # 组合成最终文本
        final_text = "\n".join(output_lines)

        # 写入文件
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(final_text)

            QMessageBox.information(self, "成功", f"聊天记录已导出：\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败：{e}")


    # ------------- 调参窗口 -------------
    def open_settings_dialog(self):
        dialog = SettingsDialog(self)
        if dialog.exec():  # 用户点击保存
            self.temperature = dialog.temp_spin.value()
            self.top_p = dialog.top_p_spin.value()
            self.max_tokens = int(dialog.max_tokens_spin.value())
            self.frequency_penalty = dialog.freq_spin.value()
            self.presence_penalty = dialog.pres_spin.value()

            QMessageBox.information(self, "成功", "参数已更新！")

    # ------------- 网页总结窗口 -------------
    def open_url_dialog(self):
        """
        打开 URL 输入对话框，并处理结果。
        """
        dialog = UrlInputDialog(self) 
        url, query, ok = dialog.get_values()

        if not ok or not url:
            if not ok:
                return # 用户取消
            else:
                QMessageBox.warning(self, "错误", "网址不能为空。")
                return

        # 告诉用户正在处理
        self.append_chat(
            self.assistant_name,
            f"正在从 <b>{url}</b> 获取内容并总结，请稍候...",
            color="#FFA500" # 橙色提示
        )

        # 调用核心逻辑
        summary = self.fetch_and_summarize(url, query)
        
        # 显示总结结果
        self.append_chat(self.assistant_name, summary, color="#34A853")
        
        # 记录到历史
        self.history.append({"role": "user", "content": f"请总结网页: {url}，要求: {query}"})
        self.history.append({"role": "assistant", "content": summary})


    # ------------ 阅读指定静态网页 ------------
    def fetch_and_summarize(self, url, query="请总结这篇网页的主要内容"):
        """
        联网获取指定URL的内容，清洗后交由LLM进行总结。
        增强了反爬机制（User-Agent）和内容类型检查。
        """
        # 添加 User-Agent 标头，伪装成浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
        }

        try:
            # 1. 网页内容获取，增加User-Agent和较长超时时间
            response = requests.get(url, headers=headers, timeout=20) # 超时增加到 20 秒
            response.raise_for_status() # 检查HTTP错误（如 404, 500）

            # 2. 检查内容类型 (新增步骤：阻止 PDF 或其他二进制文件解析)
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' not in content_type:
                # 针对 PDF 文件给出特定提示
                if 'application/pdf' in content_type:
                    return f"<b style='color:red'>[内容错误]</b> 抱歉，目前不支持直接阅读 PDF 文档。"
                # 针对其他非 HTML 内容给出提示
                else:
                    return f"<b style='color:red'>[内容错误]</b> 抱歉，获取到的内容不是HTML格式（{content_type}）。"

            # 3. 内容清洗（提取可读文本）
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 移除脚本、样式、导航等不相关元素
            for script_or_style in soup(['script', 'style', 'header', 'footer', 'nav', 'aside']): 
                script_or_style.decompose() 

            # 提取所有可见文本，并去除多余空行
            text = soup.get_text(separator='\n', strip=True)

            # （打打补丁）如果任务超出静态阅读的能力范围，给出提示
            # 检查文本是否过短且包含 JavaScript 提示
            # 如果文本长度小于 2000 且包含 "javascript", "enable scripts", "动态加载" 等关键字，则判断为动态网站骨架
            if len(text) < 2000 and any(kw in text.lower() for kw in ["javascript", "enable scripts", "动态加载", "启用脚本"]):
                # 发现动态内容提示，立即返回错误信息，不再调用 LLM
                error_message = (
                    f"<b style='color:red'>[功能限制]</b> 目标网页内容是 <b>JavaScript 动态加载</b>的。<br>"
                    f"当前的静态网页抓取功能 (requests+BeautifulSoup) <b>无法获取</b>动态加载的内容。<br>"
                    f"请尝试使用纯文本/静态内容的网址。"
                )
                return error_message
            
            # 限制发送给LLM的文本长度，防止超出Token限制
            max_summary_tokens = 50000 
            if len(text) > max_summary_tokens:
                text = text[:max_summary_tokens]
                
            # 4. 准备 LLM 总结 Prompt
            summary_prompt = (
                f"{query}，请根据以下提供的网页内容进行总结：\n\n"
                f"--- 网页内容开始 ---\n"
                f"{text}\n"
                f"--- 网页内容结束 ---\n"
            )
            
            # 5. 调用 LLM 进行总结
            messages = [
                {"role": "system", "content": "你是一位专业的网页内容总结助手，请根据提供的文本简洁明了地总结核心要点。"},
                {"role": "user", "content": summary_prompt}
            ]
            
            summary_response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7 
            )
            summary = summary_response.choices[0].message.content

            # 将 Markdown 转 HTML
            return markdown2.markdown(summary)
            
        except requests.exceptions.RequestException as e:
            # 专门处理网络连接和HTTP错误
            return f"<b style='color:red'>[网络错误]</b> 无法连接或获取网页内容：{e}"
        except Exception as e:
            # 统一处理其他任何意外的程序错误
            return f"<b style='color:red'>[处理错误]</b> 网页内容处理失败：{e}"

 


    # ====== 发送消息逻辑 ======
    def send_message(self):
        user_text = self.input_box.text().strip()
        if not user_text:
            return

        # 显示用户消息
        self.append_chat(self.user_name, user_text, color="#1A73E8")
        self.input_box.clear() # 清空输入框

        # 保存用户消息到历史
        self.history.append({"role": "user", "content": user_text})
        
        # ---------------识别时间日期询问-------------
        datetime_answer = get_datetime_answer(user_text)
        if datetime_answer:
            self.append_chat(self.assistant_name, datetime_answer, color="#34A853")
            return # 直接返回，不调用API
        
        # -------------- 扫描知识库匹配相关内容 ------------
        matched_kb = []
        if self.knowledge_base:
            for item in self.knowledge_base:
                tag = item["tag"].lower()
                content = item["content"]
                if tag in user_text.lower():
                    matched_kb.append(f"[{tag}] {content}")

        kb_prompt = ""
        if matched_kb:
            kb_prompt = "请参考以下知识库内容回答用户问题：\n" + "\n".join(matched_kb)

        # ----------- 将memory、知识库作为system消息加入历史 ------------
        messages = []
        # 加入知识库
        if kb_prompt:
            messages.append({"role": "system", "content": kb_prompt})

        # ---------------- 加入重要记忆 ----------------
        memory_prompt = ""
        if self.important_memory:
            memory_prompt = "助手请记住以下信息，在回答问题时参考：\n" + "\n".join(self.important_memory)
            messages.append({"role": "system", "content": memory_prompt})

        # ---------------- 加入历史对话 ----------------
        messages += self.history


        
        # =============正常的API调用流程=============
        try:
            response = self.client.chat.completions.create(
                model = self.model_name ,
                messages = messages,
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=(None if self.max_tokens == 0 else self.max_tokens),
                frequency_penalty=self.frequency_penalty,
                presence_penalty=self.presence_penalty
            )
            answer = response.choices[0].message.content

            # 将 Markdown 转 HTML,  免得又来一堆**符号
            html = markdown2.markdown(answer)

            # 请求助手判断是否记忆该信息
            memory_check_response = self.client.chat.completions.create(
                model = self.model_name ,
                messages=[
                    {"role": "system", "content": "请从以下用户消息中判断哪些信息值得记忆，只输出一句或几个重点，不需要解释 // 要求慎重选择记忆的内容 // 如果没有特别重要的内容，可以不记忆："},
                    {"role": "user", "content": answer}
                ],
                max_tokens = 80
            )
            memory_text = memory_check_response.choices[0].message.content.strip()
            if memory_text:
                self.important_memory.append(memory_text)

        except Exception as e:
            answer = f"[错误] {str(e)}"
            html = answer

        # 记录助手消息
        self.history.append({"role": "assistant", "content": answer})
        # 显示助手消息
        self.append_chat(self.assistant_name, html, color="#34A853")

    # ====== 聊天显示函数 ======
    def append_chat(self, speaker, text, color="#000000"):
        """
        使用 insertHtml 渲染 HTML（支持 Markdown2 转 HTML）
        """
        self.chat_area.moveCursor(QTextCursor.MoveOperation.End)  # 光标移到末尾(需要用PyQt6的语法，所以加上MoveOperation)
        self.chat_area.insertHtml(f"<b style='color:{color}'>{speaker}：</b> {text}<br><br>")
        self.chat_area.verticalScrollBar().setValue(self.chat_area.verticalScrollBar().maximum())  # 自动滚动到底部


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ChatWindow()
    win.show()
    sys.exit(app.exec())


"""
有点无聊的“更新日志”

2025/12/2 上午
1.0 : “原始”对话程序的基础上，有UI了
      用的是tkinter，界面真的... ... 啧，梦回千禧年（笑）
      脑子说它蛮喜欢的，但手指不同意
1.1 ：改用PyQt6制作UI，原版UI我觉得可以拿来做个怀旧版，嘿咻~
1.2 ：可以自定义昵称、API、Base URL
1.3 ：加入enter发送功能；把讨厌的markdown转成html显示
1.4 ：加入时间日期识别功能，（一字一顿）修复了部分已知bug（玛德哪门子套话）

2025/12/2 下午
1.5 : 加入重点记忆功能
1.6 : 加入侧边栏，支持一键开启新对话
1.7 : 加入外部知识库导入功能
1.8 ：支持导出对话记录

2025/12/2 晚上
1.9 ：修复导出功能bug（谜之乱码 & html/markdownd的古怪痕迹）

2025/12/3 早上
1.10 ：支持自定义调参（含预设）
（放弃了流式输出，直接输出都能偶尔卡一下）

2025/12/3 晚上
1.11 ：加入网页总结功能（仅限静态网页）

2025/12/4 
啧，Gemini啥馊主意，用UIAutomation获取聊天记录。。。
不对，该死的还有微信，更新了个啥啊woc
OCR也一团糟，找窗口也一团糟（笑

2025/12/5 凌晨
dead line在即，那么...
（暂时  吧？）放弃微信总结功能，小白姑且不折腾了
所以————

2.0
完结
    撒花


"""

# 哦，对了，这个不能忘：
# 指导老师：（或者说打工牛马doge）(一码归一码，这货的产品思维若汁得一言难尽)
# ChatGPT & Gemini & DeepSeek  

# 特别鸣谢：
# skycode秋令营的学长们

# 课题一（暂为旁听）
# 周宇博