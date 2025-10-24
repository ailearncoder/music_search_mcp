"""
HTTP 请求缓存管理模块

功能:
1. 支持 GET 和 POST 请求的缓存
2. GET 请求: URL 匹配即命中
3. POST 请求: URL + Body 匹配才命中
4. 缓存有效期 24 小时
5. 过期后网络失败时返回过时缓存
6. 缓存格式: JSON
"""

import os
import json
import hashlib
import time
from typing import Optional, Dict, Any, Union
from pathlib import Path
import logging

from .logging_config import logger


class RequestCache:
    """HTTP 请求缓存管理器"""

    # 缓存有效期: 24 小时 (秒)
    CACHE_EXPIRY = 24 * 60 * 60

    def __init__(self, cache_dir: Optional[str] = None):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录路径，如果为 None 则从环境变量 CACHE_DIR 读取，
                      如果环境变量也为空则使用 /tmp
        """
        if cache_dir is None:
            cache_dir = os.environ.get('CACHE_DIR', '/tmp')
        
        self.cache_dir = Path(cache_dir) / 'http_cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"缓存目录初始化: {self.cache_dir}")

    def _generate_cache_key(
        self,
        url: str,
        method: str = "GET",
        data: Optional[Union[Dict[str, Any], str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        生成缓存键

        Args:
            url: 请求 URL
            method: 请求方法 (GET/POST)
            data: POST 请求的表单数据
            json_data: POST 请求的 JSON 数据

        Returns:
            缓存键的 MD5 哈希值
        """
        # 基础键: 方法 + URL
        key_parts = [method.upper(), url]

        # POST 请求需要包含请求体
        if method.upper() == "POST":
            if json_data:
                # JSON 数据排序后序列化，确保一致性
                body_str = json.dumps(json_data, sort_keys=True)
                key_parts.append(body_str)
            elif data:
                if isinstance(data, dict):
                    # 字典数据排序后序列化
                    body_str = json.dumps(data, sort_keys=True)
                else:
                    # 字符串数据直接使用
                    body_str = str(data)
                key_parts.append(body_str)

        # 生成 MD5 哈希
        key_string = "|".join(key_parts)
        cache_key = hashlib.md5(key_string.encode('utf-8')).hexdigest()
        
        logger.debug(f"生成缓存键: {cache_key} (来自: {key_string})")
        return cache_key

    def _get_cache_file_path(self, cache_key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{cache_key}.json"

    def get(
        self,
        url: str,
        method: str = "GET",
        data: Optional[Union[Dict[str, Any], str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        cache_expiry: int | None = None
    ) -> Optional[Dict[str, Any]]:
        """
        从缓存中获取响应数据

        Args:
            url: 请求 URL
            method: 请求方法
            data: POST 请求的表单数据
            json_data: POST 请求的 JSON 数据
            cache_expiry: 缓存有效期 (秒)，如果为 None 则使用默认值

        Returns:
            缓存的响应数据，包含:
            - status_code: HTTP 状态码
            - headers: 响应头
            - content: 响应内容
            - text: 响应文本
            - timestamp: 缓存时间戳
            - is_expired: 是否过期
            如果缓存不存在则返回 None
        """
        if cache_expiry is None:
            cache_expiry = self.CACHE_EXPIRY
        cache_key = self._generate_cache_key(url, method, data, json_data)
        cache_file = self._get_cache_file_path(cache_key)

        if not cache_file.exists():
            logger.debug(f"缓存未命中: {url}")
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # 检查缓存是否过期
            current_time = time.time()
            cached_time = cache_data.get('timestamp', 0)
            age = current_time - cached_time
            is_expired = age > cache_expiry

            cache_data['is_expired'] = is_expired

            if is_expired:
                logger.info(f"缓存已过期 ({age/3600:.1f} 小时): {url}")
            else:
                logger.info(f"缓存命中 (剩余 {(cache_expiry - age)/3600:.1f} 小时): {url}")

            return cache_data

        except Exception as e:
            logger.error(f"读取缓存失败: {e}")
            return None

    def set(
        self,
        url: str,
        response_data: Dict[str, Any],
        method: str = "GET",
        data: Optional[Union[Dict[str, Any], str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        将响应数据保存到缓存

        Args:
            url: 请求 URL
            response_data: 响应数据，应包含 status_code, headers, content, text 等
            method: 请求方法
            data: POST 请求的表单数据
            json_data: POST 请求的 JSON 数据

        Returns:
            是否保存成功
        """
        cache_key = self._generate_cache_key(url, method, data, json_data)
        cache_file = self._get_cache_file_path(cache_key)

        try:
            # 添加时间戳
            cache_data = {
                'timestamp': time.time(),
                'url': url,
                'method': method.upper(),
                **response_data,
            }

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            logger.info(f"缓存已保存: {url}")
            return True

        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
            return False

    def clear(self) -> int:
        """
        清除所有缓存文件

        Returns:
            清除的文件数量
        """
        count = 0
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
                count += 1
            logger.info(f"已清除 {count} 个缓存文件")
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")
        
        return count

    def clear_expired(self, cache_expiry: int = CACHE_EXPIRY) -> int:
        """
        清除过期的缓存文件

        Returns:
            清除的文件数量
        """
        count = 0
        current_time = time.time()
        
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    cached_time = cache_data.get('timestamp', 0)
                    if current_time - cached_time > cache_expiry:
                        cache_file.unlink()
                        count += 1
                except Exception:
                    # 如果读取失败，也删除该文件
                    cache_file.unlink()
                    count += 1
            
            logger.info(f"已清除 {count} 个过期缓存文件")
        except Exception as e:
            logger.error(f"清除过期缓存失败: {e}")
        
        return count
