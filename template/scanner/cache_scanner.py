# -*- coding: utf-8 -*-
"""
缓存扫描器 — 优先从本地文件缓存和 EXE 自身嵌入数据中快速定位目标。

这是最高优先级的扫描策略，命中则零延迟。
"""
import json
import os
from typing import List, Optional

from .base_scanner import BaseScanner


class CacheScanner(BaseScanner):

    def __init__(self, target_exe: str, target_name: str,
                 known_paths: Optional[List[str]] = None) -> None:
        super().__init__(target_exe, target_name)
        self.known_paths: List[str] = known_paths or []

        # 本地缓存路径
        self.cache_dir: str = os.path.join(
            os.environ.get("LOCALAPPDATA", "."), "FakeLauncherCache"
        )
        self.cache_file: str = os.path.join(self.cache_dir, "known_paths.json")
        self._ensure_dir()
        self.cache: dict = self._load_cache()

    def _ensure_dir(self) -> None:
        if not os.path.exists(self.cache_dir):
            try:
                os.makedirs(self.cache_dir)
            except OSError:
                pass

    def _load_cache(self) -> dict:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError, ValueError):
                return {}
        return {}

    def update_cache(self, path: str) -> None:
        """将新发现的路径写入本地缓存。"""
        self.cache[self.target_exe.lower()] = path
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    # ------------------------------------------------------------------ #
    #  主扫描入口
    # ------------------------------------------------------------------ #

    def scan(self) -> Optional[str]:
        """依次检查本地缓存和自身嵌入数据。"""
        result = self._scan_local_cache()
        if result:
            return result
        return self._scan_self_data()

    def _scan_local_cache(self) -> Optional[str]:
        self.log("检查本地缓存记录...")
        path = self.cache.get(self.target_exe.lower())
        if path and os.path.exists(path):
            self.log(f"在缓存中快速定位到: {path}")
            self.found_path = path
            return path
        return None

    def _scan_self_data(self) -> Optional[str]:
        """检查 EXE 自身携带的嵌入数据。"""
        if not self.known_paths:
            return None

        self.log(f"检查自身携带的 {len(self.known_paths)} 条记录...")
        for path in self.known_paths:
            check_path = path
            if not path.lower().endswith(self.target_exe.lower()):
                check_path = os.path.join(path, self.target_exe)

            if os.path.exists(check_path) and os.path.isfile(check_path):
                self.log(f"在自身记录中发现: {check_path}")
                self.found_path = check_path
                return check_path
        return None
