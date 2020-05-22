import json

from django.shortcuts import render, HttpResponse
from .models import GraphSession, UserTypes, TabId
from django.contrib.auth.decorators import login_required
from django.utils import timezone

# the one and only view
@login_required
def graph_session(req, gs_id):
    ct = {
        "gs_id" : gs_id,
        "tab_id" : 0,
        }
    return render(req, "ns/graphs.html", context=ct)

# DEBUG temporary'
# TODO: integrate
def tpeedt(req):
    return render(req, "ns/tpelist.html")

# ajax requests
def ajax_load(req, gs_id):
    session = GraphSession.objects.get(id=gs_id)
    if session:
        return HttpResponse(json.dumps({ "graphdef" : json.loads(session.graphdef) }))
    return HttpResponse('{"error" : "session %s not found"}' % gs_id)

def ajax_commit(req):
    data_str = req.POST.get("data_str", None)
    gs_id = req.POST.get("gs_id", None)
    # TODO: include TabId check
    #tab_id = req.POST.get("tab_id", None)
    if data_str == None:
        return HttpResponse('{ "msg" : "no data received" }')
    obj = json.loads(data_str)

    # save to db
    session = GraphSession.objects.get(id=gs_id)
    session.graphdef = json.dumps(obj["graphdef"])
    session.modified = timezone.now()
    session.save()
    tree = UserTypes.objects.get_or_create(id=0)[0]
    tree.typetree = json.dumps(obj["typetree"])
    tree.modified = timezone.now()
    tree.save()
    
    # return success
    return HttpResponse('{ "msg" : "graphdef saved" }')

    # TODO: implement cogen and goto-ellimination

def tab_validate(req):
    pass
