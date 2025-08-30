"""
认证服务：处理 OAuth 2.0 和 API 密钥管理
"""
import os
import secrets
import base64
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass

import requests
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from pydantic import BaseModel, Field, validator

from mcp_core.shared.exceptions import AuthenticationError, AuthorizationError, ConfigurationError
from mcp_core.shared.config import Config
from mcp_core.shared.logger import get_logger


class AuthType(str, Enum):
    """认证类型枚举"""
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    BASIC = "basic"


class OAuth2GrantType(str, Enum):
    """OAuth 2.0 授权类型"""
    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"
    PASSWORD = "password"
    REFRESH_TOKEN = "refresh_token"


@dataclass
class OAuth2Config:
    """OAuth 2.0 配置"""
    client_id: str
    client_secret: str
    authorization_url: str
    token_url: str
    redirect_uri: str
    scope: str = "api_v3"
    grant_type: OAuth2GrantType = OAuth2GrantType.AUTHORIZATION_CODE


@dataclass
class TokenInfo:
    """令牌信息"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

    @property
    def is_expired(self) -> bool:
        """检查令牌是否过期"""
        return datetime.now() > self.created_at + timedelta(seconds=self.expires_in)

    @property
    def expires_at(self) -> datetime:
        """获取令牌过期时间"""
        return self.created_at + timedelta(seconds=self.expires_in)


class APIKeyInfo(BaseModel):
    """API 密钥信息"""
    key_id: str
    key_secret: str
    description: str
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    permissions: List[str] = Field(default_factory=list)

    @property
    def is_expired(self) -> bool:
        """检查 API 密钥是否过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


class CredentialStorage:
    """安全凭据存储"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        self.fernet = self._initialize_encryption(encryption_key)
        self._credentials: Dict[str, bytes] = {}
        
    def _initialize_encryption(self, key: Optional[str] = None) -> Optional[Fernet]:
        """初始化加密"""
        if key is None:
            # 从环境变量获取或生成随机密钥
            key = os.getenv("MCP_ENCRYPTION_KEY")
            if key is None:
                # 生产环境应该设置加密密钥
                return None
        
        # 确保密钥是 32 字节的 URL-safe base64 编码字符串
        if len(key) != 44 or not key.endswith('='):
            # 生成新的加密密钥
            key = Fernet.generate_key().decode()
        
        return Fernet(key.encode())
    
    def encrypt(self, data: str) -> str:
        """加密数据"""
        if self.fernet is None:
            return data  # 不加密
        
        encrypted = self.fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """解密数据"""
        if self.fernet is None:
            return encrypted_data  # 未加密
        
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            raise AuthenticationError(f"解密失败: {str(e)}")
    
    def store_credential(self, key: str, value: str) -> None:
        """存储凭据"""
        encrypted = self.encrypt(value)
        self._credentials[key] = encrypted.encode()
    
    def retrieve_credential(self, key: str) -> Optional[str]:
        """检索凭据"""
        encrypted = self._credentials.get(key)
        if encrypted is None:
            return None
        
        return self.decrypt(encrypted.decode())


class AuthenticationService:
    """认证服务"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger(__name__)
        self.credential_storage = CredentialStorage()
        self._tokens: Dict[str, TokenInfo] = {}
        self._api_keys: Dict[str, APIKeyInfo] = {}
        
    async def initialize(self) -> None:
        """初始化认证服务"""
        self.logger.info("Initializing authentication service")
        # 可以在这里加载持久化的令牌和 API 密钥
        
    # OAuth 2.0 相关方法
    
    def get_oauth2_authorization_url(self, config: OAuth2Config, state: Optional[str] = None) -> str:
        """获取 OAuth 2.0 授权 URL"""
        if not state:
            state = secrets.token_urlsafe(16)
        
        params = {
            "client_id": config.client_id,
            "response_type": "code",
            "redirect_uri": config.redirect_uri,
            "scope": config.scope,
            "state": state
        }
        
        # 构建授权 URL
        from urllib.parse import urlencode
        return f"{config.authorization_url}?{urlencode(params)}"
    
    async def exchange_oauth2_code_for_token(self, config: OAuth2Config, code: str) -> TokenInfo:
        """使用授权码交换访问令牌"""
        try:
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": config.redirect_uri,
                "client_id": config.client_id,
                "client_secret": config.client_secret
            }
            
            response = requests.post(
                config.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30
            )
            
            if response.status_code != 200:
                raise AuthenticationError(
                    f"OAuth 2.0 token exchange failed: {response.status_code} - {response.text}"
                )
            
            token_data = response.json()
            token_info = TokenInfo(
                access_token=token_data["access_token"],
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data.get("expires_in", 3600),
                refresh_token=token_data.get("refresh_token"),
                scope=token_data.get("scope")
            )
            
            # 存储令牌
            self._tokens[config.client_id] = token_info
            
            return token_info
            
        except requests.RequestException as e:
            raise AuthenticationError(f"OAuth 2.0 token exchange request failed: {str(e)}")
    
    async def refresh_oauth2_token(self, config: OAuth2Config, refresh_token: str) -> TokenInfo:
        """刷新 OAuth 2.0 访问令牌"""
        try:
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": config.client_id,
                "client_secret": config.client_secret
            }
            
            response = requests.post(
                config.token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30
            )
            
            if response.status_code != 200:
                raise AuthenticationError(
                    f"OAuth 2.0 token refresh failed: {response.status_code} - {response.text}"
                )
            
            token_data = response.json()
            token_info = TokenInfo(
                access_token=token_data["access_token"],
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data.get("expires_in", 3600),
                refresh_token=token_data.get("refresh_token"),
                scope=token_data.get("scope")
            )
            
            # 更新存储的令牌
            self._tokens[config.client_id] = token_info
            
            return token_info
            
        except requests.RequestException as e:
            raise AuthenticationError(f"OAuth 2.0 token refresh request failed: {str(e)}")
    
    def get_token_for_client(self, client_id: str) -> Optional[TokenInfo]:
        """获取客户端的令牌信息"""
        token_info = self._tokens.get(client_id)
        if token_info and token_info.is_expired:
            # 自动移除过期令牌
            del self._tokens[client_id]
            return None
        return token_info
    
    # API 密钥相关方法
    
    def generate_api_key(self, description: str, permissions: List[str], 
                        expires_in_days: Optional[int] = 365) -> APIKeyInfo:
        """生成新的 API 密钥"""
        key_id = secrets.token_urlsafe(8)
        key_secret = secrets.token_urlsafe(32)
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)
        
        api_key_info = APIKeyInfo(
            key_id=key_id,
            key_secret=key_secret,
            description=description,
            expires_at=expires_at,
            permissions=permissions
        )
        
        # 存储 API 密钥（生产环境应该持久化到数据库）
        self._api_keys[key_id] = api_key_info
        
        # 安全存储密钥（加密）
        storage_key = f"api_key_{key_id}"
        self.credential_storage.store_credential(storage_key, key_secret)
        
        return api_key_info
    
    def validate_api_key(self, key_id: str, key_secret: str) -> bool:
        """验证 API 密钥"""
        api_key_info = self._api_keys.get(key_id)
        if not api_key_info:
            return False
        
        if not api_key_info.is_active:
            return False
        
        if api_key_info.is_expired:
            # 自动禁用过期密钥
            api_key_info.is_active = False
            return False
        
        # 从安全存储中检索并验证密钥
        storage_key = f"api_key_{key_id}"
        stored_secret = self.credential_storage.retrieve_credential(storage_key)
        
        if stored_secret != key_secret:
            return False
        
        return True
    
    def get_api_key_info(self, key_id: str) -> Optional[APIKeyInfo]:
        """获取 API 密钥信息"""
        return self._api_keys.get(key_id)
    
    def revoke_api_key(self, key_id: str) -> bool:
        """撤销 API 密钥"""
        if key_id not in self._api_keys:
            return False
        
        self._api_keys[key_id].is_active = False
        return True
    
    def list_api_keys(self) -> List[APIKeyInfo]:
        """列出所有 API 密钥"""
        return list(self._api_keys.values())
    
    # 通用认证方法
    
    async def authenticate(self, auth_type: AuthType, credentials: Dict[str, Any]) -> bool:
        """通用认证方法"""
        try:
            if auth_type == AuthType.API_KEY:
                return self._authenticate_api_key(credentials)
            elif auth_type == AuthType.OAUTH2:
                return await self._authenticate_oauth2(credentials)
            elif auth_type == AuthType.BASIC:
                return self._authenticate_basic(credentials)
            else:
                raise AuthenticationError(f"Unsupported authentication type: {auth_type}")
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            raise AuthenticationError(f"Authentication failed: {str(e)}")
    
    def _authenticate_api_key(self, credentials: Dict[str, Any]) -> bool:
        """API 密钥认证"""
        key_id = credentials.get("key_id")
        key_secret = credentials.get("key_secret")
        
        if not key_id or not key_secret:
            raise AuthenticationError("API key ID and secret are required")
        
        return self.validate_api_key(key_id, key_secret)
    
    async def _authenticate_oauth2(self, credentials: Dict[str, Any]) -> bool:
        """OAuth 2.0 认证"""
        # 这里可以验证 OAuth 2.0 令牌的有效性
        # 实际实现应该调用令牌内省端点
        access_token = credentials.get("access_token")
        if not access_token:
            raise AuthenticationError("Access token is required for OAuth 2.0 authentication")
        
        # 简单验证 - 生产环境应该调用内省端点
        return len(access_token) > 10  # 基本验证
    
    def _authenticate_basic(self, credentials: Dict[str, Any]) -> bool:
        """基本认证"""
        username = credentials.get("username")
        password = credentials.get("password")
        
        if not username or not password:
            raise AuthenticationError("Username and password are required for basic authentication")
        
        # 这里应该验证用户名和密码
        # 实际实现应该连接到用户存储
        return True  # 简化实现
    
    # 工具方法
    
    def get_auth_headers(self, auth_type: AuthType, credentials: Dict[str, Any]) -> Dict[str, str]:
        """获取认证头"""
        if auth_type == AuthType.API_KEY:
            return {"Authorization": f"Bearer {credentials.get('key_secret', '')}"}
        elif auth_type == AuthType.OAUTH2:
            return {"Authorization": f"Bearer {credentials.get('access_token', '')}"}
        elif auth_type == AuthType.BASIC:
            import base64
            auth_str = f"{credentials.get('username', '')}:{credentials.get('password', '')}"
            encoded = base64.b64encode(auth_str.encode()).decode()
            return {"Authorization": f"Basic {encoded}"}
        else:
            return {}


def create_authentication_service(config: Config) -> AuthenticationService:
    """创建认证服务工厂函数"""
    return AuthenticationService(config)