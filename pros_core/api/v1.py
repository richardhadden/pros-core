from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def get_pros_core():
    return "pros_core app created!"
