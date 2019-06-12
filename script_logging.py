"""Module that handles logging of status & error messages.
These scripts are assumed to run unattended, so writing things out to files
is a way to audit processes after they run.

10.27.2016 tps Started module. Using Python version 2.7.12.

11.02.2016 tps
This can be replaced by using the Python logging module to create
3 logging handlers:
- Handler for DEBUG level & higher that writes to the console.
- Handler for DEBUG level & higher that writes to a log file.
- Handler for ERROR (or EXCEPTION?) level & higher that writes to an error file.

However, if we use the Python logging module, we'll also get logging messages
from all the other libraries that use it, which we may not want & which will
make the error logs harder to read.

11.22.2016 tps Added clear_status_log() & clear_err_log().
11.23.2016 tps Added clear_all_logs().
12.15.2017 tps Changed output stream to handle unicode, for unicode data errors.
"""

import datetime
import io
import os

########### Constants ###########

LOG_FILE_NAME = 'log.txt'
ERR_FILE_NAME = 'err.txt'

########### Helper Functions ###########

def write_string_to_file(message, file_name):
    """Write string to a log file."""

    # Record a time stamp for each message
    str = datetime.datetime.now().strftime('%m-%d-%Y %H:%M:%S..') + message

    # with open(file_name, 'a') as log_file:
    with io.open(file_name, 'a', encoding='utf') as log_file:
        log_file.write(unicode(str) + '\n')


########### Logging Functions ###########

def log_status(message):
    """Write string to a status log file."""
    write_string_to_file(message, LOG_FILE_NAME)
    print(message)  # Echo to standard output.

def log_error(message):
    """Write string to error file."""
    write_string_to_file(message, ERR_FILE_NAME)
    log_status(message)     # Error should be recorded to status log for audit as well.

def clear_status_log():
    """Delete status log file."""
    if os.path.isfile(LOG_FILE_NAME):
        os.remove(LOG_FILE_NAME)

def clear_error_log():
    """Delete error file. Existence of error file can be used to test for errors."""
    if os.path.isfile(ERR_FILE_NAME):
        os.remove(ERR_FILE_NAME)

def clear_logs():
    """Delete all log files."""
    clear_status_log()
    clear_error_log()