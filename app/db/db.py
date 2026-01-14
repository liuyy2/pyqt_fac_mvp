"""
数据库连接与初始化模块
Database Connection and Initialization Module
"""
import sqlite3
import os
from pathlib import Path
from typing import Optional

# 数据库文件路径
DB_DIR = Path(__file__).parent.parent.parent / "data"
DB_PATH = DB_DIR / "risk_assessment.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class Database:
    """数据库连接管理类"""
    
    _instance: Optional['Database'] = None
    
    def __init__(self, db_path: str = None):
        """初始化数据库连接"""
        if db_path is None:
            db_path = str(DB_PATH)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        
    def connect(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # 返回字典形式的结果
            self.conn.execute("PRAGMA foreign_keys = ON")  # 启用外键约束
        return self.conn
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def init_schema(self):
        """初始化数据库Schema"""
        conn = self.connect()
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        conn.commit()
        print(f"数据库已初始化: {self.db_path}")
    
    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """执行SQL语句"""
        conn = self.connect()
        cursor = conn.execute(sql, params)
        return cursor
    
    def executemany(self, sql: str, params_list: list) -> sqlite3.Cursor:
        """批量执行SQL语句"""
        conn = self.connect()
        cursor = conn.executemany(sql, params_list)
        return cursor
    
    def commit(self):
        """提交事务"""
        if self.conn:
            self.conn.commit()
    
    def rollback(self):
        """回滚事务"""
        if self.conn:
            self.conn.rollback()
    
    def fetchone(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """查询单条记录"""
        cursor = self.execute(sql, params)
        return cursor.fetchone()
    
    def fetchall(self, sql: str, params: tuple = ()) -> list:
        """查询所有记录"""
        cursor = self.execute(sql, params)
        return cursor.fetchall()
    
    def table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        result = self.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return result is not None
    
    def clear_all_data(self):
        """清空所有数据（保留表结构）"""
        tables = ['result_snapshot', 'fmea_item', 'risk_event', 
                  'indicator_value', 'indicator', 'indicator_category', 'mission']
        for table in tables:
            self.execute(f"DELETE FROM {table}")
        self.commit()
        # 重置自增ID
        self.execute("DELETE FROM sqlite_sequence")
        self.commit()


# 全局数据库实例
_db_instance: Optional[Database] = None


def get_db() -> Database:
    """获取全局数据库实例（单例模式）"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
        # 自动初始化Schema
        if not _db_instance.table_exists('mission'):
            _db_instance.init_schema()
    return _db_instance


def reset_db():
    """重置数据库实例"""
    global _db_instance
    if _db_instance:
        _db_instance.close()
    _db_instance = None
