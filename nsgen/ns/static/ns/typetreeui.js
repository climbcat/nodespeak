
class ViewTypeDef {
  constructor(text, address, conf, clickCB, delCB) {
    this.text = text;
    this.address = address; // passed with del cb
    this.conf = conf; // passed with click cb
    this.clickCB = clickCB;
    this.delCB = delCB;
  }
  wordClicked() { this.clickCB(this.conf); }
  deleteClicked() { this.delCB(this.address); }
}

class TypeTreeUi {
  // listeners
  rgstrClickConf(l) { this._clickConfListn.push(l); }
  fireClickConf(...args) { fireEvents(this._clickConfListn, "clickConf", ...args); }

  // addresses: the only ones object this instance of ttui should worry about!
  // type_tree: the actual, entire type tree (global addressing used for now)
  constructor(title, root, addresses, branch_name, type_tree, usetbx=true) {
    this._clickConfListn = [];

    // data members
    this.title = title;
    this.type_tree = type_tree;
    this.addresses = addresses;
    this.branch_name = branch_name; // this will be prefixed new type words
    this.vtd_lst = [];

    // define base groups for each kind of object
    this.typegrp = root.append("g");
    this.statusgrp = root.append("g");
    // input textbox
    let tbxid = "tbxenter" + this.title;
    if (usetbx == true) {
      this.typegrp
        .append("input")
        .attr("id", tbxid)
        .on("change", function(d) {
          let el = d3.select("#" + tbxid);
          let val = el.property("value");
          this._tryCreateType(val);
          // clear
          el.property("value", "");
        }.bind(this));
      // TODO: docstring
    }
    // dynamic elements get a subgroup (so we can use delete *)
    this.typegrp = this.typegrp.append("g");

    this._pullAndShow();
  }
  _tryCreateType(word) {
    // parse word -> status and return if error
    let parseresult = null;
    try {
      parseresult = tpeparser.parse(word);
    } catch(err) {
      // TODO: find "Expected" or "Unrecognized" and show err from that point
      this._showMsg(err.message);
      return;
    }

    // create conf
    let res = parseresult;
    let conf = null;
    let branch_name = this.branch_name; // NOTE: this is not the same for methods, as for the rest
    if (res[0] == "PRtype") {
      let name = res[1][0];
      let cn = new CreateNode("object_typed", name, name)
      conf = cn.getNode(branch_name);
    }
    else if (res[0] == "PRfunc") {
      let name = res[1][0];
      let tpe = res[1][0];
      let args = [];
      let rettpe = null;
      let hasrettpe = res[1].length == 3;
      if (hasrettpe == true) rettpe = res[1][2];
      let hasargs = res[1][1] != null;
      if (hasargs > 0) args = res[1][1];
      let cn = new CreateNode("function_named", name, tpe, args, rettpe);
      conf = cn.getNode(branch_name);
    }
    else if (res[0] == "PRconstr") {
      let name = res[1][0];
      let tpe = res[1][0];
      let args = [];
      let rettpe = tpe; // constructor: ret type is type
      let hasargs = res[1][1] != null;
      if (hasargs > 0) args = res[1][1];
      let cn = new CreateNode("function_named", name, tpe, args, rettpe, true);
      conf = cn.getNode(branch_name);
    }
    else if (res[0] == "PRmethod") {
      let name = res[1][0] + '.' + res[1][1][0];
      let cls = res[1][0];
      let tpe = res[1][1][0];
      let args = [];
      let rettpe = null;
      let hasrettpe = res[1].length == 3;
      if (hasrettpe == true) rettpe = res[1][2];
      let hasargs = res[1][1][1]!=null;
      if (hasargs > 0) args = res[1][1][1];
      let cn = new CreateNode("method", name, tpe, args, rettpe);
      branch_name += "." + cls;
      conf = cn.getNode(branch_name);
    }
    else throw "createNode bad format: " + res[0];

    // check global tt uniquness - assume existence, look for "not found" exception
    let exists = true;
    try { nodeTypeReadTree(conf.address, this.type_tree) } catch { exists = false; }
    if (exists) {
      this._showMsg(conf.address + " already exists in scope");
      return;
    }

    // type check the new conf
    let check_builtin = checkConfTypes(conf, "user.builtin", this.type_tree);
    let check_custom = checkConfTypes(conf, "user.custom", this.type_tree);
    if (!check_builtin && !check_custom) {
      this._showMsg("missing type for: " + conf.name);
      return;
    }

    // put into tree
    try {
      nodeTypePutTree(conf, conf.type, branch_name, this.type_tree);
      this.addresses.push(conf.address);
      // TODO: sort tree & addresses to have methods displayed after their clsses
    } catch (err) {
      console.log(err);
      return;
    }

    // show/ sync menus
    this._pullAndShow();
  }
  _tryDeleteCB(addr) {
    // del from tt and addresses
    nodeTypeDelTree(addr, this.type_tree);
    remove(this.addresses, addr);
    // show/ sync menus
    this._pullAndShow();
  }
  _showMsg(msg) {
    if (msg == null) return false;
    this.statusgrp.selectAll("*").remove();
    this.statusgrp.append("div").html(msg);
  }
  _pullAndShow() {
    // get initial objects and sync
    try {
      this.vtd_lst = this.addresses.map( (itm) => {
          let conf = nodeTypeReadTree(itm, this.type_tree);
          // TODO: throw if not found
          let label = conf.name;
          return new ViewTypeDef(label, itm, conf, this.fireClickConf.bind(this), this._tryDeleteCB.bind(this));
      }, this);
    } catch(err) {
      console.log("tpeedt pull: " + err);
    }
    this._sync(this.typegrp, this.vtd_lst);
  }
  _sync(group, vtd_lst) {
    group
      // clear everything
      .selectAll("div")
      .remove();
    let containers = group
      // line container div
      .selectAll("div")
      .data(vtd_lst)
      .enter()
      .append("div")
      .style("text-align", "left")
      .style("margin", "auto");
    containers
      // text element
      .append("div")
      .style("display", "inline-block")
      .style("cursor", "pointer")
      .on("click", function(d) {
        d.wordClicked();
      })
      .html(function(d) { return d.text; })
    containers
      // delete btn (x)
      .append("div")
      .style("display", "inline-block")
      .style("margin-left", "25px")
      .style("width", "15px")
      .style("height", "100%")
      .style("background", "white")
      .style("cursor", "pointer")
      .on("click", function(d) {
        d.deleteClicked();
      })
      .html("x");
  }
}

function checkConfTypes(conf, branch_name, type_tree) {
  // Check if all types used by conf exist in the type tree.
  // The check is based on existing type or constructor entries.
  let st = conf.type;
  let ot = conf.otypes[0];
  let hits = conf.itypes.concat(conf.otypes).map( (tpe) => {
    if (tpe == "" || tpe == null) return true;
    return checkTpeExists(tpe, st, branch_name, type_tree);
  } );
  if (hits.indexOf(false) > -1) return false;
  return true;
}

function checkTpeExists(tpe, self_type, branch_name, type_tree) {
  // 1. self-satisfaction
  if (tpe == self_type) return true;
  // 2. external satisfaction
  let address = [branch_name, tpe].join(".");
  let exists = true;
  conf = null;
  try { conf = nodeTypeReadTree(address, type_tree) } catch { exists = false; }
  if (exists==true) {
    exists = false;
    if (conf.basetype == "object_typed") exists = true;
    if (conf.basetype == "function_named" && tpe.match(/[A-Z][\w0-9]*$/)) exists = true;
  }
  return exists;
}


class CreateNode {
  constructor(basetype, name, type, args_result=null, rettpe=null, hiderettpe=false) {
    this.basetype = basetype;
    this.name = name;
    this.label = name;
    this.type = type;
    this.args = null;
    this.rettpe = rettpe;
    if (args_result != null) {
      this.args = []; // [name, tpe] entres go here
      this._recurseArgs(args_result);
      // TO the reader: sorry for this line
      this.name += "(" + this.args.map((itm)=>{ return (itm[1] + " " + itm[0]).trim(); }).join(", ") + ")";
      this.label += "()";
    }
    // put a label (including args): name is actually type_tree key, so we need a label to display Cls.Mthd(...)
    if (rettpe != null && hiderettpe == false) this.name = rettpe + " " + this.name;
  }
  _recurseArgs(args_result) {
    let res = args_result;
    if (res.length == 0)
      return;
    if (res.length == 1) {
      this.args.push([res[0], ""]);
      return;
    }
    else if (res.length == 2 && !Array.isArray(res[1])) {
      this.args.push([res[1], res[0]]);
      return;
    }
    else if (res.length == 3 && Array.isArray(res[2])) {
      this.args.push([res[1], res[0]]);
      this._recurseArgs(res[2]);
    }
    else if (res.length == 2 && Array.isArray(res[1])) {
      this.args.push([res[0], ""]);
      this._recurseArgs(res[1]);
    }
    else throw "recursArgs: bad format";
  }
  getNode(branch_name) {
    let conf = {};
    conf.docstring = "";
    conf.type = this.type;
    conf.address = branch_name + "." + this.type;
    conf.basetype = this.basetype;
    conf.ipars = ( this.args==null ? [] : this.args.map((itm) => {return itm[0]}) );
    conf.itypes = ( this.args==null ? [] : this.args.map((itm) => {return itm[1]}) );
    conf.otypes = [this.type];
    if (this.rettpe != null) conf.otypes = [this.rettpe];
    conf.name = this.name;
    conf.label = this.label;
    return conf;
  }
}
