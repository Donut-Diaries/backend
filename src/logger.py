import logging
import sys
import os

import uvicorn.logging

DEBUG = os.getenv("DEBUG")

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

if DEBUG:
    file_handler = logging.FileHandler("app-debug.log")
else:
    file_handler = logging.FileHandler("app.log")

# set formatters
stream_handler.setFormatter(stdout_formatter)
file_handler.setFormatter(file_formatter)

# add handlers to logger
logger.handlers = [stream_handler, file_handler]

# set log level
if DEBUG:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
