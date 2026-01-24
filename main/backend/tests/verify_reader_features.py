import sys
import os
import asyncio
from uuid import uuid4
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from base.config import settings
from base.pg.entity import User, Paper, Note, Annotation, Job
from base.pg.service import ReaderRepository, PaperRepository, UserRepository
from service.reader.note_service import NoteService
from service.reader.reader_service import ReaderService
from service.reader.schema import NoteCreateDTO, NoteUpdateDTO, AnnotationRequest

async def main():
    # Setup DB
    database_url = settings.database_url
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(database_url, echo=False)
    AsyncSessionFactory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionFactory() as session:
        print("Starting verification...")
        
        # 1. Create User
        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"test_reader_{user_id}@example.com",
            hashed_password="test",
            full_name="Test Reader User"
        )
        session.add(user)
        await session.commit()
        print(f"Created User: {user_id}")
        
        # 2. Create Paper
        paper_id = uuid4()
        paper = Paper(
            id=paper_id,
            user_id=user_id,
            title="Test Paper",
            file_key="test/paper.pdf",
            analysis_status="completed"
        )
        session.add(paper)
        await session.commit()
        print(f"Created Paper: {paper_id}")
        
        try:
            # 3. Test Note Service
            note_service = NoteService(session)
            
            # Create Note
            note_in = NoteCreateDTO(title="Test Note", content="This is a test note.")
            note = await note_service.create_note(paper_id, user_id, note_in)
            print(f"Created Note: {note.id}")
            assert note.title == "Test Note"
            assert note.content == "This is a test note."
            
            # Get Notes
            notes = await note_service.get_notes_by_paper(paper_id, user_id)
            print(f"Got {len(notes)} notes")
            assert len(notes) >= 1
            
            # Update Note
            update_in = NoteUpdateDTO(content="Updated content")
            updated_note = await note_service.update_note(note.id, user_id, update_in)
            print(f"Updated Note: {updated_note.id}")
            assert updated_note.content == "Updated content"
            
            # Delete Note
            deleted = await note_service.delete_note(note.id, user_id)
            print(f"Deleted Note: {deleted}")
            assert deleted is True
            
            # Verify deletion
            remaining = await note_service.get_notes_by_paper(paper_id, user_id)
            print(f"Remaining notes: {len(remaining)}")
            assert len(remaining) == 0
            
            print("Note Service Verified!")
            
            # 4. Test Annotation (ReaderService)
            reader_service = ReaderService(session)
            
            # Add Annotation
            ann_req = AnnotationRequest(
                type="highlight",
                rects=[{"x": 10.0, "y": 10.0, "width": 100.0, "height": 20.0, "pageIndex": 1.0}],
                content="Test highlight",
                color="#FFFF00"
            )
            # reader_service.add_annotation returns None, it just adds
            await reader_service.add_annotation(paper_id, ann_req, user_id)
            print("Added Annotation")
            
            # Get Annotations
            anns = await reader_service.get_annotations(paper_id, user_id)
            print(f"Got {len(anns)} annotations")
            assert len(anns) >= 1
            ann = anns[0]
            print(f"Annotation ID: {ann.id}")
            
            # Update Annotation
            update_req = AnnotationRequest(
                type="highlight",
                rects=[{"x": 10.0, "y": 10.0, "width": 100.0, "height": 20.0, "pageIndex": 1.0}],
                content="Updated highlight",
                color="#FF0000"
            )
            # reader_service.update_annotation(paper_id, annotation_id, req, user_id)
            # The schema has annotation_id aliased as id. 
            # ann.id is UUID.
            await reader_service.update_annotation(paper_id, ann.id, update_req, user_id)
            print("Updated Annotation")
            
            # Verify Update
            anns_after = await reader_service.get_annotations(paper_id, user_id)
            assert anns_after[0].content == "Updated highlight"
            assert anns_after[0].color == "#FF0000"
            
            # Delete Annotation
            await reader_service.delete_annotation(paper_id, ann.id, user_id)
            print("Deleted Annotation")
            
            # Verify Deletion
            anns_final = await reader_service.get_annotations(paper_id, user_id)
            assert len(anns_final) == 0
            
            print("Annotation Service Verified!")
            
        except Exception as e:
            print(f"Verification Failed: {e}")
            import traceback
            traceback.print_exc()
            raise
        finally:
            # Clean up
            print("Cleaning up...")
            await PaperRepository.delete_paper(session, paper_id)
            # User delete? No direct repo method, do manual
            await session.delete(user)
            await session.commit()
            print("Cleanup done.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
