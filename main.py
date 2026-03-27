from typing import Annotated
from contextlib import asynccontextmanager

from fastapi import FastAPI
from database import Base, engine


# Lifespan is a modern way in fastapi to handle startup and shutdown events. replaces older decoreator on_startup, on_shutdown
@asynccontextmanager
async def lifespan(_app: FastAPI):
    '''this function is only for creating databse tables'''
    # Startup
    async with engine.begin() as conn:  # engine.begin() - get an async connection
        await conn.run_sync(Base.metadata.create_all)   # this runs sync create_all inside our async context
    yield   # this is where our app actually runs

    # Shutdown
    await engine.dispose()  # this is important to close the connection pool and free up resources. not needed for sqlite but good practice for other dbs like postgres or mysql


app = FastAPI(lifespan=lifespan)


@app.get("/")
def root():
    return {"message": "Hello world!"}

