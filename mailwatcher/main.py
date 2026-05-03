import logging
import time
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Mailwatcher starting up...")
    logger.info("Mailwatcher ready - IMAP polling disabled (no SMTP configured)")
    while True:
        time.sleep(60)
        logger.info("poll_completed - idle")

if __name__ == "__main__":
    main()