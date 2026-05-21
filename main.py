from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import db
from app.api import tickets, admin, reports
from app.seed_data import seed_initial_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    await db.connect()
    print("Database connected")
    await seed_initial_data()
    print("Initial data seeded")
    yield
    print("Shutting down...")
    await db.close()
    print("Database closed")

app = FastAPI(title="Bus Ticket System", lifespan=lifespan)

app.include_router(tickets.router)
app.include_router(admin.router)
app.include_router(reports.router)

@app.get("/")
async def root():
    return {"message": "Bus Ticket System API", "status": "running"}