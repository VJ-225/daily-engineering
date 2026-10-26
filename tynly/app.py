from fastapi import FastAPI
from  fastapi.responses import RedirectResponse
import json

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


# # Test
# if __name__ == "__main__":
#     for i in [0, 1, 61, 62, 100, 10000, 999999]:
#         code = encode(i)
#         back = decode(code)
#         print(f"{i} -> {code} -> {back}")



app = FastAPI(title="TYNLy")

# load_db()
# Input: nothing
# Output: dict
# Rule: If db.json exists, read it and return. If not, return {}
def load_db():
    try:
        with open('db.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

# save_db(data)
# Input: data = your urls dict, like {"g9": "https://google.com"}
# Output: nothing, just writes to db.json
# Rule: Use json.dump

def save_db(urls):
    with open("db.json", "w") as file:
        json.dump(urls, file, indent=4)


urls = load_db()
counter = 1000 + len(urls) 

def generate_code():
    global counter
    counter += 1
    return encode(counter)


@app.get("/")
def home():
    return {"message": "TYNLy is working! Day 2"}

@app.get("/{short_code}")
def redirect_to_long(short_code: str):
    if short_code in urls:
        return RedirectResponse(url=urls[short_code])
    return {"error": "Not found"}

@app.post("/shorten")
def shorten(long_url: str):
    existing = [k for k, v in urls.items() if v == long_url]
    if existing:
        code = existing[0]
        return {"short": f"http://127.0.0.1:8000/{code}", "long": long_url, "cached": True}
    
    code = generate_code()
    urls[code] = long_url
    save_db(urls)
    return {"short": f"http://127.0.0.1:8000/{code}", "long": long_url}



    



