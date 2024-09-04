import logging
import os

logger = logging.getLogger('static_analyzer')

DEBUG = os.environ.get('DEBUG', 'False').lower() in ['true', '1', 'yes']


formatter = logging.Formatter(
    '%(asctime)s - %(name)s:%(levelname)s: %(filename)s:%(lineno)s - %(message)s',
    datefmt='%H:%M:%S',
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
if DEBUG:
    console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
file_name = f'static_analyzer.log'
file_handler = logging.FileHandler(os.path.join(log_dir, file_name))
file_handler.setLevel(logging.INFO)
if DEBUG:
    file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
logger.addHandler(console_handler)
logger.addHandler(file_handler)
