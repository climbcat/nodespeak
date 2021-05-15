
class ViewTypeDef {
  constructor(text, address, conf, clickCB, delCB, sortidx=0) {
    this.text = text;
    this.address = address; // passed with del cb
    this.conf = conf; // passed with click cb
    this.clickCB = clickCB;
    this.delCB = delCB;
    this.sidx = sortidx;
  }
  wordClicked() { this.clickCB(this.conf); }
  deleteClicked() { this.delCB(this.address); }
}

function vtdCompareBySortIdxFirst(v1, v2) {
  let ret1 = v1.sidx < v2.sidx ? -1 : v1.sidx > v2.sidx ? 1 : 0;
  if (ret1 != 0) return ret1;
  return v1.text < v2.text ? -1 : v1.text > v2.text ? 1 : 0;
}

class TypeTreeUi {
  // listeners
  rgstrClickConf(l) { this._clickConfListn.push(l); }
  fireClickConf(...args) { fireEvents(this._clickConfListn, "clickConf", ...args); }

  // exclusive_root: WARNING: must be an exclusive, clearable branch
  // addresses: the only ones object this instance of ttui should worry about!
  // type_tree: the actual, entire type tree (global addressing used for now)
  // canDelHook: a function that checks (address) and returns a bool
  constructor(title, exclusive_root, addresses, branch_name, type_tree, canDelHook, usetbx=true) {
    this._clickConfListn = [];
    let root = exclusive_root;

    // data members
    this.title = title;
    this.type_tree = type_tree;
    this.addresses = addresses;
    this.branch_name = branch_name; // this will be prefixed new type words
    this.vtd_lst = [];
    this._canDeleteHook = canDelHook;

    // define base groups for each kind of object
    root.selectAll("*")
      .remove();
    this.typegrp = root.append("g");
    this.statusgrp = root.append("g");

    // input textbox
    let tbxid = "tbxenter" + this.title;
    if (usetbx == true) {
      this.typegrp
        .append("input")
        .style("margin-bottom", "5px")
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
  _checkConfExists(conf, branch_name) {
    let exists = true;
    let addr = [branch_name, conf.type].join(".");
    try { nodeTypeReadTree(addr, this.type_tree) } catch { return false; }
    return true;
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
      conf.label = ""; // a label would be a varname, which the user should set, else we use the id
      conf.sort_idx = 0;
      if (name!=name.toLowerCase()) conf.sort_idx = 1;
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
      conf.sort_idx = 2;
    }
    else if (res[0] == "PRconstr") {
      let name = res[1][0];
      let tpe = res[1][0];
      let args = [];
      let rettpe = tpe; // constructor: ret type is type
      let hasargs = res[1][1] != null;
      if (hasargs > 0) args = res[1][1];
      let cn = new CreateNode("constructor", name, tpe, args, rettpe, true);
      conf = cn.getNode(branch_name);
      conf.sort_idx = 1;
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
      conf.sort_idx = 1;
    }
    else throw "CreateNode bad format: " + res[0];

    // check global tt uniquness - assume existence, look for "not found" exception
    if (this._checkConfExists(conf, "user.builtin") || this._checkConfExists(conf, "user.custom")) {
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
  _clearMsg() {
    this._showMsg("");
  }
  _tryDeleteCB(addr) {
    // clear
    // this._clearMsg();

    // this "delete hook" prevents deletion of types with active graph nodes
    if (this._canDeleteHook != null && !this._canDeleteHook(addr)) {
      this._showMsg(addr + " could not be deleted");
      return false;
    }
    // this prevents classes/types from beng deleted if methods exist
    if (addrHasBranchTypesTree(addr, this.type_tree)) {
      this._showMsg(addr + " could not be deleted (has non-empty branch)");
      return false;
    }
    // del from tt and addresses
    nodeTypeDelTree(addr, this.type_tree);
    remove(this.addresses, addr);
    // show/ sync menus
    this._pullAndShow();
  }
  _showMsg(msg) {
    if (msg == null) return false;
    this.statusgrp.selectAll("*").remove();
    this.statusgrp.append("div").style("margin-top","5px").html(msg);
  }
  _pullAndShow() {
    // clear messages
    this._clearMsg();

    // get objects and sync
    try {
      this.vtd_lst = this.addresses.map( (itm) => {
        let conf = nodeTypeReadTree(itm, this.type_tree);
        let label = conf.name;
        return new ViewTypeDef(label, itm, conf,
          this.fireClickConf.bind(this), this._tryDeleteCB.bind(this),
          conf.sort_idx == undefined ? 0 : conf.sort_idx
        );
      }, this);
    } catch(err) {
      console.log("tpeedt pull: " + err);
    }
    this.vtd_lst.sort(vtdCompareBySortIdxFirst);
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
      .style("margin", "auto");
    let txt_divs = containers
      // text element
      .append("div")
      .style("display", "inline-block")
      .style("cursor", "pointer")
      .on("click", function(d) {
        d.wordClicked();
      })
      .html(function(d) { return d.text; });

    containers
      // delete btn (x) floating to the right
      .append("div")
      .style("margin-left", "25px")
      .style("width", "15px")
      .style("height", "100%")
      .style("background", "white")
      .style("cursor", "pointer")
      .style("float", "right")
      .on("click", function(d) {
        d.deleteClicked();
      })
      .html("x");

    // get max width
    let maxwidth = 0;
    txt_divs
      .each(function(d) {
        let width = d3.select(this).node().getBoundingClientRect().width;
        if (maxwidth < width) maxwidth = width;
      });

    // this should not be done, but I want to finish this project !
    d3.select("#tpeedt_wrapper")
      .style("min-width", maxwidth + 50 + "px")

    // NOTE: duplicate code from nsgen GraphInterfaceNSGen._resizeCB():
    let tpeedt = d3.select("#tpeedt_wrapper");
    let w = tpeedt.node().getBoundingClientRect().width;
    tpeedt.style("left", window.innerWidth - w + "px");

    // reset the text box width
    d3.select("#" + "tbxenter" + this.title)
      .style("width", w - 75 + "px");
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
    this.label = type;
    this.type = type;
    this.args = null;
    this.rettpe = rettpe;
    if (args_result != null) {
      this.args = []; // [name, tpe] entres go here
      this._recurseArgs(args_result);
      // TO the reader: sorry for this line
      this.name += "("+ this.args.map( (itm)=>{
          return (itm[1] + " " + itm[0]).trim();
        }).join(", ") + ")";
      this.label += "()";
    }
    // put a label (including args): name is actually type_tree key, so we need a label to display Cls.Mthd(...)
    // original C-style ret type notation:
    if (rettpe != null && hiderettpe == false) this.name = rettpe + " " + this.name;
    // next-level notation:
    //if (rettpe != null && hiderettpe == false) this.name = this.name + " -> " + rettpe;
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
    conf.otypes = this.rettpe != null ? [this.rettpe] : [];
    if (this.rettpe != null) conf.otypes = [this.rettpe];
    conf.name = this.name;
    conf.label = this.label;
    return conf;
  }
}
