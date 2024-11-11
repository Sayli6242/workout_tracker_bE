from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routes.route import router
from fastapi.middleware.cors import CORSMiddleware





app = FastAPI()


# Mount static directory for serving images
app.mount("/static", StaticFiles(directory="static"), name="static")


app.include_router(router)

# CORS middleware to allow requests from your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],  # Adjust according to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
