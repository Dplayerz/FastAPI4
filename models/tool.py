from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class Tool(Base):
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    company = Column(String)
    is_verified = Column(Boolean)
    avatar_url = Column(String)
    status = Column(String)
    role = Column(String)
