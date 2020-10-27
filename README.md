# nsgen

#### Development setup:

Django version:
- pip install Django==2.2.12

Files:
- git clone https://github.com/climbcat/nodespeak/
- download the files d3.v4.min.js and jquery.min.js, and put them in nsgen/ns/static/ns
- or link directly to source, e.g. https://d3js.org/d3.v4.min.js

Run these commands from nsgen:
- python3 manage.py migrate
- python3 manage.py createsuperuser
- python3 manage.py gentypes02
- python3 manage.py runserver
