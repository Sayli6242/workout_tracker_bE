from fastapi import FastAPI
from api.routes import route
from api.routes import logs
from api.routes import measurements
from api.routes import sessions
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # "https://workout-tracker-application-qk3w.vercel.app",  S# Add your frontend domain
        "http://localhost:3001", # For local development
        # "https://github.com"  # to allow github IP
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Authorization", "Content-Type"],

)

app.include_router(route.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(measurements.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")

@app.get("/health")
async def health_check():
    return {"status": "ok"}