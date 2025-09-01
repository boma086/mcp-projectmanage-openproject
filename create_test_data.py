#!/usr/bin/env python3
"""
创建OpenProject测试数据脚本
用于为增强型报告生成器创建测试数据
"""
import requests
import json
from datetime import datetime, timedelta
import random

# OpenProject配置
OPENPROJECT_URL = "http://localhost:8090"
API_KEY = "your_api_key_here"  # 请替换为实际的API密钥
PROJECT_ID = 2

# 工作包状态映射
STATUSES = [
    "New", "In Progress", "Closed", "Rejected", "On Hold"
]

# 工作包类型
TYPES = [
    "Task", "Bug", "Feature", "Epic", "User Story"
]

# 团队成员
TEAM_MEMBERS = [
    "张三", "李四", "王五", "赵六", "钱七"
]

def create_test_work_packages():
    """创建测试工作包"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {API_KEY}"
    }
    
    # 创建一些有不同状态的工作包
    for i in range(10):
        status = random.choice(STATUSES)
        wp_type = random.choice(TYPES)
        assignee = random.choice(TEAM_MEMBERS)
        
        # 随机进度（0-100）
        progress = 0
        if status == "In Progress":
            progress = random.randint(30, 80)
        elif status == "Closed":
            progress = 100
        
        # 随机日期（最近30天内）
        created_date = datetime.now() - timedelta(days=random.randint(1, 30))
        updated_date = created_date + timedelta(days=random.randint(0, 10))
        due_date = created_date + timedelta(days=random.randint(5, 20))
        
        work_package_data = {
            "subject": f"测试工作包 {i+1} - {wp_type}",
            "description": f"这是第 {i+1} 个测试工作包的描述，类型为 {wp_type}，状态为 {status}",
            "type": wp_type,
            "status": status,
            "assignee": assignee,
            "progress": progress,
            "createdAt": created_date.isoformat(),
            "updatedAt": updated_date.isoformat(),
            "dueDate": due_date.isoformat() if random.random() > 0.3 else None
        }
        
        try:
            response = requests.post(
                f"{OPENPROJECT_URL}/api/v3/projects/{PROJECT_ID}/work_packages",
                headers=headers,
                json=work_package_data,
                timeout=10
            )
            
            if response.status_code == 201:
                print(f"✓ 成功创建工作包: {work_package_data['subject']}")
            else:
                print(f"✗ 创建工作包失败: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"✗ 请求失败: {e}")
            break

def update_existing_work_packages():
    """更新现有工作包的状态和进度"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {API_KEY}"
    }
    
    try:
        # 获取现有工作包
        response = requests.get(
            f"{OPENPROJECT_URL}/api/v3/projects/{PROJECT_ID}/work_packages",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            work_packages = response.json().get("_embedded", {}).get("elements", [])
            
            for wp in work_packages[:10]:  # 只更新前10个
                wp_id = wp["id"]
                
                update_data = {
                    "status": random.choice(STATUSES),
                    "progress": random.randint(0, 100),
                    "assignee": random.choice(TEAM_MEMBERS),
                    "updatedAt": datetime.now().isoformat()
                }
                
                update_response = requests.patch(
                    f"{OPENPROJECT_URL}/api/v3/work_packages/{wp_id}",
                    headers=headers,
                    json=update_data,
                    timeout=10
                )
                
                if update_response.status_code == 200:
                    print(f"✓ 成功更新工作包 ID {wp_id}")
                else:
                    print(f"✗ 更新工作包失败: {update_response.status_code}")
                    
        else:
            print(f"✗ 获取工作包失败: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"✗ 请求失败: {e}")

if __name__ == "__main__":
    print("开始创建OpenProject测试数据...")
    
    # 创建新的测试工作包
    print("\n1. 创建新的测试工作包:")
    create_test_work_packages()
    
    # 更新现有工作包
    print("\n2. 更新现有工作包状态:")
    update_existing_work_packages()
    
    print("\n测试数据创建完成！")
    print("现在可以重新生成增强型报告来查看完整的数据效果。")