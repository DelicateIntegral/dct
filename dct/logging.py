import logging


def set_log(log_path):
    logging.basicConfig(
        filename=log_path, format="%(asctime)s %(message)s", filemode="w"
    )
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    return logger
