import requests
from typing import Dict, Any, Optional

class HttpClient:
    """HTTP客户端工具类"""
    
    @staticmethod
    def get(url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送GET请求
        
        Args:
            url: 请求URL
            headers: 请求头
            params: 查询参数
            
        Returns:
            响应数据
        """
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    
    @staticmethod
    def post(url: str, headers: Optional[Dict[str, str]] = None, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送POST请求
        
        Args:
            url: 请求URL
            headers: 请求头
            json: 请求体
            
        Returns:
            响应数据
        """
        response = requests.post(url, headers=headers, json=json)
        response.raise_for_status()
        return response.json()
    
    @staticmethod
    def put(url: str, headers: Optional[Dict[str, str]] = None, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送PUT请求
        
        Args:
            url: 请求URL
            headers: 请求头
            json: 请求体
            
        Returns:
            响应数据
        """
        response = requests.put(url, headers=headers, json=json)
        response.raise_for_status()
        return response.json()
    
    @staticmethod
    def delete(url: str, headers: Optional[Dict[str, str]] = None) -> None:
        """发送DELETE请求
        
        Args:
            url: 请求URL
            headers: 请求头
        """
        response = requests.delete(url, headers=headers)
        response.raise_for_status()