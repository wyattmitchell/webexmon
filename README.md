# Webex Spaces Monitor

## Description
Runs a Docker container to pull recent Webex Room/Space membership changes
capturing new room creation by students and moving them to admin control.

Container can also be run as a license verification script to iterate through all users and verify or update licenses to match those specified.

## Usage
All variables MUST be defined in "webexinfo.json" for script to function.

#### Configuration:

webexinfo.json contains all operational configuration as follows.
- ClientID and ClientSecret - from Webex Integration (used for token renewal and access to API)
- BotID and AuthToken - for Webex Bot (Bot to post messages to Teams Space)
- SpaceID - Webex space ID where the Bot is a member and will post logs
- studentMail and facultyMail - Pattern to match for student and faculty accounts.
- action - options are "update" or "delete" - Update will add the admin to the room and remove all other members. Delete will delete the room unless part of a Team. Delete action on a Team room will behave like an update due to the way Team Spaces are handled.
- harmless - options are "yes" or no" - Yes will disable the action changes from occuring and
 only log what action would be taken. No will process the actions.
- loglevel - options are INFO or DEBUG - Adjust logging verbosity.

process.json allows enable/disable of processes run by the script
- processlicenses - options are "yes" or "no" - Yes will check all Webex users for correct licenses. No disables this process.
- harmlesslicenses - options are "yes" or "no" - Yes will disable changes and only report expected changes. No will attempt updates to the licenses assigned.

licenses.json defines which licenses employees and students should have
- employee - List of licenses to verify for employees. Adds any missing licenses, does not remove existing licenses.
- student - List of licenses to verify for students. Replaces license list with those defined. Will remove extra licenses.

#### Docker container setup:
- Script runs within a Docker container. Info on Docker and setup can be 
found at https://www.docker.com/get-started

- Once Docker is running, navigate in your terminal program to the path 
where the included dockerfile resides and build with the following command: "docker build -t webexmon ."

- To run the space moderation function, navigate to the "persist" folder included and run the container with:
"docker run -d -v $PWD:/persist webexmon python ./app/monitor.py"

- To run the license verification use the same container build and execute with:
"docker run -d -v $PWD:/persist webexmon python ./app/licensecheck.py"

## Version
- v.2.0.1 - all earlier revs built by James Martin. This version is repackaged 
            based on webexteamssdk. Tokens managed via requests library.
            Wrapped in Docker for standardized deployment.
- v.2.1.0 - Added action, harmless and loglevel functionality.
- v.2.1.1 - Force ReportToSpace message encoding to correct emoji in room name error
            Catch errors and bypass when events are missing required fields.
- v.2.2.0 - Add license processing functionality.
- v.2.2.1 - Fix handling of Team Spaces (isModerator flag enabled)

## Acknowledgements
Thanks to Jim Martin for sharing the logging and token handling components and the awesome script this is based on.
Thanks to Jeremy Knutson for testing and bug fixes.