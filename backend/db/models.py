import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, Integer, DateTime, ForeignKey, JSON
from db.database import Base


class Paper(Base):
    __tablename__ = "papers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(Text, nullable=True)
    authors = Column(JSON, default=list)
    source_type = Column(String(10), nullable=False)  # 'pdf', 'url', 'arxiv'
    source_ref = Column(Text, nullable=True)
    file_path = Column(Text, nullable=True)
    status = Column(String(20), default="uploaded")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    paper_id = Column(String, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    knowledge_card = Column(JSON, nullable=True)
    simplified_explanation = Column(JSON, nullable=True)
    related_papers = Column(JSON, nullable=True)
    literature_review = Column(JSON, nullable=True)
    gap_analysis = Column(JSON, nullable=True)
    code_prototype = Column(JSON, nullable=True)
    pipeline_status = Column(JSON, default=dict)
    total_execution_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    paper_id = Column(String, ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    agent_name = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    execution_time = Column(Float, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
