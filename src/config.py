from decouple import config
from pydantic import BaseModel
from urllib.parse import quote_plus


class Config(BaseModel):
    # MongoDB settings
    MONGODB_URI: str = config("MONGODB_URI", "")
    MONGODB_USER: str = quote_plus(config("MONGODB_USER", ""))
    MONGODB_PW: str = quote_plus(config("MONGODB_PW", ""))
    MONGODB_HOST: str = config("MONGODB_HOST", "localhost")
    MONGODB_PORT: str = config("MONGODB_PORT", "27017")
    MONGODB_SCHEME: str = config("MONGODB_SCHEME", "mongodb")


CONFIG = Config()
