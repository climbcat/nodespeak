# GOTO-Eliminating Flowchart Compiler

This is a fun, experimental project I did to learn more about compiler tech and web-based UIs.

Flowcharts are code with GOTOs, which are considered bad practice, but also a convenient way to visualize small branching programs or processes.

What if we could draw a flowchart and then export it as legal Python code, without any of the silly GOTO's? Well, now you can! This d3js/Django app implements a visual flowchart editor and flowchart-to-Python compiler.

In the service of transparency, it should be noted that the (totally legal and correct) code output by this project is actually not much more readable than the goto-riddled mess it came from, but it sure was fun to write the project though: Building the AST, read and implement the GOTO-elimination steps, the recursive code generator, and make it all come together.

## GOTO elimination

Flowcharts can be transformed into structured code following a process called "GOTO elimination".

Structued code is code that can be represented as a tree - an abstract syntax tree (AST). Flowchars are represented by a graph (with potential cyclical pahts).

The GOTO elimination process compiles your flowchart-AST (a graph) into a structured code-AST. The AST is a central concept in compiler tech, and a data format that corresponds to structured code. Real compilers perform various optimizing operations on the AST in order to generate more optimized code. In our case, we perform GOTO-elimination on the AST instead, and are able to transform the AST into legal, structured code.

This project implements a combined flowchart & datagraph and goto-elimination tool. So perhaps, the code it outputs tends to be unreadable, however, it does work! Declared a successful tech demo.

#### NOTE

However, what even is a datagraph? The datagraph corresponds to the tree of function calls and return values that can be nested as a gree, while the flowchart corresponds to a control flow graph. That simple.

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
