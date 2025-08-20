# Flowchart Compiler

Flowcharts correspond to code with GOTOs, and the use of GOTOs is broadly considered bad programming practice.

At the same time, flowcharts are low-key considered a convenient "back-of-an-envelope" way of describing small programs. They are actually quite useful.

So - what if you could run your flowchart as code in a high-level language like Python or C++?

Well, now you can!

This d3js/Django app implements a visual flowchart & datagraph editor, with a flowchart compiler outputting legal Python translations of your favourite flowcharts.

It was a experimental project I did around 2020 to learn about compiler tech, web-based UI, and a fun exploration of the concepts of flowcharts, datagraphs and GOTOs.

## GOTO elimination

Flowcharts can be transformed into structured code following a process called "GOTO elimination".

The GOTO elimination process compiles your flowchart-AST into a structured code-AST. AST stands for "abstract syntax tree", a central concept in most compilers - a data format that corresponds to code. Most compilers perform various optimizing operations on the AST in order to later code generate something that is more optimized. In our case, we perform GOTO-elimination on the flowchart-AST, and are able to generate structured code from that.

This project implements a combined flowchart & datagraph and goto-elimination tool. So perhaps, the code it outputs tends to be unreadable, however, it does work! Declared a successful tech demo.

#### NOTE

But what in the world is a datagraph? The datagraph corresponds to function calls and return values, while the flowchart corresponds to control flow. It also bears mentioning that the flowchart-AST is generally a graph just like the flowchart itself, and not strictly a tree.

## Setup

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
