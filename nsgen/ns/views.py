import json

from django.shortcuts import render, HttpResponse
from .models import GraphSession, TabId
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
    graphdef_str = req.POST.get("data_str", None)
    gs_id = req.POST.get("gs_id", None)
    tab_id = req.POST.get("tab_id", None)
    if graphdef_str == None:
        return HttpResponse('{ "msg" : "no graphdef received" }')
    # save to db
    session = GraphSession.objects.get(id=gs_id)
    session.graphdef = graphdef_str
    session.modified = timezone.now()
    session.save();
    # return success
    return HttpResponse('{ "msg" : "graphdef saved" }')

    # TODO: implement cogen and goto-ellimination

def tab_validate(req):
    pass
