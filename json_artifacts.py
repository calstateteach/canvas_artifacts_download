"""Retrieve all the JSON data sets from Canvas API we'll need to archive all
student artifacts for all courses. Store the JSON data in external files for 
retrieval without having to hit Canvas API.

11.22.2016 tps
11.25.2016 tps Build file paths in a platform-independent manner.
11.27.2016 tps Fixed syntax error in time stamp log messsage.
11.28.2016 tps Added more information to logging messages for record count tests.
11.29.2016 tps Move data retrieval test into function so we can run this from other modules.\
02.20.2017 tps Rename function test_json_retrieval() to retrieve_json().
08.01.2018 tps Add optional command line parameters to download data for just specific courses.
"""

import datetime
import json
import os
import sys

import canvas_data
import script_logging

#################### File Name Constants ####################

# File names for storing JSON data sets.
JSON_FOLDER             = 'json'   # Folder to store JSON files in. Assumed to exist.
COURSES_FILE_NAME       = os.path.join(JSON_FOLDER, 'courses.json')
STUDENTS_FILE_NAME      = os.path.join(JSON_FOLDER, 'students_%s.json')    # Substitute course ID
USERS_FILE_NAME         = os.path.join(JSON_FOLDER, 'users_%s.json')       # Substitute course ID
ASSIGNMENTS_FILE_NAME   = os.path.join(JSON_FOLDER, 'assignments_%s.json') # Substitute course ID
SUBMISSIONS_FILE_NAME   = os.path.join(JSON_FOLDER, 'submissions_%s.json') # substitute assignment ID
TIME_STAMP_FILE_NAME    = os.path.join(JSON_FOLDER, 'time_stamp.txt')

#################### Helper Functions ####################

def dump_json(json_data, file_name_template, record_id, content_description):
    """Helper function to output JSON data to external file.
    json_data -- JSON collection to write to external file.
    file_name_template -- Template for building file name. Expected to contain a
        string substitution element, whose value is specified by the record_id parameter.
        e.g. 'json/students_%s.json'
    record_id -- Value to use in substitution to build output file name.
        e.g. 39310000000000056
    content_description -- String that describes the data being written to file.
        Used to create status log message.
    """
    file_name = file_name_template % (record_id)
    script_logging.log_status('Storing %s JSON to %s' % (content_description, file_name))
    with open(file_name, 'w') as f:
        json.dump(json_data, f, indent = 2)

def load_json(file_name_template, record_id):
    """Helper function to return JSON data saved to an external file.
    file_name_template -- Template for building file name. Expected to contain a
        string substitution element whose value is specified by the record_id parameter.
        e.g. 'json/students_%s.json'
    record_id -- Value to use in substitution to build output file name.
        e.g. 39310000000000056
    Returns JSON object loaded from external file.
    """
    with open(file_name_template % (record_id)) as f:
        json_data = json.load(f)
    return json_data

def make_time_stamp_file():
    """Write a small time stamp file to output directory so we know
    when this snapshot of the Canvas database was taken.
    """
    with open(TIME_STAMP_FILE_NAME, 'w') as f:
        f.write(datetime.datetime.now().strftime('%m/%d/%Y %I:%M%p'))

def get_time_stamp():
    """Retrieve time stamp string."""
    with open(TIME_STAMP_FILE_NAME, 'r') as f:
        s = f.readline()
    return s

#################### JSON Data Storage & Retrieval Functions ####################

def dump_all_json():
    """Retrieve all relevant artifact data from Canvas API & store to files.
    """

    # Set up process logging.
    # Existence of error log file can tell us if errors occur.
    script_logging.clear_status_log()
    script_logging.clear_error_log()

    # Pull list of courses
    courses = canvas_data.pull_courses()

    # If there are course ID parameters, just load the specified courses
    if len(sys.argv) > 1:
        course_id_list = map(int, sys.argv[1:])
        courses = [course for course in courses if course['id'] in course_id_list]

        # course_id = int(sys.argv[1])
        # courses = [course for course in courses if course['id'] == course_id]

    script_logging.log_status('Storing courses JSON to %s' % (COURSES_FILE_NAME))
    with open(COURSES_FILE_NAME, 'w') as f:
        json.dump(courses, f, indent = 2)
    
    for course in courses:
        course_id = course['id']

        # Pull students in each course
        students = canvas_data.pull_course_students(course_id)
        dump_json(students, STUDENTS_FILE_NAME, course_id, "course students")

        # Pull users for each course.
        # We'll need this to look up comment submitters.
        users = canvas_data.pull_course_users(course_id)
        dump_json(users, USERS_FILE_NAME, course_id, "course users")

        # pull assignments for each course
        assignments = canvas_data.pull_assignments(course_id)
        dump_json(assignments, ASSIGNMENTS_FILE_NAME, course_id, 'course assignments')

        # pull submissions for each assignment
        for assignment in assignments:
            assignment_id = assignment["id"]
            submissions = canvas_data.pull_submissions_with_comments(course_id, assignment_id)
            dump_json(submissions, SUBMISSIONS_FILE_NAME, assignment_id, 'assignment submissions')


def load_courses_json():
    with open(COURSES_FILE_NAME, 'r') as f:
        json_data = json.load(f)
    return json_data

def load_students_json(course_id):
    return load_json(STUDENTS_FILE_NAME, course_id)

def load_users_json(course_id):
    return load_json(USERS_FILE_NAME, course_id)

def load_assignments_json(course_id):
    return load_json(ASSIGNMENTS_FILE_NAME, course_id)

def load_submissions_json(assignment_id):
    return load_json(SUBMISSIONS_FILE_NAME, assignment_id)

def create_user_lookup(users_json):
    """Create a dictionary containing user profiles keyed to Canvas user ID.log_status.
    We'll need this lookup user names for submission commenters.
    users_json -- JSON collection of user profiles, as returned by load_users_json().
    Returns dictionary.

    """
    lookup_dict = {}
    for user in users_json:
        lookup_dict[user['id']] = user
    return lookup_dict

def retrieve_json():
    """Retrieve JSON data from Canvas we'll need to download student artifacts."""

    # Download the JSON files to a working directory.
    if not os.path.exists(JSON_FOLDER):
        os.makedirs(JSON_FOLDER)

    make_time_stamp_file()
    
    dump_all_json()
    
    # Report counts of what we got back.
    courses = load_courses_json()
    script_logging.log_status("Course count: %s" % len(courses))
    
    for course in courses:
        course_id = course['id']

        students = load_students_json(course_id)
        script_logging.log_status("Student count for course %s: %s" % (course_id, len(students)))
    
        users = load_users_json(course_id)
        script_logging.log_status("User count for course %s: %s" % (course_id, len(users)))

        assignments = load_assignments_json(course_id)
        script_logging.log_status("Assignment count for course %s: %s" % (course_id, len(assignments)))

        for assignment in assignments:
            assignment_id = assignment['id']
            submissions = load_submissions_json(assignment_id)
            script_logging.log_status("Submission count for assignment %s: %s" % (assignment_id, len(submissions)))

    script_logging.log_status("Time stamp: %s" % get_time_stamp())
   

######### Stand-Alone Execution #########

if __name__ == "__main__":

    # # sysarg test
    # print len(sys.argv)
    # for arg in sys.argv:
    #     print arg

    script_logging.clear_logs()
    retrieve_json()
