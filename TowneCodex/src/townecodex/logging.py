import logging
from logging import Logger


"""
Logger setup for Towne Codex.
this can be used to log messages to the console, from any part of the program.

author: Cole McGregor
date: 2025-09-20
version: 0.1.0
"""

# LOGGER_NAME is used to identify the logger.
LOGGER_NAME = "towne_codex"

#now we create the logger from the LOGGER_NAME
logger: Logger = logging.getLogger(LOGGER_NAME)  # import this anywhere

def setup(level: str = "INFO") -> None:
    """
    Setup the logger.
    """
    if logger.handlers:
        return  # already configured
    # set the level of the logger
    logger.setLevel(level.upper())

    # create a formatter
    fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
    # create a stream handler
    h = logging.StreamHandler()
    # set the formatter
    h.setFormatter(logging.Formatter(fmt))
    # add the handler to the logger
    logger.addHandler(h)

    # Let child loggers (towne_codex.*) propagate to this handler
    logging.getLogger("towne_codex").propagate = False
