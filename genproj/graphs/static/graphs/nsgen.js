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
  static getLinkBasetype(a1, a2) {
    if (a1.idx==-1 && a2.idx==-1) return "link_double_center"; else return "link_single";
  }
}


class GraphInterfaceNSGen extends GraphInterface {
  constructor(gs_id, tab_id) {
    super(gs_id, tab_id, ConnectionRulesNSGen);
  }
  // server communication
  ajaxcall(url, data, success_cb, fail_cb=null) {
    this.isalive = simpleajax(url, data, this.gs_id, this.tab_id, success_cb, fail_cb, true);
  }
  ajaxcall_noerror(url, data, success_cb) {
    // call with showfail=false, which turns off django and offline fails
    this.isalive = simpleajax(url, data, this.gs_id, this.tab_id, success_cb, null, false);
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


function simpleajax(url, data, gs_id, tab_id, success_cb, fail_cb=null, showfail=true) {
  // GraphInterface utility function
  let isalive = true;
  $.ajax({
    type: "POST",
    url: url,
    data: { "gs_id": gs_id, "tab_id": tab_id, "data_str" : JSON.stringify(data) },
  })
  .fail(function(xhr, statusText, errorThrown) {
    if (!showfail) return
    if (fail_cb) fail_cb();
    $("body").css("cursor", "default");
    $(window.open().document.body).html(errorThrown + xhr.status + xhr.responseText);
  })
  .success(function(msg) {
    // parse & json errors
    let obj = null;
    try {
      obj = JSON.parse(msg);
    }
    catch(error) {
      console.log("JSON.parse error on string: ", msg);
      alert("uncomprehensible server response: ", msg);
      throw error;
    }

    // fatal errors
    let fatalerror = obj["fatalerror"];
    if (fatalerror) {
      isalive = false;
      alert("Please restart the session. Fatal error: " + fatalerror);
      //location.reload();
      close();
    }

    // timeouts
    let timeout = obj["timeout"];
    if (timeout) {
      alert("timeout: " + timeout);
    }

    // pass it on
    success_cb(obj)
  });
  return isalive;
}


//  base node types
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


NodeLinkConstrucionHelper.register_node_class(NodeFCTerm);
NodeLinkConstrucionHelper.register_node_class(NodeFCProcess);
NodeLinkConstrucionHelper.register_node_class(NodeFCDec);
