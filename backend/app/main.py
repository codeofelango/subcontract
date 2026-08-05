import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    activity,
    attachments,
    change_orders,
    contracts,
    dashboard,
    evaluations,
    manpower,
    penalties,
    users,
    workflows,
)

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Subcontract Management Module API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(contracts.router)
app.include_router(manpower.router)
app.include_router(change_orders.router)
app.include_router(penalties.router)
app.include_router(evaluations.router)
app.include_router(activity.router)
app.include_router(users.router)
app.include_router(workflows.router)
app.include_router(attachments.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
