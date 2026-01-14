"""
低空无人机飞行风险评估系统

主程序入口
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from app.ui.main_window import MainWindow
from app.db import get_db


def main():
    """主函数"""
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("低空无人机飞行风险评估系统")
    app.setApplicationVersion("1.0.0")
    
    # 设置默认字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 初始化数据库
    db = get_db()
    print(f"数据库路径: {db.db_path}")
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
