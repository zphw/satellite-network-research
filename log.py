import logging
import sys


logger = logging.getLogger("satellite_network_research")

logger_handler = logging.StreamHandler(sys.stdout)
logger_formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")

logger_handler.setFormatter(logger_formatter)
logger.addHandler(logger_handler)

logger.setLevel(logging.DEBUG)
