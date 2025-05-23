//
//  NGSen extension to graphui.js.
//


class ConnectionRulesNSGen extends ConnectionRulesBase {
  // bare-bones rules determining whether and how nodes can be connected
  static canConnect(a1, a2, could=false) {
    //  universal
    let ta = a2.i_o && !a1.i_o; // a1 is input and a2 is output anchor
    let tc = a1.idx==-1 && a2.idx==-1; // both are center anchors
    if (!ta && !tc) return false;

    // flowchart
    let fctypes = ConnectionRulesNSGen.fctypes;
    let isflowchart = (fctypes.indexOf(a1.owner.owner.basetype)>=0 && fctypes.indexOf(a2.owner.owner.basetype)>=0);
    if (isflowchart) {
      // output nodes must have a well-defined destination
      let tfc1 = a1.numconnections == 0;
      let tfc2 = a1.idx!=-1 && a2.idx!=-1; // we don't want to connect fc nodes by their centers!
      return (tfc1 || could) && tfc2;
    }

    // datagraph
    let isdatagraph = (fctypes.indexOf(a1.owner.owner.basetype)==-1 && fctypes.indexOf(a2.owner.owner.basetype)==-1);
    if (isdatagraph) {
      // method links
      if (a1.idx==-1 && a2.idx==-1) {
        let tpe1 = a1.owner.owner.basetype;
        let tpe2 = a2.owner.owner.basetype;
        let t1 = tpe1 == "object" && tpe2 == "method";
        let t3 = a1.numconnections == 0;
        let t4 = a2.numconnections == 0;
        return t1 && (t4 || could);
      }
      // type matches or wildcard (pseudo-polymorphism, since not uni-directional)
      let t5 = a1.type == a2.type;
      let t6 = a1.type == '' || a2.type == '';
      let t7 = a1.type == 'obj' || a2.type == 'obj';
      // input nodes must have a well-defined origin
      let t8 = a2.numconnections == 0
      return (t5 || t6 || t7) && (t8 || could);
    }

    // fc->dg centerlinks
    let iscombo = (fctypes.indexOf(a1.owner.owner.basetype)>=0 && fctypes.indexOf(a2.owner.owner.basetype)==-1);
    if (iscombo) {
      // process nodes assigned to objects
      let tcb_1 = a2.owner.owner.basetype == "object"; // assign
      let tcb_5 = a2.owner.owner.basetype == "method"; // read/activate
      let tcb_6 = a2.owner.owner.basetype == "function_named"; // direct function call flag
      let proc_to_func_flag = true; // this will enable/disable tcb_6
      let tcb_2 = a1.owner.owner.basetype == "proc"; // procs can execute
      let tcb_3 = a1.numconnections == 0;
      let tcb_4 = a1.owner.owner.basetype == "term"; // terms also

      // decision nodes connected to (boolean evaluation) functions
      // TODO: includ "obj" and let that be enterprited as null==false, true otherwise
      // OR:   introduce a retfunc which is just a (bool/int returning) func that
      //       happily becomes white/active even without a target obj to catch
      //       its output value
      let anch2 = a2.owner.anchors;
      let a2_tpe = anch2.length > 0 ? anch2[anch2.length-1].type : null; // this one does not have an exit type
      let tcb_1b = ["bool", "int"].indexOf(a2_tpe) >= 0;
      let tcb_2b = a1.owner.owner.basetype == "dec";
      let tcb_3b = a1.numconnections == 0;

      return ((tcb_1 || tcb_5 || (tcb_6 && proc_to_func_flag)) && (tcb_2 || tcb_4) && (tcb_3 || could))  ||  (tcb_1b && tcb_2b && (tcb_3b || could));
    }

    // neither, undefined
    return false;
  }
  static couldConnect(a1, a2) {
    return ConnectionRulesNSGen.canConnect(a1, a2, true);
  }
  static getLinkBasetype(a1, a2) {
    let fctypes = ConnectionRulesNSGen.fctypes;
    let t1 = fctypes.indexOf(a1.owner.owner.basetype)>=0 && fctypes.indexOf(a2.owner.owner.basetype)==-1;
    let t2 = (a1.idx==-1 && a2.idx==-1);
    let t3 = a1.owner.owner.basetype == "dec";
    if (t1 && t2 && !t3)
      return "link_straight";
    if (t1 && t2 && t3)
      return "link_straight_black";
    else if (t2)
      return "link_double_center";
    else
      return "link_single";
  }
  static canConverge(basetypeUp, basetypeDown) {
    let t1 = ConnectionRulesNSGen.fctypes.indexOf(basetypeUp) >= 0;
    let t2 = ConnectionRulesNSGen.fctypes.indexOf(basetypeDown) >= 0;
    return (t1 && t2) || (t1 && !t2);
  }
  static canDiverge(basetypeUp, basetypeDown) {
    let t1 = ConnectionRulesNSGen.fctypes.indexOf(basetypeUp) == -1;
    let t2 = ConnectionRulesNSGen.fctypes.indexOf(basetypeDown) == -1;
    return t1 && t2;
  }
}
ConnectionRulesNSGen.fctypes = ['term', 'proc', 'dec'];

class UserTypeTree {
  constructor(typetree) {
    this.tpes = typetree["tpes"];
    this.functions = typetree["functions"];
    this.methods = typetree["methods"];
  }
}

class GraphInterfaceNSGen extends GraphInterface {
  // cogen event
  rgstrCogenComplete(f) { this._cogenCompleteListeners.push(f); }
  deregCogenComplete(f) { remove(this._cogenCompleteListeners, f); }
  fireCogenComplete(...args) { fireEvents(this._cogenCompleteListeners, "cogenComplete", ...args); }

  // setup
  constructor(gs_id, tab_id) {
    super(gs_id, tab_id, ConnectionRulesNSGen);
    this.allSessionData = null;

    // event handler lists
    this._cogenCompleteListeners = [];
  }

  // label set handling - only set labels on "variables" and flow control nodes
  pushSelectedNodeLabel(text) { // override
    let seln = this.graphData.getSelectedNode();
    let bt = seln.basetype;
    let t1 = ConnectionRulesNSGen.fctypes.indexOf(bt) >= 0;
    let t2 = bt == "object" || bt == "object_typed" || bt == "object_literal"
    if (seln != null && (t1 || t2)) super.node_label(seln.id, text);
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
    // TODO: simplify - server can extract gs_id from the standard request generated by ajaxcall
    this.ajaxcall("/ajax_load/" + this.gs_id, null, function(obj) {
      let error = obj["error"];
      // be explicit about this error
      if (obj["graphdef"] == undefined) {
        alert("no graphdef found in session");
        return;
      }
      // handle server data
      if (error == null) {
        this.reset();
        // set base type tree to match addresses
        intface.setTypeTree(obj);
        // our own custom handle
        this.allSessionData = obj;
        this.injectGraphDefinition(obj["graphdef"]);
        fireEvents(this._onLoadListn, "sessionLoad", obj);
      } else {
        alert(error);
      }
      $("body").css("cursor", "default");
    }.bind(this));
  }
  commitSession() {
    $("body").css("cursor", "wait");
    // allSessionData contains live type trees, and a graphdef slow
    let gd = this.graphData.extractGraphDefinition();
    this.allSessionData['graphdef'] = gd;
    this.ajaxcall("/ajax_commit/", this.allSessionData, function(obj) {
      $("body").css("cursor", "default");
    }.bind(this));
  }
  cogenSession() {
    $("body").css("cursor", "wait");
    // allSessionData contains live type trees, and a graphdef slow
    let gd = this.graphData.extractGraphDefinition();
    this.allSessionData['graphdef'] = gd;
    this.ajaxcall("/ajax_cogen/", this.allSessionData, function(obj) {
      let code_txt = atob(obj["code"])
      console.log(code_txt);
      this.fireCogenComplete(code_txt);
      $("body").css("cursor", "default");
    }.bind(this));
  }
  _resizeCB() {
    // useful line to center some div in the windows:
    //btnsmenu.style("left", window.innerWidth/2-btnsmenu.node().clientWidth/2 + "px");

    // TODO: move this out into graphs.html and put in a resize cb? (localization)
    //let tpeedt = d3.select("#tpeedt_1");

    let tpeedt = d3.select("#tpeedt_wrapper");
    let w = tpeedt.node().getBoundingClientRect().width;
    tpeedt.style("left", window.innerWidth - w + "px");
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
    try {
      obj = JSON.parse(msg);
      if (obj['msg'] != null) console.log(obj['msg']);
    }
    catch(error) {
      console.log("JSON.parse error on server response: ", msg);
      alert("JSON.parse error on server response: ", msg);
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
  get basetype() { return NodeFCTerm.basetype; }
  static get prefix() { return "t"; }
  constructor(x, y, id, name, label, typeconf, iangles=null, oangles=null) {
    if (id == "" && label == "") label = id;
    super(x, y, id, name, label, typeconf, iangles, oangles);
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
  isActive(connectivity) {
    return this.isConnected(connectivity);
  }
}


class NodeFCProcess extends NodeFCTerm {
  static get basetype() { return "proc"; }
  get basetype() { return NodeFCProcess.basetype; }
  static get prefix() { return "p"; }
  isConnected(connectivity) {
    return connectivity.indexOf(false) == -1;
  }
  isActive(connectivity) {
    let active = this.gNode.centerAnchor.numconnections > 0;
    let connected = this.isConnected(connectivity);
    return connected && active;
  }
}

/*
class NodeFCProcessHorizontal extends NodeFCTerm {
  static get basetype() { return "proc"; }
  get basetype() { return NodeFCProcess.basetype; }
  static get prefix() { return "p"; }
  constructor(x, y, id, name, label, typeconf) {
    // TODO: is it better to hide id's? (What use do they have?)
    //if (id == "" && label == "") label = id;
    if (label == "") label = id;
    super(x, y, id, name, label, typeconf, [180], [360]);
  }
  isConnected(connectivity) {
    return connectivity.indexOf(false) == -1;
  }
  isActive(connectivity) {
    let active = this.gNode.centerAnchor.numconnections > 0;
    let connected = this.isConnected(connectivity);
    return connected && active;
  }
}
*/

class NodeFCDec extends Node {
  static get basetype() { return "dec"; }
  get basetype() { return NodeFCDec.basetype; }
  static get prefix() { return "d"; }
  constructor(x, y, id, name, label, typeconf) {
    if (id == "" && label == "") label = id;
    super(x, y, id, name, label, typeconf, [90], [270, 360]);
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
  isActive(connectivity) {
    let active = this.gNode.centerAnchor.numconnections > 0;
    let connected = this.isConnected(connectivity);
    return connected && active;
  }
}


NodeLinkConstrucionHelper.register_node_class(NodeFCTerm);
NodeLinkConstrucionHelper.register_node_class(NodeFCProcess);
NodeLinkConstrucionHelper.register_node_class(NodeFCDec);
