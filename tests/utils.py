from fastapi.testclient import TestClient
from httpx import Response as HttpxResponse


class LoggedInClient(TestClient):
    """Subclass of TestClient to automatically include the access token
    into the header of any request"""

    def __init__(self, app, access_token: str, *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self._access_token = access_token

    def get(self, *args, **kwargs) -> HttpxResponse:
        return super().get(
            *args,
            **kwargs,
            headers={
                "Authorization": f"Bearer {self._access_token}",
                **kwargs.get("headers", {}),
            },
        )

    def post(self, *args, **kwargs) -> HttpxResponse:
        return super().post(
            *args,
            **kwargs,
            headers={
                "Authorization": f"Bearer {self._access_token}",
                **kwargs.get("headers", {}),
            },
        )

    def put(self, *args, **kwargs) -> HttpxResponse:
        return super().put(
            *args,
            **kwargs,
            headers={
                "Authorization": f"Bearer {self._access_token}",
                **kwargs.get("headers", {}),
            },
        )

    def patch(self, *args, **kwargs) -> HttpxResponse:
        return super().patch(
            *args,
            **kwargs,
            headers={
                "Authorization": f"Bearer {self._access_token}",
                **kwargs.get("headers", {}),
            },
        )

    def delete(self, *args, **kwargs) -> HttpxResponse:
        return super().delete(
            *args,
            **kwargs,
            headers={
                "Authorization": f"Bearer {self._access_token}",
                **kwargs.get("headers", {}),
            },
        )
