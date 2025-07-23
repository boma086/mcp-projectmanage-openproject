from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class Project(BaseModel):
    id: str
    name: str
    identifier: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: Optional[str] = None

class WorkPackage(BaseModel):
    id: str
    subject: str
    description: Optional[str] = None
    status: Optional[str] = None
    type: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    progress: Optional[float] = Field(None, ge=0, le=100)

class ReportSection(BaseModel):
    title: str
    content: str

class Report(BaseModel):
    title: str
    project_name: str
    period: str
    generated_at: datetime = Field(default_factory=datetime.now)
    summary: str
    sections: List[ReportSection]
    statistics: Dict[str, Any] = Field(default_factory=dict)