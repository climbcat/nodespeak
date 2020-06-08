from django.shortcuts import render, HttpResponse, redirect
from .models import GraphSession, TypeSchema, TabId
from django.contrib.auth.decorators import login_required
from django.utils import timezone

import base64
import json

from cogen import cogen

# the one and only view
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

# ajax requests
def ajax_load(req, gs_id):
    ''' data is loaded to client as-is '''
    session = GraphSession.objects.get(id=gs_id)
    if session:
        return HttpResponse(session.data_str)
    return HttpResponse('{"error" : "session %s not found"}' % gs_id)

def ajax_commit(req):
    ''' data is not unpacked, just saved as-is '''
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

def ajax_cogen(req):
    data_str = req.POST.get("data_str", None)
    if data_str == None:
        return HttpResponse('{ "msg" : "no data received" }')

    obj = json.loads(data_str)
    try:
        text = cogen(obj["graphdef"], obj)
    except Exception as e:
        return HttpResponse('{ "msg" : "cogen error" }')

    # make this a base64 string
    encoded = base64.b64encode(text.encode('utf-8'))
    text = encoded.decode('utf-8')

    return HttpResponse('{ "msg" : "pseudocode generation successful", "pseudocode" : "%s" }' % text)

def tab_validate(req):
    # TODO: port from IFL
    pass
