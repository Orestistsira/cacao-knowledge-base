from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.playbooks import router as playbooks_router
from routers.soarca import router as soarca_router


app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include playbooks router
app.include_router(playbooks_router)

# Include soarca router
app.include_router(soarca_router)
