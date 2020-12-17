FROM python

RUN pip install webexteamssdk
RUN pip install requests

COPY ./app /app