"""
开发者: LangGraphAgent
当前版本: v1.0.1
创建时间: 2026-01-14
更新时间: 2026-01-24
更新记录: 
    [2026-01-14:v1.0.0:定义 MindMapAgentState]
    [2026-01-24:v1.0.1:增加 MindMap 结构化定义]
"""

from typing import Optional, List, Dict, Any, TypedDict
from pydantic import BaseModel, Field
from ..base.state import BaseAgentState
from agent.common.schema import BaseRuntimeWithModelConfig

class MindMapNode(BaseModel):
    id: str = Field(..., description="节点唯一标识")
    label: str = Field(..., description="节点显示的文本")
    type: str = Field(default="topic", description="节点类型: root, main, sub")
    
class MindMapEdge(BaseModel):
    source: str = Field(..., description="起始节点ID")
    target: str = Field(..., description="目标节点ID")
    label: Optional[str] = Field(None, description="连线上的文本")

class MindMapStructure(BaseModel):
    nodes: List[MindMapNode] = Field(..., description="节点列表")
    edges: List[MindMapEdge] = Field(..., description="边列表")

class MindMapAgentState(BaseAgentState):
    """
    MindMapAgent (脑图生成助手) 的状态定义。
    """
    
    # 目标论文 ID (输入)
    paper_id: str
    
    # 论文全文内容 (中间状态)
    paper_content: Optional[str]
    
    # 生成的脑图数据 (输出)
    # 使用结构化对象而非字符串
    mindmap_data: Optional[Dict[str, Any]] 
    
    # 脑图层级深度 (配置)
    depth: int = 2

class MindMapAgentRuntimeContext(TypedDict):
    """
    MindMapAgent 的运行时上下文定义。
    """
    llm_config: BaseRuntimeWithModelConfig #模型配置
    paper_id: str # 论文ID
