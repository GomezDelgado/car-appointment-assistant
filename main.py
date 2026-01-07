"""Main entry point for the car appointment assistant."""

# Load environment variables BEFORE other imports
from dotenv import load_dotenv
load_dotenv()

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from src.api.schema import schema

# Create FastAPI app
app = FastAPI(
    title="Car Appointment Assistant",
    description="Voice-based car dealership appointment booking assistant",
    version="0.1.0",
)

# Add CORS middleware
import os
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GraphQL router
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
async def root():
    """Root endpoint with basic info."""
    return {
        "name": "Car Appointment Assistant",
        "version": "0.1.0",
        "graphql_endpoint": "/graphql",
        "graphql_playground": "/graphql",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


def run():
    """Run the server."""
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    run()
