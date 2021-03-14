from requests import get, post
import json
from dateutil import parser
import datetime
import os
import re
import bs4
import requests
from dateutil.relativedelta import relativedelta



# Module variables to connect to moodle api:
# Insert token and URL for your site here.
# Mind that the endpoint can start with "/moodle" depending on your installation.
KEY = "bc7ad59923ad95f17dd955868790ccb5"
URL = "http://f0ae7213ef73.eu.ngrok.io/"
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




############################################################
### Setup
############################################################



courseid = "7"  # Set our Course ID
sec = LocalGetSections(courseid) # Get all sections of the course.
data = [{'type': 'num', 'section': 0, 'summary': '', 'summaryformat': 1, 'visible': 1 , 'highlight': 0, 'sectionformatoptions': [{'name': 'level', 'value': '1'}]}] #  Assemble the payload



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
    video_date = re.search(r'\d{4}-\d{2}-\d{2}', str(video)) #Get the date of each video
    video_date = video_date.group() #Take the date string only
    video_date = datetime.datetime(*(int(s) for s in video_date.split('-'))) #Convert date string to datetime class
    list_of_video_dictionaries[counter_2]["date"] = video_date #Assign the date to the "date" key in the dictionary
    counter_2 += 1 #Increase the counter by 1 to track the indices of our list



#############################################################################
### Compare date of video to week name and add the video to the correct week
#############################################################################



list_of_datetime_dictionaries = [{}] #Create a list with one empty dictionary in it. Used to add our datetime dictionaries
counter_3 = 0 #Create counter for the indices of our list

for j in range(1,26): 
    list_of_datetime_dictionaries.append({}) #Add a new dictionary to the list each time we find a new video
    week_start = parser.parse(list(sec.getsections)[j]['name'].split('-')[0]) # Split the section name by dash and convert the date into the timestamp, and set as start date
    week_end = parser.parse(list(sec.getsections)[j]['name'].split('-')[1]) # Split the section name by dash and convert the date into the timestamp, and set as end date
    if week_start > datetime.datetime(2021,8,1): #Check to see if start date is after August 1st
        week_start -= relativedelta(years=1) #If it is, deduct a year from the start date to ensure we are dealing with the correct year
    if week_end > datetime.datetime(2021,8,1): #Check to see if end date is after August 1st
        week_end -= relativedelta(years=1) #If it is, deduct a year from the end date to ensure we are dealing with the correct year
    list_of_datetime_dictionaries[counter_3]["start_date"] = week_start #Add the start date to the list of dictionaries
    list_of_datetime_dictionaries[counter_3]["end_date"] = week_end #Add the end date to the list of dictionaries
    counter_3 += 1 #Increase the counter by 1 to track the indices of our list



############################################
### Update html links on Moodle
############################################



for d in list_of_folder_dictionaries: 
    summary = '<a href="https://mikhail-cct.github.io/ca3-test/wk{wk}/">Week {wk} Slides</a><br><a href="https://mikhail-cct.github.io/ca3-test/wk{wk}.pdf/">Week {wk} PDF</a><br>'.format(wk =d["week_number"])
    data[0]['summary'] = summary #set the summary variable as the html text we want to write to our Moodle page 
    data[0]['section'] = d["week_number"] #Set the week number, to update the correct week
    sec_write = LocalUpdateSections(courseid, data) #Write the new information to our Moodle page



############################################
### Update videos on Moodle
############################################


week_counter = 1 #Create a counter to track the week number we are looking at
video_counter = 1 #Create a counter to track the video we are looking at

'''
for video in videos: #Loop through each of the videos on the Google drive
    while True: 
        #Check if the date of the video falls between the start date and end date of a Week number on Moodle
        if list_of_video_dictionaries[week_counter]["date"] >= list_of_datetime_dictionaries[video_counter]["start_date"] and list_of_video_dictionaries[week_counter]["date"] <= list_of_datetime_dictionaries[video_counter]["end_date"]:
            # summary = sec.getsections[week_counter]["summary"] # Temporarily hold the current Moodle summary in this variable
            # if list_of_video_dictionaries[week_counter]["hash"] not in summary: #Check if the video has already been added to Moodle
            # #If not, update the summary variable to include the video link
            #     summary +='<a href="https://drive.google.com/file/d/{hash}/">Week {wk} Video</a><br>'.format(hash = list_of_video_dictionaries[week_counter]["hash"], wk = week_counter)
            data[0]['summary'] = '' #Set the section summary to blank so we can clear the summary details on Moodle
            data[0]['section'] = week_counter #Set the week number
            sec_write = LocalUpdateSections(courseid, data) #Write to Moodle to clear each of the section summaries
            #data[0]['summary'] = summary #Set the section summary the new summary so we can update the summary details on Moodle
            #sec_write = LocalUpdateSections(courseid, data) #Write to Moodle to update each of the section summaries
            break #Break from the While loop
        elif video_counter == len(videos): #Break from the While loop if we have visited each of the videos
            break #Break from the While loop
        else:
            video_counter += 1 #Increase the video counter so we can check each video in each week.
    if week_counter < 17: #Exit the loop if we have reached the last week of the semester.
        week_counter +=1 #Increase the week counter so we can check each video in each week.
'''


for video in videos: #Loop through each of the videos on the Google drive
    while True: 
        #Check if the date of the video falls between the start date and end date of a Week number on Moodle
        if list_of_video_dictionaries[week_counter]["date"] >= list_of_datetime_dictionaries[video_counter]["start_date"] and list_of_video_dictionaries[week_counter]["date"] <= list_of_datetime_dictionaries[video_counter]["end_date"]:
            summary = sec.getsections[week_counter]["summary"] # Temporarily hold the current Moodle summary in this variable
            if list_of_video_dictionaries[week_counter]["hash"] not in summary: #Check if the video has already been added to Moodle
            #If not, update the summary variable to include the video link
                summary +='<a href="https://drive.google.com/file/d/{hash}/">Week {wk} Video</a><br>'.format(hash = list_of_video_dictionaries[week_counter]["hash"], wk = week_counter)
            data[0]['summary'] = '' #Set the section summary to blank so we can clear the summary details on Moodle
            data[0]['section'] = week_counter #Set the week number
            sec_write = LocalUpdateSections(courseid, data) #Write to Moodle to clear each of the section summaries
            data[0]['summary'] = summary #Set the section summary the new summary so we can update the summary details on Moodle
            sec_write = LocalUpdateSections(courseid, data) #Write to Moodle to update each of the section summaries
            break #Break from the While loop
        elif video_counter == len(videos): #Break from the While loop if we have visited each of the videos
            break #Break from the While loop
        else:
            video_counter += 1 #Increase the video counter so we can check each video in each week.
    if week_counter < 12: #Exit the loop if we have reached the last week of the semester.
        week_counter +=1 #Increase the week counter so we can check each video in each week.
