from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import Link, get_db,get_link_by_code


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


app = FastAPI(title="TYNLy")

counter = 1000 

def generate_code():
    global counter
    counter += 1
    return encode(counter)


@app.get("/")
def home():
    return {"message": "TYNLy is working! Day 2"}


@app.get("/{short_code}")
async def redirect_to_long(short_code: str, db: AsyncSession = Depends(get_db)):
    link = await get_link_by_code (db,short_code)
    link.clicks+=1
    if link:
        return RedirectResponse(url=link.long_url)
    return {"error": "Not found"}


@app.post("/shorten")
async def shorten(long_url: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Link).where(Link.long_url == long_url))
    link =  result.scalars().first()
    if link:
        return {"short": f"http://127.0.0.1:8000/{link.short_code}", "long": link.long_url}
    code =  generate_code()
    new_link =  Link(short_code = code,long_url = long_url)
    db.add(new_link)
    await db.commit()
    return {"short": f"http://127.0.0.1:8000/{code}", "long": long_url}



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



    



