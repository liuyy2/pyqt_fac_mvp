"""
模型统一接口与注册器
Model Base Class and Registry - 提供模型的标准接口和动态注册机制
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type
from dataclasses import dataclass, field
from enum import Enum
import json


class ParamType(Enum):
    """参数类型枚举"""
    INT = "int"
    FLOAT = "float"
    STR = "str"
    BOOL = "bool"
    ENUM = "enum"


@dataclass
class ParamSpec:
    """参数规格定义"""
    name: str                          # 参数名
    label: str                         # 显示标签
    param_type: ParamType             # 参数类型
    default: Any                       # 默认值
    description: str = ""              # 参数描述
    min_value: Optional[float] = None  # 最小值(数值类型)
    max_value: Optional[float] = None  # 最大值(数值类型)
    enum_values: List[str] = field(default_factory=list)  # 枚举选项
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "param_type": self.param_type.value,
            "default": self.default,
            "description": self.description,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "enum_values": self.enum_values
        }


@dataclass
class ModelResult:
    """模型运行结果基类"""
    model_id: str
    model_name: str
    success: bool = True
    error_message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "success": self.success,
            "error_message": self.error_message,
            "data": self.data
        }


class ModelBase(ABC):
    """
    模型基类 - 所有风险评估模型必须继承此类
    
    子类必须实现:
    - model_id: 唯一标识
    - model_name: 显示名称
    - description: 模型描述
    - param_schema(): 返回参数规格列表
    - run(context): 执行模型并返回结果
    """
    
    @property
    @abstractmethod
    def model_id(self) -> str:
        """模型唯一标识"""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """模型显示名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """模型描述"""
        pass
    
    @property
    def category(self) -> str:
        """模型分类（可选）"""
        return "通用"
    
    @abstractmethod
    def param_schema(self) -> List[ParamSpec]:
        """
        返回模型参数规格列表
        用于UI动态生成参数输入面板
        """
        pass
    
    @abstractmethod
    def run(self, context: Dict[str, Any]) -> ModelResult:
        """
        执行模型计算
        
        Args:
            context: 上下文信息，包含:
                - mission_id: 任务ID
                - params: 用户设置的参数字典
                - dataset: 风险数据集(可选)
                
        Returns:
            ModelResult: 模型计算结果
        """
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> tuple[bool, str]:
        """
        验证参数是否合法
        
        Returns:
            (is_valid, error_message)
        """
        schema = self.param_schema()
        for spec in schema:
            if spec.name not in params:
                # 使用默认值
                continue
            
            value = params[spec.name]
            
            # 类型检查
            if spec.param_type == ParamType.INT:
                if not isinstance(value, int):
                    return False, f"参数 {spec.label} 必须是整数"
                if spec.min_value is not None and value < spec.min_value:
                    return False, f"参数 {spec.label} 不能小于 {spec.min_value}"
                if spec.max_value is not None and value > spec.max_value:
                    return False, f"参数 {spec.label} 不能大于 {spec.max_value}"
                    
            elif spec.param_type == ParamType.FLOAT:
                if not isinstance(value, (int, float)):
                    return False, f"参数 {spec.label} 必须是数值"
                if spec.min_value is not None and value < spec.min_value:
                    return False, f"参数 {spec.label} 不能小于 {spec.min_value}"
                if spec.max_value is not None and value > spec.max_value:
                    return False, f"参数 {spec.label} 不能大于 {spec.max_value}"
                    
            elif spec.param_type == ParamType.ENUM:
                if value not in spec.enum_values:
                    return False, f"参数 {spec.label} 必须是 {spec.enum_values} 之一"
        
        return True, ""
    
    def get_default_params(self) -> Dict[str, Any]:
        """获取默认参数字典"""
        return {spec.name: spec.default for spec in self.param_schema()}
    
    def get_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "description": self.description,
            "category": self.category,
            "param_schema": [p.to_dict() for p in self.param_schema()]
        }


class ModelRegistry:
    """
    模型注册器 - 管理所有可用的风险评估模型
    
    使用单例模式确保全局唯一
    """
    
    _instance = None
    _models: Dict[str, ModelBase] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._models = {}
        return cls._instance
    
    def register(self, model: ModelBase) -> None:
        """注册一个模型"""
        self._models[model.model_id] = model
    
    def unregister(self, model_id: str) -> None:
        """取消注册一个模型"""
        if model_id in self._models:
            del self._models[model_id]
    
    def get(self, model_id: str) -> Optional[ModelBase]:
        """获取指定模型实例"""
        return self._models.get(model_id)
    
    def get_all(self) -> List[ModelBase]:
        """获取所有已注册模型"""
        return list(self._models.values())
    
    def get_model_ids(self) -> List[str]:
        """获取所有已注册模型ID"""
        return list(self._models.keys())
    
    def get_models_by_category(self, category: str) -> List[ModelBase]:
        """按分类获取模型"""
        return [m for m in self._models.values() if m.category == category]
    
    def get_all_info(self) -> List[Dict[str, Any]]:
        """获取所有模型的信息"""
        return [m.get_info() for m in self._models.values()]
    
    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """列出所有模型及其信息"""
        result = {}
        for model_id, model in self._models.items():
            result[model_id] = {
                "name": model.model_name,
                "description": model.description,
                "category": model.category
            }
        return result


# 全局注册器实例
model_registry = ModelRegistry()


def register_model(model_class: Type[ModelBase]) -> Type[ModelBase]:
    """
    模型注册装饰器
    
    使用方法:
    @register_model
    class MyModel(ModelBase):
        ...
    """
    model_registry.register(model_class())
    return model_class


def get_model(model_id: str) -> Optional[ModelBase]:
    """便捷函数：获取模型"""
    return model_registry.get(model_id)


def get_all_models() -> List[ModelBase]:
    """便捷函数：获取所有模型"""
    return model_registry.get_all()
