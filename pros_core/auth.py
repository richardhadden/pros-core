from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_login import LoginManager
from fastapi_login.exceptions import InvalidCredentialsException

SECRET = "super-secret-key"

login_manager = LoginManager(SECRET, "/login")


# Fake DB
DB = {"users": {"johndoe@mail.com": {"name": "John Doe", "password": "hunter2"}}}


@login_manager.user_loader()
def query_user(user_id: str):
    """
    Get a user from the db
    :param user_id: E-Mail of the user
    :return: None or the user object
    """
    return DB["users"].get(user_id)


def build_auth(_app: FastAPI):
    @_app.post("/login/")
    def login(data: OAuth2PasswordRequestForm = Depends()):
        email = data.username
        password = data.password

        user = query_user(email)
        if not user:
            # you can return any response or error of your choice
            raise InvalidCredentialsException
        elif password != user["password"]:
            raise InvalidCredentialsException

        access_token = login_manager.create_access_token(data={"sub": email})
        return {"access_token": access_token}


LoggedInUser = Depends(login_manager)
