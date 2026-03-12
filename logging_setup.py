import logging
import logging.handlers
import os

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'hw_acceptance.log')


def setup_logging(level=logging.DEBUG):
    """Configure root logger with rotating file and console handlers.

    Call this once at the start of each test script. Library modules
    should only call logging.getLogger(__name__) without calling this.
    """
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(level)

    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=1_000_000, backupCount=5,
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    ))
    root.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        '%(name)s %(levelname)s: %(message)s',
    ))
    root.addHandler(console_handler)
