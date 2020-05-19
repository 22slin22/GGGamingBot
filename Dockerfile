FROM python:3
ADD bot.py /
COPY conf.json /
RUN pip install discord.py
CMD [ "python", "./bot.py" ]