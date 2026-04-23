# -*- coding: utf-8 -*-
import os
import json
import logging

logger = logging.getLogger(__name__)

class I18n:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(I18n, cls).__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.current_lang = "zh_CN"
        self.strings = {}
        self.locale_dir = os.path.dirname(os.path.abspath(__file__))
        self.load_lang(self.current_lang)

    def load_lang(self, lang_code: str):
        file_path = os.path.join(self.locale_dir, f"{lang_code}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.strings = json.load(f)
                self.current_lang = lang_code
                logger.info(f"Loaded language: {lang_code}")
            except Exception as e:
                logger.error(f"Failed to load language {lang_code}: {e}")
        else:
            logger.warning(f"Language file not found: {file_path}, falling back to defaults")

    def t(self, key: str, default: str = None) -> str:
        """Translate a key."""
        return self.strings.get(key, default if default is not None else key)

# Global instance shortcut
_i18n_instance = I18n()

def t(key: str, default: str = None) -> str:
    return _i18n_instance.t(key, default)

def set_lang(lang_code: str):
    _i18n_instance.load_lang(lang_code)

def get_current_lang() -> str:
    return _i18n_instance.current_lang
