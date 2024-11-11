from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.route import router
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://workout-tracker-application-y4gq.vercel.app/"],  # Update this with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your router
app.include_router(router)

# Mount static files - Note: In serverless, you'll need to handle static files differently
if not os.environ.get("VERCEL"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Required for Vercel
app = app