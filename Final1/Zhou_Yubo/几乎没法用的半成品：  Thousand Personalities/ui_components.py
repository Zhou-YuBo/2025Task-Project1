import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QTextEdit, QLineEdit, QGroupBox,
    QSizePolicy, QFileDialog,
    QDialog, QFormLayout, QComboBox, QDialogButtonBox,
    QMessageBox, QApplication
    
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

from api_handler import APIHandler
from data_manager import DataManager


# 全局配置（后续可抽成配置文件）
DEFAULT_EMOTION_VALUES = {"liking": 80, "trust": 75}  # 初始好感度/信任度
DAYS_COUNTER = 1  # 初始陪伴天数

# 新增：人设编辑弹窗类
class PersonaEditDialog(QDialog):
    def __init__(self, parent=None, existing_persona=None):
        super().__init__(parent)
        self.setWindowTitle("创建/编辑人设")
        self.setFixedSize(500, 600)  # 固定弹窗尺寸
        self.persona_data = None  # 存储最终的人设数据
        
        # 初始化控件
        self._init_ui()
        
        # 如果是编辑已有人设，填充数据
        if existing_persona:
            self._fill_persona_data(existing_persona)

    def _init_ui(self):
        """初始化弹窗UI，包含所有自定义字段"""
        main_layout = QVBoxLayout(self)
        
        # 表单布局：存放所有输入项
        form_layout = QFormLayout()
        
        # 1. 基础信息
        self.name_input = QLineEdit()
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["男", "女", "动物", "无性别"])
        self.age_input = QLineEdit()
        self.age_input.setPlaceholderText("如：18/25/3岁（动物）")
        self.career_input = QLineEdit()
        self.relation_input = QLineEdit()
        self.relation_input.setPlaceholderText("如：恋人/朋友/宠物/兄妹")
        
        # 2. 形象信息
        self.appearance_input = QTextEdit()
        self.appearance_input.setPlaceholderText("外貌描述（如：粉色头发、猫耳、穿洛丽塔）")
        self.outfit_input = QLineEdit()
        self.outfit_input.setPlaceholderText("默认穿搭（如：白色卫衣+牛仔裤）")
        
        # 3. 性格与互动
        self.personality_input = QTextEdit()
        self.personality_input.setPlaceholderText("性格描述（如：傲娇、粘人、慢热）")
        self.hobby_input = QTextEdit()
        self.hobby_input.setPlaceholderText("爱好（如：追剧、吃甜食、遛弯）")
        self.call_player_input = QLineEdit()
        self.call_player_input.setPlaceholderText("如何称呼玩家（如：主人/宝贝/同学）")
        self.chat_style_input = QTextEdit()
        self.chat_style_input.setPlaceholderText("对话风格（如：带颜文字、语气软、毒舌）")
        
        # 添加到表单布局
        form_layout.addRow("人设名称*", self.name_input)
        form_layout.addRow("性别*", self.gender_combo)
        form_layout.addRow("年龄", self.age_input)
        form_layout.addRow("职业", self.career_input)
        form_layout.addRow("与玩家关系*", self.relation_input)
        form_layout.addRow("外貌描述", self.appearance_input)
        form_layout.addRow("默认穿搭", self.outfit_input)
        form_layout.addRow("性格描述*", self.personality_input)
        form_layout.addRow("爱好", self.hobby_input)
        form_layout.addRow("称呼玩家", self.call_player_input)
        form_layout.addRow("对话风格*", self.chat_style_input)
        
        # 按钮区（确认/取消）
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self._on_ok)
        btn_box.rejected.connect(self.reject)
        
        # 组装布局
        main_layout.addLayout(form_layout)
        main_layout.addWidget(btn_box)

    def _fill_persona_data(self, persona):
        """填充已有人设数据到输入框"""
        self.name_input.setText(persona.get("name", ""))
        self.gender_combo.setCurrentText(persona.get("gender", "女"))
        self.age_input.setText(persona.get("age", ""))
        self.career_input.setText(persona.get("career", ""))
        self.relation_input.setText(persona.get("relation", ""))
        self.appearance_input.setText(persona.get("appearance", ""))
        self.outfit_input.setText(persona.get("outfit", ""))
        self.personality_input.setText(persona.get("personality", ""))
        self.hobby_input.setText(persona.get("hobby", ""))
        self.call_player_input.setText(persona.get("call_player", ""))
        self.chat_style_input.setText(persona.get("chat_style", ""))

    def _on_ok(self):
        """点击确认按钮，验证并保存人设数据"""
        # 必填项验证
        name = self.name_input.text().strip()
        relation = self.relation_input.text().strip()
        personality = self.personality_input.toPlainText().strip()
        chat_style = self.chat_style_input.toPlainText().strip()
        if not name or not relation or not personality or not chat_style:
            QMessageBox.warning(self, "提示", "人设名称、与玩家关系、性格、对话风格为必填项！")
            return
        
        # 组装人设数据
        self.persona_data = {
            "name": name,
            "gender": self.gender_combo.currentText(),
            "age": self.age_input.text().strip(),
            "career": self.career_input.text().strip(),
            "relation": relation,
            "appearance": self.appearance_input.toPlainText().strip(),
            "outfit": self.outfit_input.text().strip(),
            "personality": personality,
            "hobby": self.hobby_input.toPlainText().strip(),
            "call_player": self.call_player_input.text().strip() or "你",
            "chat_style": chat_style
        }
        self.accept()  # 关闭弹窗并返回成功

    def get_persona_data(self):
        """获取最终的人设数据"""
        return self.persona_data
    



class EmotionChatUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("千面人格 - 情感陪伴聊天程序（内测版）")
        self.setFixedSize(1200, 800)  # 固定窗口尺寸（适配设计稿）
        
        # 初始化核心变量
        self.current_mode = None  # 当前互动模式：chat/travel/do_together
        self.role_images = []     # 角色图片列表
        self.current_img_index = 0  # 当前显示图片索引
        self.emotion_values = DEFAULT_EMOTION_VALUES.copy()
        self.api_handler = APIHandler() 
        self.data_manager = DataManager() 
        
        # 重构：详细的人设列表（替代原有简单列表）
        self.role_personas = [
            # 默认示例人设
            {
                "name": "作者梦到什么写什么",
                "gender": "男",
                "age": "26",
                "career": "黑水镇在逃通缉犯",
                "relation": "朋友",
                "appearance": "金色短发",
                "outfit": "法奥斯军校制服",
                "personality": "调皮捣蛋，嘻嘻哈哈，走路从不认真看路",
                "hobby": "跑非洲开酒馆、吃甜品、走街串巷兜售千纸鹤",
                "call_player": "妹妹",
                "chat_style": "冷静、略带疏离感，喜爱医学隐喻，含蓄的掌控感，有时极致反差感"
            }
        ]
        self.current_persona = self.role_personas[0]  # 当前选中的详细人设

        # 构建主布局
        self._init_main_layout()
        
    def _init_main_layout(self):
        # 中心容器
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # 1. 顶部信息栏（独立布局，加在主窗口顶部）
        self._init_top_bar()
        
        # 2. 左侧角色展示区（宽度占比20%）
        left_widget = self._init_left_role_area()
        main_layout.addWidget(left_widget, stretch=2)
        
        # 3. 中间聊天交互区（宽度占比50%）
        middle_widget = self._init_middle_chat_area()
        main_layout.addWidget(middle_widget, stretch=5)
        
        # 4. 右侧功能按键区（宽度占比30%）
        right_widget = self._init_right_func_area()
        main_layout.addWidget(right_widget, stretch=3)
    
    def _init_top_bar(self):
        """顶部信息栏：好感度+信任度+陪伴天数+时间戳"""
        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        # 情感值展示
        self.liking_label = QLabel(f"好感度：{self.emotion_values['liking']}")
        self.trust_label = QLabel(f"信任度：{self.emotion_values['trust']}")
        # 陪伴天数+时间
        self.days_label = QLabel(f"陪TA的第{DAYS_COUNTER}天")
        self.time_label = QLabel(f"当前时间：{QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')}")
        
        # 样式美化（可选，基础版先实现功能）
        for label in [self.liking_label, self.trust_label, self.days_label, self.time_label]:
            label.setStyleSheet("font-size: 14px; padding: 5px;")
        
        top_layout.addWidget(self.liking_label)
        top_layout.addWidget(self.trust_label)
        top_layout.addStretch()  # 右对齐天数和时间
        top_layout.addWidget(self.days_label)
        top_layout.addWidget(self.time_label)
        
        # 把顶部栏加到主窗口
        self.setMenuWidget(top_bar)
    

    def _init_left_role_area(self):
        """左侧角色展示区：图片+切换按钮"""
        left_group = QGroupBox("角色展示")
        left_layout = QVBoxLayout(left_group)
        
        # 角色图片显示框
        self.role_img_label = QLabel("请上传角色图片")
        self.role_img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.role_img_label.setStyleSheet("border: 1px solid #ccc; min-height: 400px;")
        left_layout.addWidget(self.role_img_label)
        
        # 图片操作按钮
        img_btn_layout = QHBoxLayout()
        self.upload_img_btn = QPushButton("上传图片")
        self.prev_img_btn = QPushButton("上一张")
        self.next_img_btn = QPushButton("下一张")
        # 初始禁用切换按钮（无图片时）
        self.prev_img_btn.setEnabled(False)
        self.next_img_btn.setEnabled(False)

        # 绑定上传/切换图片按钮的点击事件
        self.upload_img_btn.clicked.connect(self._upload_role_image)
        self.prev_img_btn.clicked.connect(self._prev_role_image)
        self.next_img_btn.clicked.connect(self._next_role_image)
        
        img_btn_layout.addWidget(self.upload_img_btn)
        img_btn_layout.addWidget(self.prev_img_btn)
        img_btn_layout.addWidget(self.next_img_btn)
        left_layout.addLayout(img_btn_layout)
        
        return left_group
    
    # 新增图片操作方法
    def _upload_role_image(self):
        """上传角色图片（支持多选）"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择角色图片", "", "图片文件 (*.png *.jpg *.jpeg)"
        )
        if file_paths:
            self.role_images = file_paths  # 存储图片路径
            self.current_img_index = 0     # 重置索引
            # 显示第一张图片
            self._show_current_image()
            # 启用切换按钮
            self.prev_img_btn.setEnabled(True)
            self.next_img_btn.setEnabled(True)
            self.chat_display.append(f"【系统】成功上传{len(self.role_images)}张角色图片～")

    def _show_current_image(self):
        """显示当前索引的角色图片"""
        if 0 <= self.current_img_index < len(self.role_images):
            pixmap = QPixmap(self.role_images[self.current_img_index])
            # 缩放图片适配显示框（保持比例）
            scaled_pixmap = pixmap.scaled(
                self.role_img_label.size(), 
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.role_img_label.setPixmap(scaled_pixmap)

    def _prev_role_image(self):
        """上一张图片"""
        if self.current_img_index > 0:
            self.current_img_index -= 1
            self._show_current_image()
        else:
            self.chat_display.append("【系统】已是第一张图片～")

    def _next_role_image(self):
        """下一张图片"""
        if self.current_img_index < len(self.role_images) - 1:
            self.current_img_index += 1
            self._show_current_image()
        else:
            self.chat_display.append("【系统】已是最后一张图片～")
    


    # ====================================================
    def _init_middle_chat_area(self):
        """中间聊天区：对话展示+输入框+发送按钮"""
        middle_group = QGroupBox("聊天交互")
        middle_layout = QVBoxLayout(middle_group)
        
        # 对话展示区
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)  # 仅可读
        self.chat_display.setStyleSheet("font-size: 14px; padding: 10px;")
        middle_layout.addWidget(self.chat_display)
        
        # 输入操作栏
        input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("请输入对话内容（仅在启用模式后可发送）")
        self.send_btn = QPushButton("发送")
        self.send_btn.clicked.connect(self._send_chat_message)
        self.end_chat_btn = QPushButton("结束对话")
        # 初始禁用输入和发送（未选模式）
        self.chat_input.setEnabled(False)
        self.send_btn.setEnabled(False)
        
        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(self.send_btn)
        input_layout.addWidget(self.end_chat_btn)
        middle_layout.addLayout(input_layout)
        
        return middle_group
    

    # ==================================================================
    def _init_right_func_area(self):
        """右侧功能区：API配置+模式切换+日记+背包+人设+保存"""
        right_group = QGroupBox("功能操作")
        right_layout = QVBoxLayout(right_group)

        # 1. API配置（简化版）
        api_group = QGroupBox("API配置")
        api_layout = QVBoxLayout(api_group)

        # 模型名称
        self.model_name_input = QLineEdit("gpt-3.5-turbo")
        self.model_name_input.setPlaceholderText("输入模型名称（如：gpt-3.5-turbo/ernie-x1.1-preview）")

        # API地址
        self.api_url_input = QLineEdit()
        self.api_url_input.setPlaceholderText("API基础地址（如：https://api.openai.com/v1）")

        # API密钥
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("API密钥")

        # 测试按钮
        self.api_test_btn = QPushButton("初始化连接")
        self.api_test_btn.clicked.connect(self._test_api_connection)  # 绑定测试方法

        # 添加到布局
        api_layout.addWidget(QLabel("模型名称："))
        api_layout.addWidget(self.model_name_input)
        api_layout.addWidget(QLabel("API基础地址："))
        api_layout.addWidget(self.api_url_input)
        api_layout.addWidget(QLabel("API密钥："))
        api_layout.addWidget(self.api_key_input)
        api_layout.addWidget(self.api_test_btn)
        
        right_layout.addWidget(api_group)

        
        # 2. 互动模式切换
        mode_group = QGroupBox("互动模式")
        mode_layout = QVBoxLayout(mode_group)
        self.chat_mode_btn = QPushButton("聊天")
        self.travel_mode_btn = QPushButton("出行")
        self.do_mode_btn = QPushButton("一起做")
        # 模式按钮统一样式（初始灰色）
        mode_btns = [self.chat_mode_btn, self.travel_mode_btn, self.do_mode_btn]
        for btn in mode_btns:
            btn.setStyleSheet("background-color: #ccc; padding: 8px;")
            btn.clicked.connect(lambda checked, b=btn: self._switch_mode(b))
        mode_layout.addWidget(self.chat_mode_btn)
        mode_layout.addWidget(self.travel_mode_btn)
        mode_layout.addWidget(self.do_mode_btn)
        right_layout.addWidget(mode_group)
        
        # 3. 其他功能按钮
        other_btn_layout = QVBoxLayout()
        self.diary_btn = QPushButton("生成日记")
        self.backpack_btn = QPushButton("查看背包")
        self.create_persona_btn = QPushButton("创建新人设")      
        self.role_switch_btn = QPushButton("切换人设")
        self.save_btn = QPushButton("保存存档")

        # 样式统一
        for btn in [self.diary_btn, self.backpack_btn, self.role_switch_btn, self.save_btn]:
            btn.setStyleSheet("padding: 8px; margin: 5px 0;")

        # 绑定新按钮事件
        self.create_persona_btn.clicked.connect(self._create_new_persona)
        self.role_switch_btn.clicked.connect(self._switch_role_persona)
        self.save_btn.clicked.connect(self._save_game)
        self.diary_btn.clicked.connect(self._generate_diary)
        self.backpack_btn.clicked.connect(self._show_backpack)
    
        other_btn_layout.addWidget(self.diary_btn)
        other_btn_layout.addWidget(self.backpack_btn)
        other_btn_layout.addWidget(self.create_persona_btn)
        other_btn_layout.addWidget(self.role_switch_btn)
        other_btn_layout.addWidget(self.save_btn)
        right_layout.addLayout(other_btn_layout)
        
        return right_group
    
    def _switch_mode(self, btn):
        """切换互动模式，更新按钮状态+解锁聊天输入"""
        # 重置所有模式按钮样式（灰色）
        mode_btns = [self.chat_mode_btn, self.travel_mode_btn, self.do_mode_btn]
        for b in mode_btns:
            b.setStyleSheet("background-color: #ccc; padding: 8px;")
        # 激活当前按钮（蓝色）
        btn.setStyleSheet("background-color: #1E90FF; color: white; padding: 8px;")
        # 记录当前模式
        if btn == self.chat_mode_btn:
            self.current_mode = "chat"
        elif btn == self.travel_mode_btn:
            self.current_mode = "travel"
        elif btn == self.do_mode_btn:
            self.current_mode = "do_together"
        # 解锁聊天输入
        self.chat_input.setEnabled(True)
        self.send_btn.setEnabled(True)
        # 提示模式切换
        self.chat_display.append(f"【系统】已切换至「{btn.text()}」模式，可开始对话～")

    # 添加API测试连接方法
    def _test_api_connection(self):
        """测试API连接"""
        api_key = self.api_key_input.text().strip()
        base_url = self.api_url_input.text().strip()
        model_name = self.model_name_input.text().strip()

        # 初始化客户端
        success, msg = self.api_handler.init_client(api_key, base_url)
        if success:
            # 更新模型名称
            self.api_handler.model_name = model_name
            msg += f"，模型：{model_name}"
        
        self.chat_display.append(f"【API测试】{msg}")


    def _create_new_persona(self):
        """创建新人设：弹出编辑弹窗，保存到列表"""
        dialog = PersonaEditDialog(self)
        if dialog.exec():  # 弹窗确认关闭
            new_persona = dialog.get_persona_data()
            self.role_personas.append(new_persona)
            self.current_persona = new_persona  # 自动选中新人设
            # 提示创建成功
            self.chat_display.append(f"【系统】成功创建新人设「{new_persona['name']}」！")
            # 打印人设详情（便于调试）
            self._show_persona_detail(new_persona)

    def _switch_role_persona(self):
        """切换人设：支持手动循环切换+情感值自动切换"""
        if len(self.role_personas) == 0:
            self.chat_display.append("【系统】暂无可用人设，请先创建！")
            return
        
        # 1. 手动循环切换
        current_idx = self.role_personas.index(self.current_persona)
        next_idx = (current_idx + 1) % len(self.role_personas)
        self.current_persona = self.role_personas[next_idx]
        
        # 2. 情感值自动切换逻辑（示例：好感度≥90优先选女友类人设）
        if self.emotion_values["liking"] >= 90:
            # 筛选“女友/恋人”类人设
            lover_personas = [p for p in self.role_personas if "女友" in p["relation"] or "恋人" in p["relation"]]
            if lover_personas:
                self.current_persona = lover_personas[0]
        elif self.emotion_values["trust"] >= 90:
            # 筛选“朋友/家人”类人设
            friend_personas = [p for p in self.role_personas if "朋友" in p["relation"] or "兄妹" in p["relation"]]
            if friend_personas:
                self.current_persona = friend_personas[0]
        
        # 提示切换成功，并显示人设详情
        self.chat_display.append(f"【系统】已切换至人设「{self.current_persona['name']}」")
        self._show_persona_detail(self.current_persona)

    def _show_persona_detail(self, persona):
        """显示人设详细信息到聊天区"""
        detail = f"""
    【人设详情】
    姓名：{persona['name']} | 性别：{persona['gender']} | 年龄：{persona['age']}
    职业：{persona['career']} | 与你的关系：{persona['relation']}
    外貌：{persona['appearance']} | 穿搭：{persona['outfit']}
    性格：{persona['personality']} | 爱好：{persona['hobby']}
    对你的称呼：{persona['call_player']} | 对话风格：{persona['chat_style']}
    """
        self.chat_display.append(detail)

    # 存档/日记/背包方法
    def _save_game(self):
        """保存存档"""
        # 更新存档数据
        self.data_manager.save_data["emotion_values"] = self.emotion_values
        self.data_manager.save_data["days_counter"] = DAYS_COUNTER
        self.data_manager.save_data["role_images"] = self.role_images
        self.data_manager.save_data["current_persona"] = self.current_persona if hasattr(self, "current_persona") else "默认人设"
        # 保存到文件
        success, msg = self.data_manager.save_data_to_file()
        self.chat_display.append(f"【系统】{msg}")

    def _generate_diary(self):
        """生成日记"""
        if not hasattr(self, "last_chat"):
            self.chat_display.append("【系统】暂无对话记录，无法生成日记～")
            return
        # 生成日记
        diary = self.data_manager.generate_diary(
            self.current_mode,
            self.last_chat["user"],
            self.last_chat["ai"],
            self.current_persona if hasattr(self, "current_persona") else "默认人设"
        )
        self.chat_display.append("【日记】\n" + diary)

    def _show_backpack(self):
        """查看背包"""
        backpack = self.data_manager.save_data["backpack"]
        if not backpack:
            self.chat_display.append("【背包】暂无物品～")
            return
        backpack_str = "【背包】\n"
        for idx, item in enumerate(backpack, 1):
            backpack_str += f"{idx}. {item['item']}（添加时间：{item['add_time']}）\n"
        self.chat_display.append(backpack_str)


    # ==================================================================
    def _send_chat_message(self):
        """发送聊天消息，调用AI回复"""
        user_input = self.chat_input.text().strip()
        if not user_input:
            return
        # 清空输入框
        self.chat_input.clear()
        # 显示用户消息
        self.chat_display.append(f"【你】{user_input}")

        # 重构：组装完整的人设提示词（让AI理解详细人设）
        persona_prompt = f"""
    你需要扮演以下角色：
    姓名：{self.current_persona['name']}
    性别：{self.current_persona['gender']}，年龄：{self.current_persona['age']}，职业：{self.current_persona['career']}
    与玩家的关系：{self.current_persona['relation']}，需称呼玩家为：{self.current_persona['call_player']}
    外貌：{self.current_persona['appearance']}，日常穿搭：{self.current_persona['outfit']}
    性格：{self.current_persona['personality']}，爱好：{self.current_persona['hobby']}
    对话风格要求：{self.current_persona['chat_style']}
    当前对玩家的好感度：{self.emotion_values['liking']}，信任度：{self.emotion_values['trust']}
    """
        
        # 调用AI回复（传入完整人设提示词）
        ai_response = self.api_handler.call_ai_api(
            user_input, 
            self.current_mode, 
            role_persona=persona_prompt  # 传入人设提示词
        )


        
        # 显示AI回复
        self.chat_display.append(f"【TA】{ai_response}")
        # 随机增减情感值（模拟情感互动）
        import random
        self.emotion_values["liking"] += random.randint(-2, 5)
        self.emotion_values["trust"] += random.randint(-1, 4)
        # 修正情感值范围（0-100）
        self.emotion_values["liking"] = max(0, min(100, self.emotion_values["liking"]))
        self.emotion_values["trust"] = max(0, min(100, self.emotion_values["trust"]))
        # 更新顶部情感值显示
        self.liking_label.setText(f"好感度：{self.emotion_values['liking']}")
        self.trust_label.setText(f"信任度：{self.emotion_values['trust']}")

        # 记录最后一次对话（用于生成日记）
        self.last_chat = {
            "user": user_input,
            "ai": ai_response
        }
        # 模拟添加背包物品（关键词触发）
        if "给你" in user_input or "送你" in user_input:
            item = user_input.replace("给你", "").replace("送你", "").strip()
            if item:
                msg = self.data_manager.add_backpack_item(item)
                self.chat_display.append(f"【系统】{msg}")

# 测试基础UI（单独运行该文件时生效）
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EmotionChatUI()
    window.show()
    sys.exit(app.exec())