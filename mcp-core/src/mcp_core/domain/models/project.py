"""
项目领域模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class Project(BaseModel):
    """项目实体"""
    
    id: str = Field(..., description="项目唯一标识")
    name: str = Field(..., description="项目名称")
    identifier: str = Field(..., description="项目标识符")
    description: Optional[str] = Field(None, description="项目描述")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    status: Optional[str] = Field(None, description="项目状态")
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('项目名称不能为空')
        return v.strip()
    
    @validator('identifier')
    def identifier_must_be_valid(cls, v):
        if not v or not v.strip():
            raise ValueError('项目标识符不能为空')
        # 项目标识符通常只包含字母、数字、下划线和连字符
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v.strip()):
            raise ValueError('项目标识符只能包含字母、数字、下划线和连字符')
        return v.strip()
    
    def is_active(self) -> bool:
        """检查项目是否处于活跃状态"""
        return self.status and self.status.lower() in ['active', 'on_track', 'in_progress']
    
    def get_display_name(self) -> str:
        """获取显示名称"""
        return f"{self.name} ({self.identifier})"
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
