"""Library module containing functions to retrieve course info through Canvas API.

API reference https://canvas.instructure.com/doc/api/submissions.html
Initially hacked from https://github.com/unsupported/canvas/tree/master/api/pull_course_grades

10.15.2016 tps Created module. Using Python version 2.7.12.
10.27.2016 tps Added exception handling around API call.
11.14.2016 tps Added pull_submissions_with_comments().
11.15.2016 tps Added pull_course_info().
11.15.2016 tps Fixed query_endpoint() to handle case of single JSON object
    being returned by Canvas API instead of a collection of objects.
11.15.2016 tps Added pull_assignment_info().
11.15.2016 tps Removed pull_course_student_submissions(). Use assignments API instead.
11.17.2016 tps Added pull_user_files(user_id).
11.18.2016 tps Added pull_user_profile(user_id).
11.18.2016 tps Added pull_submission(course_id, assignment_id, user_id).
11.18.2016 tps Changed BASE_URL so endpoint names don't need to start with '/'.
11.18.2016 tps Added pull_file_(file_id).
11.22.2016 tps Added RESULTS_PER_PAGE constant.
11.22.2016 tps Added pull_course_students,
11.22.2016 tps Removed obsolete pull functions.
11.22.2016 tps Shortened names for some functions.
11.23.2016 tps Fixed wrong domain in BASE_URL.
09.14.2018 tps Query for courses list using admin level account, so we get all courses in Canvas.
"""

#import re
import requests

import script_logging

########### Endpoint constants ###########

BASE_URL = 'https://ourdomain.instructure.com/api/v1/%s'
ACCESS_TOKEN = 'SECRETSQUIRREL'
REQUEST_HEADERS = {'Authorization':'Bearer %s' % ACCESS_TOKEN}

# 01.23.2019 tps Endpoint constants for test site
# BASE_URL = 'https://yourdomain.test.instructure.com/api/v1/%s'

# Number of results to return per request.
RESULTS_PER_PAGE = 1000



######## Utility Functions ##########

def query_endpoint(endpoint, request_params = {}):
    """Helper function to retrieve list of JSON objects from Canvas API endpoint.

    endpoint - Endpoint portion of request URL.
    request_params - Dictionary containing optional query parameters for request.

    Canvas API returns paged result sets, which is useful for Web apps but not
    really necessary here. To reduce number of API calls, I specify a large number 
    of results per page.
    """

    # Build full endpoint URL
    endpoint_url = BASE_URL % endpoint

    # Specify number of results to return in each request.
    submission_params = {'per_page':RESULTS_PER_PAGE}

    # Add additional request parameters from caller
    submission_params.update(request_params)
    # for key in request_params.keys():
    #     submission_params[key] = request_params[key]

    # Return this list filled with JSON dictionaries from Canvas API call.
    resp_data = []
    
    try:
        # Results are paged, so we have to keep requesting until we get all of them.
        while 1:
            resp = requests.get(endpoint_url, params=submission_params, headers=REQUEST_HEADERS)
            # print(resp.url)

            # The response might be a list of JSON dictionaries or it may be a single 
            # JSON dictionary. If we have a list, we want to concatenate it to the 
            # result list. If we have a single JSON dictionary, we want to append it
            # to the result list.
            resp_json = resp.json()
            if isinstance(resp_json, list):
                resp_data += resp_json
            else:
                resp_data.append(resp_json)

            # print "data count after page: %s" % len(resp_data)
            if 'next' in resp.links.keys():
                endpoint_url = resp.links['next']['url']
                # print endpoint_url
            else:
                break

    # If something bad happens while accessing Canvas API,
    # record the offending endpoint for debugging purposes.
    # A request error is catastrophic & there is no point in trying to continue.
    except Exception as e:
        script_logging.log_error('Error making API request at: ' + endpoint_url)
        script_logging.log_error('Error object: ' + str(e))
        raise

    return resp_data


######## Data Entity Retrieval ##########

def pull_courses():
    """Retrieve list of JSON objects describing all the courses."""
    # return query_endpoint('courses')
    return query_endpoint('accounts/1/courses')


def pull_assignments(course_id):
    """Retrieve list containing JSON assignment description for a given course."""
    return query_endpoint('courses/%s/assignments' % (course_id))


def pull_submissions(course_id, assignment_id):
    """Retrieve list containing JSON submissions for specific course assignment."""
    return query_endpoint('courses/%s/assignments/%s/submissions' % (course_id, assignment_id))

def pull_submissions_with_comments(course_id, assignment_id):
    """Retrieve list containing JSON submissions with comments for specific course assignment.
    08.01.2018 tps Include rurbric data.
    """
    # submission_params = {
    #     # 'include[]':'submission_comments'
    #     'include[]': ['submission_comments', 'rubric_assessment']
    # }
    # return query_endpoint('courses/%s/assignments/%s/submissions' % (course_id, assignment_id), submission_params)

    """ 01.23.2019 tps Retrieve submission data with query that includes submissions from inactive students.
    """
    submission_params = {
        'include[]': ['submission_comments', 'rubric_assessment'],
        'student_ids[]': ['all'],
        'assignment_ids[]': [assignment_id]

    }
    json_resp = query_endpoint('courses/%s/students/submissions' % course_id, submission_params)

    """ If the assignment happens to have no submissions, the API response will be a structure like this:
    [
      {
        "error": "invalid assignment ids requested"
      }
    ]
    
    In this case, it's appropriate to return an empty list.
    """

    if (len(json_resp) > 0) and (json_resp[0].get('error') == "invalid assignment ids requested"):
        return []
    else:
        return json_resp

def pull_course_users(course_id):
    """Retrieve list of JSON users in a course."""

    # 01.24.2019 tps We want to report on inactive students as well.
    request_params = { 'enrollment_state[]': ['active', 'invited', 'inactive'] }
    return query_endpoint('courses/%s/users' % (course_id), request_params)

    # return query_endpoint('courses/%s/users' % (course_id))


def pull_course_students(course_id):
    """Retrieve list of JSON users who are students enrolled in course."""

    # We just want to see the students
    request_params = {'enrollment_type[]':'student'}

    # 01.23.2019 tps We want to see inactive students as well
    # But API still doesn't retrieve submissions for inactive students.
    request_params = {
        'enrollment_type[]': 'student',
        'enrollment_state[]': ['active', 'invited', 'inactive']
    }

    return query_endpoint('courses/%s/users' % (course_id), request_params)
    
    # # Include pending students
    # request_params = { 'type[]': 'StudentEnrollment' }
    # student_enrollments = query_endpoint('courses/%s/enrollments' % (course_id), request_params)
    # return [enrollment['user'] for enrollment in student_enrollments]

 
def pull_course_info(course_id):
    """Retrieve JSON information for one specific course.
    course_id -- Canvas API internal course ID as a numeric value.
    """

    return query_endpoint('courses/%s' % (course_id))

    
def pull_assignment_info(course_id, assignment_id):
    """Retrieve JSON information for one specific assignment."""
    return query_endpoint('courses/%s/assignments/%s' % (course_id, assignment_id))


def pull_user_files(user_id):
    """Retrieve JSON describing a user's file uploads."""
     
    # Include the user information.
    #request_params = { 'include[]':'usage_rights' } 
    # request_params = { 'include[]':'user' }
    return query_endpoint('users/%s/files/' % (user_id))


def pull_user_profile(user_id):
    """Retrieve user profile for specified user ID."""
    return query_endpoint('users/%s/profile/' % (user_id))


def pull_submission(course_id, assignment_id, user_id):
    """Retrieve JSON for a single submission."""
    request_params = {'include[]':['submission_history', 'submission_comments']}
    return query_endpoint('courses/%s/assignments/%s/submissions/%s' % (course_id, assignment_id, user_id), request_params)


def pull_file(file_id):
    """Retrieve JSON for a single file upload."""
    return query_endpoint('files/%s' % (file_id))
