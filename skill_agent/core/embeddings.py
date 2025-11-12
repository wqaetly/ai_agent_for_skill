"""
文本嵌入生成模块
负责将技能描述、Action信息转换为向量表�?
使用本地 Qwen3-Embedding-0.6B 模型
"""

import os
import logging
from typing import List, Union, Optional
import torch
from sentence_transformers import SentenceTransformer
from cachetools import LRUCache
import hashlib

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Qwen3 Embedding生成�?
    使用 SentenceTransformer 加载本地 Qwen3-Embedding-0.6B 模型
    """

    def __init__(self, config: dict):
        """
        初始化嵌入生成器

        Args:
            config: 嵌入配置字典，包含以下字段：
                - model_name: 本地模型路径（如 "../Data/models/Qwen3-Embedding-0.6B"�?
                - device: 设备类型�?cpu" �?"cuda"�?
                - batch_size: 批量大小
                - max_length: 最大序列长度（Qwen3支持32K，建�?192�?
                - cache_dir: 模型缓存目录（通常无需设置�?
                - use_flash_attention: 是否使用flash_attention_2加速（需要GPU�?
        """
        self.config = config
        self.model_name = config.get("model_name", "../Data/models/Qwen3-Embedding-0.6B")
        self.device = config.get("device", "cpu")
        self.batch_size = config.get("batch_size", 32)
        self.max_length = config.get("max_length", 8192)  # Qwen3支持32K，默�?192
        self.cache_dir = config.get("cache_dir", None)
        self.use_flash_attention = config.get("use_flash_attention", False)

        # 加载本地模型
        logger.info(f"Loading Qwen3 embedding model from: {self.model_name}")

        # 加载本地模型
        if self.use_flash_attention and self.device == "cuda":
            # 使用 flash_attention_2 加速（需要GPU�?
            logger.info("Using flash_attention_2 for acceleration")
            self.model = SentenceTransformer(
                self.model_name,
                model_kwargs={
                    "attn_implementation": "flash_attention_2",
                    "device_map": "auto"
                },
                tokenizer_kwargs={"padding_side": "left"},
                cache_folder=self.cache_dir
            )
        else:
            # 标准加载方式（从本地路径�?
            self.model = SentenceTransformer(
                self.model_name,
                device=self.device,
                cache_folder=self.cache_dir,
                tokenizer_kwargs={"padding_side": "left"},
                trust_remote_code=True  # 信任本地模型代码
            )

        # 内存缓存（LRU，最多缓�?000个embedding�?
        self._cache = LRUCache(maxsize=1000)

        logger.info(f"Qwen3 embedding model loaded on device: {self.device}")
        logger.info(f"Embedding dimension: {self.model.get_sentence_embedding_dimension()}")

    def get_embedding_dimension(self) -> int:
        """获取嵌入向量维度"""
        return self.model.get_sentence_embedding_dimension()

    def _get_cache_key(self, text: str) -> str:
        """生成缓存�?""
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

        按照Qwen3官方文档�?
        - 查询文本建议使用 prompt_name="query" 以获得更好的检索性能
        - 文档文本不需要使�?prompt

        Args:
            texts: 单个文本或文本列�?
            use_cache: 是否使用缓存
            show_progress: 是否显示进度�?
            prompt_name: 提示名称，用于优化query编码（如"query"�?

        Returns:
            单个向量或向量列�?
        """
        # 统一处理为列�?
        is_single = isinstance(texts, str)
        if is_single:
            texts = [texts]

        # 检查缓存（缓存时需要考虑prompt_name�?
        cache_suffix = f"_{prompt_name}" if prompt_name else ""
        embeddings = []
        texts_to_encode = []
        text_indices = []

        for i, text in enumerate(texts):
            if use_cache:
                cache_key = self._get_cache_key(text) + cache_suffix
                if cache_key in self._cache:
                    embeddings.append(self._cache[cache_key])
                    continue

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
                'normalize_embeddings': True  # L2归一化，适合余弦相似�?
            }

            # 按照文档：查询使�?prompt_name="query"，文档不需要prompt
            if prompt_name:
                encode_kwargs['prompt_name'] = prompt_name

            new_embeddings = self.model.encode(
                texts_to_encode,
                **encode_kwargs
            )

            # 更新缓存和结�?
            for i, embedding in enumerate(new_embeddings):
                text = texts_to_encode[i]
                embedding_list = embedding.tolist()

                if use_cache:
                    cache_key = self._get_cache_key(text) + cache_suffix
                    self._cache[cache_key] = embedding_list

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
            batch_size: 批量大小，None使用默认�?
            show_progress: 是否显示进度�?
            prompt_name: 提示名称（通常文档编码不需要，查询时可�?query"�?

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
            'normalize_embeddings': True  # L2归一�?
        }

        # 如果需要（如批量编码查询），可以添加prompt_name
        if prompt_name:
            encode_kwargs['prompt_name'] = prompt_name

        embeddings = self.model.encode(texts, **encode_kwargs)

        return [emb.tolist() for emb in embeddings]

    def compute_similarity(
        self,
        text1: Union[str, List[float]],
        text2: Union[str, List[float]]
    ) -> float:
        """
        计算两个文本或向量的余弦相似�?

        Args:
            text1: 文本或向�?
            text2: 文本或向�?

        Returns:
            相似度分数（0-1�?
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

        # 计算余弦相似�?
        similarity = torch.nn.functional.cosine_similarity(
            vec1.unsqueeze(0),
            vec2.unsqueeze(0)
        )

        return similarity.item()

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("Embedding cache cleared")

    def get_cache_info(self) -> dict:
        """获取缓存信息"""
        return {
            "size": len(self._cache),
            "max_size": self._cache.maxsize,
            "hit_rate": getattr(self._cache, 'hits', 0) / max(getattr(self._cache, 'hits', 0) + getattr(self._cache, 'misses', 0), 1)
        }


if __name__ == "__main__":
    # 测试代码 - 使用本地模型
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("Testing Qwen3 Embedding Generator (Local Model)")
    print("=" * 60)

    config = {
        "model_name": "../Data/models/Qwen3-Embedding-0.6B",  # 本地模型路径
        "device": "cpu",
        "batch_size": 32,
        "max_length": 8192,  # Qwen3支持32K，这里设�?192
        "cache_dir": None,
        "use_flash_attention": False  # CPU不支持flash attention
    }

    generator = EmbeddingGenerator(config)
    print(f"\nModel: {config['model_name']}")
    print(f"Embedding dimension: {generator.get_embedding_dimension()}")

    # 测试文档编码（按照文档：不需要prompt�?
    print("\n--- Testing Document Encoding ---")
    documents = [
        "释放一道火焰冲击波，对敌人造成魔法伤害",
        "召唤一个火元素，持续攻击敌�?
    ]
    doc_embeddings = generator.encode(documents)
    print(f"Encoded {len(doc_embeddings)} documents")
    print(f"Document 1 dimension: {len(doc_embeddings[0])}")
    print(f"Document 1 first 5 values: {doc_embeddings[0][:5]}")

    # 测试查询编码（按照文档：使用prompt_name="query"�?
    print("\n--- Testing Query Encoding ---")
    queries = [
        "火焰伤害技�?,
        "召唤火元�?
    ]
    query_embeddings = generator.encode(queries, prompt_name="query")
    print(f"Encoded {len(query_embeddings)} queries with prompt_name='query'")
    print(f"Query 1 dimension: {len(query_embeddings[0])}")
    print(f"Query 1 first 5 values: {query_embeddings[0][:5]}")

    # 计算相似度（按照文档示例�?
    print("\n--- Testing Similarity Calculation ---")
    from sentence_transformers import util
    similarity_matrix = util.cos_sim(query_embeddings, doc_embeddings)
    print("Similarity Matrix (Query x Document):")
    print(similarity_matrix)

    # 缓存信息
    print("\n--- Cache Info ---")
    print(generator.get_cache_info())

    print("\n" + "=" * 60)
    print("�?All tests passed!")
