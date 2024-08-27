import logging

def setup_logging():
    """
    Set up basic logging configuration.
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

# Create a logger instance
logger = setup_logging()

# Add a test log message to verify the logger is working
logger.info("Logger initialized successfully")

# Export the logger methods directly
info = logger.info
error = logger.error
warning = logger.warning
debug = logger.debug