from dependencies import get_db
from models import YourDataModel
from sqlalchemy.ext.asyncio import AsyncSession

async def store_to_db(data: dict):
    async for db in get_db():
        new_entry = YourDataModel(
            name=data["name"],  # Adapt keys to your payload
            tag_id=data["tag_id"],
            timestamp=data["timestamp"]
        )
        db.add(new_entry)
        await db.commit()