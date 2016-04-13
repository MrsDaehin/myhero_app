FROM python:2-onbuild
EXPOSE 5000
CMD [ "python", "./myhero_app/myhero_app.py" ]

