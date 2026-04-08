from typing import List, Optional
import os
import asyncio
import numpy as np
from langchain_core.embeddings import Embeddings
from loguru import logger
from base.config import settings

class LocalOnnxEmbeddings(Embeddings):
    """
    本地ONNX嵌入模型 (BGE-M3) - LangChain 兼容适配器
    """

    def __init__(self, model_path: str, tokenizer_path: Optional[str] = None):
        self.model_path = model_path
        self.tokenizer_path = tokenizer_path or os.path.join(model_path, "tokenizer.json")
        self._tokenizer = None
        self._session = None
        self._dimension = 1024 # BGE-M3 default

        self._load_model()

    def _load_model(self):
        try:
            import onnxruntime as ort
            from tokenizers import Tokenizer

            # 加载Tokenizer
            if os.path.exists(self.tokenizer_path):
                self._tokenizer = Tokenizer.from_file(self.tokenizer_path)
                # 启用截断和填充
                self._tokenizer.enable_truncation(max_length=8192)
                self._tokenizer.enable_padding(pad_id=0, pad_token="[PAD]", length=8192)
            else:
                # 尝试直接加载 tokenizer.json 如果 model_path 是目录
                if os.path.isdir(self.model_path):
                    tokenizer_json = os.path.join(self.model_path, "tokenizer.json")
                    if os.path.exists(tokenizer_json):
                        self._tokenizer = Tokenizer.from_file(tokenizer_json)
                        self._tokenizer.enable_truncation(max_length=8192)
                        self._tokenizer.enable_padding(pad_id=0, pad_token="[PAD]", length=8192)
                    else:
                         logger.error(f"Tokenizer文件未找到: {self.tokenizer_path}")
                         # raise FileNotFoundError(f"Tokenizer not found at {self.tokenizer_path}")
                else:
                    logger.error(f"Tokenizer文件未找到: {self.tokenizer_path}")
                    # raise FileNotFoundError(f"Tokenizer not found at {self.tokenizer_path}")

            # 加载ONNX模型
            model_file = os.path.join(self.model_path, "model.onnx")
            if not os.path.exists(model_file):
                 # 尝试直接使用 model_path 如果它本身就是文件
                 if self.model_path.endswith(".onnx") and os.path.exists(self.model_path):
                     model_file = self.model_path
                 elif os.path.isdir(self.model_path):
                     # 再次尝试查找
                     pass
                 else:
                    logger.error(f"ONNX模型文件未找到: {model_file}")
                    # raise FileNotFoundError(f"ONNX model not found at {model_file}")

            # 使用CPU
            providers = ['CPUExecutionProvider']
            self._session = ort.InferenceSession(model_file, providers=providers)
            
            logger.info(f"本地ONNX模型加载成功: {model_file}")

        except ImportError as e:
            logger.error(f"缺少必要的依赖库: {e}. 请安装 onnxruntime 和 tokenizers")
            raise
        except Exception as e:
            logger.error(f"本地模型加载失败: {e}")
            raise

    def _compute_embedding(self, text: str) -> List[float]:
        if not self._tokenizer or not self._session:
            raise RuntimeError("Model or Tokenizer not initialized")

        # Tokenization
        encoded = self._tokenizer.encode(text)
       
        input_ids = np.array([encoded.ids], dtype=np.int64)
        attention_mask = np.array([encoded.attention_mask], dtype=np.int64)
        
        inputs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask
        }
       
        # Check model inputs
        model_inputs = [x.name for x in self._session.get_inputs()]
        if "token_type_ids" in model_inputs:
             inputs["token_type_ids"] = np.array([encoded.type_ids], dtype=np.int64)

        # Inference
        outputs = self._session.run(None, inputs)
       
        # BGE-M3: use the first output (last_hidden_state), take CLS token (index 0)
        # Ensure normalization
        last_hidden_state = outputs[0] # [batch, seq_len, hidden_size]
        # Check dimensions
        # Usually [1, seq_len, hidden_size] because batch size is 1 here
        
        if len(last_hidden_state.shape) == 3:
             cls_embedding = last_hidden_state[0, 0, :]
        elif len(last_hidden_state.shape) == 2:
             # Some models might return [batch, hidden_size] directly if pooled?
             # Or [seq_len, hidden_size] if batch dimension is squeezed?
             # Assuming standard transformer output [batch, seq, hidden]
             # If shape is [1, 1024], it might be pooled output.
             cls_embedding = last_hidden_state[0, :]
        else:
             # Unexpected shape
             logger.warning(f"Unexpected embedding shape: {last_hidden_state.shape}")
             # Try to flatten or take first
             cls_embedding = last_hidden_state.flatten()[:self._dimension]
       
        # Normalize
        norm = np.linalg.norm(cls_embedding)
        if norm > 0:
            cls_embedding = cls_embedding / norm
           
        return cls_embedding.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入文本 (LangChain Interface)"""
        # 使用信号量限制并发数，防止内存爆炸
        # 考虑到ONNX Runtime在CPU上的内存占用，限制并发数为4
        # 这里使用同步循环或者 asyncio.run 如果在异步环境调用同步方法
        
        # 注意: embed_documents 是同步方法，但我们的计算是 CPU bound
        # 直接串行处理或者使用 ThreadPool
        
        embeddings = []
        for text in texts:
            embeddings.append(self._compute_embedding(text))
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """嵌入单个查询文本 (LangChain Interface)"""
        return self._compute_embedding(text)

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """异步批量嵌入 (Optional)"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.embed_documents, texts)

    async def aembed_query(self, text: str) -> List[float]:
        """异步嵌入查询 (Optional)"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.embed_query, text)
