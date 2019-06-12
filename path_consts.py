"""Shared folder paths & file names for outputting artifact data files.
11.25.2016 tps
01.16.2019 tps Add file for rubric assessments.
"""

import os

#################### File Name Constants for Exports Folder ####################

EXPORTS_FOLDER                  = 'exports'   # Folder in which to output artifact data. Assumed to exist.
SUBMISSIONS_FILE_NAME           = 'submissions.csv'
COMMENTS_FILE_NAME              = 'comments.csv'
ATTACHMENTS_FILE_NAME           = 'attachments.csv'
RUBRIC_ASSESSMENTS_FILE_NAME    = 'rubric_assessments.csv'
TIME_STAMP_FILE_NAME = os.path.join(EXPORTS_FOLDER, 'timestamp.txt')