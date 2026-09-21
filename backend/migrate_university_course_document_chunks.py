from app.database.connection import Base, engine
from app.university_ai.models.course_document import CourseDocument
from app.university_ai.models.course_document_chunk import CourseDocumentChunk

Base.metadata.create_all(bind=engine)

print("PHASE 8.9 COURSE DOCUMENT CHUNKS MIGRATION OK")
