"""
工作包领域模型
"""
from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, validator


class WorkPackageType(str, Enum):
    """工作包类型枚举"""
    TASK = "task"
    MILESTONE = "milestone"
    PHASE = "phase"
    FEATURE = "feature"
    BUG = "bug"
    EPIC = "epic"
    USER_STORY = "user_story"
    OTHER = "other"


class WorkPackagePriority(str, Enum):
    """工作包优先级枚举"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    IMMEDIATE = "immediate"


class WorkPackageStatus(str, Enum):
    """工作包状态枚举"""
    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    FEEDBACK = "feedback"
    CLOSED = "closed"
    REJECTED = "rejected"
    ON_HOLD = "on_hold"


class WorkPackage(BaseModel):
    """工作包实体"""
    
    id: str = Field(..., description="工作包唯一标识")
    subject: str = Field(..., description="工作包标题")
    description: Optional[str] = Field(None, description="工作包描述")
    status: Optional[str] = Field(None, description="工作包状态")
    type: Optional[str] = Field(None, description="工作包类型")
    priority: Optional[str] = Field(None, description="优先级")
    assigned_to: Optional[str] = Field(None, description="分配给")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    due_date: Optional[datetime] = Field(None, description="截止日期")
    progress: Optional[float] = Field(None, ge=0, le=100, description="完成进度 (0-100)")
    project_id: Optional[str] = Field(None, description="所属项目ID")
    
    @validator('subject')
    def subject_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('工作包标题不能为空')
        return v.strip()
    
    @validator('progress')
    def progress_must_be_valid(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('进度必须在 0-100 之间')
        return v
    
    def is_completed(self) -> bool:
        """检查工作包是否已完成"""
        return self.status and self.status.lower() in ['closed', 'resolved']
    
    def is_in_progress(self) -> bool:
        """检查工作包是否正在进行中"""
        return self.status and self.status.lower() in ['in_progress', 'feedback']
    
    def is_overdue(self) -> bool:
        """检查工作包是否已延期"""
        if not self.due_date or self.is_completed():
            return False
        return datetime.now() > self.due_date
    
    def get_priority_level(self) -> int:
        """获取优先级数值（用于排序）"""
        priority_map = {
            'low': 1,
            'normal': 2,
            'high': 3,
            'urgent': 4,
            'immediate': 5
        }
        return priority_map.get(self.priority.lower() if self.priority else 'normal', 2)
    
    def get_display_status(self) -> str:
        """获取显示状态"""
        status_map = {
            'new': '新建',
            'in_progress': '进行中',
            'resolved': '已解决',
            'feedback': '反馈中',
            'closed': '已关闭',
            'rejected': '已拒绝',
            'on_hold': '暂停'
        }
        return status_map.get(self.status.lower() if self.status else 'new', self.status or '未知')
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        schema_extra = {
            "example": {
                "id": "1",
                "subject": "实现用户登录功能",
                "description": "开发用户登录和认证功能",
                "status": "in_progress",
                "type": "feature",
                "priority": "high",
                "assigned_to": "张三",
                "progress": 60.0,
                "project_id": "1"
            }
        }
