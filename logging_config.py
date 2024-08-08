import logging
import sys

def setup_logging(level=logging.INFO):
    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')

    # Create a stream handler for stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Remove any existing handlers
    logger.handlers = []

    # Add the handler to the logger
    logger.addHandler(handler)

    return logger
