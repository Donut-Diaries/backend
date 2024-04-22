import logging
import sys
import os

import uvicorn.logging

DEBUG = os.getenv("DEBUG")
DEVELOPMENT = os.getenv("DEVELOPMENT")

# get logger
logger = logging.getLogger()

# create formatter
stdout_formatter = uvicorn.logging.DefaultFormatter(
    fmt="%(levelprefix)s %(asctime)s | %(message)s - %(pathname)s - %(lineno)s"
)

file_formatter = logging.Formatter(
    fmt="%(levelname)s - %(asctime)s - %(message)s - %(pathname)s - %(lineno)s"
)

# create handler
stream_handler = logging.StreamHandler(sys.stdout)

stream_handler.setFormatter(stdout_formatter)

# Add file_handler in dev
if DEVELOPMENT:
    if DEBUG:
        file_handler = logging.FileHandler("app-debug.log")
    else:
        file_handler = logging.FileHandler("app.log")
        
    file_handler.setFormatter(file_formatter)
    
    logger.handlers = [stream_handler, file_handler]

else:
    logger.handlers = [stream_handler]


# set log level
if DEBUG:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
