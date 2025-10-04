from fastapi import FastAPI
from backend.app.routes import query

app = FastAPI(title="Agentic SQL Generator")

# Include routes
app.include_router(query.router, prefix="/api")