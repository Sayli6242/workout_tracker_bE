from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.route import router
import os

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # "http://localhost:3001"
        "https://workout-tracker-application-y4gq.vercel.app",
        # Add your frontend URL on Render if different
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your router
app.include_router(router)

# Required for Render
app = app