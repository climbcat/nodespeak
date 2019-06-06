//
//  IFL extension to graphui.js.
//


class ConnectionRulesNSGen extends ConnectionRulesBase {
  // bare-bones rules determining whether and how nodes can be connected
  static canConnect(a1, a2) {
    if (a1.idx==-1 && a2.idx==-1) {
      let tpe1 = a1.owner.owner.basetype;
      let tpe2 = a2.owner.owner.basetype;
      let t1 = ["object_idata", "object_ifunc", "obj"].indexOf(tpe1) != -1 && tpe2 == "method";
      let t2 = tpe1 == "method" && ["object_idata", "object_ifunc", "obj"].indexOf(tpe2) != -1;
      let t3 = a1.numconnections == 0;
      let t4 = a2.numconnections == 0;
      return t1 && t4 || t2 && t3;
    }

    //  a2 input anchor, a1 output
    let t1 = a2.i_o;
    let t2 = !a1.i_o;
    // inputs can only have one connection
    let t5 = a2.numconnections == 0;
    // both anchors must be of the same type
    let t6 = a1.type == a2.type;
    let t7 = a1.type == '' || a2.type == '';
    let t8 = a1.type == 'obj' || a2.type == 'obj';

    let ans = ( t1 && t2 ) && t5 && (t6 || t7 || t8);
    return ans;
  }
  static couldConnect(a1, a2) {
    // could a1 and a2 be connected if a2 was unoccupied?
    //  a2 input anchor, a1 output
    let t1 = a2.i_o;
    let t2 = !a1.i_o;
    // both anchors must be of the same type
    let t6 = a1.type == a2.type;
    let t7 = a1.type == '' || a2.type == '';
    let t8 = a1.type == 'obj' || a2.type == 'obj';

    let ans = ( t1 && t2 ) && (t6 || t7 || t8);
    return ans;
  }
}


class GraphInterfaceNSGen extends GraphInterface {
  constructor(gs_id, tab_id) {
    super(gs_id, tab_id, ConnectionRulesNSGen);
  }
  loadSession() {
    $("body").css("cursor", "wait");
    this.ajaxcall("/ajax_load/" + gs_id, null, function(obj) {
      let gd = obj["graphdef"]
      let error = obj["graphdef"]
      if (gd != null) {
        this.reset();
        this.injectGraphDefinition(obj);
      }
      if (error != null) {
        alert(error);
      }
      $("body").css("cursor", "default");
    }.bind(this));
  }
  commitSession() {
    $("body").css("cursor", "wait");
    let post_data = {};
    post_data = this.graphData.extractGraphDefinition();

    this.ajaxcall("/ajax_commit/", post_data, function(obj) {
      $("body").css("cursor", "default");
    }.bind(this));
  }
  _recenterCB() {
    let btnsmenu = d3.select("#buttons");
    btnsmenu.style("left", window.innerWidth/2-btnsmenu.node().clientWidth/2 + "px");
  }
}
