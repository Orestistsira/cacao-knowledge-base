import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.playbooks import router as playbooks_router
from routers.soarca import router as soarca_router
from routers.taxii import router as taxii_router
from routers.stats import router as stats_router

from apitally.fastapi import ApitallyMiddleware


load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.add_middleware(
    ApitallyMiddleware,
    client_id=os.getenv("APITALLY_CLIENT_ID"),
    env="dev",  # or "prod"
)

# Include playbooks router
app.include_router(playbooks_router)

# Include soarca router
app.include_router(soarca_router)

# Include soarca router
app.include_router(taxii_router)

# Include stats router
app.include_router(stats_router)
