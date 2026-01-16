from uuid import UUID
from typing import List, Optional
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select

from base.pg.entity import Note
from service.reader.schema import NoteCreate, NoteUpdate

# TODO: 还是一样的仓储层定义问题。
class NoteService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_notes_by_paper(self, paper_id: UUID, user_id: UUID) -> List[Note]:
        stmt = select(Note).where(Note.paper_id == paper_id, Note.user_id == user_id).order_by(Note.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_note(self, note_id: UUID, user_id: UUID) -> Optional[Note]:
        stmt = select(Note).where(Note.id == note_id, Note.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_note(self, paper_id: UUID, user_id: UUID, note_in: NoteCreate) -> Note:
        note = Note(
            paper_id=paper_id,
            user_id=user_id,
            title=note_in.title,
            content=note_in.content
        )
        self.session.add(note)
        await self.session.commit()
        await self.session.refresh(note)
        return note

    async def update_note(self, note_id: UUID, user_id: UUID, note_in: NoteUpdate) -> Optional[Note]:
        note = await self.get_note(note_id, user_id)
        if not note:
            return None
        
        if note_in.title is not None:
            note.title = note_in.title
        if note_in.content is not None:
            note.content = note_in.content
            
        note.updated_at = datetime.now()
        self.session.add(note)
        await self.session.commit()
        await self.session.refresh(note)
        return note

    async def delete_note(self, note_id: UUID, user_id: UUID) -> bool:
        note = await self.get_note(note_id, user_id)
        if not note:
            return False
        
        await self.session.delete(note)
        await self.session.commit()
        return True
