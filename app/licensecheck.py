#########################################################################
#
# Copyright 2020 Mitchell Wyatt
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#########################################################################

from webexteamssdk import WebexTeamsAPI
import logging
import requests
import json
import time
import datetime

global scriptVersion
scriptVersion = "2.2.1"

# Create static variables - Unless the Webex Teams API endpoints change, these shouldn't need updating.
apiMessage = "https://webexapis.com/v1/messages"
apiToken = "https://webexapis.com/v1/access_token"
apiEvents = "https://webexapis.com/v1/events"

# Logging, token and webexinfo path.
global workdir
workdir = "./persist"

# Setup Logging
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
def setup_logger(name, log_file, level):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

# Create Webex Bot Reporting
def ReportToSpace(ReportMessage):
    encodedReport = str(repr(ReportMessage.encode('ascii', errors='ignore'))[2:-1])
    payload = "{\"roomId\" : \"" + \
        str(SpaceID) + "\",\"text\" : \"" + str(encodedReport) + "\"}"
    headers = {
        'Authorization': "Bearer "+str(BotAuthToken),
        'Content-Type': "application/json",
        'cache-control': "no-cache",
    }
    response = requests.post(apiMessage, data=payload, headers=headers)
    logging.info(f"Message reported to space: {encodedReport} - {response.status_code}")

# Token Management
def do_getTokens():
    logging.info("Checking to see if we have the latest Access Token.")
    with open(str(workdir)+"/tokens.json", "r") as token_store:
        tokens_dict = json.load(token_store)
    global accessToken
    accessToken = (tokens_dict["access_token"])
    global refreshToken
    refreshToken = (tokens_dict["refresh_token"])
    try:
        tokenIssued = (tokens_dict["issued_on"])
    except:
        tokenIssued = 0
    token_store.close()
    token_age = int(epoch_time) - int(tokenIssued)
    logging.info(f"The access token age is: {datetime.timedelta(seconds=token_age)}")
    if token_age > 259200:
        logging.info(
            "The access token is a little stale, refreshing it now..")
        headers = {'cache-control': 'no-cache', 'accept': 'application/json',
                   'content-type': 'application/x-www-form-urlencoded'}
        data = ("grant_type=refresh_token&client_id={0}&client_secret={1}&refresh_token={2}").format(
            ClientID, ClientSecret, refreshToken)
        response = requests.post(apiToken, headers=headers, data=data)
        tokenResponse = response.json()
        tokens_dict["issued_on"] = str(epoch_time)
        tokens_dict["access_token"] = str(tokenResponse["access_token"])
        tokens_dict["refresh_token"] = str(tokenResponse["refresh_token"])
        token_store = open(str(workdir)+"/tokens.json", "w+")
        token_store.write(json.dumps(tokens_dict))
        accessToken = (tokens_dict["access_token"])
        refreshToken = (tokens_dict["refresh_token"])
        token_store.close()
        logging.info(
            "Done! The access token has been refreshed. Getting back to work.")
    else:
        logging.info(
            "The access token looks daisy fresh.. continuing on with the license reconciliation process.")

# Import configurable variables from webexinfo.json file.
def importvars():

    #Import vars
    with open(str(workdir)+"/webexinfo.json", "r") as vars_store:
        vars_dict = json.load(vars_store)

    global ClientID
    global ClientSecret
    global BotID
    global BotAuthToken
    global SpaceID
    global studentMail
    global facultyMail
    global processInterval
    global timediff
    global adminaccount
    global action
    global harmless
    global loglevel

    ClientID = (vars_dict["ClientID"])
    ClientSecret = (vars_dict["ClientSecret"])
    BotID = (vars_dict["BotID"])
    BotAuthToken = (vars_dict["BotAuthToken"])
    SpaceID = (vars_dict["SpaceID"])
    studentMail = (vars_dict["studentMail"])
    facultyMail = (vars_dict["facultyMail"])
    processInterval = int((vars_dict["processInterval"]))
    adminaccount = (vars_dict["adminaccount"])
    action = (vars_dict["action"])
    harmless = (vars_dict["harmless"])
    loglevel = (vars_dict["loglevel"])

    # Validate loglevel
    if loglevel == "INFO":
        pass
    elif loglevel == "DEBUG":
        pass
    else:
        raise Exception("Loglevel not defined as INFO or DEBUG.")

    # Validate action
    if action == "update":
        pass
    elif action == "delete":
        pass
    else:
        raise Exception("Action not defined as update or delete.")

    # Validate harmless
    if harmless == "no":
        pass
    elif harmless == "yes":
        pass
    else:
        raise Exception("Harmless not defined as yes or no.")

# Import processes to take action on from process.json
def importprocesses():

    #Import processes
    with open(str(workdir)+"/process.json", "r") as vars_store:
        vars_dict = json.load(vars_store)

    global processlicenses
    global harmlesslicenses

    processlicenses = (vars_dict["processlicenses"])
    harmlesslicenses = (vars_dict["harmlesslicenses"])

    # Validate process licensess
    if processlicenses == "no":
        pass
    elif processlicenses == "yes":
        pass
    else:
        raise Exception("Process License not defined as yes or no.")

    # Validate harmless license
    if harmlesslicenses == "no":
        pass
    elif harmlesslicenses == "yes":
        pass
    else:
        raise Exception("Harmless license not defined as yes or no.")

# Import license lists
def importlicenses():

    #Import vars
    with open(str(workdir)+"/licenses.json", "r") as vars_store:
        vars_dict = json.load(vars_store)

    global employeeLics
    global studentLics

    employeeLics = (vars_dict["employee"])
    studentLics = (vars_dict["student"])

def updatetime():
    # Create or update runtime variables
    global timediff
    global epoch_time
    global today
    global eventtime
    # There is a better way to do this timediff.
    # For now this fixed number (seconds) should be equal to or greater than the length of time the script takes to run.
    # For a smaller processInterval the script should complete relatively quickly so 15-30 seconds should be plenty.
    timediff = processInterval + 15 
    epoch_time = int(time.time())
    today = time.strftime("%Y%m%d-%H%M")
    eventtime = datetime.datetime.utcfromtimestamp(int(epoch_time)-int(timediff)).strftime('%Y-%m-%dT%H:%M:%S.000Z')

def license(api):
    # Load Webex Users and update licenses as necessary.
    total_records = 0
    modified_records = 0
    people = api.people.list()
    for person in people:
        total_records = int(total_records) + 1

        # Match non-students (employees) and check their licenses list matches licenses.json. If mis-match, update.
        if str(studentMail) not in str(person.emails):
            needsupdate = False
            currentlic = person.licenses

            for lic in employeeLics:
                if str(lic) not in str(person.licenses):
                    needsupdate = True
                    currentlic.append(lic)
            
            if needsupdate == True:
                logging.debug(f"Start license list: {person.licenses}")
                logging.debug(f"Final license list: {currentlic}")           
                if harmlesslicenses == "no":
                    ReportToSpace(f"Looks like employee {str(person.emails)} needs a Webex license update.")
                    try:
                        api.people.update(person.id, emails=person.emails, displayName=person.displayName, firstName=person.firstName,
                                                    lastName=person.lastName, avatar=person.avatar, orgId=person.orgId, roles=person.roles,
                                                    licenses=currentlic)
                        modified_records = int(modified_records) + 1
                    except:
                        errorlog.debug(f"User failed info: {person}")
                        ReportToSpace(f"License update failed for employee: {person.emails}")
                elif harmlesslicenses == "yes":
                    logging.info(f"*** HARMLESS *** Employee {str(person.emails)} would have received a license update.")

        # Match students and check license matches license.json. If mis-match, update.    
        elif str(studentMail) in str(person.emails) and person.licenses != studentLics:
            if harmlesslicenses == "no":
                try:
                    ReportToSpace(f"Looks like student {str(person.emails)} needs a Webex license update.")
                    api.people.update(person.id, emails=person.emails, displayName=person.displayName, firstName=person.firstName,
                                             lastName=person.lastName, avatar=person.avatar, orgId=person.orgId, roles=person.roles,
                                             licenses=studentLics)
                    modified_records = int(modified_records) + 1
                except:
                    errorlog.debug(f"User failed info: {person}")
                    ReportToSpace(f"License update failed for student: {person.emails}")
            elif harmlesslicenses == "yes":
                logging.info(f"*** HARMLESS *** Student {str(person.emails)} would have received a license update.")       
    
    ReportToSpace(f"License processing thread complete. {modified_records} users updated.")

# Primary function
def main():

    importvars()
    importprocesses()
    importlicenses()
    
    updatetime()

    logging.basicConfig(level=loglevel,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename="" + str(workdir) + "/logs/license.log",
                        filemode='a')
    
    errorLogpath = str(workdir) + "/logs/lic-error.log"
    global errorlog
    errorlog = setup_logger('error_log', errorLogpath, logging.DEBUG)

    # Report script initiation
    ReportToSpace(f"Validation of Webex Cloud services has started. Using: licensecheck.py {str(scriptVersion)}")
    
    token_check = -1

    while True:

        if token_check < 0:

            # Get Tokens and create API object
            do_getTokens()
            api = WebexTeamsAPI(access_token=accessToken)

            # How often to check token (daily @ 86400)
            token_check = 86400

            # Included with token refresh to only run daily.
            if processlicenses == "yes":
                ReportToSpace(f"Starting license processing thread.")
                license(api)

        # Update time interval variables.
        updatetime()

        logging.info(f"Sleeping for {processInterval} seconds.")
        token_check = token_check - processInterval
        time.sleep(processInterval)
    
if __name__ == "__main__":
    main()