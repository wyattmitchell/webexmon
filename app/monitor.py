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
    ReportToSpace("Checking to see if we have the latest Access Token.")
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
    if token_age > 172800:
        ReportToSpace(
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
        ReportToSpace(
            "Done! The access token has been refreshed. Getting back to work.")
    else:
        ReportToSpace(
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

# Gets all membership events over the specified interval.
# For rooms created by students this will add the admin account and remove all other members.
def auditSpaces(api):

    logging.info(f"Beginning next run...")
    
    events = api.events.list(resource="memberships",type="created",_from=eventtime)
    for event in events:
        try:
            if str(studentMail) in str(event.data.personEmail) and str(event.data.roomType) == "group":
                
                logging.debug(f"Event id processing {event.id} by user {event.data.personEmail}.")
                currentroom = api.rooms.get(event.data.roomId)
                logging.debug(currentroom)
                
                if str(event.data.personId) in str(currentroom.creatorId):
                    
                    if harmless == "no":
                        ReportToSpace(f"Processing room {currentroom.title} in {action} mode. Harmless is set to {harmless}.")
                    elif harmless == "yes":
                        ReportToSpace(f"-- Harmless mode is enabled. This is a notification only. -- Script would have processed room {currentroom.title} in {action} mode but no action has been taken.")

                    if str(action) in "update":
                        roommembers = api.memberships.list(roomId=event.data.roomId)
                        try:
                            if harmless == "no":
                                api.memberships.create(currentroom.id, personEmail=adminaccount, isModerator=True)
                                ReportToSpace(f"--- Admin added to room {currentroom.title}.")
                                logging.debug(f"--- Room ID {currentroom.id}.")
                            else:
                                logging.info(f"--- HARMLESS -- Admin would be added to room {currentroom.title}.")
                                logging.debug(f"--- HARMLESS -- Room ID: {currentroom.id}.")
                        except:
                            logging.debug("--- Unable to add admin or already exists. Attempting escalation to moderator.")
                            try:
                                if harmless == "no":
                                    for member in roommembers:
                                        if str(member.personEmail) in str(adminaccount) and member.isModerator==False:
                                            api.memberships.delete(member.id)
                                            api.memberships.create(currentroom.id, personEmail=adminaccount, isModerator=True)
                                            logging.debug(f"------ Elevated admin account to moderator.")
                                    else:
                                        logging.debug(f"------- Admin already in room as moderator. Continuing.")
                                else:
                                    logging.info(f"--- HARMLESS --- Admin would be elevated to moderator.")
                            except:
                                logging.debug(f"------ Could not elevate admin to moderator.")
                        try:
                            roommembers = api.memberships.list(roomId=event.data.roomId)
                            for member in roommembers:
                                if str(member.personEmail) in str(adminaccount) and member.isModerator==True:
                                    logging.debug(f"------ Skipping admin account removal.")                        
                                else:
                                    try:
                                        if harmless == "no":
                                            api.memberships.delete(member.id)
                                            ReportToSpace(f"------ Member {member.personEmail} removed from room {currentroom.title}.")
                                            logging.debug(f"------ Member ID: {member.id}")
                                        else:
                                            logging.info(f"------ HARMLESS -- Member {member.personEmail} would be removed from room {currentroom.title}.")
                                    except:
                                        ReportToSpace(f"------ Could not delete {member.personEmail} from room {currentroom.title}.")
                            ReportToSpace(f"All members processed for room {currentroom.title}.")
                        except:
                            ReportToSpace(f"Unable to update room {currentroom.title} membership.")
                            
                    if str(action) in "delete":
                        roommembers = api.memberships.list(roomId=event.data.roomId)
                        try:
                            if harmless == "no":
                                api.memberships.create(currentroom.id, personEmail=adminaccount, isModerator=True)
                                ReportToSpace(f"--- Admin added to room {currentroom.title}.")
                                logging.debug(f"--- Room ID {currentroom.id}.")
                            else:
                                logging.info(f"--- HARMLESS -- Admin would be added to room {currentroom.title}.")
                                logging.debug(f"--- HARMLESS -- Room ID: {currentroom.id}.")
                        except:
                            logging.debug("--- Unable to add admin or already exists. Attempting escalation to moderator.")
                            try:
                                if harmless == "no":
                                    for member in roommembers:
                                        if str(member.personEmail) in str(adminaccount) and member.isModerator==False:
                                            api.memberships.delete(member.id)
                                            api.memberships.create(currentroom.id, personEmail=adminaccount, isModerator=True)
                                            logging.debug(f"------ Elevated admin account to moderator.")
                                    else:
                                        logging.debug(f"------- Admin already in room as moderator. Continuing.")
                                else:
                                    logging.info(f"--- HARMLESS --- Admin would be elevated to moderator.")
                            except:
                                logging.debug(f"------ Could not elevate admin to moderator.")
                        try:
                            for member in roommembers:
                                if str(member.personEmail) in str(adminaccount):
                                    logging.debug(f"------ Skipping admin account removal.")
                                else:
                                    try:
                                        if harmless == "no":
                                            api.memberships.delete(member.id)
                                            logging.debug(f"------ Member {member.personEmail} removed from room {currentroom.title}.")
                                            logging.debug(f"------ Member ID: {member.id}")
                                        else:
                                            logging.debug(f"------ HARMLESS -- Member {member.personEmail} would be removed from room {currentroom.title}.")
                                    except:
                                        logging.debug(f"------ Could not delete {member.personEmail} from room {currentroom.title}.")
                        except:
                            logging.debug(f"------Could not clear room members.")
                        try:
                            if harmless == "no":
                                api.rooms.delete(currentroom.id)
                                ReportToSpace(f"------ Room {currentroom.title} created by {event.data.personEmail} deleted.")
                            else:
                                logging.info(f"------ HARMLESS -- Room {currentroom.title} created by {event.data.personEmail} would be deleted.")
                        except:
                            ReportToSpace("------ Room could not be deleted. Possibly already processed in prior run.")
        except:
            errorlog.debug(f"Failed to process event data: {event}")

# Primary function
def main():

    importvars()
    updatetime()

    logging.basicConfig(level=loglevel,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename="" + str(workdir) + "/logs/processing.log",
                        filemode='a')
    
    errorLogpath = str(workdir) + "/logs/error.log"
    global errorlog
    errorlog = setup_logger('error_log', errorLogpath, logging.DEBUG)

    # Report script initiation
    ReportToSpace(f"Validation of Webex Cloud services has started. Using: monitor.py {str(scriptVersion)}")
    
    token_check = -1

    while True:

        if token_check < 0:

            # Get Tokens and create API object
            do_getTokens()
            token_check = 86400
            api = WebexTeamsAPI(access_token=accessToken)

        # Update time interval variables.
        updatetime()

        # Run process
        auditSpaces(api)

        logging.info(f"Sleeping for {processInterval} seconds.")
        token_check = token_check - processInterval
        time.sleep(processInterval)
    
if __name__ == "__main__":
    main()