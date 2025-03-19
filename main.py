import os
import random
import subprocess
import platform
from datetime import datetime

from qfluentwidgets import PrimaryPushButton, PushButton, DisplayLabel
from qframelesswindow import FramelessDialog, FramelessWindow

from .ClassWidgets.base import PluginBase, SettingsBase
from PyQt5 import uic
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QMouseEvent
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QDialog,
    QVBoxLayout,
    QDesktopWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QHBoxLayout
)


def read_names_from_file(file_path):
    """读取名单文件并返回处理后的名单列表"""
    if not os.path.exists(file_path):
        # 默认名单，格式为：[名字, 概率等级]，默认概率为3(普通)
        default_names = [
            ["小明", 3],
            ["李华", 3],
            ["张四", 3],
            ["小五", 3]
        ]
        save_names_to_file(file_path, default_names)
        return default_names

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        
        names = []
        for line in lines:
            if not line.strip():
                continue
                
            parts = line.split(',')
            name = parts[0].strip()
            if not name:
                continue
                
            # 尝试获取概率等级，默认为3(普通)
            try:
                probability = int(parts[1].strip()) if len(parts) > 1 else 3
                # 确保概率在1-5范围内
                probability = max(1, min(5, probability))
            except:
                probability = 3
                
            names.append([name, probability])
            
        return names
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return []


def save_names_to_file(file_path, names):
    """保存名单到文件"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            for name_data in names:
                if isinstance(name_data, list) and len(name_data) >= 2:
                    f.write(f"{name_data[0]},{name_data[1]}\n")
                else:
                    f.write(f"{name_data},3\n")  # 默认概率为3
    except Exception as e:
        print(f"保存文件时出错: {e}")


class FloatingWindow(QWidget):
    closed = pyqtSignal()
    name_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.shuffled_names = []
        self.current_index = 0
        self.selected_history = []  # 记录已选择的学生
        self.load_names()
        self.drag_pos = QPoint()
        self.mouse_press_pos = QPoint()
        self.name_dialog = None
        self.init_ui()

    def init_ui(self):
        """初始化界面组件"""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 更加美观的悬浮按钮设计
        self.label = QLabel("点名", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(70, 130, 255, 0.8);
                font-family: 微软雅黑;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                padding: 2px;
            }
            QLabel:hover {
                background-color: rgba(90, 150, 255, 0.9);
            }
        """)
        self.label.setFixedSize(50, 40)
        self.setFixedSize(50, 40)
        self.move_to_corner()

    def load_names(self):
        """加载名单并初始化洗牌队列"""
        file_path = os.path.join(os.path.dirname(__file__), "names.txt")
        self.names_data = read_names_from_file(file_path)
        # 提取名字列表(不含概率信息)
        self.names = [item[0] for item in self.names_data]
        self.reset_shuffle()

    def reset_shuffle(self):
        """根据概率权重创建抽取池"""
        # 创建一个加权抽取池
        self.weighted_pool = []
        
        # 概率等级对应的权重
        probability_weights = {
            1: 0,     # 不可能 - 权重为0
            2: 10,    # 小概率 - 权重为10
            3: 30,    # 普通 - 权重为30
            4: 60,    # 大概率 - 权重为60
            5: 100    # 绝对 - 权重为100
        }
        
        # 是否有"绝对"级别的学生
        has_absolute = any(item[1] == 5 for item in self.names_data)
        
        for name_data in self.names_data:
            name = name_data[0]
            probability = name_data[1]
            
            # 如果存在"绝对"级别的学生，且当前学生不是"绝对"级别，则不加入池中
            if has_absolute and probability < 5:
                continue
                
            # 根据权重将学生名字添加到抽取池中
            weight = probability_weights.get(probability, 30)
            for _ in range(weight):
                self.weighted_pool.append(name)
                
        # 如果抽取池为空(可能全是"不可能"级别)，添加所有名字各一次
        if not self.weighted_pool:
            self.weighted_pool = self.names.copy()
            
        # 打乱抽取池
        random.shuffle(self.weighted_pool)
        self.current_index = 0

    def move_to_corner(self):
        """移动窗口到屏幕右下角"""
        screen = QDesktopWidget().availableGeometry()
        taskbar_height = 72
        x = screen.width() - self.width() - 1
        y = screen.height() - taskbar_height
        self.move(x, y)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            self.mouse_press_pos = event.globalPos()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            if (event.globalPos() - self.mouse_press_pos).manhattanLength() <= QApplication.startDragDistance():
                self.show_random_name()
            event.accept()

    def show_random_name(self):
        """触发随机点名"""
        name = self.get_next_name()
        # 发出信号而不是显示对话框
        self.name_selected.emit(name)

    def get_next_name(self):
        """从加权池中获取下一个名字"""
        if not self.weighted_pool:
            return "名单为空"

        if self.current_index >= len(self.weighted_pool):
            self.reset_shuffle()

        name = self.weighted_pool[self.current_index]
        self.current_index += 1
        
        # 记录选择历史
        self.selected_history.append(name)
        if len(self.selected_history) > 10:
            self.selected_history.pop(0)
            
        return name

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)


class NameDialog(QDialog):
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.animation_names = []
        self.timer = None
        self.final_name = name
        self.animation_count = 0
        self.init_ui(name)
        self.move_center()
        
    def init_ui(self, name):
        """初始化结果显示对话框"""
        self.setWindowTitle("随机点名结果")
        self.resize(600, 400)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 0, 0, 0)
        self.name_label = DisplayLabel(name)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setFont(QFont("黑体", 150))

        self.confirm_btn = PushButton()
        self.confirm_btn.setText("确定")
        self.confirm_btn.setFixedSize(100, 40)
        self.confirm_btn.clicked.connect(self.close)

        layout.addWidget(self.name_label)
        layout.addWidget(self.confirm_btn, alignment=Qt.AlignCenter)

    def update_content(self, new_name):
        self.name_label.setText(new_name)

    def move_center(self):
        """移动窗口到屏幕中心"""
        screen = QDesktopWidget().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def start_animation(self):
        """开始动画效果"""
        # 准备用于动画显示的随机名字
        file_path = os.path.join(os.path.dirname(__file__), "names.txt")
        all_names = read_names_from_file(file_path)
        self.animation_names = all_names
        random.shuffle(self.animation_names)
        
        self.animation_count = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(80)  # 初始速度较快
        
    def update_animation(self):
        """更新动画显示"""
        if self.animation_count < 12:
            # 随机显示一个名字
            name = random.choice(self.animation_names)
            self.name_label.setText(name)
            self.animation_count += 1
            # 逐渐减慢动画速度
            delay = 80 + int(self.animation_count * 20)
            self.timer.start(delay)
        else:
            # 动画结束，显示最终结果
            self.timer.stop()
            self.name_label.setText(self.final_name)


class ProbabilitySettingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("点名概率设置")
        self.resize(500, 600)
        self.setup_ui()
        self.load_names()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 添加说明标签
        description = QLabel("设置每位学生被点名的概率：")
        description.setFont(QFont("微软雅黑", 10))
        layout.addWidget(description)
        
        # 概率说明
        prob_desc = QLabel(
            "1 - 不可能: 几乎不会被点到\n"
            "2 - 小概率: 很少被点到\n"
            "3 - 普通: 正常概率\n"
            "4 - 大概率: 较高概率被点到\n"
            "5 - 绝对: 一定会被点到 (如有此类学生，仅从中选择)"
        )
        prob_desc.setFont(QFont("微软雅黑", 9))
        layout.addWidget(prob_desc)
        
        # 创建表格
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["学生姓名", "概率等级(1-5)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.save_btn = PushButton("保存设置")
        self.save_btn.clicked.connect(self.save_settings)
        
        self.cancel_btn = PushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
    def load_names(self):
        file_path = os.path.join(os.path.dirname(__file__), "names.txt")
        self.names_data = read_names_from_file(file_path)
        
        # 填充表格
        self.table.setRowCount(len(self.names_data))
        for row, name_data in enumerate(self.names_data):
            name_item = QTableWidgetItem(name_data[0])
            self.table.setItem(row, 0, name_item)
            
            prob_item = QTableWidgetItem(str(name_data[1]))
            self.table.setItem(row, 1, prob_item)
            
    def save_settings(self):
        # 收集表格中的数据
        updated_data = []
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text().strip()
            if not name:
                continue
                
            try:
                prob = int(self.table.item(row, 1).text())
                # 确保概率在1-5范围内
                prob = max(1, min(5, prob))
            except:
                prob = 3
                
            updated_data.append([name, prob])
            
        # 保存到文件
        file_path = os.path.join(os.path.dirname(__file__), "names.txt")
        save_names_to_file(file_path, updated_data)
        
        self.accept()


class Plugin(PluginBase):
    def __init__(self, cw_contexts, method):
        super().__init__(cw_contexts, method)
        self.floating_window = None
        self.result_widget_code = "random_name_result"
        self.animation_timer = None
        self.animation_count = 0
        self.animation_max = 15
        self.final_name = ""
        self.time_timer = None  # 用于时间更新的计时器
        self.showing_name = False  # 是否正在显示点名结果
        self.animation_active = False
        
    def execute(self):
        """启动插件主功能，确保时间显示正常初始化"""
        try:
            print("执行随机点名插件初始化...")
            
            # 关闭现有计时器，防止重复
            if hasattr(self, 'time_timer') and self.time_timer:
                self.time_timer.stop()
            
            # 重置状态变量
            self.showing_name = False
            self.animation_active = False
            
            # 首先注册小组件
            self.method.register_widget(
                widget_code=self.result_widget_code,
                widget_name="随机点名结果",
                widget_width=250
            )
            
            # 立即更新初始时间
            current_time = datetime.now().strftime("%H:%M:%S")
            self.method.change_widget_content(
                widget_code=self.result_widget_code,
                title="当前时间",
                content=current_time
            )
            
            # 创建悬浮窗
            if not self.floating_window:
                self.floating_window = FloatingWindow()
                self.floating_window.name_selected.connect(self.show_name_in_widget)
            self.floating_window.show()
            
            # 创建时间更新计时器，但确保只有一个
            if not hasattr(self, 'time_timer') or not self.time_timer:
                self.time_timer = QTimer()
                self.time_timer.timeout.connect(self.update_time_display)
            
            # 启动计时器
            if not self.time_timer.isActive():
                self.time_timer.start(1000)
            
        except Exception as e:
            print(f"插件初始化错误: {e}")
    
    def update_time_display(self):
        """更新小组件显示当前时间，增强防冲突机制"""
        # 如果正在显示点名结果或动画，不更新时间
        if self.showing_name or getattr(self, 'animation_active', False):
            return
        
        try:
            # 获取当前小组件状态
            widget = self.method.get_widget(self.result_widget_code)
            if not widget:
                return
            
            # 检查当前标题，如果是点名相关的不要更新
            current_title = ''
            try:
                current_title = widget.title()
            except:
                pass
            
            if current_title == "点名中..." or current_title == "点名结果":
                return
            
            # 更新时间
            current_time = datetime.now().strftime("%H:%M:%S")
            self.method.change_widget_content(
                widget_code=self.result_widget_code,
                title="当前时间",
                content=current_time
            )
        except Exception as e:
            print(f"时间更新错误: {e}")
        
    def show_name_in_widget(self, name):
        """在小组件中显示点名结果"""
        self.final_name = name
        self.showing_name = True  # 标记正在显示点名结果
        
        # 开始动画效果
        self.start_name_animation()
    
    def start_name_animation(self):
        """开始名字切换动画，添加更严格的状态控制"""
        try:
            # 设置动画活动状态
            self.animation_active = True
            self.showing_name = True
            
            names = self.floating_window.names
            if not names:
                self.method.change_widget_content(
                    widget_code=self.result_widget_code,
                    title="错误",
                    content="名单为空"
                )
                # 短暂显示错误后恢复时间显示
                QTimer.singleShot(3000, self.reset_to_time_display)
                return
            
            self.animation_count = 0
            
            # 确保停止所有其他计时器
            if hasattr(self, 'time_timer') and self.time_timer and self.time_timer.isActive():
                self.time_timer.stop()
            
            # 清理已有的动画计时器
            if self.animation_timer:
                if self.animation_timer.isActive():
                    self.animation_timer.stop()
            
            # 创建新的动画计时器
            self.animation_timer = QTimer()
            self.animation_timer.timeout.connect(self.update_animation)
            self.animation_timer.start(80)
        except Exception as e:
            print(f"动画启动错误: {e}")
            self.reset_to_time_display()
    
    def update_animation(self):
        """更新动画显示"""
        if self.animation_count < self.animation_max:
            # 随机显示一个名字
            temp_name = random.choice(self.floating_window.names)
            self.method.change_widget_content(
                widget_code=self.result_widget_code,
                title="点名中...",
                content=temp_name
            )
            self.animation_count += 1
            # 逐渐减慢动画速度
            delay = 80 + int(self.animation_count * 20)
            self.animation_timer.start(delay)
        else:
            # 动画结束，显示最终结果
            self.animation_timer.stop()
            
            # 更新小组件显示
            self.method.change_widget_content(
                widget_code=self.result_widget_code,
                title="点名结果",
                content=self.final_name
            )
            
            # 发送通知
            self.method.send_notification(
                state=4,
                title="随机点名",
                subtitle="已选中学生",
                content=f"恭喜{self.final_name}同学被点到！",
                duration=5000
            )
            
            # 设置结果显示计时器，10秒后恢复时间显示
            QTimer.singleShot(10000, self.reset_to_time_display)
    
    def reset_to_time_display(self):
        """重置为时间显示，确保状态正确恢复"""
        # 重置状态变量
        self.showing_name = False
        self.animation_active = False
        
        # 停止任何可能仍在运行的动画计时器
        if hasattr(self, 'animation_timer') and self.animation_timer:
            if self.animation_timer.isActive():
                self.animation_timer.stop()
        
        # 重新启动时间计时器
        if hasattr(self, 'time_timer') and self.time_timer:
            if not self.time_timer.isActive():
                self.time_timer.start(1000)
        
        # 立即更新为当前时间
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            self.method.change_widget_content(
                widget_code=self.result_widget_code,
                title="当前时间",
                content=current_time
            )
        except Exception as e:
            print(f"重置时间显示时出错: {e}")

    def update(self, cw_contexts):
        """增强的状态更新函数，确保小组件在各种情况下都能正常显示"""
        super().update(cw_contexts)
        
        try:
            # 先检查小组件是否存在，不存在则重新注册
            widget = self.method.get_widget(self.result_widget_code)
            if not widget:
                print("小组件不存在，重新注册...")
                self.method.register_widget(
                    widget_code=self.result_widget_code,
                    widget_name="随机点名结果",
                    widget_width=250
                )
                # 确保重新注册后检查其内容
                widget = self.method.get_widget(self.result_widget_code)
            
            # 确保在不显示点名结果时保持时间更新
            if not self.showing_name and widget:
                try:
                    widget_title = widget.title()
                    if widget_title != "点名中..." and widget_title != "点名结果":
                        self.update_time_display()
                except:
                    self.update_time_display()
            
            # 始终确保小组件宽度足够
            self.method.adjust_widget_width(
                widget_code=self.result_widget_code,
                width=250
            )
        except Exception as e:
            print(f"更新状态时出错: {e}")


class Settings(SettingsBase):
    def __init__(self, plugin_path, parent=None):
        super().__init__(plugin_path, parent)
        uic.loadUi(os.path.join(self.PATH, "settings.ui"), self)
        open_names_list = self.findChild(PrimaryPushButton, "open_names_list")
        open_names_list.clicked.connect(self.open_names_file)
        
        # 添加查看历史记录功能
        self.history_btn = self.findChild(PushButton, "view_history")
        if self.history_btn:
            self.history_btn.clicked.connect(self.show_history)
            
        # 添加概率设置按钮
        self.prob_btn = self.findChild(PushButton, "probability_settings")
        if self.prob_btn:
            self.prob_btn.clicked.connect(self.show_probability_settings)
        
    def open_names_file(self):
        """打开名单文件进行编辑"""
        file_path = os.path.join(self.PATH, "names.txt")
        if platform.system() == "Windows":
            os.startfile(file_path)
        elif platform.system() == "Linux":
            subprocess.call(["xdg-open", file_path])
        elif platform.system() == "Darwin":
            subprocess.call(["open", file_path])

    def show_history(self):
        """显示点名历史记录"""
        history_dialog = QDialog(self)
        history_dialog.setWindowTitle("点名历史记录")
        history_dialog.resize(300, 400)
        
        layout = QVBoxLayout(history_dialog)
        
        # 从主窗口获取历史记录
        floating_window = None
        plugin_instance = self.findPlugin()
        if plugin_instance and plugin_instance.floating_window:
            floating_window = plugin_instance.floating_window
        
        if floating_window and hasattr(floating_window, 'selected_history'):
            history = floating_window.selected_history
            if history:
                for i, name in enumerate(reversed(history), 1):
                    item_label = QLabel(f"{i}. {name}")
                    item_label.setFont(QFont("微软雅黑", 12))
                    layout.addWidget(item_label)
            else:
                layout.addWidget(QLabel("暂无点名记录"))
        else:
            layout.addWidget(QLabel("无法获取点名记录"))
            
        close_btn = PushButton("关闭")
        close_btn.clicked.connect(history_dialog.close)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        
        history_dialog.exec_()
        
    def findPlugin(self):
        """查找插件实例"""
        # 这需要在实际环境中实现
        return None  # 占位符

    def show_probability_settings(self):
        """显示概率设置对话框"""
        dialog = ProbabilitySettingDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # 如果设置被保存，刷新插件实例
            plugin_instance = self.findPlugin()
            if plugin_instance and plugin_instance.floating_window:
                plugin_instance.floating_window.load_names()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = FloatingWindow()
    window.show()
    sys.exit(app.exec_())
