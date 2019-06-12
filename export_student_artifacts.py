"""Export artifact data to individual student folders.
Assumes that json_artifacts.py has already been run to populate
JSON folder with snapshot of Canvas data.

The file structure of the export directory looks like:
/exports/
    /course 1 folder/
        /student 1 folder/
        /student 2 folder/
        /student 3 folder/
        ...
    /course 2 folder/
        /student 4 folder/
        ...
    ...

Each student folder contains CSV files:
    submissions.csv -- Flat file containing 1 row for each submission artifact.
    comments.csv -- Flat file containing 1 row for each submission comment, 
        linked to the submission by the submssion_id.
    attachments.csv -- Flat file containing 1 row for each submission comment, 
        linked to the submission by the submssion_id.

I'm using the csv module to output the data files, but it has problems with some of the
unicode strings in the data set. To work around this, I explicitly encode fields that
may cause problems to UTF-8. 

11.23.2016 tps
11.24.2016 tps Move path constants to separate module so they can be shared.
11.24.2016 tps Fix bug that was writing out the same user name to every student's file.
11.28.2016 tps Added load_csv_file() so script can also be used as module.
02.20.2017 tps Fix case of Null assignment description string in write_student_folders().
05.02.2017 tps Fix for case of student without a login ID.
08.28.2017 tps Ignore submissions by Canvas "Test Student".
08.28.2017 tps Ignore submissions by students with pending enrollment.
09.02.2017 tps Collect media_comment objects for media_recording submission types.
09.04.2016 tps Handle case of attachment file names that contain forward slashes.
12.15.2017 tps Replace csv with unicodecsv that can handle unicode characters in the data.
08.02.2018 tps Include rubric assessment data.
08.31.2018 tps Include submission grade data.
09.18.2018 tps Include attachment filename. What was being output as the attachment's "file_name"
               was actually the attachment's "display_name". This caused problems when we tried
               saving the attachment to a file name constructed from the display name instead of
               the file name.
01.11.2019 tps Handle case of submission comment author having been dropped from the course.
01.16.2019 tps Handle multiple rubric assessments per assignment.
05.08.2019 tps Add a thumbnail file name that we make up to the attachments output, since Canvas does not supply
               thunbnail file names.
"""

import collections
# import csv
import os
import unicodecsv as csv
import io


import script_logging
import json_artifacts
import path_consts

#################### String Constants ####################

# Dictionary keys used to identify student data entries.
DICT_KEY_USER_NAME          = 'user_name'
DICT_KEY_SUBMISSIONS        = 'submissions'
DICT_KEY_COMMENTS           = 'submission_comments'
DICT_KEY_ATTACHMENTS        = 'submission_attachments'
DICT_KEY_RUBRIC_ASSESSMENTS = 'submission_rubric_assessments'

#################### CSV File Headers ####################

SUBMISSION_HEADERS = (
    'submission_id',
    'user_name',
    'course_name',
    'course_start_at',
    'assignment_name',
    'assignment_description',
    'submitted_at',
    'submission_type',
    'submission_body',
    'submission_url',
    'media_file',
    'media_type',
    'media_url',
    'submission_grade'
    # 'rubric_points',    # 01.16.2019 tps No longer used to generate HTML pages.
    # 'rubric_comments'  # 01.16.2019 tps No longer used to generate HTML pages.
)

SUBMISSION_COMMENT_HEADERS = (
    'submission_id',
    'created_at',
    'comment',
    'user_name')

SUBMISSION_ATTACHMENT_HEADERS = (
    'submission_id',
    'url',
    'file_name',
    'display_name',
    'thumbnail_url',
    'thumbnail_file')

SUBMISSION_RUBRIC_ASSESSMENT_HEADERS = (
    'submission_id',
    'description',
    'points',
    'rating',
    'comments')

#################### Helper Functions ####################

def get_user_name(user_json):
    """Derive user name used in export from user profile JSON. 
    User name is the bit of their login ID before the @.
        # e.g. "someuser@ourdomain.net" --> "someuser"

    It's possible that the user structure passed in will not
    have a login ID at all, in which case there is no user name.
    """
    #return user_json["login_id"].split("@")[0]
    return user_json["login_id"].split("@")[0] if ('login_id' in user_json) else None

def write_csv_file(file_path, csv_headers, csv_data):
    """Output student data to a csv file.
    file_path -- Full path name for output file.
    csv_headers -- Tuple containing csv headers.
    csv_data -- List of tuples containing csv data rows.
    """
    script_logging.log_status('Writing %s' % file_path)

    # with open(file_path,'w') as f:
    #     csv_writer = csv.writer(f)
    #     csv_writer.writerow(csv_headers)
        # csv_writer.writerows(csv_data)    # 12.15.2017 Can't handle unicode characters

        #? Try find the row that is causing write error
        # for data in csv_data:
        #     print(file_path)
        #     print(csv_headers)
        #     print(data)
        #     csv_writer.writerow(data)

    with io.FileIO(file_path, 'w') as f:
        w = csv.writer(f, encoding='utf-8')
        w.writerow(csv_headers)
        w.writerows(csv_data)


def load_csv_file(csv_file_path):
    """Read csv data file into list.
    Data rows are returned as namedtuples so that caller can access
    a data element by column header.
    """

    csv_list = []
    if (os.path.isfile(csv_file_path)):
        # f_csv = csv.reader(open(csv_file_path, 'r'))
        f_csv = csv.reader(io.FileIO(csv_file_path, 'r'), encoding='utf-8')
        csv_headers = f_csv.next()
        csv_list.append(csv_headers)
        named_tuple_type = collections.namedtuple('row_tuple_type', csv_headers)
        csv_list += map(named_tuple_type._make, f_csv)
    return csv_list


    # csv_list = []
    # if (os.path.isfile(csv_file_path)):
    #     with open(csv_file_path, 'r') as f:
    #         f_csv = csv.reader(f)
    #         csv_list = list(f_csv)
    # return csv_list


#################### Data Parsing Functions ####################

def write_student_folders():
    """Create student data folders from JSON data files."""

    # Make sure the top-level exports folder exist.
    if not os.path.isdir(path_consts.EXPORTS_FOLDER):
        os.mkdir(path_consts.EXPORTS_FOLDER)

    # Include time stamp file in exports folder.
    with open(path_consts.TIME_STAMP_FILE_NAME, 'w') as f:
        f.write(json_artifacts.get_time_stamp())

    # Walk through exports for each course.
    courses = json_artifacts.load_courses_json()
    for course in courses:
        
        # Course data needed for export records
        course_id = course['id']
        course_name = course['name']
        course_code = course['course_code']
        course_start_at = course['start_at']

        # Dictionary for resolving user IDs of students & commenters to their user names.
        user_lookup = json_artifacts.create_user_lookup(json_artifacts.load_users_json(course_id))

        # Create dictionary collection used to accumulate submissions by student.
        students_dict = {}
        students = json_artifacts.load_students_json(course_id)
        for student in students:

            # Derive a user name to associate with the student record,
            # instead of using the internal Canvas ID.
            # We might not be able to derive a user name from the student 
            # record, in which case we have to skip it.
            user_name = get_user_name(student)
            if user_name is None:
                continue

            # Stucture to accumulate submission data for each student in course.
            students_dict[student['id']] = {
                DICT_KEY_USER_NAME: user_name,
                DICT_KEY_SUBMISSIONS: [],
                DICT_KEY_COMMENTS: [],
                DICT_KEY_ATTACHMENTS: [],
                DICT_KEY_RUBRIC_ASSESSMENTS: [] }

        # Walk through assignments in the course.
        assignments = json_artifacts.load_assignments_json(course_id)
        for assignment in assignments:
            # Assume assignments are ordered by position.

            # Assignment data needed for export records.
            assignment_id = assignment['id']
            assignment_name = assignment['name']

            # Encode weird unicode characters as utf-8
            # The description string might be Null.
            assignment_description = assignment['description']
            if (assignment_description is None):
                assignment_description = ""
            assignment_description = assignment_description.encode("utf-8")

            # Walk through submissions for the assignment.
            submissions = json_artifacts.load_submissions_json(assignment_id)
            for submission in submissions:

                # Submission data needed for export records.
                submission_id = submission['id']
                submitter_id = submission['user_id']

                # 08.02.2018 tps Work on retrieving rubric points & comments, if any
                """ If a submission has a rubric, it's in a dictionary property like this:
      
                    "rubric_assessment": {
                        "_4848": {
                            "points": 3.0, 
                            "comments": ""
                    }

                    I don't know what the "_4848" key means, but it seems to be that there is only
                    ever 1 entry, so we'll just say that we can grab that one entry's data & be done.
                    
                    - The entry might not have a 'points' property
                    - 'comments' value might be null.
                """
                # submission_rubric_pts = None        # 01.16.2019 tps No longer used to generate HTML pages
                # submission_rubric_comments = None   # 01.16.2019 tps No longer used to generate HTML pages

                # if 'rubric_assessment' in submission:
                #     # script_logging.log_status(
                #     #     '**** Found rubric of type %s of length %s for course %s, assignment %s, submission %s, user %s'
                #     #     % (type(submission['rubric_assessment']), len(submission['rubric_assessment']), course_id, assignment_id, submission_id, submitter_id))
                #
                #     rubric_dict = submission['rubric_assessment']
                #     # rubric_element = rubric_dict[rubric_dict.keys()[0]]
                #     # if 'points' in rubric_element:
                #     #     submission_rubric_pts = rubric_element['points']
                #     # if rubric_element['comments'] is not None:
                #     #     submission_rubric_comments = rubric_element['comments']
                #
                #     # script_logging.log_status(
                #     #     '**** Found rubric points %s comments %s'
                #     #     % (submission_rubric_pts, submission_rubric_comments))
                #
                #     # 01.16.2019 tps Gather multiple rubric assessments into a flat data structure
                #     # The rubric description & ratings come from the assignment record.
                #     # The keys in the rubric assessment dictionary can be matched to IDs of
                #     # rubric objects in the assignment record.
                #     rubric_list = assignment['rubric']
                #     for rubric_id, assessment in rubric_dict.iteritems():   # Loop through assessments
                #
                #         # There might not be a "points" field in the assessment, in which case
                #         # there is nothing for us to report.
                #         if 'points' not in assessment:
                #             continue
                #
                #         # The "comments" value might be null, in which case use an empty string.
                #         rubric_assessment_comments = ''
                #         if assessment['comments'] is not None:
                #             rubric_assessment_comments = assessment['comments']
                #
                #         # Find the rubric description
                #         rubric = next(( x for x in rubric_list if x['id'] == rubric_id), None)
                #
                #         # Find the corresponding assessment rating
                #         # There may not be corresponding rating object for the points value
                #         rating = next(( x for x in rubric['ratings'] if x['points'] == assessment['points']), None)
                #         rating_description = ''
                #         if rating is not None:
                #             rating_description = rating['description']
                #
                #         rubric_assessment = (
                #             submission_id,
                #             rubric['description'],
                #             assessment['points'],
                #             rating_description,
                #             rubric_assessment_comments.encode("utf-8")
                #         )
                #         students_dict[submitter_id][DICT_KEY_RUBRIC_ASSESSMENTS].append(rubric_assessment)

                # We've found cases where the submitter is "Test Student",
                # which is a student created by Canvas for impersonation purposes.
                # Since this is not a real student, it won't be found in the student
                # collection, & it should be OK to skip these submissions.

                # We've found cases where the submitter is a student with pending
                # enrollment & the user object retrieved from Canvas doesn't 
                # have email login ID. This means it won't be found in the
                # student_dict collection, & it should be OK to skip it.

                if (submitter_id in user_lookup) and (submitter_id in students_dict):
                    submission_user = user_lookup[submitter_id]


                    submission_user_name = get_user_name(submission_user)
                    submitted_at = submission['submitted_at']
                    submission_type = submission['submission_type']
                    submission_body = submission['body']
                    if submission_body is not None:
                         # Encode weird unicode characters as utf-8
                        submission_body = submission_body.encode("utf-8")
                    submission_url = submission['url']

                    # 09.02.2017 tps
                    # Collect data for media_recording submission, which needs to be
                    # downloaded separately.
                    # Assume that all the media recordings are video/mp4 files.
                    submission_media_file = None    # Name for downloaded file
                    submission_media_type = None
                    submission_media_url = None
                    if submission_type == 'media_recording':
                        media_comment = submission['media_comment']
                        submission_media_file = media_comment['media_id'] + '.mp4'
                        submission_media_type = media_comment['media_type']
                        submission_media_url = media_comment['url']

                        # print('Submission for course %s %s, assignment %s, submission %s, user %s, type %s' % (course_id, course_name, assignment_id, submission_id, submission_user_name, submission_type))
                        # print(submission_media_file)
                        #print('media url: %s type: %s, display_name: %s' % (submission['media_comment']['url'], submission['media_comment']['media_type'], submission['media_comment']['display_name']))

                    # Gather student's submission data.
                    submission_data = (
                        submission_id,
                        submission_user_name,
                        course_name,
                        course_start_at,
                        assignment_name,
                        assignment_description,
                        submitted_at, 
                        submission_type,
                        submission_body,
                        submission_url,
                        submission_media_file,
                        submission_media_type,
                        submission_media_url,
                        submission['grade']
                        # submission_rubric_pts,
                        # submission_rubric_comments
                    )
                    students_dict[submitter_id][DICT_KEY_SUBMISSIONS].append(submission_data)

                    # Gather submission comments, if any.
                    submission_comments = submission[DICT_KEY_COMMENTS]
                    if len(submission_comments) > 0:
                        for submission_comment in submission_comments:

                            # Extract items we need to export records.
                            comment_created_at = submission_comment['created_at']
                            comment = submission_comment['comment'].encode("utf-8")

                            # 01.11.2019 tps We can always retrieve the author's name from the submission record.
                            author_user_name = submission_comment['author']['display_name']

                            # 01.11.2019 tps We'd prefer to show the user's login name, but We've seen cases where
                            # the comment author was dropped from the course,
                            # in which case there is no user record for them.
                            comment_author_id = submission_comment['author_id']
                            if comment_author_id in user_lookup:
                                commenter = user_lookup[submission_comment['author_id']]
                                author_user_name = get_user_name(commenter)
                            else:
                                script_logging.log_error('Encountered submission comment in course %s (%s), assignment %s (%s), submitted by user %s (%s) who is not enrolled in the course'
                                    % (
                                    course_name,
                                    course_id,
                                    assignment_name,
                                    assignment_id,
                                    author_user_name,
                                    comment_author_id
                                    ))

                            # commenter = user_lookup[submission_comment['author_id']]
                            # author_user_name = get_user_name(commenter)

                            # Accumulate submission comments for the student.
                            comment_data = (
                                submission_id,
                                comment_created_at,
                                comment,
                                author_user_name)
                            students_dict[submitter_id][DICT_KEY_COMMENTS].append(comment_data)


                    # Gather submission attachments, if any.
                    if 'attachments' in submission:
                        for submission_attachment in submission['attachments']:
                            # Accumulate submission attachment data for the student.

                            # 05.08.2019 tps If there is a thumbnail for the attachment, make up a name
                            # for its thumbnail file, since Canvas doesn't provide names for thumbnail files.
                            # Assume all thumbnails are PNG images.
                            thumbnail_file = None
                            if submission_attachment['thumbnail_url']:
                                thumbnail_file = 'thumb' + str(hash(submission_attachment['thumbnail_url'])) + '.png'

                            attachment_data = (
                                submission_id,
                                submission_attachment['url'],
                                submission_attachment['filename'],
                                submission_attachment['display_name'],
                                # submission_attachment['display_name'].replace('/', '%2F'),  # Some attachments have weird file names
                                submission_attachment['thumbnail_url'],
                                thumbnail_file
                            )
                            students_dict[submitter_id][DICT_KEY_ATTACHMENTS].append(attachment_data)

                            # print('attachment for course %s, assignment %s, submission %s, user %s, type %s, display name %s' % (course_name, assignment_id, submission_id, user_name, submission_type, submission_attachment['display_name']))
                            #print('attachment for course %s, assignment %s, submission %s, user %s, type %s, display name %s' % (course_name, assignment_id, submission_id, user_name, submission_type, submission_attachment['display_name']))

                    # 01.16.2019 tps Gather multiple rubric assessments into a flat data structure.
                    # The rubric description & ratings come from the assignment record.
                    # The keys in the rubric assessment dictionary can be matched to IDs of
                    # rubric objects in the assignment record.
                    if 'rubric_assessment' in submission:

                        rubric_dict = submission['rubric_assessment']
                        rubric_list = assignment['rubric']
                        for rubric_id, assessment in rubric_dict.iteritems():   # Loop through assessments

                            # There might not be a "points" field in the assessment, in which case
                            # there is nothing for us to report.
                            if 'points' not in assessment:
                                continue

                            # The "comments" value might be null, in which case use an empty string.
                            rubric_assessment_comments = ''
                            if assessment['comments'] is not None:
                                rubric_assessment_comments = assessment['comments']

                            # Find the rubric description
                            rubric = next(( x for x in rubric_list if x['id'] == rubric_id), None)

                            # Find the corresponding assessment rating.
                            # There may not be a corresponding rating object for the points value.
                            rating = next(( x for x in rubric['ratings'] if x['points'] == assessment['points']), None)
                            rating_description = ''
                            if rating is not None:
                                rating_description = rating['description']

                            rubric_assessment = (
                                submission_id,
                                rubric['description'],
                                assessment['points'],
                                rating_description,
                                rubric_assessment_comments.encode("utf-8")
                            )
                            students_dict[submitter_id][DICT_KEY_RUBRIC_ASSESSMENTS].append(rubric_assessment)

                else:
                    # Mention that we skipped a submission
                    script_logging.log_status(
                        'Skipped submission for course %s, assignment %s, submission %s, user %s'
                        % (course_id, assignment_id, submission_id, submitter_id))

        # Make a file directory to hold course data, named after the course.
        course_folder_name = os.path.join(path_consts.EXPORTS_FOLDER, course_name)
        if not os.path.isdir(course_folder_name):
            os.mkdir(course_folder_name)

        # We're ready to output all the course's student data csv files.
        for user_id, student_data in students_dict.items():
            # Each student gets their own folder, named by their user name.
            user_name = student_data[DICT_KEY_USER_NAME]
            student_folder_name = os.path.join(course_folder_name, user_name)
            if not os.path.isdir(student_folder_name):
                os.mkdir(student_folder_name)

            # Write submissions file.
            file_path = os.path.join(student_folder_name, path_consts.SUBMISSIONS_FILE_NAME)
            write_csv_file(file_path, SUBMISSION_HEADERS, student_data[DICT_KEY_SUBMISSIONS])

            # Write submission comments file.
            file_path = os.path.join(student_folder_name, path_consts.COMMENTS_FILE_NAME)
            write_csv_file(file_path, SUBMISSION_COMMENT_HEADERS, student_data[DICT_KEY_COMMENTS])

            # Write submission attachments file.
            file_path = os.path.join(student_folder_name, path_consts.ATTACHMENTS_FILE_NAME)
            write_csv_file(file_path, SUBMISSION_ATTACHMENT_HEADERS, student_data[DICT_KEY_ATTACHMENTS])

            # Write rubric assessments file.
            file_path = os.path.join(student_folder_name, path_consts.RUBRIC_ASSESSMENTS_FILE_NAME)
            write_csv_file(file_path, SUBMISSION_RUBRIC_ASSESSMENT_HEADERS, student_data[DICT_KEY_RUBRIC_ASSESSMENTS])



######### Stand-Alone Execution #########

if __name__ == "__main__":

    script_logging.clear_logs()     # Existence of error log can tell us if errors occured. 
    write_student_folders()

