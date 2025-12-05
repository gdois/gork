import asyncio

import uvicorn
from scheduler import scheduler
from fastapi import FastAPI

from database import init_agents
from services import set_remembers
from api import webhook_evolution_router


app = FastAPI()
app.include_router(webhook_evolution_router)

@app.on_event("startup")
async def startup_event():
    scheduler.start()


if __name__ == "__main__":
    asyncio.run(init_agents())
    asyncio.run(set_remembers(scheduler))
    uvicorn.run(app, host="0.0.0.0", port=9001)