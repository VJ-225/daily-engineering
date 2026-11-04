LIFESPAN

from contextlib import asynccontextmanager
from database import create_tables

@asynccontextmanager
    async def lifespan(app: FastAPI):
        await create_tables()
        yield

app = FastAPI(title="TYNLy", lifespan=lifespan)1. What is lifespan? 
Think of your app like a shop.
Opening the shop = when you run uvicorn app:appShop is open = server is running, handling requestsClosing the shop = when you press Ctrl + Clifespan is the code that runs at opening and closing.
Without it, FastAPI doesn't know what to do when shop opens.

2. asynccontextmanager
This is Python's way of saying:
"This function has 2 parts — before yield and after yield"pythonasync def lifespan(app):
    await create_tables()  # BEFORE yield = on startup
    yield                  # <-- PAUSE HERE, app is now running
    # AFTER yield = on shutdown (we have nothing here, so empty)yield is like a pause button.
Code before yield runs once when server startsThen it pauses, server handles all your /shorten, /health requestsCode after yield would run when server stopsRight now we have nothing after yield, so shutdown does nothing. That's fine.

3. await create_tables()
This is from your database.py:pythonasync def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)What it does:
Checks if tynly.db file exists, if not creates itChecks if links table exists, if not creates it with columns id, short_code, long_url, clicks, created_atIf table already exists, does nothing — safe to run every timeWhy await? Because create_tables is async — it's talking to DB, which takes time. await means "wait for DB to finish creating table before starting server".
Without await, server would start before table is ready, and first /shorten would fail with no such table.

4. app = FastAPI(..., lifespan=lifespan)
You are telling FastAPI:
"Hey, when you start, run my lifespan function first."Old way was @app.on_event("startup") — FastAPI removed that, now lifespan is the official way.

Full Flow When You Run Server:javascript1. You run: uvicorn app:app --reload
2. FastAPI sees lifespan=lifespan
3. Runs: await create_tables() -> creates tynly.db + links table
4. Hits yield -> pauses
5. Server starts, prints "tynly.db is created!!"
6. You hit /shorten -> works because table already exists
7. You press Ctrl+C -> code after yield runs (nothing) -> server stopsBefore this fix: You had to manually run python database.py every time. 
If you forgot, app crashed.

After this fix: Table auto-creates every time you start server. That's how real production apps work.