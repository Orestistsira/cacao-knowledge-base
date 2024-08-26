import asyncio
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from fastapi import HTTPException, status, APIRouter, BackgroundTasks
from typing import List

import httpx

from models.playbook import Playbook
from models.execution import ExecutionInDB
from database import db


load_dotenv()

router = APIRouter(
    prefix="/taxii",
    tags=["taxii"],
)

taxii_url = os.getenv("TAXII_URI")
taxii_username = os.getenv("TAXII_USERNAME")
taxii_password = os.getenv("TAXII_PASSWORD")

if not taxii_url:
    raise ValueError("TAXII_URI environment variable not set")

if not taxii_username or not taxii_password:
    raise ValueError("TAXII_USERNAME and TAXII_PASSWORD environment variables must be set")

# Set up basic authentication
auth = httpx.BasicAuth(taxii_username, taxii_password)

# Set up headers with Accept media type
headers = {
    "Accept": "application/taxii+json;version=2.1"
}

@router.get("/discovery", response_model=dict, status_code=status.HTTP_200_OK)
async def get_discovery():
    """
    Get information about the TAXII Server and any advertised API Roots

    Returns:
    - A discovery object.
    """

    try:
        async with httpx.AsyncClient(auth=auth, headers=headers) as client:
            response = await client.get(f"{taxii_url}/taxii2/")
            response.raise_for_status()
            result = response.json()

            return result

    except httpx.HTTPError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
