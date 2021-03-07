from requests import get, post
import json
from dateutil import parser
import datetime
import os
import re
import bs4
import requests

# Module variables to connect to moodle api:
# Insert token and URL for your site here.
# Mind that the endpoint can start with "/moodle" depending on your installation.
KEY = "8cc87cf406775101c2df87b07b3a170d"
URL = "https://034f8a1dcb5c.eu.ngrok.io"
ENDPOINT = "/webservice/rest/server.php"


def rest_api_parameters(in_args, prefix='', out_dict=None):
    """Transform blank_dictionary_1/array structure to a flat blank_dictionary_1, with key names
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









# Set our Course ID
courseid = "2"  

# Get all sections of the course.
sec = LocalGetSections(courseid)




# Split the section name by dash and convert the date into the timestamp, it takes the current year, so think of a way for making sure it has the correct year!
month = parser.parse(list(sec.getsections)[1]['name'].split('-')[0])
# Show the resulting timestamp
#rkprint(month)
# Extract the week number from the start of the calendar year
#rkprint(month.strftime("%V"))

#  Assemble the payload
data = [{'type': 'num', 'section': 0, 'summary': '', 'summaryformat': 1, 'visible': 1 , 'highlight': 0, 'sectionformatoptions': [{'name': 'level', 'value': '1'}]}]



#############################################################
### Create a list of dictionaries for folders in repository
#############################################################

list_of_folder_dictionaries = [] #Create an empty list to add our folder dictionaries to
counter_1 = 0 #Create counter for the indices of our list

for folder, sub_folders, files in os.walk(os.getcwd()):   #Walk through folders and files in the current directory ("/workspace/MoodleAutomation")
    if "wk" in folder:
        info = re.search(r'\d+\w*', folder) #Search each folder for the wk number
        list_of_folder_dictionaries.append({}) #If we find a new wk number, add a blank dictionary to the list 
        list_of_folder_dictionaries[counter_1]["week_number"] = info.group() #Assign the value to the "week number" key in the dictionary
        for sub_fold in sub_folders:
            break #We will not have subfolders
        for f in files:
            if f.endswith(".html"): 
                list_of_folder_dictionaries[counter_1]["index"] = f #If the file is a .html, assign that value to the "index" key in the dictionary
            if f.endswith(".md"):
                list_of_folder_dictionaries[counter_1]["slides"] = f #If the file is a .md, assign that value to the "slides" key in the dictionary
            if f.endswith(".pdf"):
                list_of_folder_dictionaries[counter_1]["pdf"] = f #If the file is a .pdf, assign that value to the "pdf" key in the dictionary
        counter_1 += 1 #Increase the counter by 1 to track the indices of our list

#print(list_of_folder_dictionaries)



#############################################################
### Create list of dictionaries with hash and date of videos
#############################################################

list_of_video_dictionaries = [] #Create an empty list to add our video dictionaries to
counter_2 = 0 #Create counter for the indices of our list

base_url = "https://drive.google.com/drive/folders/1pFHUrmpLv9gEJsvJYKxMdISuQuQsd_qX" #Address of the website hosting our videos
res = requests.get(base_url) #Grab html data from the webpage
soup = bs4.BeautifulSoup(res.text, "lxml") #Make the result readable using BeautifulSoup
videos = soup.find_all('div',class_ = 'Q5txwe') #Find all data for class = 'Q5txwe' only

for video in videos: #iterate through data from each video found in the class = 'Q5txwe
    list_of_video_dictionaries.append({}) #Add a new dictionary to the list each time we find a new video
    video_id = video.parent.parent.parent.parent.attrs['data-id'] #Get the hash for each video
    list_of_video_dictionaries[counter_2]["hash"] = video_id #Assign the hash to the "hash" key in the dictionary
    date = re.search(r'\d{4}-\d{2}-\d{2}', str(video)) #Get the date of each video
    list_of_video_dictionaries[counter_2]["date"] = date.group() #Assign the date to the "date" key in the dictionary
    counter_2 += 1 #Increase the counter by 1 to track the indices of our list

#print(list_of_video_dictionaries)


################################
### Update html links on Moodle
################################

for d in list_of_folder_dictionaries: 
    summary = '<a href="https://mikhail-cct.github.io/ca3-test/wk{}/">Week{} Slides</a><br><a href="https://mikhail-cct.github.io/ca3-test/wk{}.pdf/">Week{} PDF</a><br>'.format(d["week_number"], d["week_number"], d["week_number"], d["week_number"])
    data[0]['summary'] = summary
    data[0]['section'] = d["week_number"]
    sec_write = LocalUpdateSections(courseid, data)


#for counter_1er in range(1,13):
    #print(json.dumps(sec.getsections[counter_1er]["sectionnum"], indent=4, sort_keys=True))
    #print(json.dumps(sec.getsections[counter_1er]["summary"], indent=4, sort_keys=True))


    

#https://drive.google.com/file/d/