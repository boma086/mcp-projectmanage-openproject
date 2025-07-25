"""
用户领域模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator, EmailStr


class User(BaseModel):
    """用户实体"""
    
    id: str = Field(..., description="用户唯一标识")
    name: str = Field(..., description="用户姓名")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    login: Optional[str] = Field(None, description="登录名")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    status: Optional[str] = Field(None, description="用户状态")
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('用户姓名不能为空')
        return v.strip()
    
    @validator('login')
    def login_must_be_valid(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                return None
            # 登录名通常只包含字母、数字、下划线、点和连字符
            import re
            if not re.match(r'^[a-zA-Z0-9._-]+$', v):
                raise ValueError('登录名只能包含字母、数字、下划线、点和连字符')
        return v
    
    def is_active(self) -> bool:
        """检查用户是否处于活跃状态"""
        return self.status and self.status.lower() in ['active', 'registered']
    
    def get_display_name(self) -> str:
        """获取显示名称"""
        if self.email:
            return f"{self.name} <{self.email}>"
        return self.name
    
    def get_short_name(self) -> str:
        """获取简短名称（用于显示）"""
        # 如果名称包含空格，返回首字母缩写
        parts = self.name.split()
        if len(parts) > 1:
            return ''.join(part[0].upper() for part in parts if part)
        return self.name[:2].upper()
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        schema_extra = {
            "example": {
                "id": "1",
                "name": "张三",
                "email": "zhangsan@example.com",
                "login": "zhangsan",
                "status": "active"
            }
        }
