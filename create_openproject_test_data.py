#!/usr/bin/env python3
"""
OpenProject测试数据生成脚本
使用指定的API密钥创建测试数据
"""
import requests
import json
from datetime import datetime, timedelta
import random
import time

# OpenProject配置
OPENPROJECT_URL = "http://localhost:8090"
API_KEY = "dd1a13cef1bed2797db73f4905a8da1f886f5f4cf3353da13dd44040aaef27a5"
PROJECT_ID = "2"

# 认证头 - 使用API密钥作为用户名，密码为空
import base64

# Base64编码认证
credentials = base64.b64encode(f"apikey:{API_KEY}".encode()).decode()
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Basic {credentials}"
}

# 工作包状态
STATUSES = ["New", "In Progress", "Closed", "On Hold"]

# 工作包类型
TYPES = ["Task", "Bug", "Feature", "Epic"]

# 团队成员
TEAM_MEMBERS = ["张三", "李四", "王五", "赵六", "钱七"]

def check_api_connection():
    """检查API连接"""
    try:
        response = requests.get(
            f"{OPENPROJECT_URL}/api/v3/projects/{PROJECT_ID}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            project = response.json()
            print(f"✅ 成功连接到OpenProject项目: {project.get('name', 'Unknown')}")
            return True
        else:
            print(f"❌ 连接失败: HTTP {response.status_code}")
            print(f"响应: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 连接错误: {e}")
        return False

def get_existing_statuses():
    """获取现有的状态列表"""
    try:
        response = requests.get(
            f"{OPENPROJECT_URL}/api/v3/statuses",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            statuses = response.json().get("_embedded", {}).get("elements", [])
            # 返回状态ID和名称的映射
            return {status["name"]: status["id"] for status in statuses}
        else:
            print(f"⚠️ 无法获取状态列表，使用默认状态")
            return {}
            
    except Exception as e:
        print(f"⚠️ 获取状态列表失败: {e}")
        return {}

def get_existing_types():
    """获取现有的类型列表"""
    try:
        response = requests.get(
            f"{OPENPROJECT_URL}/api/v3/types",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            types = response.json().get("_embedded", {}).get("elements", [])
            # 返回类型ID和名称的映射
            return {type_["name"]: type_["id"] for type_ in types}
        else:
            print(f"⚠️ 无法获取类型列表，使用默认类型")
            return {}
            
    except Exception as e:
        print(f"⚠️ 获取类型列表失败: {e}")
        return {}

def create_test_work_package():
    """创建一个测试工作包"""
    # 获取实际的状态和类型ID映射
    status_map = get_existing_statuses()
    type_map = get_existing_types()
    
    # 选择可用的状态和类型
    available_statuses = list(status_map.keys()) or STATUSES
    available_types = list(type_map.keys()) or TYPES
    
    status_name = random.choice(available_statuses)
    type_name = random.choice(available_types)
    assignee = random.choice(TEAM_MEMBERS + [None])  # 有些工作包不分配
    
    # 根据状态设置进度
    if "Closed" in status_name or "Done" in status_name or "完成" in status_name:
        progress = 100
    elif "Progress" in status_name or "进行" in status_name:
        progress = random.randint(30, 80)
    else:
        progress = 0
    
    # 构建正确的链接格式
    _links = {
        "project": {
            "href": f"/api/v3/projects/{PROJECT_ID}"
        }
    }
    
    # 添加类型链接（如果知道类型ID）
    if type_name in type_map:
        _links["type"] = {
            "href": f"/api/v3/types/{type_map[type_name]}"
        }
    
    # 添加状态链接（如果知道状态ID）
    if status_name in status_map:
        _links["status"] = {
            "href": f"/api/v3/statuses/{status_map[status_name]}"
        }
    
    work_package_data = {
        "subject": f"测试工作包 - {type_name} - {status_name}",
        "description": f"这是自动生成的测试工作包，用于验证增强型报告功能。\n类型: {type_name}\n状态: {status_name}\n负责人: {assignee or '未分配'}",
        "_links": _links
    }
    
    # 添加可选的字段
    if assignee:
        work_package_data["description"] += f"\n进度: {progress}%"
    
    try:
        response = requests.post(
            f"{OPENPROJECT_URL}/api/v3/work_packages",
            headers=headers,
            json=work_package_data,
            timeout=15
        )
        
        if response.status_code == 201:
            created_wp = response.json()
            wp_id = created_wp.get("id")
            print(f"✅ 成功创建工作包 ID {wp_id}: {work_package_data['subject']}")
            
            # 更新工作包状态和进度
            update_work_package(wp_id, status_name, progress, assignee)
            return True
            
        else:
            print(f"❌ 创建工作包失败: HTTP {response.status_code}")
            print(f"响应: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return False

def update_work_package(wp_id, status, progress, assignee):
    """更新工作包状态和进度"""
    update_data = {
        "percentageDone": progress,
        "description": f"更新后的测试工作包 - 进度: {progress}% - 状态: {status}"
    }
    
    try:
        response = requests.patch(
            f"{OPENPROJECT_URL}/api/v3/work_packages/{wp_id}",
            headers=headers,
            json=update_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"   ✅ 成功更新工作包 {wp_id}: 进度={progress}%")
        else:
            print(f"   ⚠️ 更新工作包 {wp_id} 失败: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"   ⚠️ 更新工作包 {wp_id} 时出错: {e}")

def update_existing_work_packages():
    """更新现有的工作包"""
    try:
        response = requests.get(
            f"{OPENPROJECT_URL}/api/v3/projects/{PROJECT_ID}/work_packages",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            work_packages = response.json().get("_embedded", {}).get("elements", [])
            
            print(f"\n🔄 开始更新 {len(work_packages)} 个现有工作包...")
            
            for i, wp in enumerate(work_packages[:10]):  # 只更新前10个
                wp_id = wp["id"]
                
                # 随机分配状态和进度
                statuses = get_existing_statuses()
                status = random.choice(statuses)
                
                if "Closed" in status or "Done" in status:
                    progress = 100
                elif "Progress" in status:
                    progress = random.randint(30, 80)
                else:
                    progress = random.randint(0, 20)
                
                assignee = random.choice(TEAM_MEMBERS + [None])
                
                update_data = {
                    "percentageDone": progress,
                    "description": f"更新测试数据 - 状态: {status} - 进度: {progress}% - 负责人: {assignee or '未分配'}"
                }
                
                update_response = requests.patch(
                    f"{OPENPROJECT_URL}/api/v3/work_packages/{wp_id}",
                    headers=headers,
                    json=update_data,
                    timeout=10
                )
                
                if update_response.status_code == 200:
                    print(f"   ✅ 成功更新工作包 ID {wp_id}: 状态={status}, 进度={progress}%")
                else:
                    print(f"   ⚠️ 更新工作包 ID {wp_id} 失败")
                
                # 添加延迟避免请求过快
                time.sleep(0.5)
                
        else:
            print(f"❌ 获取工作包列表失败: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ 更新工作包时出错: {e}")

def main():
    """主函数"""
    print("🚀 OpenProject测试数据生成器")
    print("=" * 50)
    print(f"API密钥: {API_KEY[:10]}...{API_KEY[-10:]}")
    print(f"项目ID: {PROJECT_ID}")
    print(f"OpenProject地址: {OPENPROJECT_URL}")
    print("=" * 50)
    
    # 检查连接
    if not check_api_connection():
        print("\n❌ 无法连接到OpenProject，请检查:")
        print("1. OpenProject服务是否运行在 localhost:8090")
        print("2. API密钥是否正确")
        print("3. 项目ID是否存在")
        return
    
    # 创建新的测试工作包
    print(f"\n📝 创建新的测试工作包...")
    success_count = 0
    for i in range(5):  # 创建5个新的测试工作包
        if create_test_work_package():
            success_count += 1
        time.sleep(1)  # 添加延迟
    
    print(f"\n✅ 成功创建 {success_count}/5 个新的测试工作包")
    
    # 更新现有工作包
    print(f"\n🔄 更新现有工作包状态...")
    update_existing_work_packages()
    
    print(f"\n🎉 测试数据生成完成！")
    print(f"\n📊 现在可以重新生成增强型报告来查看完整效果:")
    print(f"curl -X POST http://localhost:8000/mcp \\")
    print(f"  -H \"Content-Type: application/json\" \\")
    print(f"  -d '{{\"jsonrpc\": \"2.0\", \"id\": 1, \"method\": \"tools/call\", \"params\": {{\"name\": \"generate_enhanced_weekly_report\", \"arguments\": {{\"project_id\": \"2\", \"start_date\": \"2025-08-01\", \"end_date\": \"2025-08-29\", \"language\": \"zh\"}}}}}}'")

if __name__ == "__main__":
    main()