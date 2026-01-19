"""
增量索引优化模块
支持：文件监听、差量更新、索引版本管理
"""

import os
import json
import hashlib
import logging
import threading
import time
from typing import Dict, List, Any, Optional, Callable, Set
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class FileChangeType(Enum):
    """文件变更类型"""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


@dataclass
class FileChange:
    """文件变更记录"""
    file_path: str
    change_type: FileChangeType
    timestamp: datetime
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None


@dataclass
class IndexVersion:
    """索引版本信息"""
    version: int
    created_at: str
    file_count: int
    total_documents: int
    file_hashes: Dict[str, str] = field(default_factory=dict)


class FileHashTracker:
    """文件哈希追踪器 - 用于检测文件变更"""
    
    def __init__(self, cache_file: Optional[str] = None):
        self.cache_file = cache_file
        self.file_hashes: Dict[str, str] = {}
        self.file_mtimes: Dict[str, float] = {}
        
        if cache_file:
            self._load_cache()
    
    def _load_cache(self):
        """加载缓存"""
        if self.cache_file and os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.file_hashes = data.get('hashes', {})
                    self.file_mtimes = data.get('mtimes', {})
            except Exception as e:
                logger.warning(f"Failed to load hash cache: {e}")
    
    def _save_cache(self):
        """保存缓存"""
        if self.cache_file:
            try:
                cache_dir = os.path.dirname(self.cache_file)
                if cache_dir:
                    os.makedirs(cache_dir, exist_ok=True)
                
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'hashes': self.file_hashes,
                        'mtimes': self.file_mtimes
                    }, f)
            except Exception as e:
                logger.warning(f"Failed to save hash cache: {e}")
    
    def compute_hash(self, file_path: str) -> Optional[str]:
        """计算文件哈希"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return None
    
    def check_file(self, file_path: str) -> Optional[FileChangeType]:
        """
        检查文件是否变更
        
        Returns:
            FileChangeType 或 None（无变更）
        """
        file_path = os.path.abspath(file_path)
        
        if not os.path.exists(file_path):
            if file_path in self.file_hashes:
                return FileChangeType.DELETED
            return None
        
        # 先检查mtime（快速检查）
        try:
            current_mtime = os.path.getmtime(file_path)
        except OSError:
            return None
        
        cached_mtime = self.file_mtimes.get(file_path)
        
        if cached_mtime is not None and current_mtime == cached_mtime:
            return None  # mtime未变，跳过哈希计算
        
        # mtime变了，计算哈希确认
        current_hash = self.compute_hash(file_path)
        if current_hash is None:
            return None
        
        cached_hash = self.file_hashes.get(file_path)
        
        if cached_hash is None:
            return FileChangeType.CREATED
        
        if current_hash != cached_hash:
            return FileChangeType.MODIFIED
        
        # 哈希相同，更新mtime缓存
        self.file_mtimes[file_path] = current_mtime
        return None
    
    def update_file(self, file_path: str):
        """更新文件的哈希记录"""
        file_path = os.path.abspath(file_path)
        
        if os.path.exists(file_path):
            self.file_hashes[file_path] = self.compute_hash(file_path)
            self.file_mtimes[file_path] = os.path.getmtime(file_path)
        else:
            self.file_hashes.pop(file_path, None)
            self.file_mtimes.pop(file_path, None)
        
        self._save_cache()
    
    def remove_file(self, file_path: str):
        """移除文件记录"""
        file_path = os.path.abspath(file_path)
        self.file_hashes.pop(file_path, None)
        self.file_mtimes.pop(file_path, None)
        self._save_cache()
    
    def get_all_tracked_files(self) -> Set[str]:
        """获取所有追踪的文件"""
        return set(self.file_hashes.keys())


class IncrementalIndexer:
    """增量索引器"""
    
    def __init__(
        self,
        watch_directory: str,
        file_pattern: str = "*.json",
        hash_cache_file: Optional[str] = None,
        index_version_file: Optional[str] = None
    ):
        """
        Args:
            watch_directory: 监听目录
            file_pattern: 文件匹配模式
            hash_cache_file: 哈希缓存文件路径
            index_version_file: 索引版本文件路径
        """
        self.watch_directory = Path(watch_directory)
        self.file_pattern = file_pattern
        self.index_version_file = index_version_file
        
        # 文件哈希追踪器
        self.hash_tracker = FileHashTracker(hash_cache_file)
        
        # 索引版本
        self.current_version = self._load_version()
        
        # 变更回调
        self._on_file_created: List[Callable] = []
        self._on_file_modified: List[Callable] = []
        self._on_file_deleted: List[Callable] = []
        
        # 文件监听器
        self._watcher = None
        self._watch_thread = None
        self._stop_watching = threading.Event()
    
    def _load_version(self) -> IndexVersion:
        """加载索引版本"""
        if self.index_version_file and os.path.exists(self.index_version_file):
            try:
                with open(self.index_version_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return IndexVersion(**data)
            except Exception as e:
                logger.warning(f"Failed to load index version: {e}")
        
        return IndexVersion(
            version=0,
            created_at=datetime.now().isoformat(),
            file_count=0,
            total_documents=0
        )
    
    def _save_version(self):
        """保存索引版本"""
        if self.index_version_file:
            try:
                version_dir = os.path.dirname(self.index_version_file)
                if version_dir:
                    os.makedirs(version_dir, exist_ok=True)
                
                with open(self.index_version_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'version': self.current_version.version,
                        'created_at': self.current_version.created_at,
                        'file_count': self.current_version.file_count,
                        'total_documents': self.current_version.total_documents,
                        'file_hashes': self.current_version.file_hashes
                    }, f, indent=2)
            except Exception as e:
                logger.warning(f"Failed to save index version: {e}")
    
    def on_file_created(self, callback: Callable[[str], None]):
        """注册文件创建回调"""
        self._on_file_created.append(callback)
    
    def on_file_modified(self, callback: Callable[[str], None]):
        """注册文件修改回调"""
        self._on_file_modified.append(callback)
    
    def on_file_deleted(self, callback: Callable[[str], None]):
        """注册文件删除回调"""
        self._on_file_deleted.append(callback)
    
    def scan_for_changes(self) -> List[FileChange]:
        """
        扫描目录检测变更
        
        Returns:
            变更列表
        """
        changes = []
        current_files: Set[str] = set()
        
        # 扫描当前文件
        if self.watch_directory.exists():
            for file_path in self.watch_directory.glob(self.file_pattern):
                file_str = str(file_path.absolute())
                current_files.add(file_str)
                
                change_type = self.hash_tracker.check_file(file_str)
                if change_type:
                    changes.append(FileChange(
                        file_path=file_str,
                        change_type=change_type,
                        timestamp=datetime.now(),
                        old_hash=self.hash_tracker.file_hashes.get(file_str),
                        new_hash=self.hash_tracker.compute_hash(file_str)
                    ))
        
        # 检测删除的文件
        tracked_files = self.hash_tracker.get_all_tracked_files()
        for tracked_file in tracked_files:
            if tracked_file not in current_files:
                # 确保是在监听目录下的文件
                if str(self.watch_directory) in tracked_file:
                    changes.append(FileChange(
                        file_path=tracked_file,
                        change_type=FileChangeType.DELETED,
                        timestamp=datetime.now(),
                        old_hash=self.hash_tracker.file_hashes.get(tracked_file)
                    ))
        
        return changes
    
    def apply_changes(
        self,
        changes: List[FileChange],
        update_tracker: bool = True
    ) -> Dict[str, int]:
        """
        应用变更并触发回调
        
        Returns:
            统计信息 {created: n, modified: n, deleted: n}
        """
        stats = {'created': 0, 'modified': 0, 'deleted': 0}
        
        for change in changes:
            try:
                if change.change_type == FileChangeType.CREATED:
                    for callback in self._on_file_created:
                        callback(change.file_path)
                    stats['created'] += 1
                
                elif change.change_type == FileChangeType.MODIFIED:
                    for callback in self._on_file_modified:
                        callback(change.file_path)
                    stats['modified'] += 1
                
                elif change.change_type == FileChangeType.DELETED:
                    for callback in self._on_file_deleted:
                        callback(change.file_path)
                    stats['deleted'] += 1
                
                # 更新哈希追踪器
                if update_tracker:
                    if change.change_type == FileChangeType.DELETED:
                        self.hash_tracker.remove_file(change.file_path)
                    else:
                        self.hash_tracker.update_file(change.file_path)
                        
            except Exception as e:
                logger.error(f"Error applying change for {change.file_path}: {e}")
        
        # 更新版本
        if any(stats.values()):
            self.current_version.version += 1
            self.current_version.file_count = len(self.hash_tracker.file_hashes)
            self._save_version()
        
        return stats
    
    def full_index(self) -> List[str]:
        """
        执行全量索引（返回所有文件路径）
        """
        files = []
        
        if self.watch_directory.exists():
            for file_path in self.watch_directory.glob(self.file_pattern):
                file_str = str(file_path.absolute())
                files.append(file_str)
                self.hash_tracker.update_file(file_str)
        
        # 更新版本
        self.current_version.version += 1
        self.current_version.file_count = len(files)
        self.current_version.created_at = datetime.now().isoformat()
        self._save_version()
        
        return files
    
    def incremental_index(self) -> Dict[str, Any]:
        """
        执行增量索引
        
        Returns:
            {
                'changes': [...],
                'stats': {created: n, modified: n, deleted: n}
            }
        """
        changes = self.scan_for_changes()
        stats = self.apply_changes(changes)
        
        return {
            'changes': changes,
            'stats': stats,
            'version': self.current_version.version
        }
    
    def start_watching(self, poll_interval: float = 5.0):
        """
        启动文件监听（轮询模式）
        
        Args:
            poll_interval: 轮询间隔（秒）
        """
        if self._watch_thread and self._watch_thread.is_alive():
            logger.warning("File watcher already running")
            return
        
        self._stop_watching.clear()
        
        def watch_loop():
            logger.info(f"Started watching {self.watch_directory}")
            while not self._stop_watching.is_set():
                try:
                    result = self.incremental_index()
                    if any(result['stats'].values()):
                        logger.info(f"Detected changes: {result['stats']}")
                except Exception as e:
                    logger.error(f"Error in watch loop: {e}")
                
                self._stop_watching.wait(poll_interval)
            
            logger.info("File watcher stopped")
        
        self._watch_thread = threading.Thread(target=watch_loop, daemon=True)
        self._watch_thread.start()
    
    def start_watching_with_watchdog(self):
        """
        使用watchdog库启动文件监听（事件驱动模式）
        需要安装: pip install watchdog
        """
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler, FileModifiedEvent, \
                FileCreatedEvent, FileDeletedEvent
        except ImportError:
            logger.warning("watchdog not installed, falling back to polling")
            self.start_watching()
            return
        
        class SkillFileHandler(FileSystemEventHandler):
            def __init__(handler_self, indexer):
                handler_self.indexer = indexer
                handler_self._debounce_timers: Dict[str, threading.Timer] = {}
            
            def _debounced_handle(handler_self, file_path: str, change_type: FileChangeType):
                """防抖处理"""
                # 取消之前的定时器
                if file_path in handler_self._debounce_timers:
                    handler_self._debounce_timers[file_path].cancel()
                
                def handle():
                    change = FileChange(
                        file_path=file_path,
                        change_type=change_type,
                        timestamp=datetime.now()
                    )
                    handler_self.indexer.apply_changes([change])
                
                # 设置新的定时器（500ms防抖）
                timer = threading.Timer(0.5, handle)
                handler_self._debounce_timers[file_path] = timer
                timer.start()
            
            def on_created(handler_self, event):
                if not event.is_directory and event.src_path.endswith('.json'):
                    handler_self._debounced_handle(
                        event.src_path, FileChangeType.CREATED
                    )
            
            def on_modified(handler_self, event):
                if not event.is_directory and event.src_path.endswith('.json'):
                    handler_self._debounced_handle(
                        event.src_path, FileChangeType.MODIFIED
                    )
            
            def on_deleted(handler_self, event):
                if not event.is_directory and event.src_path.endswith('.json'):
                    handler_self._debounced_handle(
                        event.src_path, FileChangeType.DELETED
                    )
        
        handler = SkillFileHandler(self)
        self._watcher = Observer()
        self._watcher.schedule(handler, str(self.watch_directory), recursive=False)
        self._watcher.start()
        logger.info(f"Started watchdog observer for {self.watch_directory}")
    
    def stop_watching(self):
        """停止文件监听"""
        self._stop_watching.set()
        
        if self._watcher:
            self._watcher.stop()
            self._watcher.join()
            self._watcher = None
        
        if self._watch_thread:
            self._watch_thread.join(timeout=2.0)
            self._watch_thread = None
    
    def get_status(self) -> Dict[str, Any]:
        """获取索引状态"""
        return {
            'version': self.current_version.version,
            'file_count': self.current_version.file_count,
            'total_documents': self.current_version.total_documents,
            'created_at': self.current_version.created_at,
            'watch_directory': str(self.watch_directory),
            'is_watching': (
                (self._watch_thread and self._watch_thread.is_alive()) or
                (self._watcher and self._watcher.is_alive() if self._watcher else False)
            )
        }
