from fastapi import FastAPI
from api.routes import route
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://workoutplanner-theta.vercel.app",
        "https://workout-tracker-application-qk3w.vercel.app",  # Add your frontend domain
        "http://localhost:5173",  # For local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Authorization", "Content-Type"],

)

app.include_router(route.router)