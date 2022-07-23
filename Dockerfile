FROM mcr.microsoft.com/playwright:focal
MAINTAINER Daniel Nemeth <daniel.nemeth83@yahoo.com>
WORKDIR /app
COPY requirements.txt /app
RUN apt-get update && apt-get install -y python3-pip
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN python3 -m playwright install

COPY crawler.py /app
#
#ARG USER
#ARG USER_ID
#ARG GROUP_ID
#RUN addgroup --gid $GROUP_ID $USER
#RUN adduser --disabled-password --gecos '' --uid $USER_ID --gid $GROUP_ID $USER
USER pwuser

ENTRYPOINT ["python3", "crawler.py"]
