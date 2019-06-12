"""Download all submission attachments to student folders.
Finds attachments to download by parsing exports folder, which
is assumed to have been popualated with student data by export_student_artifacts.py.

11.26.2016 tps
11.28.2016 tps Use export_student_artifacts.load_csv_file(), which returns
    rows as namedtuples, instead of local version of function.
11.28.2016 tps Save attachment file under name in attachments csv file instead of
    under the name specified by its content-disposition header.
11.29.2016 tps Save attachment's thumbnail file to the student folder.
02.20.2017 tps Fixed bad variable name in Exception handler for download_file().
02.20.2017 tps Add test for missing thumbnail image in download_all_attachments().
09.03.2017 tps Use http_downloader.py module to perform actual file download.
05.08.2019 tps Download thumbnail images to our made-up thumbnail file names.
"""

# import csv
import os
# import re
# import requests

import export_student_artifacts
import path_consts
import script_logging
import http_downloader

# Prepare the regex expression for extracting the attachment file name.
# The attachment file name is in HTTP request "Content-Disposition" header,
# which looks like:
# 'attachment; filename="websnappr20161027-16418-11ar7al.png"; filename*=UTF-8''websnappr20161027%2D16418%2D11ar7sg.png'
# We want to extract the 1st file name to use as the name of the downloaded file.
# re_filename = re.compile('filename="(.*)"')

#################### Helper Functions ####################

# def download_file(attachment_url, target_file_path):
#     """Download the file at the given URL to the target folder.
#     If something bad happens, just skip the download & log it as an error.
#     """
#     try:
#         attachment_resp = requests.get(attachment_url)
        
#         # # Extract name to use for saving file
#         # content_header = attachment_resp.headers['Content-Disposition']
#         # file_name = re_filename.search(content_header).group(1)

#         # Save attachment file to target file
#         # saved_file_name = os.path.join(target_folder, file_name)
#         script_logging.log_status('Downloading %s' % target_file_path)
#         with open(target_file_path, "wb") as ofile:
#             ofile.write(attachment_resp.content)
    
#     except Exception as e:
#         script_logging.log_error("Error downloading %s, requesting: %s " % (target_file_path, attachment_url))
#         script_logging.log_error("Error object: " + str(e))

# def png_thumbnail_file_name(attachment_file_name):
#     """Make up a thumbnail file name.
#     The Canvas API does not expose a file name or content type for an attachment's thumbnail,
#     but so far the thumbnails have all been PNG files. We'll name the thumbnail file
#     using the base name of its attachment file plus '_thumb' suffix & .png extension.
#
#     For example:
#     websnappr20161026-12490-1muw1Av.png --> websnappr20161026-12490-1muw1Av_thumb.png
#     trim.269DC7EB-0FD8-4B45-A102-D3D7BACBDEBB.MOV --> trim.269DC7EB-0FD8-4B45-A102-D3D7BACBDEBB_thumb.png
#
#     There is no test for file name collisions, so it's possible but unlikely that the thumbnail
#     file name will not be unique within the directory.
#     """
#     return '.'.join(attachment_file_name.split('.')[:-1]) + '_thumb.png'


def download_all_attachments():
    """Download all submission attachments by parsing exports folder.
    """
    
    # Walk exports directory looking for attachments csv files.
    for (folder_path, dir_list, file_list) in os.walk(path_consts.EXPORTS_FOLDER):
        if path_consts.ATTACHMENTS_FILE_NAME in file_list:

            # Walk through all the student's submission attachments.
            attachment_csv_file = os.path.join(folder_path, path_consts.ATTACHMENTS_FILE_NAME)
            attachments = export_student_artifacts.load_csv_file(attachment_csv_file)
            for attachment in attachments[1:]:  # Skip 1st row, which is the header.
            
                # #? 12.15.2017 Trap weird file name problem
                # targetFile = os.path.join(folder_path, attachment.file_name)
                # if not 'Who are all of the students in your classroom' in targetFile:
                #     continue

                # Download the attachment file
                http_downloader.download(attachment.url, os.path.join(folder_path, attachment.file_name))
                
                # Download the thumbnail preview image, if any.
                # Assume that if attachment has a preview image, it is a PNG file.
                if attachment.thumbnail_url:
                    # thumbnail_file_name = os.path.join(folder_path, png_thumbnail_file_name(attachment.file_name))
                    thumbnail_file_name = os.path.join(folder_path, attachment.thumbnail_file)
                    http_downloader.download(attachment.thumbnail_url, thumbnail_file_name)

######### Stand-Alone Execution #########

if __name__ == "__main__":

    script_logging.clear_logs()
    download_all_attachments()

