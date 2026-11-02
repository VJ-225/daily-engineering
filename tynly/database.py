import asyncio
from sqlalchemy import Integer, String, select, text, Text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime 
from sqlalchemy import func, DateTime

DATABASE_URL = "sqlite+aiosqlite:///./tynly.db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass

class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(primary_key=True)
    short_code: Mapped[str] = mapped_column( String(20), unique=True, nullable=False)
    long_url: Mapped[str] = mapped_column(Text,nullable = False)
    clicks: Mapped[int] = mapped_column(Integer, default=0,server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now())
    
    # Why: default is Python-side, server_default is DB-side. Without it, old rows will have NULL clicks.

async def get_db():
    async with async_session_maker() as session:
        yield session

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("tynly.db is created!!")

async def get_link_by_code(db: AsyncSession, short_code: str):
    result = await db.execute(select(Link).where(Link.short_code == short_code))
    return result.scalar_one_or_none()
# Box may have: 1 row, 0 rows, or error if >1 row (but you have unique, so max 1).
# scalar_one_or_none() = open box:If 1 row → give me that Link object
# If 0 rows → give me None (means "not found")If >1 rows → crash (which is good, shows bug)


if __name__ == "__main__":
    asyncio.run(create_tables())

