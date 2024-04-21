import logging
import sys

import uvicorn.logging

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
file_handler = logging.FileHandler("app.log")

# set formatters
stream_handler.setFormatter(stdout_formatter)
file_handler.setFormatter(file_formatter)

# add handlers to logger
logger.handlers = [stream_handler, file_handler]

# set log level
logger.setLevel(logging.DEBUG)
