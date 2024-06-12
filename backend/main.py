from fastapi import FastAPI
from dotenv import load_dotenv
from routers.playbooks import router as playbooks_router


load_dotenv()

app = FastAPI()

# Include playbooks router
app.include_router(playbooks_router)
