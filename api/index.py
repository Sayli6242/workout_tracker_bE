from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.route import router
import os

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://workout-tracker-application-y4gq.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your router
app.include_router(router)

# Remove static files mounting for Vercel deployment
# Vercel doesn't support local file system in serverless functions

# This is required for Vercel
app = app
