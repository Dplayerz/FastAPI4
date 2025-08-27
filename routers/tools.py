from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models.tool import Tool

router = APIRouter(prefix="/tools", tags=["tools"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def get_tools(db: Session = Depends(get_db)):
    tools = db.query(Tool).all()
    return [
        {
            "id": str(tool.id),
            "name": tool.name,
            "company": tool.company,
            "isVerified": tool.is_verified,
            "avatarUrl": tool.avatar_url,
            "status": tool.status,
            "role": tool.role,
        }
        for tool in tools
    ]
