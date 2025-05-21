# Flowchart Compiler

Flowcharts are generally not "structured", do not describe structured code, due to the goto-s. Goto elimination allows for a flowchart compiler into structured code. 

This project contains a visual flowchart definition tool, and a back-end flowchart-to-structured-code compiler.

The visual front-end allows users to define two graphs; The code path flowchart, and an associated tree of data. Both of these are combined into structured code, which is output as a python code block. The frontend uses d3js, and the web framework is django.

# nsgen

#### Development setup:

Django version:
- pip install Django==2.2.12

Files:
- git clone https://github.com/climbcat/nodespeak/
- put the files d3.v4.min.js and jquery.min.js in nsgen/ns/static/ns (or link directly to source, e.g. https://d3js.org/d3.v4.min.js, in ns/templates/ns/graphs.html)

Run these commands from nsgen to prepare a setup:
- python3 manage.py collectstatic (for release setups)
- python3 manage.py migrate
- python3 manage.py createsuperuser
- python3 manage.py gentypes02
- python3 manage.py runserver
