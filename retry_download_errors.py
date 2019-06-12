"""Retry downloading files that caused errors in http_downloader.
We can find files to try downloading again by parsing the err.txt file for error messages.
Error log lines we are interested in look like:

09-04-2017 12:45:17..Error_http_downloader 'exports/CalStateTEACH Term 1/grios/Schedule/Mentor Info.docx', 'https://ourdomain.instructure.com/files/8080/download?download_frd=1&verifier=zVZdnkpTmmJIGYAg2U0PaDqESrJBFLi0Xsm73Eldu'

A regex string that captures the file name & URL looks like:

[0-9][0-9]-[0-9][0-9]-[0-9][0-9][0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9]\.\.Error_http_downloader '(.*)', '(.*)'$

09.04.2017 tps Created.
09.17.2018 tps Change bad global Null reference to None.
"""
import script_logging
import http_downloader
import os
import re
import shutil


######### Constants #########

# Regex pattern for extracting file download details from error log.
REGEX_PATTERN = "[0-9][0-9]-[0-9][0-9]-[0-9][0-9][0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9]\.\.Error_http_downloader '(.*)', '(.*)'$"
 

def make_cp_file_name():
    """Create a unique file that looks like "retry000.txt", "retry001.txt", 
    "retry002.txt", etc.
    """

    cp_file_name = None  # Function return variable
    n = 0
    while True:
        cp_file_name = 'retry%03d.txt' % n
        if (not os.path.exists(cp_file_name)):
            break 
        else:
            n = n + 1
            continue

    return cp_file_name


def cp_err_log():
    err_log_file = script_logging.ERR_FILE_NAME
    err_log_cp = make_cp_file_name()
    script_logging.log_status('Copying error log %s to %s' % (err_log_file, err_log_cp))
    shutil.copy(err_log_file, err_log_cp)


def load_errors():
    pattern = re.compile(REGEX_PATTERN)

    err_list = []       # Accumulate the download errors

    file_name = script_logging.ERR_FILE_NAME
    if (os.path.isfile(file_name)):
        with open(file_name, 'r') as f:
            for line in f:
                match = pattern.match(line)
                if match:
                    err_list.append((match.group(1), match.group(2)))

    # Let's see what download errors we found
    if len(err_list) > 0:
        # This process might still generate errors, so save the current
        # error before starting a new one.
        cp_err_log()
        script_logging.clear_error_log()
        
        for err in err_list:
            # Retry the download
            download_file = err[0]
            download_url = err[1]
            http_downloader.download(download_url, download_file)



    else:
        script_logging.log_status('No download errors to retry.')


######### Stand-Alone Execution #########

if __name__ == "__main__":
    load_errors()
