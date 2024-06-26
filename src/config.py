from decouple import config
from dotenv import load_dotenv
from pydantic import BaseModel
from urllib.parse import quote_plus

# Load the .env
load_dotenv()


class Config(BaseModel):
    # Set to test for testing.
    ENVIRONMENT: str = config("ENVIRONMENT", "production")

    # MongoDB settings
    MONGODB_URI: str = config("MONGODB_URI", "")
    MONGODB_USER: str = quote_plus(config("MONGODB_USER", ""))
    MONGODB_PW: str = quote_plus(config("MONGODB_PW", ""))
    MONGODB_HOST: str = config("MONGODB_HOST", "localhost")
    MONGODB_PORT: str = config("MONGODB_PORT", "27017")
    MONGODB_SCHEME: str = config("MONGODB_SCHEME", "mongodb")

    # JWT
    JWT_SECRET: str = config("JWT_SECRET", "")
    JWT_SECRET_FILE: str = config("JWT_SECRET_FILE", "")
    JWT_ALGORITHM: str = config("JWT_ALGORITHM", default="HS256")


CONFIG = Config()
