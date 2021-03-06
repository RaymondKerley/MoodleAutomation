from requests import get, post
import json
from dateutil import parser
import datetime
import os
import re

# Module variables to connect to moodle api:
# Insert token and URL for your site here.
# Mind that the endpoint can start with "/moodle" depending on your installation.
KEY = "8cc87cf406775101c2df87b07b3a170d"
URL = "https://034f8a1dcb5c.eu.ngrok.io"
ENDPOINT = "/webservice/rest/server.php"


def rest_api_parameters(in_args, prefix='', out_dict=None):
    """Transform dictionary/array structure to a flat dictionary, with key names
    defining the structure.
    Example usage:
    >>> rest_api_parameters({'courses':[{'id':1,'name': 'course1'}]})
    {'courses[0][id]':1,
     'courses[0][name]':'course1'}
    """
    if out_dict == None:
        out_dict = {}
    if not type(in_args) in (list, dict):
        out_dict[prefix] = in_args
        return out_dict
    if prefix == '':
        prefix = prefix + '{0}'
    else:
        prefix = prefix + '[{0}]'
    if type(in_args) == list:
        for idx, item in enumerate(in_args):
            rest_api_parameters(item, prefix.format(idx), out_dict)
    elif type(in_args) == dict:
        for key, item in in_args.items():
            rest_api_parameters(item, prefix.format(key), out_dict)
    return out_dict


def call(fname, **kwargs):
    """Calls moodle API function with function name fname and keyword arguments.
    Example:
    >>> call_mdl_function('core_course_update_courses',
                           courses = [{'id': 1, 'fullname': 'My favorite course'}])
    """
    parameters = rest_api_parameters(kwargs)
    parameters.update(
        {"wstoken": KEY, 'moodlewsrestformat': 'json', "wsfunction": fname})
    # print(parameters)
    response = post(URL+ENDPOINT, data=parameters).json()
    if type(response) == dict and response.get('exception'):
        raise SystemError("Error calling Moodle API\n", response)
    return response

################################################
# Rest-Api classes
################################################


class LocalGetSections(object):
    """Get settings of sections. Requires courseid. Optional you can specify sections via number or id."""

    def __init__(self, cid, secnums=[], secids=[]):
        self.getsections = call('local_wsmanagesections_get_sections',
                                courseid=cid, sectionnumbers=secnums, sectionids=secids)


class LocalUpdateSections(object):
    """Updates sectionnames. Requires: courseid and an array with sectionnumbers and sectionnames"""

    def __init__(self, cid, sectionsdata):
        self.updatesections = call(
            'local_wsmanagesections_update_sections', courseid=cid, sections=sectionsdata)

################################################
# Example
################################################


courseid = "2"  # Exchange with valid id.
# Get all sections of the course.
sec = LocalGetSections(courseid)

# Output readable JSON, but print only summary
#rkprint(json.dumps(sec.getsections[1]['summary'], indent=4, sort_keys=True))



# Split the section name by dash and convert the date into the timestamp, it takes the current year, so think of a way for making sure it has the correct year!
month = parser.parse(list(sec.getsections)[1]['name'].split('-')[0])
# Show the resulting timestamp
#rkprint(month)
# Extract the week number from the start of the calendar year
#rkprint(month.strftime("%V"))

#  Assemble the payload
data = [{'type': 'num', 'section': 0, 'summary': '', 'summaryformat': 1, 'visible': 1 , 'highlight': 0, 'sectionformatoptions': [{'name': 'level', 'value': '1'}]}]

# Assemble the correct summary
#summary = '<a href="https://mikhail-cct.github.io/ca3-test/wk1/">Week 1: Introduction</a><br>'

# Assign the correct summary
#data[0]['summary'] = summary

# Set the correct section number
#data[0]['section'] = 1

# Write the data back to Moodle
#sec_write = LocalUpdateSections(courseid, data)

#sec = LocalGetSections(courseid)
#rkprint(json.dumps(sec.getsections[1]['summary'], indent=4, sort_keys=True))



#Create a list of dictionaries for folders in repsitory
list_of_dicts = []
dictionary = {}
count = 0

for folder , sub_folders , files in os.walk("/workspace/MoodleAutomation"):
    if "wk" in folder:
        info = re.search(r'\d+\w*', folder)
        list_of_dicts.append(dictionary.copy())
        list_of_dicts[count]["week_number"] = info.group()
        for sub_fold in sub_folders:
            break
        for f in files:
            if f.endswith(".html"):
                list_of_dicts[count]["index"] = f
            if f.endswith(".md"):
                list_of_dicts[count]["slides"] = f
            if f.endswith(".pdf"):
                list_of_dicts[count]["pdf"] = f
        count += 1
#print(list_of_dicts)


# Update html links on Moodle
for d in list_of_dicts:
    summary = '<a href="https://mikhail-cct.github.io/ca3-test/wk{}/">Week{} Slides</a><br><a href="https://mikhail-cct.github.io/ca3-test/wk{}.pdf/">Week{} PDF</a><br>'.format(d["week_number"], d["week_number"], d["week_number"], d["week_number"])
    data[0]['summary'] = summary
    data[0]['section'] = d["week_number"]
    sec_write = LocalUpdateSections(courseid, data)


for counter in range(1,13):
    print(json.dumps(sec.getsections[counter]["sectionnum"], indent=4, sort_keys=True))
    print(json.dumps(sec.getsections[counter]["summary"], indent=4, sort_keys=True))