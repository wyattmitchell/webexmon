# WebexMon
Webex Spaces Monitor

## Description

Runs a docker container to pull all recent Webex Room/Space membership changes
capturing new room creation by students and subsequently deletes those rooms.

Version starting with v.2.0.1 modified and assembled by Mitchell Wyatt. It's been mangled almost
beyond recognition from what Jim Martin originally built but the soul lives on.
All prior releases and function framework written by James Martin.

Version history sanitized for general use.
- v.2.0.1 - all earlier revs built by James Martin. This version is hacked up,
          mangled and repackaged by Mitchell Wyatt based on webexteamssdk
          for User API interactions. Token managed via requests library.
          Wrapped in docker for standardized deployment.
- v.2.1.0 - Added action, harmless and loglevel functionality.

## Usage
All variables MUST be defined in "webexinfo.json" for script to function.

Variable descriptions:

- ClientID and ClientSecret - from Webex Integration (used for token renewal and access to API)
- BotID and AuthToken - for Webex Bot (Bot to post messages to Teams Space)
- SpaceID - Webex space ID where the Bot is a member and will post logs
- studentMail and facultyMail - Pattern to match for student and faculty accounts.
- action - options are "update" or "delete" - Update will add the admin to the room and remove all other members. Delete will delete the room.
- harmless - options are "yes" or no" - Yes will disable the action changes from occuring and only log what action would be taken. No will process the actions.
- loglevel - options are INFO or DEBUG - Adjust logging verbosity.

Docker container setup:
- Build with from the same path as the docker file: docker build -t webexmon .
- CD into the "persist" folder and run the container with: docker run -d -v $PWD:/persist webexmon python ./app/monitor.py