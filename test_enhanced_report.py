#!/usr/bin/env python3
"""
增强型报告测试脚本
直接模拟测试数据来验证报告功能
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, '/Users/mabo/developer/repository/git/mcp-projectmanage-openproject')

from datetime import datetime, timedelta
from mcp_core.domain.models import Project, WorkPackage
from app.services.enhanced_report_generator import EnhancedReportGeneratorService, ReportLanguage

class MockOpenProjectClient:
    """模拟OpenProject客户端用于测试"""
    
    async def get_project(self, project_id):
        """模拟获取项目"""
        return Project(
            id=project_id,
            name="测试项目",
            description="这是一个测试项目"
        )
    
    async def get_work_packages(self, project_id):
        """模拟获取工作包 - 创建有意义的测试数据"""
        work_packages = []
        
        # 创建各种状态的工作包
        statuses = ["New", "In Progress", "Closed", "On Hold"]
        types = ["Task", "Bug", "Feature", "Epic"]
        assignees = ["张三", "李四", "王五", "赵六", None]  # 包含一些未分配的情况
        
        for i in range(20):
            status = statuses[i % len(statuses)]
            wp_type = types[i % len(types)]
            assignee = assignees[i % len(assignees)]
            
            # 根据状态设置进度
            if status == "Closed":
                progress = 100
            elif status == "In Progress":
                progress = random.randint(30, 80)
            else:
                progress = 0
            
            # 创建时间（最近30天内）
            created_at = datetime.now() - timedelta(days=random.randint(1, 30))
            
            work_package = WorkPackage(
                id=i + 1,
                subject=f"测试工作包 {i+1} - {wp_type}",
                description=f"这是第 {i+1} 个测试工作包的详细描述，用于验证增强型报告功能",
                type=wp_type,
                status=status,
                assigned_to=assignee,
                progress=progress,
                created_at=created_at,
                updated_at=created_at + timedelta(days=random.randint(0, 5)),
                due_date=created_at + timedelta(days=random.randint(10, 20)) if random.random() > 0.2 else None
            )
            work_packages.append(work_package)
        
        return work_packages

async def test_enhanced_report():
    """测试增强型报告生成"""
    print("🚀 开始测试增强型报告生成...")
    
    # 创建模拟客户端
    mock_client = MockOpenProjectClient()
    
    # 创建增强型报告生成器
    generator = EnhancedReportGeneratorService(mock_client)
    
    # 测试中文报告
    print("\n📊 生成中文增强型周报:")
    try:
        report = await generator.generate_enhanced_weekly_report(
            project_id="2",
            start_date="2025-08-01",
            end_date="2025-08-29",
            language=ReportLanguage.CHINESE
        )
        
        print("✅ 报告生成成功！")
        print("=" * 80)
        print(report.to_markdown())
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 报告生成失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试日语报告
    print("\n📊 生成日语增强型周报:")
    try:
        report = await generator.generate_enhanced_weekly_report(
            project_id="2", 
            start_date="2025-08-01",
            end_date="2025-08-29",
            language=ReportLanguage.JAPANESE
        )
        
        print("✅ 日语报告生成成功！")
        print("=" * 80)
        print(report.to_markdown())
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ 日语报告生成失败: {e}")

if __name__ == "__main__":
    import random
    random.seed(42)  # 设置随机种子确保结果可重现
    
    asyncio.run(test_enhanced_report())