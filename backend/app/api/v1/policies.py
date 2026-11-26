from typing import List, Dict, Any
from fastapi import APIRouter, Query
from backend.app.services.policy_service import policy_service

router = APIRouter(prefix="/policies", tags=["Policies"])

@router.get("", response_model=List[Dict[str, Any]])
def get_all_return_policies():
    return policy_service.get_all_policies()

@router.get("/search", response_model=Dict[str, Any])
def search_return_policy(q: str = Query(..., min_length=1)):
    return policy_service.search_policy(q)
