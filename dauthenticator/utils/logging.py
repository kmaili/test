import logging

class Logger:
    def __init__(self,config):

        logger = logging.getLogger(name='dauthenticator_logger')
        if not logger.hasHandlers():
            formatter = logging.Formatter(config.logging_format)
            fh=logging.FileHandler(config.logging_folder)
            #fh.setLevel(config.logging_level)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
                
            # add stream handler
            # formatter = logging.Formatter(config.logging_format)
            # sh=logging.StreamHandler()
            # sh.setFormatter(formatter)
            # logger.addHandler(sh)
            # logger.setLevel(config.logging_level)
        self.logger = logger
