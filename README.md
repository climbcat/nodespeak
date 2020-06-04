# nodespeakgen

Development setup:

Files:
- git clone https://github.com/climbcat/nodespeak/
- download the files d3.v4.min.js, index.min.js and jquery.min.js, and put them in nsgen/ns/static/ns

Run these commands from nsgen:
- python3 manage.py migrate
- python3 manage.py createsuperuser
- python3 manage.py gentypes02
- python3 manage.py runserver

In the browser:
- go to http://127.0.0.1:8000/admin and log in
- go to http://127.0.0.1:8000/new/1 where "1" is the schema id that was created by the gentypes command
