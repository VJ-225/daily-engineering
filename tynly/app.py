from fastapi import FastAPI

from short import generate_code

app = FastAPI(title="TYNLy")

urls = {}

@app.get("/")
def home():
    return {"message": "TYNLy is working! Day 2"}

@app.get("/{short_code}")
def redirect(short_code: str):
    if short_code in urls:
        return {"url": urls[short_code]}
    return {"error": "Not found"}

@app.post("/shorten")
def shorten(long_url: str):
    code = generate_code()
    urls[code] = long_url
    return {"short": f"http://127.0.0.1:8000/{code}", "long": long_url}



