import sys
from PyQt6.QtWidgets import QApplication
from ui_components import EmotionChatUI



if __name__ == "__main__":
    # 初始化QT应用
    app = QApplication(sys.argv)
    # 初始化主窗口
    main_window = EmotionChatUI()
    # 加载存档数据（同步到UI）
    main_window.emotion_values = main_window.data_manager.save_data["emotion_values"]
    main_window.liking_label.setText(f"好感度：{main_window.emotion_values['liking']}")
    main_window.trust_label.setText(f"信任度：{main_window.emotion_values['trust']}")
    # 显示窗口
    main_window.show()
    # 运行应用
    sys.exit(app.exec())


"""
虽然只是 1/4 成品，但是固定节目不能少：

指导老师 兼 打工牛马 ：
Doubao & DeepSeek


特别鸣谢：
Skycode 秋令营的学长们

"""