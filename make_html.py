"""Create HTML page that summarizes all the student data in the artifacts export folder.
Assumes export folder populated by export_student_artifacts.py.

11.24.2016 tps
11.25.2016 tps Added make_exports_html() to create top-level HTML page.
11.25.2016 tps Added code to create HTML page for each student folder.
11.25.2016 tps Added prev/next navigation to student pages.
11.26.2016 tps Made attachment files available via HTTP links.
11.28.2016 tps Use export_student_artifacts.load_csv_files(), which returns
    rows as namedtuples, instead of local version of function.
11.29.2016 tps Use local thumbnail preview image for attachments instead of Canvas URL.
11.29.2016 tps Move HTML generation to function so this can be run from another script.
02.20.2017 tps Handle missing thumbnail preview image for attachment.
09.03.2017 tps Add column to display link to media recording submission download.
12.15.2017 tps Fix streams to handle unicode data.
08.02.2018 tps Include rubric data.
08.31.2018 tps Include submission grade data.
01.16.2019 tps Render multiple rubric assessments for a submission.
01.16.2019 tps Render the assignment description HTML.
01.16.2019 tps Omit redundant submission ID from nested comment & rubric assessment tables.
05.08.2019 tps Get name of thumbnail file from submissions list instead of call to download_attachments module.
05.08.2019 tps Display attachment file name.
"""

import cgi
# import csv
import datetime
import cStringIO
import StringIO   # For handling unicode data
import os
import io
import urllib

import export_student_artifacts
# import download_attachments
import path_consts  # Export folder location
import script_logging

#################### File Name Constants ####################

INDEX_FILE = 'index.html'

#################### Module Variables ####################

time_stamp_string = None    # Populated the 1st time write_html_time_stamp() is called.

#################### Helper Functions ####################

def get_subdirs(dir_path):
    """Return list of folders within the given directory.
    """
    return [d for d in sorted(os.listdir(dir_path)) if os.path.isdir(os.path.join(dir_path, d))]


#################### HTML Generator Functions ####################

def begin_exports_html(write_stream):
    write_stream.write('''<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Artifact Exports</title>
    <style>
<!--
.studentlist { column-count:5 }
-->        
    </style>
</head>
<body>
<H1>Artifact Exports</H1>
''')

def begin_student_html(write_stream, user_name):
    write_stream.write('''<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Export for %s</title>
    <style type="text/css">
<!--
TD { vertical-align:top }
table, td, th {
    border: 1px solid gray;
    border-collapse: collapse;
    padding: 6px; }
-->        
    </style>
</head>
<body>
<H1>Export for <SPAN STYLE="font-style:italic">%s</SPAN></H1>
''' % (user_name, user_name))


    # Give page a time stamp.
    # write_stream.write('<P>' + datetime.datetime.now().strftime('%m/%d/%Y %I:%M%p') + '</P>')

def end_html(write_stream):
    write_stream.write('''</body>
</html>
''')

def write_course_html(write_stream, course_name):
    write_stream.write('<H2>%s</H2>\n' % course_name)

def write_student_html(write_stream, user_name):
    write_stream.write('<H3>%s</H3>\n' % user_name)

def write_begin_html_table(write_stream, headers):
    # write_stream.write('<TABLE BORDER="1">\n')
    write_stream.write('<TABLE>\n')
    write_stream.write('<TR>')
    write_stream.write(''.join([ '<TH>%s</TH>' % item for item in headers]))
    write_stream.write('</TR>\n')

def write_begin_html_table_row(write_stream):
    write_stream.write('<TR>')

def write_html_table_data(write_stream, row):
    write_stream.write(''.join([ '<TD>%s</TD>' % cgi.escape(item) for item in row]))    

def write_html_table_data_as_html(write_stream, row):
    write_stream.write(''.join([ '<TD>%s</TD>' % item for item in row]))

def write_html_table_data_link(write_stream, url_link, link_text):
    if url_link != '':
        # write_stream.write('<TD><A HREF="%s">%s</A></TD>' % (url_link, url_link))
        write_stream.write('<TD><A HREF="%s">%s</A></TD>' % (url_link, cgi.escape(link_text)))
    else:
        write_html_table_data(write_stream, [''])

def write_end_html_table_row(write_stream):
    write_stream.write('</TR>\n')

def write_end_html_table(write_stream):
    write_stream.write('</TABLE>\n')

def write_html_comments_table(write_stream, comments_list):
    # Write HTML table inside an HTML table data cell.
    # 01.16.2019 tps It's OK to omit the 1st column, which contains a redundant submission ID.
    if len(comments_list) > 1:
        write_stream.write('<TD>')
        # write_begin_html_table(write_stream, comments_list[0])
        write_begin_html_table(write_stream, comments_list[0][1:])

        for row in comments_list[1:]:
            write_begin_html_table_row(write_stream)
            # write_html_table_data(write_stream, row)
            write_html_table_data(write_stream, row[1:])
            write_end_html_table_row(write_stream)

        write_end_html_table(write_stream)
        write_stream.write('</TD>')
    else:
        # There may be nothing to write.
        write_html_table_data(write_stream, [''])

def write_html_attachments_table(write_stream, attachments_list):
    """Write HTML for attachment as image link to attachment file,
    which is expected to be in the student's folder.

    attachments_list -- List containing tuples describing
        attachments for the submission. It might be empty.
    """
    if len(attachments_list) > 1:
        write_stream.write('<TD>')

        # First row of attachment list contains column headers, so skip it.
        for row in attachments_list[1:]:
            # File name might have weird characters, so URL encode it.
            encoded_file_name = urllib.quote(row.file_name)

            # Get name of attachment's thumbnail preview image, which should also be
            # in the student folder. We get it from the download_attachments module,
            # which downloaded it.
            # There may not be a thumbnail preview, in which case just use a text link.
            # 05.08.2019 tps Find thumbnail file name in the attachments list instead of having to derive it.
            write_stream.write('<DIV STYLE="margin-bottom:1em">')
            if (row.thumbnail_url):
                # thumbnail_file_name = urllib.quote(download_attachments.png_thumbnail_file_name(row.file_name))
                thumbnail_file_name = urllib.quote(row.thumbnail_file)
                write_stream.write('<A HREF="%s"><IMG SRC="%s" ALT="Attachment"></A>' % (encoded_file_name, thumbnail_file_name))
                # write_stream.write('<A HREF="%s"><IMG SRC="%s" ALT="Attachment"></A>' % (row.file_name, thumbnail_file_name))
                #write_stream.write('<video controls><source src="%s" type="video/quicktime"></video>' % row[2])
            else:
                write_stream.write('<A HREF="%s">%s</A>' % (encoded_file_name, cgi.escape(row.display_name)))
                # write_stream.write('<A HREF="%s">Attachment</A>' % encoded_file_name)
                # write_stream.write('<A HREF="%s">Attachment</A>' % row.file_name)

            write_stream.write('</DIV>')
        write_stream.write('</TD>')
    else:
        # There may be nothing to write.
        write_html_table_data(write_stream, [''])

def write_html_time_stamp(write_stream):
    """Write export time stamp.
    Time stamp string is retrieved from external file.
    Only read the file once during lifetime of this module.
    """
    global time_stamp_string
    if time_stamp_string is None:
        with open(path_consts.TIME_STAMP_FILE_NAME, 'r') as f:
            s = f.read()
            time_stamp_string = '<P>Data exported at %s</P>\n' % s
    write_stream.write(time_stamp_string)

def write_html_student_navigation(write_stream, page_index, student_list):
    """Generate home/prev/next navigation for student page.
    """
    write_stream.write('<A HREF="../../%s">Artifact Exports</A>' % INDEX_FILE)
    if (page_index > 0):
        write_stream.write(' | <A HREF="../%s/%s">Prev</A>' % (student_list[page_index - 1], INDEX_FILE))
    if page_index < (len(student_list) - 1):
        write_stream.write(' | <A HREF="../%s/%s">Next</A>' % (student_list[page_index + 1], INDEX_FILE))
    write_stream.write('\n')

def write_html_csv_links(write_stream):
    """Generate links to csv data files underlying student HTML page."""
    write_stream.write('<P><A HREF="%s">%s</A>' % (path_consts.SUBMISSIONS_FILE_NAME, path_consts.SUBMISSIONS_FILE_NAME))
    write_stream.write(' | <A HREF="%s">%s</A>' % (path_consts.COMMENTS_FILE_NAME, path_consts.COMMENTS_FILE_NAME))
    write_stream.write(' | <A HREF="%s">%s</A>' % (path_consts.RUBRIC_ASSESSMENTS_FILE_NAME, path_consts.RUBRIC_ASSESSMENTS_FILE_NAME))
    write_stream.write(' | <A HREF="%s">%s</A></P>\n' % (path_consts.ATTACHMENTS_FILE_NAME, path_consts.ATTACHMENTS_FILE_NAME))

def make_exports_html():
    """Make top-level HTML page for exports directory that contains
    links to individual student pages.
    """

    # Create HTML output stream
    html_output = cStringIO.StringIO()
    begin_exports_html(html_output)
    write_html_time_stamp(html_output)

    # Walk course folders in exports directory
    course_folder_list = get_subdirs(path_consts.EXPORTS_FOLDER)
    for course_folder in course_folder_list:
        write_course_html(html_output, course_folder)

        # Walk student folders
        html_output.write('<DIV CLASS="studentlist"><UL>\n')
        student_folders_list = get_subdirs(os.path.join(path_consts.EXPORTS_FOLDER, course_folder))
        for student_folder in student_folders_list:
            student_folder_link = urllib.quote('/'.join((course_folder, student_folder, INDEX_FILE)))
            html_output.write('<LI><A HREF="%s">%s</A></LI>\n' % (student_folder_link, student_folder))
        html_output.write('</UL></DIV>\n')
                                
    end_html(html_output)

    # We're ready to output the HTML page.
    html_file_name = os.path.join(path_consts.EXPORTS_FOLDER, INDEX_FILE)
    script_logging.log_status('Making %s' % html_file_name)
    with open(html_file_name, 'w') as ofile:
        ofile.write(html_output.getvalue())

    html_output.close() # We're done with the output buffer

def make_student_html():
    """Create HTML page for each student folder."""

    # Walk course folders in exports directory
    course_folder_list = get_subdirs(path_consts.EXPORTS_FOLDER)
    for course_folder in course_folder_list:

        # Walk student folders. Folder names are same as user names.
        course_folder_path = os.path.join(path_consts.EXPORTS_FOLDER, course_folder)
        student_folders_list = get_subdirs(course_folder_path)

        # Walk folder list by index number, so we can use index
        # to generate next/prev navigation links for each page.
        for i in range(0, len(student_folders_list)):
            student_folder = student_folders_list[i]

            # Build paths we need for the student folder.
            student_folder_path = os.path.join(course_folder_path, student_folder) 
            student_html_file = os.path.join(student_folder_path, INDEX_FILE)
            script_logging.log_status('Making %s' % student_html_file)

            # Start generating HTML for the student folder.
            # html_output = cStringIO.StringIO()
            html_output = StringIO.StringIO()   # Because cStringIO doesn't handle unicode data.
            begin_student_html(html_output, student_folder)

            # Generate navigation links
            write_html_student_navigation(html_output, i, student_folders_list)

            # Display when the data was exported.
            write_html_time_stamp(html_output)

            # Read in submission comments file.
            # We'll look for places to insert its contents as we step
            # through the submissions.
            comments_list = export_student_artifacts.load_csv_file(os.path.join(student_folder_path, path_consts.COMMENTS_FILE_NAME))

            # Read in rubric assessments file.
            # We'll look for places to insert its contents as we step
            # through the submissions.
            rubric_assessments_list = export_student_artifacts.load_csv_file(os.path.join(student_folder_path, path_consts.RUBRIC_ASSESSMENTS_FILE_NAME))

            # Read in attachments file
            # We'll look for places to insert its contents as we step
            # through the submissions.
            attachments_list = export_student_artifacts.load_csv_file(os.path.join(student_folder_path, path_consts.ATTACHMENTS_FILE_NAME))
            
            # Parse student submissions file.
            # Split list into header & data rows.
            submissions_list = export_student_artifacts.load_csv_file(os.path.join(student_folder_path, path_consts.SUBMISSIONS_FILE_NAME))
            csv_headers = submissions_list[0]
            submissions_list = submissions_list[1:]

            # The last 3 columns are for media recording fields.
            # Replace them with a single column with a link to the media recording download.
            csv_headers = csv_headers[:10]
            csv_headers.append('media_recording')

            # Add a column for attachments.
            csv_headers.append('attachments')

            # Add a column for submission comments.
            csv_headers = list(csv_headers)
            csv_headers.append('comments')

            # Add a column for grade
            csv_headers.append('grade')

            # # Add 2 columns for rubric data
            # csv_headers.append('rubric_points')
            # csv_headers.append('rubric_comments')

            # Add column for rubric assessments
            csv_headers.append('rubric_assessments')


            write_begin_html_table(html_output, csv_headers)
            for row in submissions_list:
                write_begin_html_table_row(html_output)

                # # 1st 9 elements are just data to display.
                # write_html_table_data(html_output, row[:9])

                # 1st 4 elements are just data to display.
                write_html_table_data(html_output, row[:5])

                # Next column is an HTML assignment description
                write_html_table_data_as_html(html_output, row[5:6])

                # Next 4 elements are just data to display
                write_html_table_data(html_output, row[6:9])


                # Next element is for URL submission
                write_html_table_data_link(html_output, row[9], 'Online URL')

                # # Next element is media recording id
                # write_html_table_data(html_output, [row[10]])
                
                # Next element is media recording type
                write_html_table_data_link(html_output, row[10], row[11])
                
                # # Next element is media recording url
                # write_html_table_data(html_output, [row[12]])
                
                # Look for comments & attachments for this submission in other csv files.
                submission_id = row.submission_id

                # See if there are are any attachments.
                # Doing this the dumb way, by simplying looping through
                # all attachments, looking for ones that match.
                relevant_attachments = [attachments_list[0]]  # Include column headers
                for attachment in attachments_list[1:]:     # Skip header row
                    if submission_id == attachment.submission_id:
                        relevant_attachments.append(attachment)
                write_html_attachments_table(html_output, relevant_attachments)

                # See if there are are any submissions comments.
                # Doing this the dumb way, by simply looping through
                # all submission comments, looking for ones that match.
                relevant_comments = [comments_list[0]]  # We still need the headers.
                for comment in comments_list[1:]:   # Skip header row
                    if submission_id == comment.submission_id:
                        relevant_comments.append(comment)
                write_html_comments_table(html_output, relevant_comments)

                # Next columns is for grade
                write_html_table_data(html_output, row[13:14])

                # # Next 2 columns are for rubric data
                # write_html_table_data(html_output, row[14:16])

                # 01.16.2019 tps Render rubric assessments, if any.
                # Loop through all rubric assessments, looking for ones that match.
                relevant_rubric_assessments = [rubric_assessments_list[0]]  # We still need the headers.
                for rubric_assessment in rubric_assessments_list[1:]:   # Skip header row
                    if submission_id == rubric_assessment.submission_id:
                        relevant_rubric_assessments.append(rubric_assessment)
                write_html_comments_table(html_output, relevant_rubric_assessments)

                write_end_html_table_row(html_output)
            write_end_html_table(html_output)

            write_html_csv_links(html_output)   # Add links to underlying csv files.
        
            # We're done writing HTML for one student.
            end_html(html_output)

            # Output the student HTML file.
            # with open(student_html_file, 'w') as ofile:
            with io.open(student_html_file, 'w', encoding='utf-8') as ofile:
                ofile.write(html_output.getvalue())

            html_output.close() # We're done with the output buffer

def make_index_pages():
    make_exports_html()
    make_student_html()

#################### Stand-Alone Execution ####################

if __name__ == "__main__":
    script_logging.clear_logs()
    make_index_pages()
