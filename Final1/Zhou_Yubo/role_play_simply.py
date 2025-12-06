import sys
import json
import re
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QStackedWidget, QRadioButton, QFormLayout, QSpinBox,
    QTextEdit, QFileDialog, QListWidget, QListWidgetItem, QInputDialog,
    QGroupBox, QComboBox, QScrollArea, QMessageBox, QFrame
)
from PyQt6.QtGui import QPixmap, QFont, QTextCursor, QColor, QTextCharFormat, QIcon
from PyQt6.QtCore import Qt, QTimer

# Try to import the client you use in your other project.
try:
    from openai import OpenAI
except Exception as e:
    OpenAI = None
    _OPENAI_IMPORT_ERROR = e


class APIFormPage(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main
        layout = QVBoxLayout()
        title = QLabel("第 1 步 — 填写 API 配置")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:18px; margin:8px;")
        layout.addWidget(title)

        form = QFormLayout()
        self.api_key_input = QLineEdit()
        self.api_url_input = QLineEdit()
        self.model_input = QLineEdit()

        self.api_key_input.setPlaceholderText("API Key ")
        self.api_url_input.setPlaceholderText("例如：https://aistudio.baidu.com/llm/lmapi/v3")
        self.model_input.setPlaceholderText("例如：deepseek-v3")

        form.addRow("API Key:", self.api_key_input)
        form.addRow("API 地址:", self.api_url_input)
        form.addRow("模型名称:", self.model_input)
        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        next_btn = QPushButton("下一步")
        next_btn.clicked.connect(self.on_next)
        btn_layout.addWidget(next_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def on_next(self):
        # 验证必填字段
        api_key = self.api_key_input.text().strip()
        api_url = self.api_url_input.text().strip()
        model = self.model_input.text().strip()
        
        if not api_key:
            QMessageBox.warning(self, "警告", "请填写 API Key")
            return
            
        if not api_url:
            QMessageBox.warning(self, "警告", "请填写 API 地址")
            return
            
        if not model:
            QMessageBox.warning(self, "警告", "请填写模型名称")
            return
        
        # save to state
        self.main.app_state['api_key'] = api_key
        self.main.app_state['api_url'] = api_url
        self.main.app_state['model'] = model
        
        # init client immediately (so errors are detected early)
        if not self.main.init_api_client():
            QMessageBox.warning(self, "API 初始化失败", 
                               f"无法初始化 API 客户端：{self.main.app_state.get('_client_init_error', '未知错误')}")
            return
            
        # advance
        self.main.stack.setCurrentIndex(1)


class ModeSelectPage(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main
        layout = QVBoxLayout()
        title = QLabel("第 2 步 — 选择模式")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:18px; margin:8px;")
        layout.addWidget(title)

        description = QLabel("对话模式：普通的角色扮演对话\n攻略模式：包含好感度和信任度系统，数值会影响角色反应")
        description.setStyleSheet("color: #666; margin: 10px;")
        layout.addWidget(description)

        rb_layout = QHBoxLayout()
        self.chat_rb = QRadioButton("对话模式")
        self.guide_rb = QRadioButton("攻略模式（启用好感度 & 信任）")
        self.chat_rb.setChecked(True)

        rb_layout.addWidget(self.chat_rb)
        rb_layout.addWidget(self.guide_rb)
        layout.addLayout(rb_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        back_btn = QPushButton("上一步")
        back_btn.clicked.connect(lambda: self.main.stack.setCurrentIndex(0))
        next_btn = QPushButton("下一步")
        next_btn.clicked.connect(self.on_next)
        btn_layout.addWidget(back_btn)
        btn_layout.addWidget(next_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def on_next(self):
        mode = "chat"
        if self.guide_rb.isChecked():
            mode = "guide"
        self.main.app_state['mode'] = mode
        # choose which character page to show
        if mode == "chat":
            self.main.stack.setCurrentIndex(2)  # 对话模式角色页
        else:
            self.main.stack.setCurrentIndex(3)  # 攻略模式角色页


class CharacterFormPage(QWidget):
    def __init__(self, main, is_guide=False):
        super().__init__()
        self.main = main
        self.is_guide = is_guide
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        title = QLabel("角色设定（请填写）" + (" — 攻略模式额外设置" if self.is_guide else ""))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:18px; margin:8px;")
        layout.addWidget(title)

        form = QFormLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例如：作者梦到什么说什么")
        self.sex_combo = QComboBox()
        self.sex_combo.addItems(["男", "女", "动物", "其他"])
        self.age_spin = QSpinBox()
        self.age_spin.setRange(0, 200)
        self.age_spin.setValue(25)
        self.job_input = QLineEdit()
        self.job_input.setPlaceholderText("例如：学生、程序员、艺术家")
        self.identity_input = QLineEdit()
        self.identity_input.setPlaceholderText("例如：朋友、恋人、上级")
        self.appearance_input = QLineEdit()
        self.appearance_input.setPlaceholderText("例如：黑色长发，戴眼镜，身高165cm")
        self.style_input = QLineEdit()  # 默认穿搭
        self.style_input.setPlaceholderText("例如：大白褂陪运动服")
        self.personality_input = QLineEdit()
        self.personality_input.setPlaceholderText("例如：温柔但内向，喜欢帮助别人")
        self.hobby_input = QLineEdit()
        self.hobby_input.setPlaceholderText("例如：读书、看电影、画画")
        self.call_player_input = QLineEdit()
        self.call_player_input.setPlaceholderText("例如：你、朋友、伙伴")
        self.call_player_input.setText("你")
        self.dialog_style_input = QLineEdit()
        self.dialog_style_input.setPlaceholderText("例如：口语化、温柔、偶尔撒娇")

        form.addRow("名字:", self.name_input)
        form.addRow("性别:", self.sex_combo)
        form.addRow("年龄:", self.age_spin)
        form.addRow("职业:", self.job_input)
        form.addRow("关系:", self.identity_input)
        form.addRow("外貌:", self.appearance_input)
        form.addRow("默认穿搭:", self.style_input)
        form.addRow("性格:", self.personality_input)
        form.addRow("爱好:", self.hobby_input)
        form.addRow("如何称呼玩家:", self.call_player_input)
        form.addRow("对话风格:", self.dialog_style_input)

        layout.addLayout(form)

        # guide-only settings
        self.guide_group = QGroupBox("攻略模式：初始数值（仅在攻略模式可见）")
        gg_layout = QFormLayout()
        self.affection_spin = QSpinBox()
        self.affection_spin.setRange(0, 100)
        self.affection_spin.setValue(50)
        self.affection_spin.setSuffix(" (0-100)")
        self.trust_spin = QSpinBox()
        self.trust_spin.setRange(0, 100)
        self.trust_spin.setValue(50)
        self.trust_spin.setSuffix(" (0-100)")
        gg_layout.addRow("初始好感度:", self.affection_spin)
        gg_layout.addRow("初始信任度:", self.trust_spin)
        self.guide_group.setLayout(gg_layout)
        self.guide_group.setVisible(self.is_guide)
        layout.addWidget(self.guide_group)

        # 示例按钮
        example_btn = QPushButton("填充示例角色")
        example_btn.clicked.connect(self.fill_example)
        layout.addWidget(example_btn)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        back_btn = QPushButton("上一步")
        # back to mode select
        back_btn.clicked.connect(lambda: self.main.stack.setCurrentIndex(1))
        next_btn = QPushButton("下一步")
        next_btn.clicked.connect(self.on_next)
        btn_layout.addWidget(back_btn)
        btn_layout.addWidget(next_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def fill_example(self):
        """填充示例角色数据"""
        self.name_input.setText("作者梦到什么写什么")
        self.sex_combo.setCurrentText("男")
        self.age_spin.setValue(26)
        self.job_input.setText("黑水镇在逃通缉犯")
        self.identity_input.setText("朋友")
        self.appearance_input.setText("金色短发")
        self.style_input.setText("法奥斯军校制服")
        self.personality_input.setText("调皮捣蛋，嘻嘻哈哈，走路从不认真看路")
        self.hobby_input.setText("跑非洲开酒馆、吃甜品、走街串巷兜售千纸鹤")
        self.call_player_input.setText("那个那个谁")
        self.dialog_style_input.setText("冷静、略带疏离感，喜爱医学隐喻，含蓄的掌控感，有时极致反差感")

    def on_next(self):
        # 验证必填字段
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "请填写角色名字")
            return
            
        char = {
            "name": name,
            "sex": self.sex_combo.currentText(),
            "age": self.age_spin.value(),
            "job": self.job_input.text().strip() or "未指定",
            "identity": self.identity_input.text().strip() or "未指定",
            "appearance": self.appearance_input.text().strip() or "未指定",
            "default_style": self.style_input.text().strip() or "未指定",
            "personality": self.personality_input.text().strip() or "未指定",
            "hobby": self.hobby_input.text().strip() or "未指定",
            "call_player_as": self.call_player_input.text().strip() or "你",
            "dialog_style": self.dialog_style_input.text().strip() or "普通"
        }
        
        self.main.app_state['character'] = char
        
        if self.is_guide:
            self.main.app_state['affection'] = self.affection_spin.value()
            self.main.app_state['trust'] = self.trust_spin.value()
        else:
            # 对话模式也设置默认值，但不会显示
            self.main.app_state.setdefault('affection', 50)
            self.main.app_state.setdefault('trust', 50)
            
        self.main.app_state.setdefault('days', 1)
        # 初始化消息历史
        self.main.app_state.setdefault('messages', [])
        
        # 初始化pending值
        self.main.app_state.setdefault('affection_pending', 0.0)
        self.main.app_state.setdefault('trust_pending', 0.0)
        
        # 生成系统提示词
        self.main.generate_system_prompt()
        
        # go to main game page
        self.main.stack.setCurrentIndex(4)


class GameMainPage(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.images = []  # list of {"path":..., "tags":[...], "pixmap": QPixmap}
        self.current_image_index = -1
        self.showing_thinking = False
        self.thinking_message_id = None
        self.init_ui()

    def init_ui(self):
        root = QHBoxLayout()
        # Left: image area
        left = QVBoxLayout()
        left_title = QLabel("画像区")
        left_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_title.setStyleSheet("font-weight: bold; color: #555; margin-bottom: 10px;")
        left.addWidget(left_title)

        self.image_frame = QFrame()
        self.image_frame.setFixedSize(340, 340)
        self.image_frame.setStyleSheet("""
            QFrame {
                background: #f8f8f8;
                border: 2px solid #ddd;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        image_layout = QVBoxLayout(self.image_frame)
        self.image_label = QLabel()
        self.image_label.setFixedSize(320, 320)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: none;")
        image_layout.addWidget(self.image_label)
        left.addWidget(self.image_frame)

        img_btn_layout = QHBoxLayout()
        import_btn = QPushButton("📁 导入图片")
        import_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background: #5DADE2;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: #3498DB;
            }
        """)
        import_btn.clicked.connect(self.import_images)
        prev_btn = QPushButton("◀ 上一张")
        prev_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background: #95A5A6;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: #7F8C8D;
            }
        """)
        prev_btn.clicked.connect(self.prev_image)
        next_btn = QPushButton("▶ 下一张")
        next_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background: #95A5A6;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: #7F8C8D;
            }
        """)
        next_btn.clicked.connect(self.next_image)
        img_btn_layout.addWidget(import_btn)
        img_btn_layout.addWidget(prev_btn)
        img_btn_layout.addWidget(next_btn)
        left.addLayout(img_btn_layout)

        self.tag_list = QListWidget()
        self.tag_list.setFixedHeight(100)
        self.tag_list.setStyleSheet("""
            QListWidget {
                background: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 3px 5px;
                margin: 1px;
                background: #EAEDED;
                border-radius: 3px;
            }
        """)
        left.addWidget(QLabel("<b>当前图片标签（心情/状态）:</b>"))
        left.addWidget(self.tag_list)

        # Center: chat area
        center = QVBoxLayout()
        
        # 状态信息栏 - 使用卡片式设计
        top_info_frame = QFrame()
        top_info_frame.setStyleSheet("""
            QFrame {
                background: #F2F3F4;
                border: 1px solid #D5DBDB;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        top_info_layout = QHBoxLayout(top_info_frame)
        
        self.affection_label = QLabel("❤ 好感度: 50")
        self.trust_label = QLabel("🤝 信任度: 50")
        self.affection_label.setStyleSheet("""
            QLabel {
                color: #E74C3C;
                font-weight: bold;
                font-size: 14px;
                padding: 5px 10px;
                background: white;
                border-radius: 15px;
                border: 1px solid #FADBD8;
            }
        """)
        self.trust_label.setStyleSheet("""
            QLabel {
                color: #3498DB;
                font-weight: bold;
                font-size: 14px;
                padding: 5px 10px;
                background: white;
                border-radius: 15px;
                border: 1px solid #D6EAF8;
            }
        """)
        
        top_info_layout.addWidget(self.affection_label)
        top_info_layout.addWidget(self.trust_label)
        top_info_layout.addStretch()
        
        self.days_label = QLabel("📅 陪伴TA的第 1 天")
        self.days_label.setStyleSheet("""
            QLabel {
                color: #27AE60;
                font-weight: bold;
                font-size: 14px;
                padding: 5px 10px;
                background: white;
                border-radius: 15px;
                border: 1px solid #D5F4E6;
            }
        """)
        top_info_layout.addWidget(self.days_label)
        center.addWidget(top_info_frame)

        # 聊天历史区域 - 使用更美观的文本框
        self.chat_history = ChatTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            QTextEdit {
                background: #FAFAFA;
                border: 2px solid #E5E8E8;
                border-radius: 10px;
                padding: 15px;
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        center.addWidget(self.chat_history, stretch=1)

        # 发送消息区域
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background: #F8F9F9;
                border: 2px solid #D5DBDB;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        send_layout = QHBoxLayout(input_frame)
        
        self.send_input = QLineEdit()
        self.send_input.setPlaceholderText("输入消息... (按Enter发送)")
        self.send_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #AED6F1;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #5DADE2;
            }
        """)
        self.send_input.returnPressed.connect(self.on_send)
        
        send_btn = QPushButton("发送")
        send_btn.setFixedWidth(80)
        send_btn.setStyleSheet("""
            QPushButton {
                background: linear-gradient(to right, #5DADE2, #3498DB);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: linear-gradient(to right, #3498DB, #2980B9);
            }
            QPushButton:pressed {
                background: linear-gradient(to right, #2980B9, #2471A3);
            }
        """)
        send_btn.clicked.connect(self.on_send)
        
        send_layout.addWidget(self.send_input, stretch=1)
        send_layout.addWidget(send_btn)
        center.addWidget(input_frame)

        # 功能区
        right = QVBoxLayout()
        right_title = QLabel("功能面板")
        right_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_title.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 16px;
                color: #2C3E50;
                margin-bottom: 15px;
                padding-bottom: 5px;
                border-bottom: 2px solid #5DADE2;
            }
        """)
        right.addWidget(right_title)
        
        # 功能按钮样式
        button_style = """
            QPushButton {
                background: #F8F9F9;
                border: 2px solid #D5DBDB;
                border-radius: 8px;
                padding: 12px 15px;
                text-align: left;
                font-size: 13px;
                margin: 5px 0;
                color: #2C3E50;
            }
            QPushButton:hover {
                background: #EAEDED;
                border-color: #5DADE2;
                color: #21618C;
            }
        """
        
        save_chat_btn = QPushButton("💾 保存对话记录")
        save_chat_btn.setStyleSheet(button_style)
        save_chat_btn.clicked.connect(self.save_chat_history)
        right.addWidget(save_chat_btn)
        
        reset_chat_btn = QPushButton("🔄 重置对话")
        reset_chat_btn.setStyleSheet(button_style)
        reset_chat_btn.clicked.connect(self.reset_chat)
        right.addWidget(reset_chat_btn)
        
        add_day_btn = QPushButton("📅 增加一天")
        add_day_btn.setStyleSheet(button_style)
        add_day_btn.clicked.connect(self.add_day)
        right.addWidget(add_day_btn)
        
        # 手动调整好感度
        adjust_frame = QFrame()
        adjust_frame.setStyleSheet("""
            QFrame {
                background: #F4F6F6;
                border: 1px solid #D5DBDB;
                border-radius: 8px;
                padding: 10px;
                margin: 10px 0;
            }
        """)
        adjust_layout = QVBoxLayout(adjust_frame)
        adjust_layout.addWidget(QLabel("<b>手动调整好感度:</b>"))
        
        adjust_inner = QHBoxLayout()
        adjust_inner.addWidget(QLabel("调整值:"))
        self.affection_adjust = QSpinBox()
        self.affection_adjust.setRange(-10, 10)
        self.affection_adjust.setValue(0)
        self.affection_adjust.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                border: 1px solid #BDC3C7;
                border-radius: 5px;
            }
        """)
        adjust_btn = QPushButton("应用")
        adjust_btn.setStyleSheet("""
            QPushButton {
                background: #F0B27A;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background: #E67E22;
            }
        """)
        adjust_btn.clicked.connect(self.adjust_affection)
        adjust_inner.addWidget(self.affection_adjust)
        adjust_inner.addWidget(adjust_btn)
        adjust_inner.addStretch()
        adjust_layout.addLayout(adjust_inner)
        right.addWidget(adjust_frame)
        
        right.addStretch()

        root.addLayout(left, stretch=2)
        root.addLayout(center, stretch=4)
        root.addLayout(right, stretch=1)
        self.setLayout(root)

    def update_state_labels(self):
        a = self.main.app_state.get('affection', 50)
        t = self.main.app_state.get('trust', 50)
        d = self.main.app_state.get('days', 1)
        
        # 根据数值改变颜色
        if a > 70:
            affection_color = "#E74C3C"  # 红色
            affection_bg = "#FADBD8"
        elif a < 30:
            affection_color = "#7F8C8D"  # 灰色
            affection_bg = "#F2F3F4"
        else:
            affection_color = "#F39C12"  # 橙色
            affection_bg = "#FDEBD0"
            
        if t > 70:
            trust_color = "#3498DB"      # 蓝色
            trust_bg = "#D6EAF8"
        elif t < 30:
            trust_color = "#7F8C8D"      # 灰色
            trust_bg = "#F2F3F4"
        else:
            trust_color = "#2ECC71"      # 绿色
            trust_bg = "#D5F4E6"
        
        self.affection_label.setStyleSheet(f"""
            QLabel {{
                color: {affection_color};
                font-weight: bold;
                font-size: 14px;
                padding: 5px 10px;
                background: {affection_bg};
                border-radius: 15px;
                border: 1px solid {affection_color}33;
            }}
        """)
        
        self.trust_label.setStyleSheet(f"""
            QLabel {{
                color: {trust_color};
                font-weight: bold;
                font-size: 14px;
                padding: 5px 10px;
                background: {trust_bg};
                border-radius: 15px;
                border: 1px solid {trust_color}33;
            }}
        """)
        
        self.affection_label.setText(f"❤ 好感度: {a}")
        self.trust_label.setText(f"🤝 信任度: {t}")
        self.days_label.setText(f"📅 陪伴TA的第 {d} 天")

    def import_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择图片（多选）", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if not files:
            return
        for f in files:
            text, ok = QInputDialog.getText(self, "为图片添加标签/心情/状态", 
                                           f"为图片 {f.split('/')[-1]} 输入标签（用逗号分隔）:\n例如：开心,微笑,阳光")
            tags = []
            if ok and text.strip():
                tags = [t.strip() for t in text.split(",") if t.strip()]
            else:
                # 默认标签
                tags = ["默认", "中性"]
                
            pix = QPixmap(f)
            if pix.isNull():
                QMessageBox.warning(self, "错误", f"无法加载图片: {f}")
                continue
                
            display = pix.scaled(self.image_label.size(), 
                                Qt.AspectRatioMode.KeepAspectRatio, 
                                Qt.TransformationMode.SmoothTransformation)
            self.images.append({"path": f, "tags": tags, "pixmap": display})
            
        if self.images and self.current_image_index == -1:
            self.current_image_index = 0
            self.show_current_image()
            
        QMessageBox.information(self, "成功", f"已导入 {len(files)} 张图片")

    def show_current_image(self):
        if 0 <= self.current_image_index < len(self.images):
            it = self.images[self.current_image_index]
            pix = it.get("pixmap")
            if pix and not pix.isNull():
                self.image_label.setPixmap(pix)
            else:
                self.image_label.setText("无法加载图片")
            self.tag_list.clear()
            for t in it.get("tags", []):
                item = QListWidgetItem(t)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tag_list.addItem(item)
        else:
            self.image_label.setPixmap(QPixmap())
            self.image_label.setText("未导入图片")
            self.tag_list.clear()

    def prev_image(self):
        if not self.images:
            QMessageBox.information(self, "提示", "请先导入图片")
            return
        self.current_image_index = (self.current_image_index - 1) % len(self.images)
        self.show_current_image()

    def next_image(self):
        if not self.images:
            QMessageBox.information(self, "提示", "请先导入图片")
            return
        self.current_image_index = (self.current_image_index + 1) % len(self.images)
        self.show_current_image()

    def append_chat(self, who, text, is_system=False, is_typing=False):
        """添加聊天消息，is_system为True时不显示发送者"""
        from datetime import datetime
        
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # 添加时间戳（系统消息不显示时间）
        if not is_system and not is_typing:
            timestamp = datetime.now().strftime("%H:%M")
            
            # 使用不同的样式
            if who == "系统":
                cursor.insertHtml(f'<div style="margin: 5px 0;"><span style="color:#7F8C8D; font-size:11px;">{timestamp}</span> '
                                 f'<span style="color:#E74C3C; font-weight:bold;">[系统提示]</span></div>')
            elif who == self.main.app_state.get('user_name', '玩家'):
                # 玩家消息
                cursor.insertHtml(f'<div style="margin: 10px 0 10px 20px; text-align:right;">'
                                 f'<div><span style="color:#2ECC71; font-weight:bold;">{who}</span> '
                                 f'<span style="color:#95A5A6; font-size:11px;">{timestamp}</span></div>')
            else:
                # 角色消息
                cursor.insertHtml(f'<div style="margin: 10px 20px 10px 0; text-align:left;">'
                                 f'<div><span style="color:#3498DB; font-weight:bold;">{who}</span> '
                                 f'<span style="color:#95A5A6; font-size:11px;">{timestamp}</span></div>')
        
        # 消息内容
        if is_typing:
            # 正在输入提示
            cursor.insertHtml(f'<div style="margin: 5px 0 15px 0; color:#7F8C8D; font-style:italic;">'
                            f'<span style="color:#5DADE2;">{who}</span> 正在输入...</div>')
        elif is_system:
            # 系统消息（数值变化等）
            cursor.insertHtml(f'<div style="margin: 2px 0; padding: 3px 8px; background:#F2F3F4; '
                            f'border-radius:5px; color:#7F8C8D; font-size:12px;">{text}</div>')
        elif who == self.main.app_state.get('user_name', '玩家'):
            # 玩家消息样式
            cursor.insertHtml(f'<div style="margin: 3px 0 15px 0; padding: 8px 12px; background:#D5F4E6; '
                            f'border-radius:10px; border:1px solid #ABEBC6; display:inline-block; '
                            f'max-width:80%; float:right; clear:both;">{text}</div><div style="clear:both;"></div>')
        else:
            # 角色消息样式
            cursor.insertHtml(f'<div style="margin: 3px 0 15px 0; padding: 8px 12px; background:#EAF2F8; '
                            f'border-radius:10px; border:1px solid #AED6F1; display:inline-block; '
                            f'max-width:80%;">{text}</div><div style="clear:both;"></div>')
        
        # 添加分隔线（只在消息间添加）
        cursor.insertHtml('<hr style="border:none; border-top:1px solid #EAEDED; margin:5px 0;">')
        
        # 自动滚动到底部
        self.chat_history.verticalScrollBar().setValue(
            self.chat_history.verticalScrollBar().maximum()
        )

    def try_switch_image_by_text(self, text):
        """根据文本内容尝试切换图片"""
        if not self.images:
            return False
            
        text_lower = text.lower()
        matched_indices = []
        
        # 搜索所有匹配的图片
        for idx, it in enumerate(self.images):
            for tag in it.get("tags", []):
                tag_lower = tag.lower()
                # 检查标签是否在文本中
                if tag_lower in text_lower:
                    matched_indices.append(idx)
                    break
        
        if matched_indices:
            # 切换到第一个匹配的图片
            self.current_image_index = matched_indices[0]
            self.show_current_image()
            return True
            
        return False

    def parse_ai_response(self, raw_response):
        """解析AI响应，尝试提取JSON数据"""
        # 首先尝试直接解析JSON
        try:
            data = json.loads(raw_response)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
        
        # 尝试使用正则表达式提取JSON
        json_pattern = r'\{[^{}]*\}'
        matches = re.finditer(json_pattern, raw_response)
        
        for match in matches:
            try:
                data = json.loads(match.group(0))
                if isinstance(data, dict) and "reply" in data:
                    return data
            except json.JSONDecodeError:
                continue
        
        # 如果没有找到有效JSON，返回默认结构
        return {
            "reply": raw_response,
            "favor_change": 0,
            "trust_change": 0,
            "state": "中性"
        }

    def on_send(self):
        user_text = self.send_input.text().strip()
        if not user_text:
            QMessageBox.information(self, "提示", "请输入消息")
            return
            
        player_name = self.main.app_state.get('user_name', '玩家')
        
        # 显示玩家消息（优化后的样式）
        self.append_chat(player_name, user_text)

        # 获取对话历史
        history = self.main.app_state.get('messages', [])
        
        # 构建消息（使用统一的系统提示词）
        messages = [
            {"role": "system", "content": self.main.app_state.get('system_prompt', '')}
        ]
        
        # 添加历史对话（限制长度，避免token超限）
        max_history = 10  # 最多保留10轮对话历史
        messages.extend(history[-max_history*2:])  # 每轮包含user和assistant两条消息
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": user_text})
        
        # 发送到AI
        client = getattr(self.main, "client", None)
        model_name = self.main.app_state.get('model', '')
        
        if client is None:
            # 显示正在思考的提示
            char_name = self.main.app_state['character'].get('name', 'NPC')
            self.append_chat(char_name, "", is_typing=True)
            QApplication.processEvents()
            
            # 延迟显示回复
            QTimer.singleShot(800, lambda: self.handle_local_response(user_text))
            self.send_input.clear()
            return
        
        try:
            # 显示正在思考的提示
            char_name = self.main.app_state['character'].get('name', 'NPC')
            self.append_chat(char_name, "", is_typing=True)
            self.showing_thinking = True
            QApplication.processEvents()
            
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
                top_p=0.9,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            raw_response = response.choices[0].message.content
            data = self.parse_ai_response(raw_response)
            
            bot_reply = data.get("reply", raw_response)
            favor_change = data.get("favor_change", 0)
            trust_change = data.get("trust_change", 0)
            state_value = data.get("state", "")
            
            # 移除"正在输入"提示
            self.remove_thinking_indicator()
            
            # 显示AI回复（稍微延迟，增强体验）
            QTimer.singleShot(300, lambda: self.show_ai_response(bot_reply, favor_change, trust_change, state_value, user_text))
            
        except Exception as e:
            # 移除"正在输入"提示
            self.remove_thinking_indicator()
            
            # 显示错误提示（使用更友好的方式）
            self.append_chat("系统", f"请求失败，使用本地回复模式", is_system=True)
            QTimer.singleShot(500, lambda: self.handle_local_response(user_text))
        
        # 清空输入框
        self.send_input.clear()

    def remove_thinking_indicator(self):
        """移除正在输入提示"""
        if self.showing_thinking:
            # 简单的移除方法：重新获取纯文本并过滤
            current_text = self.chat_history.toPlainText()
            if "正在输入" in current_text:
                # 移除最后几行
                lines = current_text.strip().split('\n')
                new_lines = []
                for line in lines:
                    if "正在输入" not in line:
                        new_lines.append(line)
                
                self.chat_history.setPlainText('\n'.join(new_lines))
            self.showing_thinking = False

    def show_ai_response(self, bot_reply, favor_change, trust_change, state_value, user_text):
        """显示AI回复"""
        char_name = self.main.app_state['character'].get('name', 'NPC')
        self.append_chat(char_name, bot_reply)
        
        # 应用数值变化
        self.apply_stat_changes(favor_change, trust_change)
        
        # 尝试根据状态或回复切换图片
        if state_value:
            if not self.try_switch_image_by_text(state_value):
                # 如果状态没匹配到图片，尝试用回复内容匹配
                self.try_switch_image_by_text(bot_reply)
        else:
            # 直接尝试用回复内容匹配
            self.try_switch_image_by_text(bot_reply)
        
        # 添加到历史
        self.main.app_state['messages'].append({"role": "user", "content": user_text})
        self.main.app_state['messages'].append({"role": "assistant", "content": bot_reply})

    def handle_local_response(self, user_text):
        """处理本地回复"""
        char_name = self.main.app_state['character'].get('name', 'NPC')
        bot_reply = self.simple_bot_reply(user_text)
        
        self.append_chat(char_name, bot_reply)
        
        # 添加到历史
        self.main.app_state['messages'].append({"role": "user", "content": user_text})
        self.main.app_state['messages'].append({"role": "assistant", "content": bot_reply})
        
        # 尝试匹配图片
        self.try_switch_image_by_text(bot_reply)

    def apply_stat_changes(self, favor_change, trust_change):
        """应用数值变化，有最大步长限制，使用更隐蔽的提示"""
        st = self.main.app_state
        
        # 只在攻略模式下显示变化
        if self.main.app_state['mode'] != 'guide':
            return
        
        # 限制单次变化幅度
        MAX_STEP = 3
        favor_change = max(-MAX_STEP, min(MAX_STEP, favor_change))
        trust_change = max(-MAX_STEP, min(MAX_STEP, trust_change))
        
        if favor_change == 0 and trust_change == 0:
            return
        
        # 应用变化
        st['affection'] = max(0, min(100, st.get('affection', 50) + favor_change))
        st['trust'] = max(0, min(100, st.get('trust', 50) + trust_change))
        
        # 更新显示
        self.update_state_labels()
        
        # 只在变化较大时显示提示
        if abs(favor_change) >= 2 or abs(trust_change) >= 2:
            change_msg = ""
            if favor_change > 0:
                change_msg += f"❤ 好感度+{favor_change} "
            elif favor_change < 0:
                change_msg += f"❤ 好感度{favor_change} "
                
            if trust_change > 0:
                change_msg += f"🤝 信任度+{trust_change}"
            elif trust_change < 0:
                change_msg += f"🤝 信任度{trust_change}"
                
            if change_msg:
                # 使用更隐蔽的系统提示
                self.append_chat("系统", f"{change_msg.strip()}", is_system=True)

    def simple_bot_reply(self, user_text):
        """本地模拟回复（当API不可用时）"""
        char = self.main.app_state.get('character', {})
        style = char.get('dialog_style', '')
        name = char.get('name', 'NPC')
        
        # 根据对话风格生成回复
        if "撒娇" in style or "可爱" in style:
            responses = [
                f"嗯～{user_text}是什么意思呀？",
                f"好哒，我知道了～",
                f"唔...不太明白呢，可以再说清楚一点吗？",
                f"诶嘿，{user_text}吗？我明白啦！",
                f"这个...让我想想呢～"
            ]
        elif "冷静" in style or "严肃" in style:
            responses = [
                f"明白了。{user_text}",
                f"好的，我会考虑这个建议。",
                f"我知道了。",
                f"理解。{user_text}",
                f"收到。"
            ]
        elif "温柔" in style:
            responses = [
                f"谢谢你的关心，{user_text}让我感到温暖。",
                f"嗯，我理解你的意思了。",
                f"好的，我会记住的。",
                f"你总是这么细心呢。",
                f"听到你这么说，我很开心。"
            ]
        else:
            responses = [
                f"我听到你说：{user_text}",
                f"嗯，{user_text}，我明白了。",
                f"好的，我知道了。",
                f"原来如此，{user_text}",
                f"了解。"
            ]
        
        import random
        return random.choice(responses)

    def save_chat_history(self):
        """保存对话记录到文件"""
        file_name, _ = QFileDialog.getSaveFileName(self, "保存对话记录", "", "文本文件 (*.txt)")
        if not file_name:
            return
            
        try:
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(self.chat_history.toPlainText())
            QMessageBox.information(self, "成功", "对话记录已保存")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存失败：{str(e)}")

    def reset_chat(self):
        """重置对话"""
        reply = QMessageBox.question(self, "确认", "确定要重置对话吗？这会清空所有对话历史。",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.main.app_state['messages'] = []
            self.chat_history.clear()
            
            # 重新显示角色介绍（使用更好的排版）
            char = self.main.app_state.get('character', {})
            intro = f"角色 {char.get('name','')} 已创建。模式：{self.main.app_state.get('mode')}"
            self.chat_history.append(f"<div style='text-align:center; padding:20px; color:#5DADE2; font-size:16px; font-weight:bold;'>{intro}</div>")
            
            summary = (
                f"<div style='background:#F8F9F9; padding:15px; border-radius:10px; margin:10px;'>"
                f"<b>角色信息：</b><br>"
                f"<span style='color:#2C3E50;'>职业：</span>{char.get('job','')}<br>"
                f"<span style='color:#2C3E50;'>性格：</span>{char.get('personality','')}<br>"
                f"<span style='color:#2C3E50;'>默认穿搭：</span>{char.get('default_style','')}<br>"
                f"<span style='color:#2C3E50;'>爱好：</span>{char.get('hobby','')}<br><br>"
                f"<span style='color:#27AE60; font-style:italic;'>请开始和{char.get('name','')}对话吧！</span>"
                f"</div>"
            )
            self.chat_history.append(summary)
            
            # 重置数值显示
            self.update_state_labels()

    def add_day(self):
        """增加天数"""
        self.main.app_state['days'] = self.main.app_state.get('days', 1) + 1
        self.update_state_labels()
        self.append_chat("系统", f"新的一天开始了（第 {self.main.app_state['days']} 天）", is_system=True)

    def adjust_affection(self):
        """手动调整好感度"""
        change = self.affection_adjust.value()
        if change == 0:
            return
            
        self.main.app_state['affection'] = max(0, min(100, 
            self.main.app_state.get('affection', 50) + change))
        self.update_state_labels()
        self.append_chat("系统", f"手动调整：好感度{'+' if change > 0 else ''}{change}", is_system=True)
        self.affection_adjust.setValue(0)


class ChatTextEdit(QTextEdit):
    """自定义的聊天文本框，支持HTML格式"""
    def __init__(self):
        super().__init__()
        self.setAcceptRichText(True)
        self.document().setDefaultStyleSheet("""
            body {
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
                font-size: 14px;
                line-height: 1.6;
                color: #2C3E50;
            }
            hr {
                border: none;
                border-top: 1px solid #EAEDED;
                margin: 5px 0;
            }
        """)


class RPGApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI 角色扮演 游戏（沉浸感优化版）")
        self.resize(1200, 750)
        
        # 设置应用样式
        self.setStyleSheet("""
            QWidget {
                background: #F8F9F9;
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
            }
            QLabel {
                color: #2C3E50;
            }
        """)
        
        self.stack = QStackedWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.stack)
        self.setLayout(layout)

        # 共享应用状态
        self.app_state = {
            "api_key": "",
            "api_url": "",
            "model": "",
            "mode": "chat",
            "character": {},
            "affection": 50,
            "trust": 50,
            "days": 1,
            "user_name": "玩家",
            "messages": [],  # 对话历史
            "affection_pending": 0.0,
            "trust_pending": 0.0,
            "system_prompt": ""
        }

        # 页面
        self.page_api = APIFormPage(self)          # index 0
        self.page_mode = ModeSelectPage(self)      # index 1
        self.page_char_chat = CharacterFormPage(self, is_guide=False)  # index 2
        self.page_char_guide = CharacterFormPage(self, is_guide=True)  # index 3
        self.page_game = GameMainPage(self)        # index 4

        for p in [self.page_api, self.page_mode, self.page_char_chat, self.page_char_guide, self.page_game]:
            self.stack.addWidget(p)

        self.stack.currentChanged.connect(self.on_page_changed)

        # client placeholder; will be set in init_api_client
        self.client = None

    def generate_system_prompt(self):
        """生成系统提示词"""
        char = self.app_state.get('character', {})
        
        # 构建角色描述
        role_desc = (
            f"你正在扮演一个虚拟角色，以下是你的设定：\n"
            f"名字：{char.get('name','NPC')}\n"
            f"性别：{char.get('sex','')}\n"
            f"年龄：{char.get('age','')}\n"
            f"职业：{char.get('job','')}\n"
            f"身份：{char.get('identity','')}\n"
            f"外貌：{char.get('appearance','')}\n"
            f"默认穿搭：{char.get('default_style','')}\n"
            f"性格：{char.get('personality','')}\n"
            f"爱好：{char.get('hobby','')}\n"
            f"如何称呼玩家：{char.get('call_player_as','你')}\n"
            f"对话风格：{char.get('dialog_style','')}\n\n"
        )
        
        # 构建游戏指令
        if self.app_state['mode'] == 'guide':
            game_instructions = (
                f"这是一个角色扮演游戏，包含好感度和信任度系统。\n"
                f"请根据玩家的对话内容，评估对角色好感度和信任度的影响。\n"
                f"每次回复时，请输出以下JSON格式的数据：\n\n"
                f'{{"reply": "你的回复内容", "favor_change": -3到3的整数, "trust_change": -3到3的整数, "state": "当前状态标签"}}\n\n'
                f"favor_change表示好感度变化（正数增加，负数减少），trust_change表示信任度变化。\n"
                f"state可以是：开心、难过、生气、害羞、惊讶、思考、微笑等描述状态的词语。\n"
                f"请严格以JSON格式回复，不要包含其他任何文本。\n"
            )
        else:
            game_instructions = (
                f"这是一个角色扮演对话游戏。\n"
                f"请根据角色设定进行回复。\n"
                f"每次回复时，请输出以下JSON格式的数据：\n\n"
                f'{{"reply": "你的回复内容", "favor_change": 0, "trust_change": 0, "state": "当前状态标签"}}\n\n'
                f"请严格以JSON格式回复，不要包含其他任何文本。\n"
            )
        
        self.app_state['system_prompt'] = role_desc + game_instructions

    def init_api_client(self):
        """
        初始化API客户端
        返回：成功返回True，失败返回False
        """
        api_key = self.app_state.get('api_key', '')
        api_url = self.app_state.get('api_url', '')
        
        if OpenAI is None:
            self.client = None
            self.app_state['_client_init_error'] = f"无法导入 openai.OpenAI：{_OPENAI_IMPORT_ERROR}"
            return False
            
        if not api_key or not api_url:
            self.client = None
            self.app_state['_client_init_error'] = "API Key 或 API 地址为空"
            return False
            
        try:
            # 创建客户端
            self.client = OpenAI(api_key=api_key, base_url=api_url)
            self.app_state['_client_init_error'] = None
            return True
        except Exception as e:
            self.client = None
            self.app_state['_client_init_error'] = f"初始化客户端失败：{e}"
            return False

    def on_page_changed(self, idx):
        if idx == 4:  # 进入主游戏页面
            # 更新状态标签
            self.page_game.update_state_labels()
            
            # 清空并显示角色介绍
            self.page_game.chat_history.clear()
            char = self.app_state.get('character', {})
            
            # 使用HTML格式化角色介绍
            intro_html = f"""
            <div style='text-align:center; padding:20px 0;'>
                <div style='font-size:18px; font-weight:bold; color:#5DADE2; margin-bottom:10px;'>
                    角色 {char.get('name','')} 已创建
                </div>
                <div style='color:#7F8C8D; font-size:14px;'>
                    模式：{self.app_state.get('mode')} | 第 {self.app_state.get('days', 1)} 天
                </div>
            </div>
            
            <div style='background:linear-gradient(135deg, #F8F9F9, #EAEDED); 
                        padding:20px; margin:10px; border-radius:12px; 
                        border-left:4px solid #5DADE2;'>
                <div style='font-size:16px; font-weight:bold; color:#2C3E50; margin-bottom:15px;'>
                    📋 角色档案
                </div>
                <table style='width:100%; color:#34495E; font-size:14px; line-height:1.8;'>
                    <tr><td style='width:80px; font-weight:bold;'>👤 名字：</td><td>{char.get('name','')}</td></tr>
                    <tr><td style='font-weight:bold;'>🎭 职业：</td><td>{char.get('job','')}</td></tr>
                    <tr><td style='font-weight:bold;'>💫 性格：</td><td>{char.get('personality','')}</td></tr>
                    <tr><td style='font-weight:bold;'>👕 穿搭：</td><td>{char.get('default_style','')}</td></tr>
                    <tr><td style='font-weight:bold;'>🎨 爱好：</td><td>{char.get('hobby','')}</td></tr>
                </table>
                <div style='margin-top:20px; padding:10px; background:#D5F4E6; border-radius:8px; 
                            color:#27AE60; font-style:italic; text-align:center;'>
                    请开始和 {char.get('name','')} 对话吧！
                </div>
            </div>
            """
            
            self.page_game.chat_history.append(intro_html)
            
            # 显示API初始化错误（如果有） - 使用更友好的提示
            if self.app_state.get('_client_init_error'):
                error_html = f"""
                <div style='background:#FDEDEC; padding:10px; margin:10px; border-radius:8px; 
                            border-left:4px solid #E74C3C;'>
                    <div style='color:#C0392B; font-weight:bold;'>⚠️ API连接警告</div>
                    <div style='color:#7F8C8D; font-size:12px;'>将使用本地对话模式</div>
                </div>
                """
                self.page_game.chat_history.append(error_html)
            
            # 显示当前图片
            self.page_game.show_current_image()


def main():
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    win = RPGApp()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


"""
虽然只是一个“跑题”的作业，但是固定节目不能少：
    （既然都跑题了，我的作业就以Final2那份为准吧~）

指导老师 兼 打工牛马 ：
Doubao & DeepSeek


特别鸣谢：
Skycode 秋令营的学长们

"""