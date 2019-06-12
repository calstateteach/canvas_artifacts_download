"""Download all media recording submissions to student folders.
Finds media files to download by parsing exports folder, which
is assumed to have been populated with student data by export_student_artifacts.py.

09.03.2017 tps Created from download_attachments.ps.
09.03.2017 tps Use http_downloader.py module to perform actual file download.
"""

# import csv
import os
# import re
# import requests

import export_student_artifacts
import path_consts
import script_logging
import http_downloader


#################### Helper Functions ####################

# def download_file(file_url, target_file_path):
#     """Download the file at the given URL to the target folder.
#     If something bad happens, just skip the download & log it as an error.
#     """
#     try:
#         attachment_resp = requests.get(file_url)
        
#         # # Extract name to use for saving file
#         # content_header = attachment_resp.headers['Content-Disposition']
#         # file_name = re_filename.search(content_header).group(1)

#         # Save attachment file to target file
#         # saved_file_name = os.path.join(target_folder, file_name)
#         script_logging.log_status('Downloading %s' % target_file_path)
#         with open(target_file_path, "wb") as ofile:
#             ofile.write(attachment_resp.content)
    
#     except Exception as e:
#         script_logging.log_error("Error downloading %s, requesting: %s " % (target_file_path, file_url))
#         script_logging.log_error("Error object: " + str(e))



def download_all_media_recordings(doDownload = True):
    """Download all media recordings submissions by parsing exports folder.
    doDownload parameter lets us run this without actually downloading files, 
    which is useful during development.
    """
    
    # Walk exports directory looking for submissions csv files.
    for (folder_path, dir_list, file_list) in os.walk(path_consts.EXPORTS_FOLDER):
        if path_consts.SUBMISSIONS_FILE_NAME in file_list:

            # Walk through all the student's submission attachments.
            submissions_csv_file = os.path.join(folder_path, path_consts.SUBMISSIONS_FILE_NAME)
            submissions = export_student_artifacts.load_csv_file(submissions_csv_file)
            for submission in submissions[1:]:  # Skip 1st row, which is the header.

                # Look for media_recording submissions
                if submission.submission_type == 'media_recording':
                    target_file_path = os.path.join(folder_path, submission.media_file)
                    if doDownload:
                        http_downloader.download(submission.media_url, target_file_path)
                    else:
                        script_logging.log_status('Download %s to %s' % (submission.media_url, target_file_path))


######### Stand-Alone Execution #########

if __name__ == "__main__":

    script_logging.clear_logs()
    download_all_media_recordings()

