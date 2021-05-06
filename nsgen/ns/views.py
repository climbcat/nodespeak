from django.shortcuts import render, HttpResponse, redirect
from .models import GraphSession, TypeSchema
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import django.contrib.auth as auth
import base64
import json
from cogen import cogen_graphs_py

def test(req):
    return HttpResponse("test")

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

@login_required
def logout(req):
    auth.logout(req)
    return redirect("/login")

@login_required
def graphui(req, gs_id):
    ct = {
        "gs_id" : gs_id,
        "tab_id" : 0,
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
    gs.data_str = ts_data.data_str
    gs.org_version = ts_data.version
    gs.save()
    return redirect(graphui, gs_id=gs.id)

@login_required
def duplicate_gs(req, gs_id=None):
    ts_data = None
    gsold = GraphSession.objects.get(id=gs_id)
    gsnew = GraphSession()
    gsnew.data_str = gsold.data_str
    gsnew.org_version = gsold.org_version
    gsnew.save()
    return redirect(graphui, gs_id=gsnew.id)

@login_required
def delete_gs(req, gs_id):
    try:
        gs = GraphSession.objects.get(id=gs_id)
        gs.delete()
    except:
        print("graph session %s" % gs_id + " to delete not found")
    return redirect(dashboard)

@login_required
def dashboard(req):
    ct = { "sessions" : [(s.id, s.title) for s in GraphSession.objects.all() ] }
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
        text = cogen_graphs_py(obj["graphdef"], obj)
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
