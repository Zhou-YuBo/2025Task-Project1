# =================================
# 郑重声明
# 本软件为内部测试版，仅供研究参考。
# 严禁用于商业用途，否则后果自负。
# =================================
# ChatTool V3.25（试用版）
# 警告说明：
# 如果页面卡顿了，不必鸟它，装死而已。
# 消息发送后输入框不会自动清空，这是神的旨意。
# =================================
'''
目前有很多功能缺失，敬请期待完整版发布！

咳
笑死了
'''




import sys, json, csv, os, re, random, time
from datetime import datetime
import markdown2

from PyQt6.QtWidgets import (
    QApplication, QWidget, QTextEdit, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QInputDialog
)
from PyQt6.QtGui import QTextCursor, QFont
from PyQt6.QtCore import Qt, QTimer

from openai import OpenAI


# =================================
# 时间识别
# =================================
def get_datetime_answer(text):
    t = text.lower()
    now = datetime.now()
    if "时间" in t or "几点" in t:
        return f"现在时间是 {now.strftime('%H:%M:%S')}"
    if "日期" in t or "几号" in t or "今天" in t:
        return f"今天是 {now.strftime('%Y-%m-%d')}"
    if "星期" in t or "周几" in t:
        w = ["星期一","星期二","星期三","星期四","星期五","星期六","星期日"]
        return f"今天是 {w[now.weekday()]}"
    return None


# =================================
# 主界面（破感 UI）
# =================================
class BrokenChat(QWidget):
    def __init__(self):
        super().__init__()

        # 输入设置
        self.api_key = self.ask("请输入 API Key：")
        self.base_url = self.ask("请输入 Base URL：")
        self.user_name = self.ask("请输入昵称（默认“你”）") or "你"
        self.bot_name = self.ask("助手名字（默认“助手”）") or "助手"
        self.model_name = self.ask("模型名称（默认 deepseek-v3）") or "deepseek-v3"

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        self.history = []
        self.memories = []
        self.knowledge = []

        self.init_ui()
        self.introduce()

    def ask(self, msg):
        txt, ok = QInputDialog.getText(self, "设置", msg)
        if not ok:
            sys.exit()
        return txt

    # =================================
    # UI 构建
    # =================================
    def init_ui(self):
        self.setWindowTitle("ChatTool V3.25（试用版）")  # 山寨味
        self.setFixedSize(500, 400)

        # 随机把窗口移一点点，打造“抖动感”
        self.move(300 + random.randint(-2, 2), 200 + random.randint(-2, 2))

        layout = QVBoxLayout()

        # 聊天框（边框不对称，字体奇怪）
        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        self.chat.setStyleSheet("""
            QTextEdit {
                background: #F2F2F2;
                border-left: 6px solid #999;
                border-top: 1px solid #666;
                border-right: 2px solid #AAA;
                border-bottom: 3px solid #888;
                font-family: "SimSun";
                font-size: 13px;
            }
        """)
        layout.addWidget(self.chat)

        # 输入框（不自动清空）
        self.input = QLineEdit()
        self.input.setStyleSheet("""
            QLineEdit {
                background: #FCFCFC;
                border: 2px solid #777;
                font-family: "Microsoft Yahei";
            }
        """)
        layout.addWidget(self.input)

        # 按钮布局（故意排得不齐）
        bl = QHBoxLayout()

        self.send_btn = QPushButton(" 发送 ")
        self.send_btn.clicked.connect(self.fake_send_delay)
        self.btn_style(self.send_btn)
        bl.addWidget(self.send_btn)

        self.reset_btn = QPushButton("重置 ")
        self.reset_btn.clicked.connect(self.reset_chat)
        self.btn_style(self.reset_btn)
        bl.addWidget(self.reset_btn)

        self.load_btn = QPushButton(" 导入KB ")
        self.load_btn.clicked.connect(self.load_kb)
        self.btn_style(self.load_btn)
        bl.addWidget(self.load_btn)

        layout.addLayout(bl)
        self.setLayout(layout)

    # =================================
    # 按钮：山寨风
    # =================================
    def btn_style(self, btn):
        btn.setStyleSheet("""
            QPushButton {
                background: #DFDFDF;
                border: 2px solid #888;
                font-family: "Courier New";
            }
            QPushButton:pressed {
                background: #BEBEBE;
            }
        """)
        btn.setFixedHeight(32)
        btn.setFixedWidth(80 + random.randint(-5,5))  # 偏移长度

    # =================================
    # 自我介绍
    # =================================
    def introduce(self):
        intro = (
            f"欢迎使用 ChatTool V3.25（试用版）\n"
            f"助手：{self.bot_name}\n"
            f"警告：本软件为内部测试版，仅供研究参考。\n"
            f"-----------------------------"
        )
        self.append(self.bot_name, intro)

    # =================================
    # 聊天显示
    # =================================
    def append(self, who, msg):
        self.chat.append(f"{who}: {msg}")
        self.chat.moveCursor(QTextCursor.MoveOperation.End)

    # =================================
    # 假延迟（假卡顿）
    # =================================
    def fake_send_delay(self):
        # 如果用户连续点击太快
        if random.random() < 0.25:
            QMessageBox.warning(self, "提示", "指令过于频繁，请稍后再试。")
            return

        # 假闪烁
        self.chat.setStyleSheet("background: #FFECEC;")
        QTimer.singleShot(80, lambda: self.chat.setStyleSheet("""
            QTextEdit {
                background: #F2F2F2;
                border-left: 6px solid #999;
                border-top: 1px solid #666;
                border-right: 2px solid #AAA;
                border-bottom: 3px solid #888;
                font-family: "SimSun";
                font-size: 13px;
            }
        """))

        # 假卡顿：延迟 650 ms 后再调用真正发送
        QTimer.singleShot(650, self.send_message)

    # =================================
    # 重置对话
    # =================================
    def reset_chat(self):
        self.chat.clear()
        self.history.clear()
        self.memories.clear()
        self.append("系统", "对话窗口已清空（可能不完全）")

    # =================================
    # 导入知识库
    # =================================
    def load_kb(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择知识库", "", "CSV (*.csv);;JSON (*.json)")
        if not path:
            return

        imported = 0
        skipped = 0

        try:
            if path.endswith(".csv"):
                with open(path, encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        tag = row.get("tag","").strip()
                        cont = row.get("content","").strip()
                        if not tag or not cont:
                            skipped += 1
                            continue
                        self.knowledge.append({"tag":tag, "content": cont})
                        imported += 1

            else:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        tag = item.get("tag","").strip()
                        cont = item.get("content","").strip()
                        if not tag or not cont:
                            skipped += 1
                            continue
                        self.knowledge.append({"tag":tag, "content": cont})
                        imported += 1

            self.append("系统", f"KB 导入成功：{imported} 条，跳过 {skipped} 条")

        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    # =================================
    # 发送消息
    # =================================
    def send_message(self):
        text = self.input.text().strip()

        if not text:
            return

        self.append(self.user_name, text)
        # 注意：输入框故意不清空

        self.history.append({"role":"user", "content": text})

        # 时间识别
        dt = get_datetime_answer(text)
        if dt:
            self.append(self.bot_name, dt)
            return

        # KB 匹配
        kb = []
        for x in self.knowledge:
            if x["tag"].lower() in text.lower():
                kb.append(f"【{x['tag']}】 {x['content']}")

        kb_prompt = "\n".join(kb)

        msgs = []
        if kb_prompt:
            msgs.append({"role":"system","content": "知识库：\n" + kb_prompt})

        if self.memories:
            msgs.append({"role":"system","content":"记忆：\n" + "\n".join(self.memories)})

        msgs += self.history

        try:
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=msgs,
                max_tokens=1500
            )
            ans = resp.choices[0].message.content
            clean = re.sub("<[^>]+>", "", markdown2.markdown(ans))

            self.append(self.bot_name, clean)

            # 记忆提取
            memr = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role":"system","content":"提取值得记忆的内容，如无则返回空"},
                    {"role":"user","content": ans}
                ],
                max_tokens=40
            )
            mem = memr.choices[0].message.content.strip()
            if mem:
                self.memories.append(mem)

        except Exception as e:
            self.append("错误", str(e))


# =================================
# 主程序
# =================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = BrokenChat()
    win.show()
    sys.exit(app.exec())


