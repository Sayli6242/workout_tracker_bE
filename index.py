from fastapi import FastAPI
from api.routes import route
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://workout-tracker-application-qk3w.vercel.app",  # Add your frontend domain
        "http://localhost:3001", # For local development
        "https://github.com"  # to allow github IP
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Authorization", "Content-Type"],

)

app.include_router(route.router, prefix="/api")