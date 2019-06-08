//
//  NGSen extension to graphui.js.
//


class ConnectionRulesNSGen extends ConnectionRulesBase {
  // bare-bones rules determining whether and how nodes can be connected
  static canConnect(a1, a2) {
    //  a2 input anchor, a1 output
    let t1 = a2.i_o;
    let t2 = !a1.i_o;
    // both anchors must be of the same type
    let t6 = a1.type == a2.type;
    let t7 = a1.type == '' || a2.type == '';
    let t8 = a1.type == 'term' || a2.type == 'term';
    let t9 = a1.type == 'proc' || a2.type == 'proc';
    let t10 = a1.type == 'dec' || a2.type == 'dec';

    let ans = ( t1 && t2 ) && (t6 || t7 || t8 || t9 || t10);
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
    let t8 = a1.type == 'term' || a2.type == 'term';
    let t9 = a1.type == 'proc' || a2.type == 'proc';
    let t10 = a1.type == 'dec' || a2.type == 'dec';

    let ans = ( t1 && t2 ) && (t6 || t7 || t8 || t9 || t10);
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


//
//  Project specific base node types.
//


class NodeFCTerm extends Node {
  static get basetype() { return "term"; }
  get basetype() { return NodeFCTermProc.basetype; }
  static get prefix() { return "t"; }
  constructor(x, y, id, name, label, typeconf) {
    super(x, y, id, name, label, typeconf);
  }
  _getGNType() {
    return GraphicsNodeSquare;
  }
  _getAnchorType() {
    return AnchorSquare;
  }
  isConnected(connectivity) {
    return connectivity.indexOf(false) == -1;
  }
  isActive() {
    return true;
  }
}


class NodeFCProcess extends NodeFCTerm {
  static get basetype() { return "proc"; }
  get basetype() { return NodeFCTermProc.basetype; }
  static get prefix() { return "p"; }
}


class NodeFCDec extends Node {
  static get basetype() { return "dec"; }
  get basetype() { return NodeFCTermProc.basetype; }
  static get prefix() { return "d"; }
  constructor(x, y, id, name, label, typeconf) {
    super(x, y, id, name, label, typeconf);
  }
  _getGNType() {
    return GraphicsNodeDiamond;
  }
  _getAnchorType() {
    return AnchorCircular;
  }
  isConnected(connectivity) {
    return connectivity.indexOf(false) == -1;
  }
  isActive() {
    return true;
  }
}


register_node_class(NodeFCTerm);
register_node_class(NodeFCProcess);
register_node_class(NodeFCDec);
