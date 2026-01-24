"""
开发者: BackendAgent
当前版本: v1.0
创建时间: 2026年01月14日
描述: 论文总结服务，负责调用 LLM 生成论文摘要
"""

from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from loguru import logger
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from base.pg.entity import Paper, PaperSummary
from base.pg.service import ReaderRepository, PaperRepository
from service.reader.schema import SummaryCreateDTO, SummaryDTO, AISummary
from service.setting.setting_service import SettingService

class SummaryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_llm(self, user_id: UUID) -> ChatOpenAI:
        """根据用户配置获取 LLM 实例"""
        setting_service = SettingService(self.session)
        settings = await setting_service.get_ai_reader_settings(user_id)
        
        # 优先查找 summary 类型的配置
        target_setting = next((s for s in settings if s.type == 'summary'), None)
        # 其次查找 chat 类型的配置
        if not target_setting:
            target_setting = next((s for s in settings if s.type == 'chat'), None)
        # 最后尝试任意配置
        if not target_setting and settings:
             target_setting = settings[0]
             
        if target_setting and target_setting.api_key:
             return ChatOpenAI(
                 model=target_setting.llm_name or "gpt-4o-mini",
                 temperature=0.3,
                 api_key=target_setting.api_key,
                 base_url=target_setting.base_url or None
             )
        
        # 如果没有配置，尝试使用环境变量(保持向后兼容)，或者抛出明确错误
        try:
            return ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未配置 AI 模型参数，请前往设置页面配置 API Key。"
            )

    async def get_ai_summary(self, paper_id: UUID, user_id: UUID) -> Optional[AISummary]:
        summaries = await ReaderRepository.get_summaries_by_paper(self.session, paper_id, user_id)
        
        if not summaries:
            return None
            
        config = {s.summary_type: s.content for s in summaries}
        return AISummary(summary_config=config)

    async def get_summary(self, paper_id: UUID, summary_type: str) -> Optional[SummaryDTO]:
        """获取论文摘要"""
        summary = await ReaderRepository.get_summary_by_type(self.session, paper_id, summary_type)
        
        if summary:
            return SummaryDTO.model_validate(summary)
        return None

    async def get_or_create_summary(self, paper_id: UUID, create_in: SummaryCreateDTO) -> SummaryDTO:
        """获取或生成论文摘要"""
        # 1. 检查是否存在已有摘要
        summary = await ReaderRepository.get_summary_by_type(self.session, paper_id, create_in.summary_type)
        
        if summary:
            return SummaryDTO.model_validate(summary)

        # 2. 获取论文内容
        paper = await PaperRepository.get_paper_by_id(self.session, paper_id)
        
        if not paper:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paper not found"
            )

        # 3. 生成摘要
        content = await self._generate_summary_content(paper, create_in.summary_type)
        
        # 4. 保存摘要
        new_summary = PaperSummary(
            paper_id=paper_id,
            summary_type=create_in.summary_type,
            content=content
        )
        self.session.add(new_summary)
        await self.session.commit()
        await self.session.refresh(new_summary)
        
        return SummaryDTO.model_validate(new_summary)

    # TODO: 这里等Agent实现吧。
    async def _generate_summary_content(self, paper: Paper, summary_type: str) -> str:
        """调用 LLM 生成摘要内容"""
        
        # 准备上下文: 优先使用摘要，如果没有则提示用户无法生成(或者后续扩展读取 chunks)
        context = paper.summary
        if not context:
            # TODO: 如果 summary 为空，尝试读取 paper chunks (需要 PaperChunk 关联查询)
            # 暂时返回占位符或报错
            return "无法生成摘要: 论文缺少摘要信息且未实现全文读取。"

        # 定义 Prompt
        if summary_type == "abstract_rewrite":
            system_prompt = "你是一个专业的学术论文助手。请将以下论文摘要重写为通俗易懂的中文总结，保留核心观点。"
        elif summary_type == "key_points":
            system_prompt = "你是一个专业的学术论文助手。请提取以下论文摘要的3-5个关键创新点，使用Markdown列表格式。"
        elif summary_type == "methodology":
            system_prompt = "你是一个专业的学术论文助手。请专注于分析以下内容中的研究方法和技术路线。"
        else:
            system_prompt = "你是一个专业的学术论文助手。请总结以下内容。"

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "论文标题: {title}\n\n内容:\n{context}")
        ])

        llm = await self._get_llm(paper.user_id)
        chain = prompt | llm
        
        try:
            response = await chain.ainvoke({
                "title": paper.title,
                "context": context
            })
            return response.content
        except Exception as e:
            logger.error(f"摘要生成失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Summary generation failed: {str(e)}"
            )
