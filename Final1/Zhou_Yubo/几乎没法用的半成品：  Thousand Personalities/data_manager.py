import json
import os
from datetime import datetime

class DataManager:
    def __init__(self, save_path="resources/save_data.json"):
        self.save_path = save_path
        # 初始化存档结构
        self.save_data = {
            "emotion_values": {"liking": 80, "trust": 75},
            "days_counter": 1,
            "role_images": [],
            "current_persona": "默认人设",
            "travel_places": [],  # 出行地点记录
            "do_events": [],      # 一起做事件记录
            "diary": [],          # 日记列表
            "backpack": []        # 背包物品
        }
        # 确保目录存在
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        # 加载已有存档
        self.load_save()
    
    def load_save(self):
        """加载存档"""
        if os.path.exists(self.save_path):
            try:
                with open(self.save_path, "r", encoding="utf-8") as f:
                    self.save_data = json.load(f)
                print(f"【数据管理】成功加载存档：{self.save_path}")
            except Exception as e:
                print(f"【数据管理】加载存档失败：{e}，使用默认数据")
    
    def save_data_to_file(self):
        """保存存档到文件"""
        try:
            with open(self.save_path, "w", encoding="utf-8") as f:
                json.dump(self.save_data, f, ensure_ascii=False, indent=4)
            return True, "存档保存成功～"
        except Exception as e:
            return False, f"存档保存失败：{str(e)}"
    
    def add_backpack_item(self, item_name):
        """添加背包物品"""
        self.save_data["backpack"].append({
            "item": item_name,
            "add_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return f"背包新增物品：{item_name}"
    
    def generate_diary(self, mode, user_chat, ai_chat, persona):
        """生成日记"""
        diary_content = f"""
【{datetime.now().strftime('%Y-%m-%d')}】{persona}的日记
今日互动模式：{mode}
和TA的对话：
TA：{user_chat}
我：{ai_chat}
心情：{"开心" if len(user_chat) > 10 else "平静"}
"""
        self.save_data["diary"].append(diary_content)
        return diary_content

# 测试数据管理
if __name__ == "__main__":
    dm = DataManager()
    # 测试添加背包物品
    print(dm.add_backpack_item("奶茶"))
    # 测试生成日记
    print(dm.generate_diary("chat", "今天天气好", "是呀～超适合出门", "活泼少女"))
    # 测试保存存档
    print(dm.save_data_to_file())