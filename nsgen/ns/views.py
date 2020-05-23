from django.shortcuts import render, HttpResponse
from .models import GraphSession, TypeSchema, TabId
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
    session.graphdef = data_str
    session.modified = timezone.now()
    session.save()

    # return success
    return HttpResponse('{ "msg" : "graphdef saved" }')

def tab_validate(req):
    pass
