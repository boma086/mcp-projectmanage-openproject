"""
企业级国际化翻译服务
支持上下文感知翻译、复数形式和插值
"""
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path


class TranslationService:
    """企业级翻译服务"""
    
    def __init__(self, locales_dir: str = "app/i18n/locales"):
        self.locales_dir = Path(locales_dir)
        self.translations: Dict[str, Dict[str, Any]] = {}
        self._load_all_translations()
    
    def _load_all_translations(self) -> None:
        """加载所有语言的所有翻译文件"""
        if not self.locales_dir.exists():
            return
        
        for locale_dir in self.locales_dir.iterdir():
            if locale_dir.is_dir():
                locale = locale_dir.name
                self.translations[locale] = {}
                
                for translation_file in locale_dir.glob("*.json"):
                    domain = translation_file.stem
                    try:
                        with open(translation_file, 'r', encoding='utf-8') as f:
                            self.translations[locale][domain] = json.load(f)
                    except (json.JSONDecodeError, FileNotFoundError):
                        self.translations[locale][domain] = {}
    
    def translate(self, key: str, locale: str, domain: str = "reports",
                 context: Optional[Dict[str, Any]] = None,
                 count: Optional[int] = None) -> str:
        """
        获取翻译文本，支持上下文和复数形式
        
        Args:
            key: 翻译键
            locale: 语言代码 (ja, en, zh)
            domain: 翻译域 (reports, metrics, etc.)
            context: 上下文数据用于插值
            count: 数量用于复数形式
        """
        if locale not in self.translations or domain not in self.translations[locale]:
            return key
        
        translations = self.translations[locale][domain]
        
        # 处理复数形式
        if count is not None:
            plural_key = self._get_plural_key(key, count, locale)
            if plural_key in translations:
                text = translations[plural_key]
            else:
                # 回退到单数形式
                text = translations.get(key, key)
        else:
            text = translations.get(key, key)
        
        # 插值处理
        if context:
            text = self._interpolate(text, context)
        
        return text
    
    def _get_plural_key(self, base_key: str, count: int, locale: str) -> str:
        """根据语言规则获取复数键"""
        if locale == "ja":
            # 日语通常不分单复数
            return base_key
        elif locale == "zh":
            # 中文通常不分单复数
            return base_key
        else:
            # 英语和其他语言
            if count == 1:
                return f"{base_key}.singular"
            else:
                return f"{base_key}.plural"
    
    def _interpolate(self, text: str, context: Dict[str, Any]) -> str:
        """插值处理"""
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in text:
                text = text.replace(placeholder, str(value))
        return text
    
    def format_number(self, number: float, locale: str) -> str:
        """格式化数字"""
        if locale == "ja":
            # 日语数字格式: 1,000
            return f"{number:,.0f}".replace(",", "、")
        elif locale == "zh":
            # 中文数字格式: 1,000
            return f"{number:,.0f}"
        else:
            # 英语数字格式: 1,000
            return f"{number:,.0f}"
    
    def format_percentage(self, percentage: float, locale: str) -> str:
        """格式化百分比"""
        if locale == "ja":
            return f"{percentage:.1f}%"
        elif locale == "zh":
            return f"{percentage:.1f}%"
        else:
            return f"{percentage:.1f}%"


# 单例实例
translation_service = TranslationService()