"""Module that abstracts out downloading  files via HTTP.
09.03.2017 tps Created.
09.04.2017 tps Add error logging line suitable for attempting to recreate the download.
05.07.2019 tps Log more response data, to diagnose download failures.
"""
import requests
import script_logging

REQUEST_TIMEOUT = 30    # Request timeout in seconds


def download(download_url, target_file_path):
    """Download the file at the given URL to the target folder.
    If something bad happens, just skip the download & log it as an error.
    """
    try:
        script_logging.log_status('Download file %s' % target_file_path)
        script_logging.log_status('Download URL %s' % download_url)

        # attachment_resp = requests.get(download_url)
        # attachment_resp = requests.get(download_url, timeout=10)    # 10 second timeout
        attachment_resp = requests.get(download_url, timeout=REQUEST_TIMEOUT, stream=True)    # Don't download content immediately

        script_logging.log_status('Status code: %s' % attachment_resp.status_code)
        script_logging.log_status('Headers: %s' % attachment_resp.headers)

        # # Extract name to use for saving file
        # content_header = attachment_resp.headers['Content-Disposition']
        # file_name = re_filename.search(content_header).group(1)

        # Save attachment file to target file
        # saved_file_name = os.path.join(target_folder, file_name)
        # script_logging.log_status('Downloading %s' % target_file_path)
        with open(target_file_path, "wb") as ofile:
            ofile.write(attachment_resp.content)
    
        script_logging.log_status('Done downloading %s' % target_file_path)

    except Exception as e:
        # Escape file names in case they have weird characters in them.
        escaped_file = target_file_path.replace("'", "\'")
        escaped_url = download_url.replace("'", "\'")
        script_logging.log_error("Error_http_downloader '%s', '%s'" % (escaped_file, escaped_url))
        script_logging.log_error("Error object: " + str(e))
