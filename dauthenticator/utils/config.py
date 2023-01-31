import os
import logging

WORKING_DIR = os.getcwd()

# logging
logging_folder = os.path.join(WORKING_DIR, 'dauthenticator/logs', 'dauthenticator.log')
logging_level = logging.INFO
logging_format = '%(asctime)s: %(name)s: [%(levelname)s]: %(message)s'