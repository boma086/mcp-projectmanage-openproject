# Multi-Language Support and Internationalization

This document covers the internationalization (i18n) and localization (l10n) features of the OpenProject MCP integration solutions, including support for multiple languages, regions, and cultural adaptations.

## Table of Contents

- [Overview](#overview)
- [Supported Languages](#supported-languages)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Implementation by Solution](#implementation-by-solution)
- [Translation Management](#translation-management)
- [Date and Time Localization](#date-and-time-localization)
- [Number and Currency Formatting](#number-and-currency-formatting)
- [Report Templates and i18n](#report-templates-and-i18n)
- [API Localization](#api-localization)
- [Testing and Validation](#testing-and-validation)
- [Contributing Translations](#contributing-translations)
- [Best Practices](#best-practices)

## Overview

The OpenProject MCP integration provides comprehensive internationalization support to serve users across different regions and languages. The system supports:

- **Multiple Languages**: Full UI and content translation
- **Regional Formatting**: Date, time, number, and currency formats
- **Cultural Adaptation**: Localized report templates and business practices
- **Dynamic Language Switching**: Runtime language changes
- **Fallback System**: Graceful handling of missing translations

### Key Features

- **Translation Coverage**: 100% coverage for user-facing strings
- **RTL Support**: Right-to-left language support
- **Regional Variants**: Support for regional language differences
- **Accessibility**: WCAG-compliant localized interfaces
- **Performance**: Optimized translation loading and caching

## Supported Languages

### Primary Languages

| Language | Code | Region | Coverage | Status |
|----------|------|--------|----------|---------|
| English | `en` | US | 100% | ✅ Complete |
| Japanese | `ja` | JP | 100% | ✅ Complete |
| Chinese (Simplified) | `zh-CN` | CN | 95% | 🔄 In Progress |
| German | `de` | DE | 90% | 🔄 In Progress |
| French | `fr` | FR | 85% | 🔄 In Progress |
| Spanish | `es` | ES | 80% | 🔄 In Progress |
| Portuguese | `pt` | BR | 75% | 🔄 In Progress |
| Russian | `ru` | RU | 70% | 🔄 Planned |

### Regional Variants

| Language | Code | Region | Specific Features |
|----------|------|--------|-------------------|
| English (UK) | `en-GB` | GB | British English, GBP currency |
| Portuguese (PT) | `pt-PT` | PT | European Portuguese |
| Spanish (MX) | `es-MX` | MX | Mexican Spanish, MXN currency |
| French (CA) | `fr-CA` | CA | Canadian French, CAD currency |

## Architecture

### Internationalization Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
├─────────────────────────────────────────────────────────────┤
│  HTTP Solution  │  FastAPI  │  FastMCP  │  TypeScript      │
├─────────────────────────────────────────────────────────────┤
│                   i18n Framework Layer                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Python       │  │   FastAPI      │  │   Node.js   │ │
│  │   gettext      │  │   Babel        │  │   i18next   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                   Translation Storage                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   JSON Files    │  │   YAML Files    │  │   Database  │ │
│  │   .po Files     │  │   .mo Files     │  │   Cache     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                 Translation Management                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Extraction    │  │   Validation    │  │   Sync       │ │
│  │   Tools         │  │   Tools         │  │   Tools      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Translation Flow

1. **String Extraction**: Extract translatable strings from source code
2. **Translation**: Translate strings using professional translators
3. **Validation**: Validate translations for accuracy and completeness
4. **Compilation**: Compile translations into efficient format
5. **Deployment**: Deploy translations with application
6. **Runtime**: Load and use translations at runtime

## Configuration

### Environment Configuration

```bash
# .env file
DEFAULT_LANGUAGE=en
SUPPORTED_LANGUAGES=en,ja,de,fr,es,zh-CN
I18N_DEBUG=false
TRANSLATION_CACHE_ENABLED=true
TRANSLATION_CACHE_TTL=3600
LOCALE_STORAGE_PATH=./locales
```

### Application Configuration

#### Python (HTTP/FastAPI Solution)

```python
# config/i18n.py
from pathlib import Path
import gettext
from typing import Dict, List, Optional

class I18nConfig:
    def __init__(self):
        self.default_language = 'en'
        self.supported_languages = ['en', 'ja', 'de', 'fr', 'es', 'zh-CN']
        self.locale_path = Path(__file__).parent.parent / 'locales'
        self.fallback_language = 'en'
        self.cache_enabled = True
        self.cache_ttl = 3600  # 1 hour

    def get_translation(self, language: str, domain: str = 'messages'):
        """Get translation object for specified language"""
        try:
            return gettext.translation(
                domain,
                localedir=self.locale_path,
                languages=[language]
            )
        except FileNotFoundError:
            # Fallback to default language
            return gettext.translation(
                domain,
                localedir=self.locale_path,
                languages=[self.default_language]
            )

# Initialize i18n
i18n_config = I18nConfig()
```

#### TypeScript Solution

```typescript
// src/i18n/config.ts
export interface I18nConfig {
  defaultLanguage: string;
  supportedLanguages: string[];
  fallbackLanguage: string;
  debug: boolean;
  resources: {
    [language: string]: {
      [namespace: string]: any;
    };
  };
}

export const i18nConfig: I18nConfig = {
  defaultLanguage: 'en',
  supportedLanguages: ['en', 'ja', 'de', 'fr', 'es', 'zh-CN'],
  fallbackLanguage: 'en',
  debug: process.env.NODE_ENV === 'development',
  resources: {
    en: {
      translation: require('./locales/en/translation.json'),
      reports: require('./locales/en/reports.json')
    },
    ja: {
      translation: require('./locales/ja/translation.json'),
      reports: require('./locales/ja/reports.json')
    }
  }
};
```

### Language Detection

```python
# utils/language_detection.py
from flask import request, has_request_context
from typing import Optional

def detect_language() -> str:
    """Detect user's preferred language"""
    if not has_request_context():
        return i18n_config.default_language
    
    # 1. Check URL parameter
    lang = request.args.get('lang')
    if lang and lang in i18n_config.supported_languages:
        return lang
    
    # 2. Check Accept-Language header
    accept_language = request.headers.get('Accept-Language', '')
    if accept_language:
        # Parse Accept-Language header
        languages = []
        for item in accept_language.split(','):
            parts = item.strip().split(';')
            lang_code = parts[0].strip()
            quality = 1.0
            
            if len(parts) > 1 and parts[1].strip().startswith('q='):
                try:
                    quality = float(parts[1].strip()[2:])
                except ValueError:
                    quality = 1.0
            
            languages.append((lang_code, quality))
        
        # Sort by quality and find first supported language
        languages.sort(key=lambda x: x[1], reverse=True)
        for lang_code, _ in languages:
            if lang_code in i18n_config.supported_languages:
                return lang_code
    
    # 3. Fallback to default
    return i18n_config.default_language
```

## Implementation by Solution

### HTTP Solution (Python/Flask)

```python
# app/i18n.py
from flask import Flask, request, g
from babel import Locale
from datetime import datetime
import pytz

def init_i18n(app: Flask):
    """Initialize internationalization for Flask app"""
    
    @app.before_request
    def before_request():
        # Set language
        g.language = detect_language()
        
        # Set locale
        try:
            g.locale = Locale.parse(g.language)
        except:
            g.locale = Locale.parse(i18n_config.default_language)
        
        # Set timezone
        g.timezone = pytz.UTC
    
    @app.context_processor
    def inject_i18n():
        """Inject i18n variables into templates"""
        return {
            'language': g.language,
            'locale': g.locale,
            '_': get_translator(g.language),
            'format_date': format_date,
            'format_number': format_number,
            'format_currency': format_currency
        }

def get_translator(language: str):
    """Get translator function for specified language"""
    translation = i18n_config.get_translation(language)
    translation.install()
    return translation.gettext

def format_date(date: datetime, format_type: str = 'medium') -> str:
    """Format date according to locale"""
    if not date:
        return ''
    
    if hasattr(g, 'locale'):
        return g.locale.format_date(date, format=format_type)
    return date.strftime('%Y-%m-%d')

def format_number(number: float) -> str:
    """Format number according to locale"""
    if hasattr(g, 'locale'):
        return g.locale.format_number(number)
    return str(number)

def format_currency(amount: float, currency: str = 'USD') -> str:
    """Format currency according to locale"""
    if hasattr(g, 'locale'):
        return g.locale.format_currency(amount, currency)
    return f"{amount:.2f} {currency}"
```

### FastAPI Solution

```python
# app/i18n/middleware.py
from fastapi import FastAPI, Request, Response
from fastapi.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import gettext

class I18nMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.translations = {}
        self.load_translations()
    
    def load_translations(self):
        """Load all available translations"""
        for lang in i18n_config.supported_languages:
            try:
                translation = i18n_config.get_translation(lang)
                self.translations[lang] = translation
            except FileNotFoundError:
                continue
    
    async def dispatch(self, request: Request, call_next):
        """Process request with i18n support"""
        # Detect language
        language = self.detect_language(request)
        
        # Add language to request state
        request.state.language = language
        request.state.translation = self.translations.get(language)
        
        # Process request
        response = await call_next(request)
        
        # Add language headers
        response.headers['Content-Language'] = language
        
        return response
    
    def detect_language(self, request: Request) -> str:
        """Detect language from request"""
        # 1. Check query parameter
        lang = request.query_params.get('lang')
        if lang and lang in i18n_config.supported_languages:
            return lang
        
        # 2. Check Accept-Language header
        accept_language = request.headers.get('Accept-Language', '')
        if accept_language:
            # Simple parsing - in production, use proper parsing
            for lang in accept_language.split(','):
                lang_code = lang.split(';')[0].strip()
                if lang_code in i18n_config.supported_languages:
                    return lang_code
        
        # 3. Fallback to default
        return i18n_config.default_language

# Usage in FastAPI app
app = FastAPI(middleware=[Middleware(I18nMiddleware)])

@app.get("/api/projects")
async def get_projects(request: Request):
    """Get projects with localized names"""
    projects = await project_service.get_all()
    
    # Localize project names if available
    for project in projects:
        if request.state.translation:
            project.localized_name = request.state.translation.gettext(
                f"project.{project.id}.name"
            )
    
    return {"projects": projects}
```

### FastMCP Solution

```python
# mcp_i18n.py
from typing import Dict, Any, Optional
import json
from pathlib import Path

class MCPI18nHandler:
    def __init__(self):
        self.translations = {}
        self.load_translations()
    
    def load_translations(self):
        """Load translations for MCP tools"""
        translations_dir = Path(__file__).parent / 'locales'
        
        for lang_dir in translations_dir.iterdir():
            if lang_dir.is_dir():
                lang = lang_dir.name
                self.translations[lang] = {}
                
                # Load tool descriptions
                tools_file = lang_dir / 'tools.json'
                if tools_file.exists():
                    with open(tools_file, 'r', encoding='utf-8') as f:
                        self.translations[lang]['tools'] = json.load(f)
    
    def get_tool_description(self, tool_name: str, language: str) -> str:
        """Get localized tool description"""
        if language in self.translations:
            tools = self.translations[language].get('tools', {})
            return tools.get(tool_name, {}).get('description', '')
        return ''
    
    def get_tool_input_schema(self, tool_name: str, language: str) -> Dict[str, Any]:
        """Get localized tool input schema"""
        if language in self.translations:
            tools = self.translations[language].get('tools', {})
            return tools.get(tool_name, {}).get('input_schema', {})
        return {}

# Example localized tool schema (ja/tools.json)
{
  "get_projects": {
    "description": "プロジェクト一覧を取得します",
    "input_schema": {
      "type": "object",
      "properties": {
        "limit": {
          "type": "integer",
          "description": "取得するプロジェクトの最大数"
        }
      }
    }
  }
}
```

### TypeScript Solution

```typescript
// src/i18n/i18n.ts
import i18n from 'i18next';
import Backend from 'i18next-http-backend';
import LanguageDetector from 'i18next-browser-languagedetector';
import { initReactI18next } from 'react-i18next';

import { i18nConfig } from './config';

export const initializeI18n = () => {
  i18n
    .use(Backend)
    .use(LanguageDetector)
    .use(initReactI18next)
    .init({
      ...i18nConfig,
      interpolation: {
        escapeValue: false, // React already escapes by default
        format: (value, format, lng) => {
          if (format === 'uppercase') return value.toUpperCase();
          if (format === 'lowercase') return value.toLowerCase();
          if (format === 'currency') return formatCurrency(value, lng);
          return value;
        }
      },
      detection: {
        order: ['querystring', 'cookie', 'localStorage', 'navigator', 'htmlTag'],
        caches: ['localStorage', 'cookie']
      }
    });
  
  return i18n;
};

// Custom formatters
const formatCurrency = (value: number, language?: string): string => {
  const locale = language || i18n.language;
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: getCurrencyForLocale(locale)
  }).format(value);
};

const getCurrencyForLocale = (locale: string): string => {
  const currencyMap: Record<string, string> = {
    'en': 'USD',
    'ja': 'JPY',
    'de': 'EUR',
    'fr': 'EUR',
    'es': 'EUR',
    'zh-CN': 'CNY'
  };
  return currencyMap[locale] || 'USD';
};

// React hook for language switching
export const useLanguage = () => {
  const { t, i18n } = useTranslation();
  
  const changeLanguage = (language: string) => {
    i18n.changeLanguage(language);
    // Store preference
    localStorage.setItem('language', language);
  };
  
  return {
    t,
    currentLanguage: i18n.language,
    changeLanguage,
    supportedLanguages: i18nConfig.supportedLanguages
  };
};
```

## Translation Management

### Translation File Structure

```
locales/
├── en/
│   ├── LC_MESSAGES/
│   │   ├── messages.po
│   │   └── messages.mo
│   ├── tools.json
│   ├── reports.json
│   └── validation.json
├── ja/
│   ├── LC_MESSAGES/
│   │   ├── messages.po
│   │   └── messages.mo
│   ├── tools.json
│   ├── reports.json
│   └── validation.json
└── de/
    ├── LC_MESSAGES/
    │   ├── messages.po
    │   └── messages.mo
    ├── tools.json
    ├── reports.json
    └── validation.json
```

### Translation File Examples

#### Python gettext (.po file)

```po
# locales/ja/LC_MESSAGES/messages.po
msgid ""
msgstr ""
"Project-Id-Version: OpenProject MCP\n"
"Report-Msgid-Bugs-To: \n"
"POT-Creation-Date: 2023-01-20 10:30+0000\n"
"PO-Revision-Date: 2023-01-20 11:00+0000\n"
"Last-Translator: Translator Name <translator@example.com>\n"
"Language-Team: Japanese <ja@example.com>\n"
"Language: ja\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"

msgid "Project"
msgstr "プロジェクト"

msgid "Work Package"
msgstr "作業パッケージ"

msgid "Weekly Report"
msgstr "週次報告書"

msgid "Generated on {date}"
msgstr "作成日: {date}"
```

#### JSON Translation

```json
// locales/ja/reports.json
{
  "weekly_report": {
    "title": "週次報告書",
    "subtitle": "{project_name} - {week}",
    "sections": {
      "overview": "概要",
      "progress": "進捗状況",
      "issues": "課題と対策",
      "next_week": "来週の予定"
    },
    "metrics": {
      "completion_rate": "完了率",
      "hours_spent": "投入工数",
      "remaining_work": "残作業"
    }
  },
  "validation": {
    "required": "この項目は必須です",
    "invalid_email": "有効なメールアドレスを入力してください",
    "min_length": "最低{min}文字以上で入力してください"
  }
}
```

### Translation Extraction

#### Python Translation Extraction

```bash
# Extract translatable strings from Python files
pybabel extract -F babel.cfg -o messages.pot .

# Update existing translations
pybabel update -i messages.pot -d locales

# Compile translations
pybabel compile -d locales
```

#### TypeScript Translation Extraction

```json
// package.json
{
  "scripts": {
    "extract": "i18next-scanner --config i18next-scanner.config.js",
    "translate": "npm run extract && node scripts/translate.js"
  }
}
```

```javascript
// i18next-scanner.config.js
module.exports = {
  input: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.test.{js,jsx,ts,tsx}',
    '!src/i18n/**'
  ],
  output: './public/locales',
  options: {
    debug: true,
    sort: true,
    func: {
      list: ['t', 'i18n.t'],
      extensions: ['.js', '.jsx', '.ts', '.tsx']
    },
    lngs: ['en', 'ja', 'de', 'fr', 'es', 'zh-CN'],
    ns: ['translation', 'reports'],
    defaultLng: 'en',
    defaultNs: 'translation',
    resource: {
      loadPath: 'public/locales/{{lng}}/{{ns}}.json',
      savePath: 'public/locales/{{lng}}/{{ns}}.json'
    }
  }
};
```

## Date and Time Localization

### Python Implementation

```python
# utils/date_localization.py
from datetime import datetime, date
from typing import Optional
import pytz
from babel import Locale
from babel.dates import format_date, format_datetime, format_time
from babel.numbers import format_decimal

class DateLocalizer:
    def __init__(self, locale: Locale, timezone: str = 'UTC'):
        self.locale = locale
        self.timezone = pytz.timezone(timezone)
    
    def format_date(self, date_obj: date, format_type: str = 'medium') -> str:
        """Format date according to locale"""
        return format_date(date_obj, format=format_type, locale=self.locale)
    
    def format_datetime(self, datetime_obj: datetime, format_type: str = 'medium') -> str:
        """Format datetime according to locale"""
        if datetime_obj.tzinfo is None:
            datetime_obj = self.timezone.localize(datetime_obj)
        return format_datetime(datetime_obj, format=format_type, locale=self.locale)
    
    def format_relative_time(self, datetime_obj: datetime) -> str:
        """Format relative time (e.g., "2 hours ago")"""
        from babel.dates import format_timedelta
        from datetime import datetime as dt
        
        now = dt.now(pytz.UTC)
        if datetime_obj.tzinfo is None:
            datetime_obj = self.timezone.localize(datetime_obj)
        
        delta = datetime_obj - now
        return format_timedelta(delta, locale=self.locale, add_direction=True)
    
    def get_weekday_names(self) -> list:
        """Get localized weekday names"""
        return [
            self.locale.days['format']['wide'][i] 
            for i in range(7)
        ]
    
    def get_month_names(self) -> list:
        """Get localized month names"""
        return [
            self.locale.months['format']['wide'][i] 
            for i in range(1, 13)
        ]

# Usage
def get_localized_date(date_obj: date, language: str = 'en') -> str:
    """Get localized date string"""
    try:
        locale = Locale.parse(language)
        localizer = DateLocalizer(locale)
        return localizer.format_date(date_obj)
    except:
        return date_obj.strftime('%Y-%m-%d')
```

### TypeScript Implementation

```typescript
// src/utils/dateLocalization.ts
import { format, formatRelative, parseISO } from 'date-fns';
import { en, ja, de, fr, es, zhCN } from 'date-fns/locale';

const dateFnsLocales = {
  en,
  ja,
  de,
  fr,
  es,
  'zh-CN': zhCN
};

export const formatDate = (
  date: Date | string,
  formatStr: string = 'PP',
  language: string = 'en'
): string => {
  const locale = dateFnsLocales[language as keyof typeof dateFnsLocales] || en;
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  
  return format(dateObj, formatStr, { locale });
};

export const formatRelativeTime = (
  date: Date | string,
  language: string = 'en'
): string => {
  const locale = dateFnsLocales[language as keyof typeof dateFnsLocales] || en;
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  
  return formatRelative(dateObj, new Date(), { locale });
};

export const getLocalizedDateFormat = (language: string): string => {
  const formats: Record<string, string> = {
    en: 'MM/dd/yyyy',
    ja: 'yyyy/MM/dd',
    de: 'dd.MM.yyyy',
    fr: 'dd/MM/yyyy',
    es: 'dd/MM/yyyy',
    'zh-CN': 'yyyy年MM月dd日'
  };
  
  return formats[language] || formats.en;
};

// React component for localized date
export const LocalizedDate: React.FC<{
  date: Date | string;
  format?: string;
  className?: string;
}> = ({ date, format = 'PP', className }) => {
  const { currentLanguage } = useLanguage();
  
  const formattedDate = formatDate(date, format, currentLanguage);
  
  return (
    <time className={className} dateTime={typeof date === 'string' ? date : date.toISOString()}>
      {formattedDate}
    </time>
  );
};
```

## Number and Currency Formatting

### Python Implementation

```python
# utils/number_localization.py
from babel import Locale
from babel.numbers import (
    format_decimal, format_currency, format_percent,
    format_scientific, parse_decimal, parse_number
)
from typing import Union

class NumberLocalizer:
    def __init__(self, locale: Locale):
        self.locale = locale
    
    def format_decimal(self, number: Union[int, float], decimal_places: int = 2) -> str:
        """Format decimal number according to locale"""
        return format_decimal(number, format=f'###{decimal_places > 0:."0" * decimal_places}', locale=self.locale)
    
    def format_currency(self, amount: Union[int, float], currency: str = 'USD') -> str:
        """Format currency according to locale"""
        return format_currency(amount, currency, locale=self.locale)
    
    def format_percent(self, number: float, decimal_places: int = 1) -> str:
        """Format percentage according to locale"""
        return format_percent(number / 100, format=f'###{decimal_places > 0:."0" * decimal_places}%', locale=self.locale)
    
    def parse_number(self, number_string: str) -> Union[int, float]:
        """Parse localized number string"""
        return parse_number(number_string, locale=self.locale)
    
    def get_currency_symbol(self, currency: str) -> str:
        """Get currency symbol for locale"""
        return self.locale.currency_symbols.get(currency, currency)
    
    def get_decimal_separator(self) -> str:
        """Get decimal separator for locale"""
        return self.locale.number_symbols.get('decimal', '.')
    
    def get_thousands_separator(self) -> str:
        """Get thousands separator for locale"""
        return self.locale.number_symbols.get('group', ',')

# Usage examples
def format_localized_number(number: float, language: str = 'en') -> str:
    """Format number for specific language"""
    try:
        locale = Locale.parse(language)
        localizer = NumberLocalizer(locale)
        return localizer.format_decimal(number)
    except:
        return str(number)

def format_localized_currency(amount: float, currency: str, language: str = 'en') -> str:
    """Format currency for specific language"""
    try:
        locale = Locale.parse(language)
        localizer = NumberLocalizer(locale)
        return localizer.format_currency(amount, currency)
    except:
        return f"{amount:.2f} {currency}"
```

### TypeScript Implementation

```typescript
// src/utils/numberLocalization.ts
export const formatNumber = (
  number: number,
  language: string = 'en',
  options?: Intl.NumberFormatOptions
): string => {
  return new Intl.NumberFormat(language, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
    ...options
  }).format(number);
};

export const formatCurrency = (
  amount: number,
  currency: string = 'USD',
  language: string = 'en'
): string => {
  return new Intl.NumberFormat(language, {
    style: 'currency',
    currency: currency
  }).format(amount);
};

export const formatPercent = (
  number: number,
  language: string = 'en',
  decimalPlaces: number = 1
): string => {
  return new Intl.NumberFormat(language, {
    style: 'percent',
    minimumFractionDigits: decimalPlaces,
    maximumFractionDigits: decimalPlaces
  }).format(number / 100);
};

export const parseLocalizedNumber = (
  numberString: string,
  language: string = 'en'
): number => {
  // Remove locale-specific formatting
  const cleanString = numberString
    .replace(/[^\d.,-]/g, '')
    .replace(',', '.');
  
  return parseFloat(cleanString);
};

// React component for localized currency
export const LocalizedCurrency: React.FC<{
  amount: number;
  currency?: string;
  className?: string;
}> = ({ amount, currency = 'USD', className }) => {
  const { currentLanguage } = useLanguage();
  
  const formattedAmount = formatCurrency(amount, currency, currentLanguage);
  
  return <span className={className}>{formattedAmount}</span>;
};
```

## Report Templates and i18n

### Japanese Report Template Example

```yaml
# mcp-core/templates/reports/weekly_ja.yaml
name: 週次報告書
description: 日本語の週次プロジェクト報告書テンプレート
language: ja
sections:
  header:
    title: 週次報告書
    fields:
      - name: project_name
        label: プロジェクト名
        required: true
      - name: reporting_period
        label: 報告期間
        format: "{start_date} ～ {end_date}"
      - name: reporter
        label: 報告者
        required: true
  
  overview:
    title: 概要
    fields:
      - name: progress_summary
        label: 進捗概要
        type: textarea
      - name: completion_rate
        label: 完了率
        type: percentage
      - name: key_achievements
        label: 主な成果
        type: list
  
  issues:
    title: 課題と対策
    fields:
      - name: issues_identified
        label: 識別された課題
        type: list
      - name: mitigation_actions
        label: 対策策
        type: list
      - name: risk_level
        label: リスクレベル
        type: select
        options: [低, 中, 高]
  
  next_week:
    title: 来週の予定
    fields:
      - name: planned_activities
        label: 計画活動
        type: list
      - name: milestones
        label: マイルストーン
        type: list
      - name: resource_requirements
        label: 必要リソース
        type: textarea

footer:
  text: |
    この報告書はOpenProject MCPシステムにより自動生成されました。
    Generated on: {date}
```

### Template Localization

```python
# services/localized_template_renderer.py
from typing import Dict, Any, Optional
import yaml
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from babel import Locale

class LocalizedTemplateRenderer:
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self.environments = {}
        self.load_environments()
    
    def load_environments(self):
        """Load Jinja2 environments for each language"""
        for lang_dir in self.templates_dir.iterdir():
            if lang_dir.is_dir():
                language = lang_dir.name
                env = Environment(
                    loader=FileSystemLoader(str(lang_dir)),
                    autoescape=select_autoescape(['html', 'xml'])
                )
                
                # Add custom filters
                env.filters['format_date'] = self.format_date_filter
                env.filters['format_number'] = self.format_number_filter
                env.filters['format_currency'] = self.format_currency_filter
                
                self.environments[language] = env
    
    def render_template(self, template_name: str, language: str, context: Dict[str, Any]) -> str:
        """Render template with localization"""
        if language not in self.environments:
            language = 'en'  # Fallback
        
        env = self.environments[language]
        template = env.get_template(template_name)
        
        # Add locale-specific context
        context['locale'] = Locale.parse(language)
        context['language'] = language
        
        return template.render(**context)
    
    def format_date_filter(self, date_obj, format_type='medium'):
        """Jinja2 filter for date formatting"""
        if not date_obj:
            return ''
        
        # Implementation would use DateLocalizer
        return format_date(date_obj, format=format_type, locale=self.locale)
    
    def format_number_filter(self, number, decimal_places=2):
        """Jinja2 filter for number formatting"""
        return format_decimal(number, format=f'###{decimal_places > 0:."0" * decimal_places}')
    
    def format_currency_filter(self, amount, currency='USD'):
        """Jinja2 filter for currency formatting"""
        return format_currency(amount, currency)

# Usage
template_renderer = LocalizedTemplateRenderer(
    Path(__file__).parent.parent / 'templates' / 'reports'
)

report_html = template_renderer.render_template(
    'weekly.html',
    'ja',
    {
        'project_name': 'ウェブサイトリニューアル',
        'completion_rate': 0.75,
        'date': datetime.now()
    }
)
```

## API Localization

### Localized API Responses

```python
# api/localized_response.py
from fastapi import Response
from typing import Dict, Any, Optional
import json

class LocalizedResponse:
    def __init__(self, content: Dict[str, Any], language: str = 'en'):
        self.content = content
        self.language = language
    
    def to_response(self) -> Response:
        """Convert to FastAPI response with localization headers"""
        response_data = self._localize_content(self.content, self.language)
        
        return Response(
            content=json.dumps(response_data, ensure_ascii=False),
            media_type="application/json",
            headers={
                "Content-Language": self.language,
                "Content-Type": "application/json; charset=utf-8"
            }
        )
    
    def _localize_content(self, content: Any, language: str) -> Any:
        """Recursively localize content"""
        if isinstance(content, dict):
            return {k: self._localize_content(v, language) for k, v in content.items()}
        elif isinstance(content, list):
            return [self._localize_content(item, language) for item in content]
        elif isinstance(content, str):
            return self._translate_string(content, language)
        else:
            return content
    
    def _translate_string(self, text: str, language: str) -> str:
        """Translate string if it's a translation key"""
        if text.startswith('i18n:'):
            key = text[5:]  # Remove 'i18n:' prefix
            translation = self._get_translation(key, language)
            return translation if translation else text
        return text
    
    def _get_translation(self, key: str, language: str) -> Optional[str]:
        """Get translation for key"""
        # Implementation would use translation service
        return None

# Usage in API endpoint
@app.get("/api/projects/{project_id}")
async def get_project(project_id: int, language: str = 'en'):
    project = await project_service.get_by_id(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Localize response
    localized_data = {
        "id": project.id,
        "name": f"i18n:project.{project.id}.name",
        "description": f"i18n:project.{project.id}.description",
        "status": project.status,
        "created_at": project.created_at
    }
    
    return LocalizedResponse(localized_data, language).to_response()
```

### Error Message Localization

```python
# exceptions/localized_exceptions.py
from fastapi import HTTPException
from typing import Dict, Any, Optional

class LocalizedHTTPException(HTTPException):
    def __init__(
        self,
        status_code: int,
        error_key: str,
        language: str = 'en',
        detail_params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.error_key = error_key
        self.language = language
        self.detail_params = detail_params or {}
        
        # Get localized error message
        localized_message = self._get_localized_message(error_key, language, detail_params)
        
        super().__init__(
            status_code=status_code,
            detail=localized_message,
            headers=headers
        )
    
    def _get_localized_message(self, error_key: str, language: str, params: Dict[str, Any]) -> str:
        """Get localized error message"""
        error_messages = {
            'en': {
                'project_not_found': 'Project with ID {project_id} not found',
                'invalid_date_format': 'Invalid date format. Expected: {expected_format}',
                'unauthorized': 'Unauthorized access'
            },
            'ja': {
                'project_not_found': 'ID {project_id} のプロジェクトが見つかりません',
                'invalid_date_format': '無効な日付形式です。期待値: {expected_format}',
                'unauthorized': 'アクセスが認可されていません'
            },
            'de': {
                'project_not_found': 'Projekt mit ID {project_id} nicht gefunden',
                'invalid_date_format': 'Ungültiges Datumsformat. Erwartet: {expected_format}',
                'unauthorized': 'Nicht autorisierter Zugriff'
            }
        }
        
        message_template = error_messages.get(language, {}).get(error_key, error_key)
        
        # Format message with parameters
        try:
            return message_template.format(**params)
        except KeyError:
            return message_template

# Usage
@app.put("/api/projects/{project_id}")
async def update_project(project_id: int, project_data: dict, language: str = 'en'):
    try:
        updated_project = await project_service.update(project_id, project_data)
        return {"message": "Project updated successfully", "project": updated_project}
    except ProjectNotFoundError:
        raise LocalizedHTTPException(
            status_code=404,
            error_key="project_not_found",
            language=language,
            detail_params={"project_id": project_id}
        )
```

## Testing and Validation

### Translation Testing

```python
# tests/test_i18n.py
import pytest
from app.i18n import i18n_config, get_translator

class TestInternationalization:
    @pytest.mark.parametrize("language", ['en', 'ja', 'de'])
    def test_language_detection(self, language):
        """Test language detection functionality"""
        # Test with language parameter
        with app.test_request_context(f'/?lang={language}'):
            detected_lang = detect_language()
            assert detected_lang == language
    
    def test_translation_loading(self):
        """Test translation loading for all supported languages"""
        for language in i18n_config.supported_languages:
            translation = get_translator(language)
            assert translation is not None
    
    def test_fallback_translation(self):
        """Test fallback to default language"""
        # Test with unsupported language
        translation = get_translator('unsupported')
        assert translation is not None
        
        # Should fall back to default language
        default_translation = get_translator(i18n_config.default_language)
        assert translation.gettext('test') == default_translation.gettext('test')
    
    def test_date_localization(self):
        """Test date formatting for different locales"""
        from datetime import date
        from utils.date_localization import get_localized_date
        
        test_date = date(2023, 12, 25)
        
        # Test different languages
        en_date = get_localized_date(test_date, 'en')
        ja_date = get_localized_date(test_date, 'ja')
        
        assert en_date != ja_date  # Should be different formats
        assert '2023' in en_date
        assert '2023' in ja_date
    
    def test_number_localization(self):
        """Test number formatting for different locales"""
        from utils.number_localization import format_localized_number
        
        test_number = 1234.56
        
        en_number = format_localized_number(test_number, 'en')
        de_number = format_localized_number(test_number, 'de')
        
        assert en_number != de_number  # Should be different formats
        assert '1,234.56' in en_number
        assert '1.234,56' in de_number
```

### Translation Coverage Testing

```bash
# Translation coverage test script
#!/bin/bash

# Check translation coverage for each language
for lang in en ja de fr es zh-CN; do
    echo "Checking translation coverage for $lang..."
    
    # Count translatable strings
    total_strings=$(grep -r "i18n\|gettext" src/ | wc -l)
    
    # Count translated strings
    translated_strings=$(find "locales/$lang" -name "*.po" -exec grep -c "msgstr" {} \; | awk '{sum += $1} END {print sum}')
    
    if [ $total_strings -gt 0 ]; then
        coverage=$((translated_strings * 100 / total_strings))
        echo "Language: $lang - Coverage: $coverage%"
        
        if [ $coverage -lt 80 ]; then
            echo "Warning: Low translation coverage for $lang"
        fi
    fi
done
```

## Contributing Translations

### Translation Guidelines

1. **Cultural Adaptation**: Translate meaning, not just words
2. **Consistency**: Use consistent terminology across the application
3. **Context**: Consider the context where the translation will be used
4. **Length**: Keep translations similar in length to avoid UI issues
5. **Formality**: Match the formality level appropriate for the target culture

### Translation Workflow

```bash
# 1. Extract new strings
pybabel extract -F babel.cfg -o messages.pot .

# 2. Create new language files (if needed)
pybabel init -i messages.pot -d locales -l fr

# 3. Update existing translations
pybabel update -i messages.pot -d locales

# 4. Edit translations
# Edit locales/fr/LC_MESSAGES/messages.po

# 5. Compile translations
pybabel compile -d locales

# 6. Validate translations
python scripts/validate_translations.py
```

### Translation Validation Script

```python
# scripts/validate_translations.py
import polib
from pathlib import Path
from typing import List, Dict, Any

class TranslationValidator:
    def __init__(self, locales_dir: Path):
        self.locales_dir = locales_dir
        self.errors = []
    
    def validate_all_translations(self) -> List[Dict[str, Any]]:
        """Validate all translation files"""
        for lang_dir in self.locales_dir.iterdir():
            if lang_dir.is_dir():
                self._validate_language(lang_dir.name)
        
        return self.errors
    
    def _validate_language(self, language: str) -> None:
        """Validate translations for a specific language"""
        po_file = self.locales_dir / language / 'LC_MESSAGES' / 'messages.po'
        
        if not po_file.exists():
            self.errors.append({
                'language': language,
                'type': 'missing_file',
                'message': f'Missing translation file for {language}'
            })
            return
        
        try:
            po = polib.pofile(str(po_file))
            self._validate_po_entries(po, language)
        except Exception as e:
            self.errors.append({
                'language': language,
                'type': 'parse_error',
                'message': f'Error parsing {po_file}: {str(e)}'
            })
    
    def _validate_po_entries(self, po: polib.POFile, language: str) -> None:
        """Validate individual translation entries"""
        for entry in po:
            if not entry.msgid.strip():
                continue  # Skip empty entries
            
            if not entry.msgstr.strip():
                self.errors.append({
                    'language': language,
                    'type': 'missing_translation',
                    'message': f'Missing translation for: {entry.msgid}',
                    'line': entry.linenum
                })
            
            # Check for format string mismatches
            if self._has_format_strings(entry.msgid) and not self._format_strings_match(entry.msgid, entry.msgstr):
                self.errors.append({
                    'language': language,
                    'type': 'format_mismatch',
                    'message': f'Format string mismatch for: {entry.msgid}',
                    'line': entry.linenum
                })
    
    def _has_format_strings(self, text: str) -> bool:
        """Check if text contains format strings"""
        import re
        return bool(re.search(r'\{[^}]+\}', text))
    
    def _format_strings_match(self, msgid: str, msgstr: str) -> bool:
        """Check if format strings match between msgid and msgstr"""
        import re
        msgid_formats = set(re.findall(r'\{([^}]+)\}', msgid))
        msgstr_formats = set(re.findall(r'\{([^}]+)\}', msgstr))
        return msgid_formats == msgstr_formats

# Usage
if __name__ == '__main__':
    validator = TranslationValidator(Path('locales'))
    errors = validator.validate_all_translations()
    
    if errors:
        print(f"Found {len(errors)} translation errors:")
        for error in errors:
            print(f"  [{error['language']}] {error['type']}: {error['message']}")
        exit(1)
    else:
        print("All translations are valid!")
```

## Best Practices

### Performance Optimization

1. **Cache Translations**: Cache loaded translations in memory
2. **Lazy Loading**: Load translations only when needed
3. **Precompile Templates**: Precompile Jinja2 templates for better performance
4. **Minimize Translations**: Only load necessary translation files
5. **Use Efficient Formats**: Use compiled formats (.mo files) for production

### Security Considerations

1. **Sanitize Input**: Always sanitize user-provided language parameters
2. **Validate Language Codes**: Validate language codes against supported list
3. **Prevent Path Traversal**: Ensure language codes don't allow path traversal
4. **Cache Control**: Implement proper cache invalidation for translations

### User Experience

1. **Language Switcher**: Provide easy language switching interface
2. **Persistent Preferences**: Store user's language preference
3. **Fallback Handling**: Gracefully handle missing translations
4. **RTL Support**: Support right-to-left languages properly
5. **Accessibility**: Ensure translated content meets accessibility standards

This comprehensive internationalization system ensures that the OpenProject MCP integration can serve users worldwide with culturally appropriate and properly localized interfaces and content.