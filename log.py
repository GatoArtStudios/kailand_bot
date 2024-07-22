import logging as logger

# ------------------------------------ Configuracion de logs ------------------------------------

def logging_config():
    logger.basicConfig(
        filename='discord_bot.log',
        level=logger.DEBUG,
        encoding='utf-8',
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logger

logging = logging_config()