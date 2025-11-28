from fastapi import APIRouter
from clients.neo4j_client import run_query

router = APIRouter(prefix="/neo4j")

@router.get("/q")
def q(query: str):
    return run_query(query)

