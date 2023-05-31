from fastapi import APIRouter


router = APIRouter()
# TODO: don't need this file... just manually add stuff to router in setup_app


@router.get("/")
def get_test_app():
    return "test_app app created!"
