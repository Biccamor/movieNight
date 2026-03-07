from fastapi import FastAPI
from routers.recommendation import recommendation

app = FastAPI()
app.add_route(recommendation)

@app.get("/")
async def main():
    return "Server dziala"