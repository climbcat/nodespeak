from django.shortcuts import render, HttpResponse
from .models import GraphSession, TabId

# the one and only view
def graph_session(req, gs_id):
    print("gs_id: %s" % gs_id)
    ct = {
        "gs_id" : gs_id,
        "tab_id" : 0,
        }
    return render(req, "graphs/graphs.html", context=ct)

# ajax requests
def ajax_load(req, gs_id):
    session = GraphSession.objects.filter(id=gs_id).get()
    if session:
        return HttpResponse('{"graphdef" : "%s"}' % session.graphdef)
    return HttpResponse('{"error" : "session %s not found"}' % gs_id)
def ajax_commit(req):
    print(req.POST)

    # TODO: implement cogen and goto-ellimination
    return HttpResponse("was printed to terminal")
