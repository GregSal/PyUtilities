'''Standard Logging initialization.
Includes calling references.
'''

import logging

def config_logger(level: str = 'DEBUG', prefix=__name__)->logging.Logger:
    '''Configure a basic logger.
    Creates a logger that prints to the standard output with the given level.
    Arguments:
        level (optional, str) -- The level of the logger. One of:
            DEBUG (Default)
            INFO
            WARNING
            ERROR
            CRITICAL
        prefix (optional, str) -- The text to prefix all logger messages with.
            Default is the logger module name.
    Returns:
        An std-out logger of a given level.
    Example:
        from logging_tools import config_logger
        logger = config_logger('DEBUG')
        logger.debug('This is a debug message')
    '''
    # create logger
    format_str = '%(name)-20s - %(levelname)s: %(message)s'
    logging.basicConfig(format=format_str)
    logger = logging.getLogger(prefix)
    # Set Level
    if level == 'DEBUG':
        logger.setLevel(logging.DEBUG)
    elif level == 'INFO':
        logger.setLevel(logging.INFO)
    elif level == 'WARNING':
        logger.setLevel(logging.WARNING)
    elif level == 'ERROR':
        logger.setLevel(logging.ERROR)
    elif level == 'CRITICAL':
        logger.setLevel(logging.CRITICAL)
    else:
        msg_str = 'Level must be one of: {}; got {}'
        msg = msg_str.format(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], level)
        raise ValueError(msg)
    return logger


# Log to a file
def file_logger(file_name: str, level: str = 'DEBUG', prefix=__name__)->logging.Logger:
    '''Configure a logger that outputs to the specified file.
    Creates a logger that outputs to theb specified file with the given level.
    Arguments:
        file_name (str) -- The name of the file to save logging messages to.
        level (optional, str) -- The level of the logger. One of:
            DEBUG
            INFO
            WARNING
            ERROR
            CRITICAL
        prefix (optional, str) -- The text to prefix all logger messages with.
            Default is the logger module name.
    Returns:
        An std-out logger of a given level.
    Example:
        from logging_tools import file_logger
        logger = file_logger('log_file.txt, ''DEBUG')
        logger.debug('This is a debug message')
    '''
    msg_format = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
    date_fmt = '%m-%d %H:%M'
    file_name = str(file_name)
    save_mode = 'w'
    logging.basicConfig(format=msg_format, filename=file_name,
                                         filemode=save_mode, datefmt=date_fmt)
    logger = logging.getLogger(prefix)
    if level == 'DEBUG':
        logger.setLevel(logging.DEBUG)
    elif level == 'INFO':
        logger.setLevel(logging.INFO)
    elif level == 'WARNING':
        logger.setLevel(logging.WARNING)
    elif level == 'ERROR':
        logger.setLevel(logging.ERROR)
    elif level == 'CRITICAL':
        logger.setLevel(logging.CRITICAL)
    else:
        msg_str = 'Level must be one of: {}; got {}'
        msg = msg_str.format(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], level)
        raise ValueError(msg)
    return logger

def ch_logger(logger: logging.Logger = None, level: str = 'DEBUG', prefix=__name__)->logging.Logger:
    '''Create a console handler to basic logger.
    Creates a logger if not supplied and adds a handler that prints to the
    console with the given level.
    Arguments:
        logger {optional, logging.Logger} -- the logger to add the handler to.
        level {optional, str} -- The level of the logger. One of:
            DEBUG
            INFO
            WARNING
            ERROR
            CRITICAL
        prefix (optional, str) -- The text to prefix all logger messages with.
            Default is the logger module name.
    Returns:
        An std-out logger of a given level.
    Example:
        from logging_tools import file_logger, ch_logger
        logger = file_logger('log_file.txt, ''DEBUG')
        logger = ch_logger(logger, 'WARNING')
        logger.debug('This is a debug message sent just to the file')
        logger.warning('This is a warning message sent to both the file and the console')
    '''
    if logger is None:
        # create logger
        logger = logging.getLogger(prefix)
    # create console handler
    ch = logging.StreamHandler()
    # create formatter
    formatter = logging.Formatter('%(name)-20s - %(levelname)s: %(message)s')
    # add formatter to ch
    ch.setFormatter(formatter)
    # Set Level
    if level == 'DEBUG':
        ch.setLevel(logging.DEBUG)
    elif level == 'INFO':
        ch.setLevel(logging.INFO)
    elif level == 'WARNING':
        ch.setLevel(logging.WARNING)
    elif level == 'ERROR':
        ch.setLevel(logging.ERROR)
    elif level == 'CRITICAL':
        ch.setLevel(logging.CRITICAL)
    else:
        msg_str = 'Level must be one of: {}; got {}'
        msg = msg_str.format(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], level)
        raise ValueError(msg)
    # add ch to logger
    logger.addHandler(ch)
    return logger

def log_dict(logger: logging.Logger, dict_var: dict, text: str = None):
    '''Logger output dictionary values formatted
    '''
    var_list = ['{}:\t{}'.format(key,item) for key, item in dict_var.items()]
    var_str = '\n'.join(var_list)
    if text:
        var_str = text + '\n' + var_str
    var_str = var_str + '\n'
    logger.debug(var_str)


def main():
    # logger = config_logger('DEBUG')
    # logger.debug('This is a debug message')
    logger = file_logger('log_file.txt', 'DEBUG')
    logger.debug('This is a debug message')
    c_logger = ch_logger(logger, 'WARNING')
    c_logger.debug('This is a debug message sent just to the file')
    c_logger.warning('This is a warning message sent to both the file and the console')

if __name__ == '__main__':
    main()
