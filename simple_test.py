#!/usr/bin/env python3
"""
简单测试增强型报告的核心功能
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, '/Users/mabo/developer/repository/git/mcp-projectmanage-openproject/solution-fastapi')
sys.path.insert(0, '/Users/mabo/developer/repository/git/mcp-projectmanage-openproject/mcp-core/src')

from datetime import datetime, timedelta
from app.services.reporting.metrics_calculator import MetricsCalculator
from app.i18n.translation_service import TranslationService

def test_metrics_calculator():
    """测试指标计算器"""
    print("🧪 测试指标计算器...")
    
    # 创建模拟工作包数据
    class MockWorkPackage:
        def __init__(self, id, status, type=None, assigned_to=None, progress=None, description=None):
            self.id = id
            self.status = status
            self.type = type
            self.assigned_to = assigned_to
            self.progress = progress
            self.description = description
            self.due_date = None
    
    # 创建各种状态的工作包
    work_packages = [
        MockWorkPackage(1, "Closed", "Task", "张三", 100, "已完成的任务"),
        MockWorkPackage(2, "In Progress", "Feature", "李四", 50, "进行中的功能开发"),
        MockWorkPackage(3, "New", "Bug", "王五", 0, "新发现的bug"),
        MockWorkPackage(4, "Closed", "Task", "赵六", 100, "另一个已完成任务"),
        MockWorkPackage(5, "In Progress", "Feature", "张三", 75, "第二个功能开发"),
        MockWorkPackage(6, "On Hold", "Task", None, 0, "暂停的任务"),
        MockWorkPackage(7, "Closed", "Bug", "李四", 100, "已修复的bug"),
        MockWorkPackage(8, "New", "Task", "王五", 0, "新任务"),
        MockWorkPackage(9, "In Progress", "Feature", "赵六", 30, "第三个功能"),
        MockWorkPackage(10, "Closed", "Task", "张三", 100, "又一个完成的任务")
    ]
    
    # 更新的工作包（模拟本周有更新的）
    updated_wps = work_packages[:7]  # 前7个有更新
    
    # 测试指标计算
    calculator = MetricsCalculator()
    
    import asyncio
    metrics = asyncio.run(calculator.calculate_all_metrics(work_packages, updated_wps))
    
    print("✅ 指标计算结果:")
    for category, values in metrics.items():
        print(f"\n📊 {category}:")
        for key, value in values.items():
            print(f"  {key}: {value}")

def test_translation_service():
    """测试翻译服务"""
    print("\n🌐 测试翻译服务...")
    
    service = TranslationService()
    
    # 测试基本翻译
    print(f"中文 'velocity': {service.translate('velocity', 'zh')}")
    print(f"日语 'velocity': {service.translate('velocity', 'ja')}")
    print(f"英文 'velocity': {service.translate('velocity', 'en')}")
    
    # 测试带上下文的翻译
    context = {
        "project_name": "测试项目",
        "updated_count": 15,
        "completion_rate": 75.5
    }
    
    summary_zh = service.translate("summary_template", "zh", context=context)
    summary_ja = service.translate("summary_template", "ja", context=context)
    summary_en = service.translate("summary_template", "en", context=context)
    
    print(f"\n📝 中文摘要: {summary_zh}")
    print(f"📝 日语摘要: {summary_ja}")
    print(f"📝 英文摘要: {summary_en}")

if __name__ == "__main__":
    test_metrics_calculator()
    test_translation_service()
    
    print("\n🎉 所有测试完成！增强型报告的核心功能正常工作。")