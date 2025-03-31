import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.link import Link

_executor = ThreadPoolExecutor()

def _update_link_stats(short_code: str):
    db: Session = next(get_db())
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if link:
        link.access_count += 1
        link.last_accessed = datetime.utcnow()
        db.commit()
    db.close()

async def update_link_stats(short_code: str):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_executor, _update_link_stats, short_code)