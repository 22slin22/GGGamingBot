FROM python:3
ADD bot.py /
RUN pip install discord.py
RUN pip install python-dotenv
CMD [ "python", "./bot.py" ]