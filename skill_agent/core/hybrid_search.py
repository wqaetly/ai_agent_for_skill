"""
混合检索模块 (Hybrid Search)
结合BM25关键词检索和向量语义检索，使用RRF融合排序
"""

import math
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import re
import json

logger = logging.getLogger(__name__)


class BM25Index:
    """BM25关键词检索索引"""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Args:
            k1: 词频饱和参数 (1.2-2.0)
            b: 文档长度归一化参数 (0-1)
        """
        self.k1 = k1
        self.b = b
        
        # 索引数据
        self.documents: Dict[str, str] = {}  # doc_id -> document text
        self.doc_lengths: Dict[str, int] = {}  # doc_id -> token count
        self.avg_doc_length: float = 0.0
        self.doc_count: int = 0
        
        # 倒排索引: term -> {doc_id: term_frequency}
        self.inverted_index: Dict[str, Dict[str, int]] = defaultdict(dict)
        
        # IDF缓存
        self.idf_cache: Dict[str, float] = {}
        
        # 中文分词器（简单实现，可替换为jieba）
        self._tokenizer = None
    
    def _tokenize(self, text: str) -> List[str]:
        """分词（支持中英文混合）"""
        if not text:
            return []
        
        tokens = []
        
        # 中文字符单独切分
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
        english_pattern = re.compile(r'[a-zA-Z0-9]+')
        
        # 提取中文词（按字切分，简单实现）
        for match in chinese_pattern.finditer(text):
            chinese_text = match.group()
            # 按2-gram切分中文
            for i in range(len(chinese_text)):
                tokens.append(chinese_text[i])
                if i < len(chinese_text) - 1:
                    tokens.append(chinese_text[i:i+2])
        
        # 提取英文词
        for match in english_pattern.finditer(text.lower()):
            tokens.append(match.group())
        
        return tokens
    
    def add_documents(
        self,
        documents: List[str],
        doc_ids: List[str],
        metadatas: Optional[List[Dict]] = None
    ):
        """
        添加文档到索引
        
        Args:
            documents: 文档文本列表
            doc_ids: 文档ID列表
            metadatas: 元数据列表（可选，用于存储额外信息）
        """
        for i, (doc_id, doc_text) in enumerate(zip(doc_ids, documents)):
            # 分词
            tokens = self._tokenize(doc_text)
            
            # 存储文档
            self.documents[doc_id] = doc_text
            self.doc_lengths[doc_id] = len(tokens)
            
            # 构建倒排索引
            term_freq = defaultdict(int)
            for token in tokens:
                term_freq[token] += 1
            
            for term, freq in term_freq.items():
                self.inverted_index[term][doc_id] = freq
        
        # 更新统计信息
        self.doc_count = len(self.documents)
        if self.doc_count > 0:
            self.avg_doc_length = sum(self.doc_lengths.values()) / self.doc_count
        
        # 清空IDF缓存
        self.idf_cache.clear()
        
        logger.info(f"BM25 indexed {len(documents)} documents, vocabulary size: {len(self.inverted_index)}")
    
    def _compute_idf(self, term: str) -> float:
        """计算IDF值"""
        if term in self.idf_cache:
            return self.idf_cache[term]
        
        doc_freq = len(self.inverted_index.get(term, {}))
        if doc_freq == 0:
            idf = 0.0
        else:
            # BM25 IDF公式
            idf = math.log((self.doc_count - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
        
        self.idf_cache[term] = idf
        return idf
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        doc_ids_filter: Optional[List[str]] = None
    ) -> List[Tuple[str, float]]:
        """
        BM25检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            doc_ids_filter: 限制搜索范围的文档ID列表
        
        Returns:
            [(doc_id, score), ...] 按分数降序排列
        """
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
        
        scores: Dict[str, float] = defaultdict(float)
        
        for term in query_tokens:
            if term not in self.inverted_index:
                continue
            
            idf = self._compute_idf(term)
            
            for doc_id, tf in self.inverted_index[term].items():
                # 如果有过滤条件，跳过不在范围内的文档
                if doc_ids_filter and doc_id not in doc_ids_filter:
                    continue
                
                doc_len = self.doc_lengths[doc_id]
                
                # BM25评分公式
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_length)
                scores[doc_id] += idf * numerator / denominator
        
        # 排序并返回top_k
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]
    
    def clear(self):
        """清空索引"""
        self.documents.clear()
        self.doc_lengths.clear()
        self.inverted_index.clear()
        self.idf_cache.clear()
        self.doc_count = 0
        self.avg_doc_length = 0.0
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        return {
            "doc_count": self.doc_count,
            "vocabulary_size": len(self.inverted_index),
            "avg_doc_length": round(self.avg_doc_length, 2),
            "k1": self.k1,
            "b": self.b
        }


class HybridSearchEngine:
    """混合检索引擎 - 融合BM25和向量检索"""
    
    def __init__(
        self,
        vector_store,
        embedding_generator,
        bm25_weight: float = 0.3,
        vector_weight: float = 0.7,
        rrf_k: int = 60
    ):
        """
        Args:
            vector_store: 向量存储实例
            embedding_generator: 嵌入生成器实例
            bm25_weight: BM25权重 (用于加权融合)
            vector_weight: 向量检索权重 (用于加权融合)
            rrf_k: RRF融合参数 (通常60)
        """
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.rrf_k = rrf_k
        
        # BM25索引
        self.bm25_index = BM25Index()
        
        # 文档元数据缓存
        self._metadata_cache: Dict[str, Dict] = {}
    
    def index_documents(
        self,
        documents: List[str],
        doc_ids: List[str],
        metadatas: List[Dict[str, Any]],
        embeddings: Optional[List[List[float]]] = None
    ) -> bool:
        """
        索引文档到混合检索引擎
        
        Args:
            documents: 文档文本列表
            doc_ids: 文档ID列表
            metadatas: 元数据列表
            embeddings: 预计算的嵌入向量（可选）
        
        Returns:
            是否成功
        """
        try:
            # 1. 索引到BM25
            self.bm25_index.add_documents(documents, doc_ids, metadatas)
            
            # 2. 缓存元数据
            for doc_id, metadata in zip(doc_ids, metadatas):
                self._metadata_cache[doc_id] = metadata
            
            # 3. 索引到向量存储（如果没有预计算嵌入）
            if embeddings is None:
                embeddings = self.embedding_generator.encode_batch(documents)
            
            success = self.vector_store.add_documents(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=doc_ids
            )
            
            logger.info(f"Hybrid search indexed {len(documents)} documents")
            return success
            
        except Exception as e:
            logger.error(f"Error indexing documents: {e}")
            return False
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        fusion_method: str = "rrf",
        filters: Optional[Dict[str, Any]] = None,
        return_scores: bool = False
    ) -> List[Dict[str, Any]]:
        """
        混合检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            fusion_method: 融合方法 ("rrf" 或 "weighted")
            filters: 元数据过滤条件
            return_scores: 是否返回详细分数
        
        Returns:
            检索结果列表
        """
        # 获取更多候选以便融合
        candidate_k = min(top_k * 3, 100)
        
        # 1. BM25检索
        bm25_results = self.bm25_index.search(query, top_k=candidate_k)
        
        # 2. 向量检索
        query_embedding = self.embedding_generator.encode(query, prompt_name="query")
        vector_results = self.vector_store.query(
            query_embeddings=[query_embedding],
            top_k=candidate_k,
            where=filters
        )
        
        # 解析向量检索结果
        vector_scores: Dict[str, float] = {}
        if vector_results and vector_results['ids'] and vector_results['ids'][0]:
            for i, doc_id in enumerate(vector_results['ids'][0]):
                distance = vector_results['distances'][0][i]
                # 转换距离为相似度
                similarity = 1.0 - distance
                vector_scores[doc_id] = similarity
        
        # 3. 融合排序
        if fusion_method == "rrf":
            fused_results = self._rrf_fusion(bm25_results, vector_scores, top_k)
        else:
            fused_results = self._weighted_fusion(bm25_results, vector_scores, top_k)
        
        # 4. 构建返回结果
        results = []
        for doc_id, fused_score in fused_results:
            result = {
                "doc_id": doc_id,
                "fused_score": round(fused_score, 4)
            }
            
            # 添加元数据
            if doc_id in self._metadata_cache:
                result["metadata"] = self._metadata_cache[doc_id]
            
            # 添加文档内容
            if doc_id in self.bm25_index.documents:
                result["document"] = self.bm25_index.documents[doc_id]
            
            # 添加详细分数
            if return_scores:
                bm25_score = dict(bm25_results).get(doc_id, 0.0)
                vector_score = vector_scores.get(doc_id, 0.0)
                result["bm25_score"] = round(bm25_score, 4)
                result["vector_score"] = round(vector_score, 4)
            
            results.append(result)
        
        return results
    
    def _rrf_fusion(
        self,
        bm25_results: List[Tuple[str, float]],
        vector_scores: Dict[str, float],
        top_k: int
    ) -> List[Tuple[str, float]]:
        """
        Reciprocal Rank Fusion (RRF) 融合
        
        RRF公式: score = sum(1 / (k + rank_i))
        """
        rrf_scores: Dict[str, float] = defaultdict(float)
        
        # BM25排名贡献
        for rank, (doc_id, _) in enumerate(bm25_results):
            rrf_scores[doc_id] += 1.0 / (self.rrf_k + rank + 1)
        
        # 向量检索排名贡献
        sorted_vector = sorted(vector_scores.items(), key=lambda x: x[1], reverse=True)
        for rank, (doc_id, _) in enumerate(sorted_vector):
            rrf_scores[doc_id] += 1.0 / (self.rrf_k + rank + 1)
        
        # 排序返回
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]
    
    def _weighted_fusion(
        self,
        bm25_results: List[Tuple[str, float]],
        vector_scores: Dict[str, float],
        top_k: int
    ) -> List[Tuple[str, float]]:
        """加权融合"""
        # 归一化BM25分数
        bm25_dict = dict(bm25_results)
        max_bm25 = max(bm25_dict.values()) if bm25_dict else 1.0
        
        # 归一化向量分数
        max_vector = max(vector_scores.values()) if vector_scores else 1.0
        
        # 融合
        all_doc_ids = set(bm25_dict.keys()) | set(vector_scores.keys())
        fused_scores: Dict[str, float] = {}
        
        for doc_id in all_doc_ids:
            bm25_norm = bm25_dict.get(doc_id, 0.0) / max_bm25 if max_bm25 > 0 else 0
            vector_norm = vector_scores.get(doc_id, 0.0) / max_vector if max_vector > 0 else 0
            
            fused_scores[doc_id] = (
                self.bm25_weight * bm25_norm + 
                self.vector_weight * vector_norm
            )
        
        sorted_results = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]
    
    def clear(self):
        """清空索引"""
        self.bm25_index.clear()
        self._metadata_cache.clear()
        self.vector_store.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "bm25": self.bm25_index.get_statistics(),
            "vector_store": self.vector_store.get_statistics(),
            "fusion_config": {
                "bm25_weight": self.bm25_weight,
                "vector_weight": self.vector_weight,
                "rrf_k": self.rrf_k
            }
        }
