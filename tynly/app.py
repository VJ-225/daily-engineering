from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets, string
from contextlib import asynccontextmanager
import re
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timedelta,timezone


from database import Link, get_db, get_link_by_code, create_tables, engine


# TYNLy - Day 1: Base62 logic

CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def encode(num):
    if num == 0:
        return CHARS[0]
    result = ""
    while num > 0:
        result = CHARS[num % 62] + result
        num //= 62
    return result

def decode(s):
    num = 0
    for c in s:
        num = num * 62 + CHARS.index(c)
    return num

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    print("TYNLy started - tables ready")
    yield
    await engine.dispose()
    print("TYNLy stopped - engine closed")

app = FastAPI(title="TYNLy",lifespan = lifespan)

def generate_code():
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(6))


@app.get("/")
def home():
    return {"message": "TYNLy Pro is working!!"}

@app.get("/health")
def health():
    return {"ok": True, "service": "tynly-pro"}

# --- NEW: LIST ALL ---
@app.get("/links")
async def list_links(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Link).order_by(Link.created_at.desc()))
    links = result.scalars().all()
    return [
        {
            "short_code": l.short_code,
            "long_url": l.long_url,
            "clicks": l.clicks,
            "created_at": l.created_at,
            "expires_at": l.expires_at
        }
        for l in links
    ]

# --- NEW: TOP 5 ---
@app.get("/top")
async def top_links(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Link).order_by(Link.clicks.desc()).limit(5))
    links = result.scalars().all()
    return [
        {
            "short_code": l.short_code,
            "long_url": l.long_url,
            "clicks": l.clicks,
            "created_at": l.created_at,
            "expires_at": l.expires_at
        }
        for l in links
    ]

@app.get("/stats/{short_code}")
async def get_stats(short_code: str, db: AsyncSession = Depends(get_db)):
    link = await get_link_by_code(db,short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Not found")

    return {
        "short_code" : link.short_code,
        "long_url"   : link.long_url,
        "clicks"     : link.clicks,
        "created_at" : link.created_at,
        "expires_at": link.expires_at
        }

@app.get("/{short_code}")
async def redirect_to_long(short_code: str, db: AsyncSession = Depends(get_db)):
    link = await get_link_by_code (db,short_code)
    
    if not link:
        raise HTTPException(status_code=404, detail="Not found")
    # if link.expires_at is not None and link.expires_at < datetime.now(timezone.utc):
    #     raise HTTPException(status_code=410, detail="Link already expired" )
    if link.expires_at is not None:
        expires = link.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="Link expired")

    link.clicks += 1
    await db.commit()
    return RedirectResponse(url=link.long_url)


# --- NEW: DELETE ---
@app.delete("/{short_code}")
async def delete_link(short_code: str, db: AsyncSession = Depends(get_db)):
    link = await get_link_by_code(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Short code not found")
    await db.delete(link)
    await db.commit()
    return {"message": f"Link {short_code} deleted"}

# Line 1: Define a class named ShortenRequest that inherits from BaseModel
# Line 2: Inside it, first attribute: name long_url, type is string, required - no default
# Line 3: Inside it, second attribute: name custom_code, type is Optional string, default is None - meaning user can skip it

class ShortenRequest(BaseModel):
    long_url : str
    custom_code : Optional[str] =  None
    expires_in_days : Optional[int] = None


@app.post("/shorten")
async def shorten(req: ShortenRequest, db: AsyncSession = Depends(get_db)):
    if not req.custom_code:
        existing = (await db.execute(select(Link).where(Link.long_url == req.long_url))).scalars().first()
        if existing:
            return {
                "short_url": f"http://localhost:8000/{existing.short_code}",
                "long_url": existing.long_url,
                "note": "already existed, returned old link"
            }
    if req.custom_code:
        c_code = req.custom_code.lower().strip()
        if   len(c_code) <3 or len(c_code) > 20 :
            raise HTTPException(status_code = 400, detail ="Custom code must be 3-20 characters")
        elif not re.match(r'^[a-z0-9_-]+$', c_code):
            raise HTTPException(status_code = 400 , detail = "Custom code can only contain a-z, 0-9, - and _")    
        res = (await db.execute(select(Link).where(Link.short_code == c_code ))).scalars().first()        
        if res :
            raise HTTPException(status_code = 409 ,  detail = "custom code already taken" )
    else :
        while True:
            c_code =  generate_code()
            res = (await db.execute(select(Link).where(Link.short_code == c_code ))).scalars().first() 
            if not res :
                break
    expiry = None
    if req.expires_in_days :
        expiry = datetime.now(timezone.utc)+timedelta(days = req.expires_in_days)
    new_link = Link(short_code = c_code, long_url = req.long_url, expires_at = expiry)
    db.add(new_link)
    await db.commit()
    await db.refresh(new_link)   

    return {"short_url": f"http://localhost:8000/{new_link.short_code}", "long_url": new_link.long_url}                 







# 3. secrets.choice(chars)
# Pick 1 random character from chars. 
# Why secrets and not random?random = predictable, uses seed. 
# Hacker can guess next short code.secrets = cryptographically secure, uses OS randomness. 
# Safe for tokens, URLs, passwords.So 1 call = 'a', next call = '9', etc.
# use secrets not random because random is pseudo-random and predictable from seed, 
# which can lead to enumeration attacks on short URLs. 
# secrets uses OS-level entropy from /dev/urandom, making codes cryptographically secure and unpredictable."


# counter = 1000 

# def generate_code():
#     global counter
#     counter += 1
#     return encode(counter)



# def load_db():
#     try:
#         with open('db.json', 'r', encoding='utf-8') as file:
#             data = json.load(file)
#             return data
#     except FileNotFoundError:
#         return {}
#     except json.JSONDecodeError:
#         return {}


# def save_db(urls):
#     with open("db.json", "w") as file:
#         json.dump(urls, file, indent=4)    

# db: AsyncSession — type hint. 
# Tells Python "db will be an AsyncSession". 
# Just for autocomplete, not required but Pro style.Depends(get_db) — Magic. 
# Means:"FastAPI, before running this route, please call get_db() first, get a DB session, and give it to me as db variable. 
# After route finishes, close it

# @app.get("/{short_code}")
# def redirect_to_long(short_code: str):
#     if short_code in urls:
#         return RedirectResponse(url=urls[short_code])
#     return {"error": "Not found"}

# @app.post("/shorten")
# def shorten(long_url: str):
#     existing = [k for k, v in urls.items() if v == long_url]
#     if existing:
#         code = existing[0]
#         return {"short": f"http://127.0.0.1:8000/{code}", "long": long_url, "cached": True}
    
#     code = generate_code()
#     urls[code] = long_url
#     save_db(urls)
#     return {"short": f"http://127.0.0.1:8000/{code}", "long": long_url}

   

# @app.get("/{short_code}")
# async def redirect_to_long(short_code: str, db: AsyncSession = Depends(get_db)):
#     link = await get_link_by_code(db, short_code)
    
#     if not link:  # 1. check first
#         raise HTTPException(status_code=404, detail="Not found")
    
#     link.clicks += 1  # 2. then increment
#     await db.commit() # 3. then save BEFORE return
    
#     return RedirectResponse(url=link.long_url) # 4. then redirect



# @app.post("/shorten")
# async def shorten(long_url: str, db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(Link).where(Link.long_url == long_url))
#     link =  result.scalars().first()
#     if link:
#         return {"short": f"http://127.0.0.1:8000/{link.short_code}", "long": link.long_url}
#     code =  generate_code()
#     new_link =  Link(short_code = code,long_url = long_url)
#     db.add(new_link)
#     await db.commit()
#     return {"short": f"http://127.0.0.1:8000/{code}", "long": long_url}
