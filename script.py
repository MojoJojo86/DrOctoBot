import mechanicalsoup
import datetime
import bs4
from bs4 import BeautifulSoup
import smtplib
from string import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


#My Data File
import config

# Creates and sets the d variable as the current date today. The formats it below into the format I need for using in the API call. This could probably be minimised tbh.
d = datetime.datetime.today()
dateToday = d.strftime("%d-%B-%Y")

# Create Stateful browser instance from mechanical soup
browser = mechanicalsoup.StatefulBrowser()

# Open browser at the requested URL
browser.open(config.url)

# Only 1 form on page i.e. Login Form. Enter the username and password into these and submit.
browser.select_form('form')
browser["username"] = config.username
browser["password"] = config.password
resp = browser.submit_selected()

# Set variable page as an instance of the current page after login.
#page = browser.get_current_page()

# Dictionary containing all the doctors to request and their id codes. I've tried to keep the list alphebeticalised.
doctors = {
    'AD': 90,
    'BF': 17,
    'CB': 22,
    'CJF': 28,
    'CMB': 147,
    'JEM': 15,
    'JL': 42,
    'KSD': 26,
    'LD': 82,
    'MCW': 38,
    'MQH': 29,
    'MYA': 43,
    'OPP': 18,
    'OSD': 56,
    'PMF': 11,
    'RC': 59, 
    'SDP': 13,
    'SJC': 23,
    'TD': 46,
    'VS': 124,
    'VW': 83
}

# Dictionary containing all the data that will be passed with the POST request.
data = {
    'date': '30/01/2018',#dateToday,
    'options': 13,
    'locations': "All Locations",
    'sites': "All Sites"
}

scheduleData = {}

# Creation and setting of the API_ENDPOINT variable which consists of the url + the POST endpoint extras added on.
API_ENDPOINT = config.url + "/schedule/xml/"

# Perform POST request passing the API_ENDPOINT and the data dictionary.
# Set the text of the response to the response variable
r = browser.post(url = API_ENDPOINT, data = data)
response = r.text

# Parse the response data using BeautifulSoup. I realise this is a dependency of MechanicalSoup so this probably isn't required to be imported as an additional module but hey :P
soup = BeautifulSoup(response, "html.parser")

# Response contains CDATA section so this pulls all the data that is in the CDATA tags out as a string and stores in info variable.
info = soup.find(text=lambda tag: isinstance(tag, bs4.CData)).string.strip()

# Parses the info string containing the CDATA into html using BeautifulSoup so I can call against it with the find and find_all commands.
items = BeautifulSoup(info, "html.parser")

# Finds the first schedule object. This is what I wanted as the first object is of the current day the code is being ran.
schedule = items.find("div", class_="schedule")

# Creates and stores all instances of the required info from the schedule object.
times = schedule.find_all("div", class_="time")
hospital = schedule.find_all("div", class_="itemLocation")
location = schedule.find_all("span", class_="detailsleft")

# While loop to go through each instance of all the arrays. 
print(dateToday)
i = 0
while i < len(hospital):
    if hospital[i].text != 'ABSENT':
        #print(times[i].text + "   " + hospital[i].text + "   " + location[i-1].text)
        scheduleData['time'] = times[i].text
        scheduleData['hospital'] = hospital[i].text
        scheduleData['location'] = location[i-1].text
    elif hospital[i].text == 'ABSENT':
        #print(hospital[i].text)
        scheduleData['hospital'] = hospital[i].text
    i = i + 1

# SUDO Make the code perform multiple POST requests, one for each doctor. This data dictionary value for the doctor will change eachtime based on an array of doctor IDs

print(scheduleData)

# Function to get list of names and contacts from file
def get_contacts(filename):
    names = []
    emails = []
    with open(filename, mode='r', encoding='utf-8') as contacts_file:
        for a_contact in contacts_file:
            names.append(a_contact.split()[0])
            emails.append(a_contact.split()[1])
    return names, emails

# Function to get the msg template from file
def read_template(filename):
    with open(filename, 'r', encoding='utf-8') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)

# Login to the email server to send emails
def send_email():
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(config.email, config.emailPass)

    # Get the names, emails and template from files
    names, emails = get_contacts('contacts.txt')
    message_template = read_template('scheduletemplate.txt')

    for name, email in zip(names, emails):
        msg = MIMEMultipart() # Create a message

        # Add the persons name to the actual email replacing the PERSON_NAME template string
        message = message_template.substitute(PERSON_NAME=name.title())


        # Set email parameters
        msg['From'] = config.email
        msg['To'] = email
        msg['Subject'] = "Dr Schedule for " + dateToday

        # Add the message to the body
        msg.attach(MIMEText(message, 'plain'))

        server.send_message(msg)

        del msg

    server.quit()

#send_email()
