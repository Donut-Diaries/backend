from pydantic import BaseModel


class HTTPError(BaseModel):
    detail: str


class StatusUpdateOut(BaseModel):
    detail: str
    status: str
