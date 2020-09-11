import logging

def get_logger(LOG_FILE):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    file_formatter = logging.Formatter('%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s')
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8') 
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter) 

    stream_formatter = logging.Formatter('%(asctime)s - %(levelname)-8s - %(message)s') 
    stream_handler = logging.StreamHandler() 
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(stream_formatter) 

    logger.addHandler(file_handler) 
    logger.addHandler(stream_handler)
    return logger