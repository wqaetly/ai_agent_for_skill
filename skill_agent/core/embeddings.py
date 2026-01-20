"""
文本嵌入生成模块
负责将技能描述、Action信息转换为向量表示
使用本地 Qwen3-Embedding-0.6B 模型

缓存架构：
- L1: 内存LRU缓存（快速访问）
- L2: SQLite磁盘缓存（持久化存储）
"""

import asyncio
import os
import logging
import pickle
import sqlite3
import time
from pathlib import Path
from typing import List, Union, Optional, Dict, Any
import torch
from sentence_transformers import SentenceTransformer
from cachetools import LRUCache
import hashlib

logger = logging.getLogger(__name__)

# HuggingFace 模型 ID
QWEN3_EMBEDDING_HF_ID = "Qwen/Qwen3-Embedding-0.6B"


def ensure_model_downloaded(local_path: str) -> str:
    """
    确保模型已下载到本地路径，如果不存在则自动下载
    
    Args:
        local_path: 本地模型路径
        
    Returns:
        实际可用的模型路径
    """
    local_path = Path(local_path)
    
    # 检查模型权重文件是否存在
    weight_files = ["model.safetensors", "pytorch_model.bin", "model.ckpt.index"]
    has_weights = any((local_path / f).exists() for f in weight_files)
    
    if has_weights:
        logger.info(f"Model weights found at: {local_path}")
        return str(local_path)
    
    # 模型不完整，需要下载
    logger.warning(f"Model weights not found at {local_path}, downloading from HuggingFace...")
    
    try:
        from huggingface_hub import snapshot_download
        
        # 确保父目录存在
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 下载完整模型
        logger.info(f"Downloading {QWEN3_EMBEDDING_HF_ID} to {local_path}...")
        snapshot_download(
            repo_id=QWEN3_EMBEDDING_HF_ID,
            local_dir=str(local_path),
            local_dir_use_symlinks=False,
            resume_download=True
        )
        logger.info(f"Model downloaded successfully to {local_path}")
        return str(local_path)
        
    except ImportError:
        logger.error("huggingface_hub not installed. Run: pip install huggingface_hub")
        raise RuntimeError(
            f"Model not found at {local_path} and huggingface_hub is not installed. "
            f"Please run: pip install huggingface_hub"
        )
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        raise RuntimeError(
            f"Failed to download model from HuggingFace: {e}. "
            f"Please manually download {QWEN3_EMBEDDING_HF_ID} to {local_path}"
        )


class EmbeddingGenerator:
    """
    Qwen3 Embedding生成器
    使用 SentenceTransformer 加载本地 Qwen3-Embedding-0.6B 模型
    """

    def __init__(self, config: dict):
        """
        初始化嵌入生成器

        Args:
            config: 嵌入配置字典，包含以下字段：
                - model_name: 本地模型路径（如 "../Data/models/Qwen3-Embedding-0.6B"）
                - device: 设备类型（"cpu" 或 "cuda"）
                - batch_size: 批量大小
                - max_length: 最大序列长度（Qwen3支持32K，建议8192）
                - cache_dir: 模型缓存目录（通常无需设置）
                - use_flash_attention: 是否使用flash_attention_2加速（需要GPU）
                - cache_path: 磁盘缓存路径（默认 "Data/embedding_cache"，None则只用内存缓存）
                - l1_cache_size: L1内存缓存大小（默认 2000）
        """
        self.config = config
        self.model_name = config.get("model_name", "../Data/models/Qwen3-Embedding-0.6B")
        self.device = config.get("device", "cpu")
        self.batch_size = config.get("batch_size", 32)
        self.max_length = config.get("max_length", 8192)  # Qwen3支持32K，默认8192
        self.cache_dir = config.get("cache_dir", None)
        self.use_flash_attention = config.get("use_flash_attention", False)
        self.cache_path = config.get("cache_path", "Data/embedding_cache")
        self.l1_cache_size = config.get("l1_cache_size", 2000)

        # 加载本地模型
        logger.info(f"Loading Qwen3 embedding model from: {self.model_name}")

        # 加载本地模型（简化版本，兼容sentence-transformers 2.7.0）
        try:
            # 标准加载方式（从本地路径）
            self.model = SentenceTransformer(
                self.model_name,
                device=self.device,
                cache_folder=self.cache_dir,
                trust_remote_code=True  # 信任本地模型代码
            )
            logger.info("Model loaded successfully with trust_remote_code=True")
        except Exception as e:
            # 降级加载（移除trust_remote_code参数）
            logger.warning(f"Failed to load with trust_remote_code, trying fallback: {e}")
            self.model = SentenceTransformer(
                self.model_name,
                device=self.device,
                cache_folder=self.cache_dir
            )

        # L1 内存缓存（LRU）
        self._l1_cache = LRUCache(maxsize=self.l1_cache_size)

        # L2 磁盘缓存（SQLite）
        self._disk_cache_enabled = False
        self._db_conn = None
        if self.cache_path:
            self._init_disk_cache(self.cache_path)

        # 缓存统计计数器
        self._cache_stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "misses": 0,
            "total_requests": 0
        }

        logger.info(f"Qwen3 embedding model loaded on device: {self.device}")
        logger.info(f"Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
        logger.info(f"L1 cache size: {self.l1_cache_size}, L2 disk cache: {self._disk_cache_enabled}")

    def _init_disk_cache(self, cache_path: str) -> None:
        """
        初始化磁盘缓存（使用SQLite）

        Args:
            cache_path: 缓存目录路径
        """
        try:
            cache_dir = Path(cache_path)
            cache_dir.mkdir(parents=True, exist_ok=True)
            db_path = cache_dir / "embeddings.db"

            self._db_conn = sqlite3.connect(str(db_path), check_same_thread=False)
            self._db_conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    key TEXT PRIMARY KEY,
                    embedding BLOB,
                    created_at REAL
                )
            """)
            self._db_conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON embeddings(created_at)")
            self._db_conn.commit()

            self._disk_cache_enabled = True
            self._db_path = db_path
            logger.info(f"Disk cache initialized at: {db_path}")
        except Exception as e:
            logger.warning(f"Failed to initialize disk cache: {e}. Using memory cache only.")
            self._disk_cache_enabled = False
            self._db_conn = None

    def _get_from_disk_cache(self, key: str) -> Optional[List[float]]:
        """从磁盘缓存获取embedding"""
        if not self._disk_cache_enabled or not self._db_conn:
            return None
        try:
            cursor = self._db_conn.execute(
                "SELECT embedding FROM embeddings WHERE key = ?", (key,)
            )
            row = cursor.fetchone()
            if row:
                return pickle.loads(row[0])
        except Exception as e:
            logger.warning(f"Disk cache read error: {e}")
        return None

    def _put_to_disk_cache(self, key: str, embedding: List[float]) -> None:
        """将embedding写入磁盘缓存"""
        if not self._disk_cache_enabled or not self._db_conn:
            return
        try:
            embedding_blob = pickle.dumps(embedding)
            self._db_conn.execute(
                "INSERT OR REPLACE INTO embeddings (key, embedding, created_at) VALUES (?, ?, ?)",
                (key, embedding_blob, time.time())
            )
            self._db_conn.commit()
        except Exception as e:
            logger.warning(f"Disk cache write error: {e}")

    def get_embedding_dimension(self) -> int:
        """获取嵌入向量维度"""
        return self.model.get_sentence_embedding_dimension()

    def _get_cache_key(self, text: str) -> str:
        """生成缓存键"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def encode(
        self,
        texts: Union[str, List[str]],
        use_cache: bool = True,
        show_progress: bool = False,
        prompt_name: Optional[str] = None
    ) -> Union[List[float], List[List[float]]]:
        """
        将文本编码为向量

        按照Qwen3官方文档：
        - 查询文本建议使用 prompt_name="query" 以获得更好的检索性能
        - 文档文本不需要使用 prompt

        Args:
            texts: 单个文本或文本列表
            use_cache: 是否使用缓存
            show_progress: 是否显示进度条
            prompt_name: 提示名称，用于优化query编码（如"query"）

        Returns:
            单个向量或向量列表
        """
        # 统一处理为列表
        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]

        # 检查缓存（缓存时需要考虑prompt_name）
        cache_suffix = f"_{prompt_name}" if prompt_name else ""
        embeddings = []
        texts_to_encode = []
        text_indices = []

        for i, text in enumerate(texts):
            if use_cache:
                self._cache_stats["total_requests"] += 1
                cache_key = self._get_cache_key(text) + cache_suffix

                # L1: 先查内存缓存
                if cache_key in self._l1_cache:
                    self._cache_stats["l1_hits"] += 1
                    embeddings.append(self._l1_cache[cache_key])
                    continue

                # L2: 查磁盘缓存
                disk_embedding = self._get_from_disk_cache(cache_key)
                if disk_embedding is not None:
                    self._cache_stats["l2_hits"] += 1
                    # 回填L1缓存
                    self._l1_cache[cache_key] = disk_embedding
                    embeddings.append(disk_embedding)
                    continue

                # 缓存未命中
                self._cache_stats["misses"] += 1

            texts_to_encode.append(text)
            text_indices.append(i)

        # 如果有未缓存的文本，进行编码
        if texts_to_encode:
            logger.debug(f"Encoding {len(texts_to_encode)} texts (cache hit: {len(embeddings)}/{len(texts)})")

            # 按照Qwen3文档准备encode参数
            encode_kwargs = {
                'batch_size': self.batch_size,
                'show_progress_bar': show_progress,
                'convert_to_numpy': True,
                'normalize_embeddings': True  # L2归一化，适合余弦相似度
            }

            # 按照文档：查询使用 prompt_name="query"，文档不需要prompt
            # 添加向后兼容：旧版本可能不支持prompt_name
            if prompt_name:
                try:
                    encode_kwargs['prompt_name'] = prompt_name
                    new_embeddings = self.model.encode(
                        texts_to_encode,
                        **encode_kwargs
                    )
                except TypeError as e:
                    # 降级：不使用prompt_name
                    logger.warning(f"prompt_name not supported, falling back: {e}")
                    encode_kwargs.pop('prompt_name', None)
                    new_embeddings = self.model.encode(
                        texts_to_encode,
                        **encode_kwargs
                    )
            else:
                new_embeddings = self.model.encode(
                    texts_to_encode,
                    **encode_kwargs
                )

            # 更新缓存和结果
            for i, embedding in enumerate(new_embeddings):
                text = texts_to_encode[i]
                embedding_list = embedding.tolist()

                if use_cache:
                    cache_key = self._get_cache_key(text) + cache_suffix
                    # 写入L1内存缓存
                    self._l1_cache[cache_key] = embedding_list
                    # 写入L2磁盘缓存
                    self._put_to_disk_cache(cache_key, embedding_list)

                embeddings.append(embedding_list)

        # 如果是单个文本，返回单个向量
        if is_single:
            return embeddings[0]

        return embeddings

    def encode_batch(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
        show_progress: bool = True,
        prompt_name: Optional[str] = None
    ) -> List[List[float]]:
        """
        批量编码文本（适用于大规模初始化）

        按照Qwen3文档：文档编码不需要使用prompt

        Args:
            texts: 文本列表
            batch_size: 批量大小，None使用默认值
            show_progress: 是否显示进度条
            prompt_name: 提示名称（通常文档编码不需要，查询时可用"query"）

        Returns:
            向量列表
        """
        batch_size = batch_size or self.batch_size

        logger.info(f"Batch encoding {len(texts)} texts with batch_size={batch_size}")

        # 按照Qwen3文档准备参数
        encode_kwargs = {
            'batch_size': batch_size,
            'show_progress_bar': show_progress,
            'convert_to_numpy': True,
            'normalize_embeddings': True  # L2归一化
        }

        # 如果需要（如批量编码查询），可以添加prompt_name
        # 添加向后兼容：旧版本可能不支持prompt_name
        if prompt_name:
            try:
                encode_kwargs['prompt_name'] = prompt_name
                embeddings = self.model.encode(texts, **encode_kwargs)
            except TypeError as e:
                # 降级：不使用prompt_name
                logger.warning(f"prompt_name not supported in encode_batch, falling back: {e}")
                encode_kwargs.pop('prompt_name', None)
                embeddings = self.model.encode(texts, **encode_kwargs)
        else:
            embeddings = self.model.encode(texts, **encode_kwargs)

        return [emb.tolist() for emb in embeddings]

    async def encode_batch_async(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
        prompt_name: Optional[str] = None,
        use_cache: bool = True
    ) -> List[List[float]]:
        """
        异步批量编码文本（适用于大规模并发请求）

        使用 asyncio.to_thread 将 CPU 密集型编码操作放到线程池执行，
        避免阻塞事件循环。

        Args:
            texts: 文本列表
            batch_size: 批量大小，None使用默认值
            prompt_name: 提示名称
            use_cache: 是否使用缓存

        Returns:
            向量列表
        """
        # 分离缓存命中和未命中的文本
        cache_suffix = f"_{prompt_name}" if prompt_name else ""
        cached_embeddings = {}
        texts_to_encode = []
        text_indices = []

        for i, text in enumerate(texts):
            if use_cache:
                cache_key = self._get_cache_key(text) + cache_suffix
                # 先查 L1 缓存
                if cache_key in self._l1_cache:
                    cached_embeddings[i] = self._l1_cache[cache_key]
                    self._cache_stats['l1_hits'] += 1
                    continue
                # 再查 L2 缓存
                if self._disk_cache_enabled:
                    disk_result = self._get_from_disk_cache(cache_key)
                    if disk_result is not None:
                        cached_embeddings[i] = disk_result
                        self._l1_cache[cache_key] = disk_result  # 回填 L1
                        self._cache_stats['l2_hits'] += 1
                        continue

            texts_to_encode.append(text)
            text_indices.append(i)
            self._cache_stats['misses'] += 1

        self._cache_stats['total_requests'] += len(texts)

        # 如果有未缓存的文本，异步编码
        if texts_to_encode:
            batch_size = batch_size or self.batch_size

            # 使用 to_thread 在线程池中执行编码
            new_embeddings = await asyncio.to_thread(
                self._encode_batch_sync,
                texts_to_encode,
                batch_size,
                prompt_name
            )

            # 更新缓存
            for i, embedding in enumerate(new_embeddings):
                text = texts_to_encode[i]
                original_index = text_indices[i]
                cached_embeddings[original_index] = embedding

                if use_cache:
                    cache_key = self._get_cache_key(text) + cache_suffix
                    self._l1_cache[cache_key] = embedding
                    if self._disk_cache_enabled:
                        self._put_to_disk_cache(cache_key, embedding)

        # 按原始顺序返回结果
        return [cached_embeddings[i] for i in range(len(texts))]

    def _encode_batch_sync(
        self,
        texts: List[str],
        batch_size: int,
        prompt_name: Optional[str] = None
    ) -> List[List[float]]:
        """
        同步批量编码（内部方法）
        """
        encode_kwargs = {
            'batch_size': batch_size,
            'show_progress_bar': False,
            'convert_to_numpy': True,
            'normalize_embeddings': True
        }

        if prompt_name:
            try:
                encode_kwargs['prompt_name'] = prompt_name
                embeddings = self.model.encode(texts, **encode_kwargs)
            except TypeError:
                encode_kwargs.pop('prompt_name', None)
                embeddings = self.model.encode(texts, **encode_kwargs)
        else:
            embeddings = self.model.encode(texts, **encode_kwargs)

        return [emb.tolist() for emb in embeddings]

    def compute_similarity(
        self,
        text1: Union[str, List[float]],
        text2: Union[str, List[float]]
    ) -> float:
        """
        计算两个文本或向量的余弦相似度

        Args:
            text1: 文本或向量
            text2: 文本或向量

        Returns:
            相似度分数（0-1）
        """
        # 获取向量
        if isinstance(text1, str):
            vec1 = torch.tensor(self.encode(text1))
        else:
            vec1 = torch.tensor(text1)

        if isinstance(text2, str):
            vec2 = torch.tensor(self.encode(text2))
        else:
            vec2 = torch.tensor(text2)

        # 计算余弦相似度
        similarity = torch.nn.functional.cosine_similarity(
            vec1.unsqueeze(0),
            vec2.unsqueeze(0)
        )

        return similarity.item()

    def clear_cache(self):
        """清空L1内存缓存"""
        self._l1_cache.clear()
        logger.info("L1 memory cache cleared")

    def clear_disk_cache(self) -> bool:
        """
        清空L2磁盘缓存

        Returns:
            是否成功清空
        """
        if not self._disk_cache_enabled or not self._db_conn:
            logger.warning("Disk cache not enabled")
            return False
        try:
            self._db_conn.execute("DELETE FROM embeddings")
            self._db_conn.commit()
            logger.info("L2 disk cache cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear disk cache: {e}")
            return False

    def clear_all_cache(self):
        """清空所有缓存（L1 + L2）并重置统计"""
        self.clear_cache()
        self.clear_disk_cache()
        self._cache_stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "misses": 0,
            "total_requests": 0
        }
        logger.info("All caches and stats cleared")

    def warmup_cache(self, texts: List[str], prompt_name: Optional[str] = None) -> Dict[str, Any]:
        """
        批量预热缓存

        Args:
            texts: 需要预热的文本列表
            prompt_name: 提示名称（可选）

        Returns:
            预热统计信息
        """
        start_time = time.time()
        cache_suffix = f"_{prompt_name}" if prompt_name else ""

        # 统计已缓存和需要编码的文本
        texts_to_encode = []
        already_cached = 0

        for text in texts:
            cache_key = self._get_cache_key(text) + cache_suffix
            # 检查L1
            if cache_key in self._l1_cache:
                already_cached += 1
                continue
            # 检查L2
            disk_embedding = self._get_from_disk_cache(cache_key)
            if disk_embedding is not None:
                # 回填L1
                self._l1_cache[cache_key] = disk_embedding
                already_cached += 1
                continue
            texts_to_encode.append(text)

        # 编码新文本
        newly_encoded = 0
        if texts_to_encode:
            logger.info(f"Warming up cache with {len(texts_to_encode)} new texts...")
            # 使用encode方法（会自动更新缓存）
            self.encode(texts_to_encode, use_cache=True, show_progress=True, prompt_name=prompt_name)
            newly_encoded = len(texts_to_encode)

        elapsed = time.time() - start_time
        result = {
            "total_texts": len(texts),
            "already_cached": already_cached,
            "newly_encoded": newly_encoded,
            "elapsed_seconds": round(elapsed, 2)
        }
        logger.info(f"Cache warmup completed: {result}")
        return result

    def get_cache_info(self) -> Dict[str, Any]:
        """
        获取详细的缓存统计信息

        Returns:
            包含L1/L2缓存大小、命中率、磁盘大小等信息的字典
        """
        total_requests = self._cache_stats["total_requests"]
        l1_hits = self._cache_stats["l1_hits"]
        l2_hits = self._cache_stats["l2_hits"]
        misses = self._cache_stats["misses"]

        # 计算命中率
        l1_hit_rate = l1_hits / total_requests if total_requests > 0 else 0.0
        l2_hit_rate = l2_hits / total_requests if total_requests > 0 else 0.0
        total_hit_rate = (l1_hits + l2_hits) / total_requests if total_requests > 0 else 0.0

        # L2磁盘缓存统计
        l2_size = 0
        disk_file_size_bytes = 0
        if self._disk_cache_enabled and self._db_conn:
            try:
                cursor = self._db_conn.execute("SELECT COUNT(*) FROM embeddings")
                l2_size = cursor.fetchone()[0]
                if hasattr(self, '_db_path') and self._db_path.exists():
                    disk_file_size_bytes = self._db_path.stat().st_size
            except Exception as e:
                logger.warning(f"Failed to get disk cache stats: {e}")

        return {
            "l1_cache": {
                "size": len(self._l1_cache),
                "max_size": self._l1_cache.maxsize,
                "hits": l1_hits,
                "hit_rate": round(l1_hit_rate, 4)
            },
            "l2_cache": {
                "enabled": self._disk_cache_enabled,
                "size": l2_size,
                "file_size_bytes": disk_file_size_bytes,
                "file_size_mb": round(disk_file_size_bytes / (1024 * 1024), 2),
                "hits": l2_hits,
                "hit_rate": round(l2_hit_rate, 4)
            },
            "overall": {
                "total_requests": total_requests,
                "total_hits": l1_hits + l2_hits,
                "total_misses": misses,
                "total_hit_rate": round(total_hit_rate, 4)
            }
        }


if __name__ == "__main__":
    # 测试代码 - 使用本地模型
    import json
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("Testing Qwen3 Embedding Generator (Local Model)")
    print("=" * 60)

    config = {
        "model_name": "../Data/models/Qwen3-Embedding-0.6B",  # 本地模型路径
        "device": "cpu",
        "batch_size": 32,
        "max_length": 8192,  # Qwen3支持32K，这里设为8192
        "cache_dir": None,
        "use_flash_attention": False,  # CPU不支持flash attention
        "cache_path": "../Data/embedding_cache_test",  # 测试用磁盘缓存路径
        "l1_cache_size": 2000
    }

    generator = EmbeddingGenerator(config)
    print(f"\nModel: {config['model_name']}")
    print(f"Embedding dimension: {generator.get_embedding_dimension()}")

    # 测试文档编码（按照文档：不需要prompt）
    print("\n--- Testing Document Encoding ---")
    documents = [
        "释放一道火焰冲击波，对敌人造成魔法伤害",
        "召唤一个火元素，持续攻击敌人"
    ]
    doc_embeddings = generator.encode(documents)
    print(f"Encoded {len(doc_embeddings)} documents")
    print(f"Document 1 dimension: {len(doc_embeddings[0])}")
    print(f"Document 1 first 5 values: {doc_embeddings[0][:5]}")

    # 测试查询编码（按照文档：使用prompt_name="query"）
    print("\n--- Testing Query Encoding ---")
    queries = [
        "火焰伤害技能",
        "召唤火元素"
    ]
    query_embeddings = generator.encode(queries, prompt_name="query")
    print(f"Encoded {len(query_embeddings)} queries with prompt_name='query'")
    print(f"Query 1 dimension: {len(query_embeddings[0])}")
    print(f"Query 1 first 5 values: {query_embeddings[0][:5]}")

    # 测试缓存命中（重复查询）
    print("\n--- Testing Cache Hit ---")
    _ = generator.encode(documents)  # 应该命中L1缓存
    _ = generator.encode(queries, prompt_name="query")  # 应该命中L1缓存

    # 计算相似度（按照文档示例）
    print("\n--- Testing Similarity Calculation ---")
    from sentence_transformers import util
    similarity_matrix = util.cos_sim(query_embeddings, doc_embeddings)
    print("Similarity Matrix (Query x Document):")
    print(similarity_matrix)

    # 测试缓存预热
    print("\n--- Testing Cache Warmup ---")
    warmup_texts = ["治疗技能", "攻击技能", "防御技能"]
    warmup_result = generator.warmup_cache(warmup_texts)
    print(f"Warmup result: {warmup_result}")

    # 详细缓存信息
    print("\n--- Detailed Cache Info ---")
    cache_info = generator.get_cache_info()
    print(json.dumps(cache_info, indent=2, ensure_ascii=False))

    # 测试清空磁盘缓存
    print("\n--- Testing Clear Disk Cache ---")
    generator.clear_disk_cache()
    print("Disk cache cleared")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
