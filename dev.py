"""
This script is used to run the job processor in a development environment.
It initializes the logger and processes active jobs.
"""
import logging
import sys
import time
from src.job_processor import JobProcessor
import argparse

# Parse command line arguments
if "-h" in sys.argv or "--help" in sys.argv:
    print("""
    Usage: dev.py [options]

    Options:
      -h, --help            Show this help message and exit
      -l LOG_LEVEL, --log-level LOG_LEVEL
                            Set the logging level (default: DEBUG).
                            Choices: DEBUG, INFO, WARNING, ERROR, CRITICAL
      -t LOG_TYPE, --log-type LOG_TYPE
                            Set the logging output type (default: console).
                            Choices: console, file
    """)
    sys.exit(0)
parser = argparse.ArgumentParser(
    description="Run the job processor in a development environment.")
parser.add_argument("-l", "--log-level", type=str, 
                    choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                    default="INFO", help="Set the logging level (default: DEBUG).")
parser.add_argument("-t", "--log-type", type=str, 
                    choices=["console", "file"], default="console",
                    help="Set the logging output type (default: console).")
args = parser.parse_args()

# Configure logging based on command line arguments
log_level = getattr(logging, args.log_level.upper(), logging.INFO)
log_handlers = []

if args.log_type == "console":
    log_handlers.append(logging.StreamHandler(sys.stdout))
elif args.log_type == "file":
    log_handlers.append(logging.FileHandler("debug.log"))

logging.basicConfig(
    level=log_level,
    format="%(levelname)s | %(asctime)s | %(name)s | %(message)s",
    handlers=log_handlers
)

logger = logging.getLogger(__name__)
# Sleep 20 seconds to allow the logger to initialize
# time.sleep(20)

logger.info('Hello world!')
logger.info('Starting to run the job scripts')


jobs = JobProcessor()
jobs.process_active_jobs()

# End of script
