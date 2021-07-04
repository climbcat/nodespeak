from django.shortcuts import render, HttpResponse, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth.models import User
import django.contrib.auth as auth
from cogen import cogen_graphs_py, cogen_typedefs_py
from .models import GraphSession, TypeSchema, SignUp
import base64
import json

import random
import math

def create_random_hex_data_str(length : int) -> str:
    chars = ["0","1","2","3","4","5","6","7","8","9","a","b","c","d","e","f"]
    data_arr = []
    for i in range(length):
        data_arr.append(chars[math.floor(random.random()*16)])
    return "".join(data_arr)

def index(req):
    return redirect("/login")

def login(req):
    return render(req, "ns/login.html")

def login_submit(req):
    user = auth.authenticate(username=req.POST["username"], password=req.POST["password"])
    if user is None or not user.is_active:
        return redirect("/login")
    auth.login(req, user)
    return redirect("/latest/")

def signup(req):
    return render(req, "ns/signup.html")

def signup_submit(req):
    email = req.POST["email"]

    # TODO: validate format
    valid = True
    if not valid:
        return HttpResponse("email format error detected, use browser back to try again")

    # check if user already exists
    user = None
    try:
        usr = User.objects.get(email=email)
    except:
        pass
    if user is not None:
        return HttpResponse("user already exists")

    # create the signup object (awaiting email confirmation)
    signup = SignUp()
    signup.email = email
    signup.token = create_random_hex_data_str(16)
    signup.save()

    conf_link_url = "127.0.0.1:8000"
    conf_link_app = "/emailconf/%s" % signup.token
    l = conf_link_url + conf_link_app
    return HttpResponse("An email should be sent containing link: <a href=\"%s\">%s</a>" % (l, l))

def emailconf(req, token):
    # get email by token
    try:
        obj = SignUp.objects.get(token=token)
    except:
        import time
        # TODO: make some error registration here to detect continued requests
        time.sleep(1)
        return HttpResponse("invalid request")

    # TODO: make a proper password and email it to the user (username can probably be equal to email for now)
    acc = User.objects.create_user(obj.email, obj.email, obj.email)

    return render(req, "ns/email_conf.html", { "email" : obj.email, "password" : acc.password })

@login_required
def edit_from_graphs(req, gs_id):
    gs = GraphSession.objects.get(id=gs_id)
    return render(req, "ns/edit_from_graphs.html", context={ "gs_id" : gs_id, "prev_title" : gs.title, "prev_description" : gs.description })

@login_required
def edit_submit_from_graphs(req, gs_id):
    gs = GraphSession.objects.get(id=gs_id)
    gs.title = req.POST["title"]
    gs.description=req.POST["description"]
    gs.save()
    return redirect(graphui, gs_id=gs_id)

@login_required
def edit_from_dashboard(req, gs_id):
    gs = GraphSession.objects.get(id=gs_id)
    return render(req, "ns/edit_from_dashboard.html", context={ "gs_id" : gs_id, "prev_title" : gs.title, "prev_description" : gs.description })

@login_required
def edit_submit_from_dashboard(req, gs_id):
    gs = GraphSession.objects.get(id=gs_id)
    gs.title = req.POST["title"]
    gs.description=req.POST["description"]
    gs.save()
    return redirect(dashboard)

@login_required
def logout(req):
    auth.logout(req)
    return redirect("/login")

@login_required
def graphui(req, gs_id):
    gs = GraphSession.objects.get(id=gs_id)
    ct = {
        "gs_id" : gs_id,
        "tab_id" : 0,
        "title" : gs.title
    }
    return render(req, "ns/graphs.html", context=ct)

@login_required
def new_gs(req, ts_id=None):
    ts_data = None
    if ts_id == None:
        # TODO: is this a safe call returning None, or can it except?
        ts_data = TypeSchema.objects.last()
    else:
        ts_data = TypeSchema.objects.get(id=ts_id)
    gs = GraphSession()
    gs.user_id = req.user.id
    gs.data_str = ts_data.data_str
    gs.org_version = ts_data.version
    gs.save()
    return redirect(graphui, gs_id=gs.id)

@login_required
def duplicate_gs(req, gs_id=None):
    gsold = None
    if req.user.is_superuser:
        gsold = GraphSession.objects.get(id=gs_id)
    else:
        gsold = GraphSession.objects.get(id=gs_id, user_id=req.user.id)
    if gsold is None:
        return redirect(dashboard)
    gsnew = GraphSession()
    gsnew.user_id = req.user.id
    gsnew.data_str = gsold.data_str
    gsnew.org_version = gsold.org_version
    gsnew.save()
    return redirect(graphui, gs_id=gsnew.id)

@login_required
def delete_gs(req, gs_id):
    try:
        gs = None
        if req.user.is_superuser:
            gs = GraphSession.objects.get(id=gs_id)
        else:
            gs = GraphSession.objects.get(id=gs_id, user_id=req.user.id)
        if gs is not None:
            gs.delete()
    except:
        print("graph session %s" % gs_id + " to delete not found")
    return redirect(dashboard)

@login_required
def dashboard(req):
    sessions = []

    # load appropriate objects     
    qset = None
    if req.user.is_superuser:
        qset = GraphSession.objects.all()
    else:
        qset = GraphSession.objects.filter(user_id=req.user.id)

    for s in qset:
        descr = ""
        if s.description is not None:
            descr = s.description[:50]
        sessions.append( (s.id, s.title, descr) )
    
    ct = { "sessions" : sessions}
    return render(req, "ns/dashboard.html", context = ct)

@login_required
def latest_gs(req):
    gslast = GraphSession.objects.last()
    return graphui(req, gslast.id)

@login_required
def ajax_load(req, gs_id):
    ''' data is loaded to client as-is '''
    session = GraphSession.objects.get(id=gs_id)
    if session:
        return HttpResponse(session.data_str)
    return HttpResponse('{"error" : "session %s not found"}' % gs_id)

@login_required
def ajax_commit(req):
    ''' data is not unpacked, but saved as-is '''
    data_str = req.POST.get("data_str", None)
    gs_id = req.POST.get("gs_id", None)
    # TODO: include TabId check
    #tab_id = req.POST.get("tab_id", None)
    if data_str == None:
        return HttpResponse('{ "msg" : "no data received" }')

    # save to db
    session = GraphSession.objects.get(id=gs_id)
    session.data_str = data_str
    session.modified = timezone.now()
    session.save()

    # return success
    return HttpResponse('{ "msg" : "graphdef saved" }')

@login_required
def ajax_cogen(req):
    data_str = req.POST.get("data_str", None)
    if data_str == None:
        return HttpResponse('{ "msg" : "no data received" }')

    obj = json.loads(data_str)
    try:
        text = cogen_typedefs_py(obj) + "\n\n" + cogen_graphs_py(obj["graphdef"], obj)
        # DEBUG print
        print(text)
    except Exception as e:
        print(str(e))
        return HttpResponse('{ "msg" : "cogen error" }')

    # make this a base64 string
    encoded = base64.b64encode(text.encode('utf-8'))
    text = encoded.decode('utf-8')

    return HttpResponse('{ "msg" : "code generation successful", "code" : "%s" }' % text)

@login_required
def tab_validate(req):
    # TODO: port from IFL
    pass
