"""One script to rule them all. This script runs all the scripts in sequence to
fully populate artifacts export folder from Canvas API.

11.29.2016 tps
09.02.2017 tps Download media recording submissions.
09.24.2018 tps Retry download errors.
"""

import json_artifacts
import export_student_artifacts
import download_attachments
import download_media_recordings
import make_html
import script_logging
import retry_download_errors

script_logging.clear_logs()
script_logging.log_status('Retrieve Canvas JSON data')
json_artifacts.retrieve_json()

script_logging.log_status('Create student folders')
export_student_artifacts.write_student_folders()

script_logging.log_status('Download attachments')
download_attachments.download_all_attachments()

script_logging.log_status('Download media recordings')
download_media_recordings.download_all_media_recordings()

script_logging.log_status('Generate HTML')
make_html.make_index_pages()

retry_download_errors.load_errors()