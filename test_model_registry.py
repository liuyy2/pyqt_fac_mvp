"""
测试模型注册是否正常工作
"""

from app.models import ModelRegistry

# 创建注册器实例
registry = ModelRegistry()

# 列出所有已注册的模型
print("已注册的模型:")
print("=" * 50)

models = registry.list_models()
for model_id, info in models.items():
    print(f"ID: {model_id}")
    print(f"  名称: {info['name']}")
    print(f"  描述: {info['description']}")
    print(f"  分类: {info['category']}")
    print("-" * 50)

print(f"\n总共注册了 {len(models)} 个模型")
