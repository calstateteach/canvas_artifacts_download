# Canvas Artifact Downloads

This repository contains Python scripts for exporting student artifacts from [Canvas](https://www.instructure.com/canvas/)  using the [Canvas API](https://canvas.instructure.com/doc/api/index.html).

## Script Files Overview
The process of extracting student artifact data from the Canvas API & exporting it to student folders happens in several steps. Each step is performed by its own Python script & relies on the artifacts produced by a previous script. In brief:

1. *json\_artifacts.py* -- Download course & student data from Canvas API.
2. *export\_student\_artifacts.py* -- Parse data into student folders.
3. *download\_attachments.py* -- Download submission attachment files.
4. *download\_media\_recordings.py* -- Download submission media recordings.
5. *make\_html.py* -- Generate HTML page for each student.
6. *retry\_download_errors.py* -- Retry file downloads that generated errors.

The script *run_all.py* executes all these scripts in sequence.

The script *run_no_dl.py* executes all these in sequence but skips steps that download attachments & media recordings, to make getting to HTML pages faster. Used for testing.

### *json_artifacts.py*
Python script that pulls all the needed course & student data from the Canvas API & stores it as text files containing JSON data. The data files are written to a directory called *json* in the same folder as the script. The script will attempt to create the *json* folder if it does not already exist. To get to the student submissions using the Canvas API, you navigate down a hierarchy where courses contain assignments, assignments contain submissions, & submissions contain comments & attachments.

```
courses
  |  
  +---assignments
        |
        +---student submission
              |
              +---comments
              |
              +---attachments
```
The script generates the following files:

* *courses.json* -- List of all courses.
* *assignments_&lt;course ID\>.json* -- List of assignment for a particular course.
* *submissions_&lt;assignments ID>.json* -- List of submissions for a particular assignment. This data also contains sublists of comments & attachments for the submission.
* *students_&lt;course ID>.json* -- List of students enrolled in a particular course.
* *users_&lt;course_ID>.json* -- List of users associated with the course. This is needed to lookup the teachers who provided comments on the submissions.
*  *time_stamp.txt* -- Text file containing a human-readable time stamp indicating when the data extract was done.

Though the script runs stand-alone, it is also used by other scripts as a module import containing functions for retrieving JSON data out of the saved files.

The script accepts one or more course IDs as command line arguments. If course ID parameters are found, the script only downloads data for the specified courses. This is useful during development to avoid having to download all the data each time.

### *export_student_artifacts.py*
While the Canvas API groups the submissions from all students  under each assignment, we want to put each student's data in its own folder. This script iterates over the JSON data extracted by *json_artifacts.py* & creates individual course & student folders for the data. A folder for each course is created under a folder called *exports/* in the same folder as the script. The script will attempt to create the *exports/* folder if it does not already exist. The script then creates a folder for each student in each course directory.

```
/exports/
  |  
  +---/course 101/ 
  |     |
  |     +---/student Alice/
  |     |     |
  |     |     +---submissions.csv
  |     |     +---comments.csv
  |     |     +---attachments.csv
  |     |
  |     |
  |     +---/student Bob/
  |     :     |
  |           +---submissions.csv
  |           +---comments.csv
  |           +---attachments.csv
  |
  |
  +---/course 102/ 
  :     |
        +---/student Edgar/
        |     |
        |     +---submissions.csv
        |     +---comments.csv
        |     +---attachments.csv
        |
        |
        +---/student Fran/
        :     |
              +---submissions.csv
              +---comments.csv
              +---attachments.csv
```
The data files in each student folder are comma-delimited data files. They each start with a header row describing the columns.

#### Data in *submissions.csv*:
Each row contains data about one of the student's submissions to an assignment. A student may have no submissions for an assignment at all. The columns are:

|Column|Description|
|------|-----------|
|submission_id|Canvas ID for submission.|
|user_name|Student's user name, derived from their login ID.|
|course_name|Course name.|
|course_start_at|Course's start date, in ISO format.|
|assignment_name|Assignment label.|
|assignment_description|Assignment prompt.|
|submitted_at|When the student made the submission, in ISO format.|
|submission_type|The type of submission. May be a text entry, a URL to an on-line app, a file upload, or none. File uploads have associated entries in the *attachments.csv* file.|
|submission_body|The text of a text entry submission.|
|submission_url|The URL of a URL submission.|
|media_file|If the submission type is "media_recording", this is an internal Canvas file name for the media file.|
|media_type|If the submission type is "media_recording", this is the type of media file. All the current submissions are of type "video".|
|media_url|If the submission type is "media_recording", this is the URL from which to download the media file.|
|rubric_points|Rubric assessment points, if any.|
|rubric_comments|Rubric assessment comments, if any.|


#### Data in *comments.csv*:
Each row contains data for a submission comment. A submission may have multiple comments. The columns are:

|Column|Description|
|------|-----------|
|submission_id|ID of associated submission.|
|created_at|When the comment was submitted, in ISO format.|
|comment|Text of the comment.|
|user_name|Commenter's user name, derived from their login ID.|

#### Data in *attachments.csv*:
Each row contains data describing an attachment file for a submission. A submission may have multiple attachments. The columns are:

|Column|Description|
|------|-----------|
|submission_id|ID of associated submission.|
|url|URL from which the file can be retrieved. A download of this file is required for the student archive.|
|file_name|Attachment's file name. Downloaded file is saved with this name. The names sometimes have characters that seem to have been URL encoded through 3 generations, e.g. *1504325580_537_Copy%252Bof%252BActivity%252B1.01.pptx*|
|display_name|Attachment's display name.|
|thumbnail_url|URL returning a thumbnail preview image for the attachment. The URL is suitable as an image source for an HTML  &lt;IMG&gt; tag.|

The time stamp file *time_stamp.txt* is also included in the *exports* folder.

Though the script runs stand-alone, it is also used by other scripts as a module import containing functions for retrieving data out of the CSV files.

### *download_attachments.py*
This script traverses all the student folders & downloads the student's submission attachments to the folder. After this is run, each student folder contains an archive of the student's submissions. In a trial run, the script retrieved 848 image & movie files, totaling about 4.6GB, in about 3 hours.

Each attachment file also has a preview thumbnail image associated with it, which can be displayed as an image source for an HTML &lt;IMG&gt; tag. 
In order to make the HTML pages created in the next step completely self-contained, this thumbnail image is also downloaded to the student folder. However, the Canvas API does not expose the content type or file name for the image. This script assumes thumbnails are always PNG files & creates a file name for a thumbnail from a hash of its URL.

Though the script runs stand-alone, it is also used by other scripts as a module import containing the function for deriving the file name of a downloaded thumbnail image.

### *download_media_recordings.py*
This script traverses all the student folders, looking for submissions of type "media_recording" to download. After this is run, each student folder contains an archive of the student's media recording submission files. Currently, these are all video/mp4 files.

### *make_html.py*
This script generates HTML pages displaying a navigable view of all the exported data. The top-level page is an *index.html* file in the *exports* folder. It contains links to *index.html* pages in each of the individual student folders. The student's submission data is displayed in a table with links to online URL submissions & to the downloaded attachment files.

### *retry_download_errors.py*
This script parses the *err.txt* file for file download errors & tries downloading the files again. This is useful because network connection errors can occur during long download runs. The script overwrites the *err.txt* file after parsing it, so a copy of the current err.txt file is saved to files named liked *retry###.txt* before the downloads are started.

## Helper Modules

These Python modules containing various utility functions:

* *canvas_data.py* -- Contains functions wrapping Canvas API calls.
* *http_downloader.py* -- Contains functions that download Canvas student submissions & attachment files from URLs.
* *path_consts.py* -- Shared path & file names for the artifact export files.
* *script_logging.py* -- Simple logging module that writes status messages to *log.txt* & *err.txt* for debugging & diagnostics.

## Dependencies

* *[requests](https://2.python-requests.org/)* Python library
* *[unicodecsv](https://github.com/jdunck/python-unicodecsv)* Python library

## Authors

* **Terence Shek** - *Programmer* - [tpshek](https://github.com/tpshek/)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
