
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
    let cn = null;
    if (res[0] == "type") { // TODO: indicate that "type" is parse level info
      // TODO: introduce typed objects
      //cn = new CreateNode("object_typed", res[1][0])
      return;
    }
    else if (res[0] == "func") { // TODO: indicate that "func" is parse level info
      cn = new CreateNode("function_named", res[1][0]); // or whatever it is ...
      if (res[1].length > 1) recurseArgs(res[1][1], cn);
    }
    else if (res[0] == "method") { // TODO: indicate that "method" is parse level info
      cn = new CreateNode("method", res[1][0] + '.' + res[1][1][0], res[1][0]); // or whatever it is ...
      if (res[1][1].length > 1) recurseArgs(res[1][1][1], cn);
    }
    else throw "createNode: bad format";
    let conf = cn.getNode(this.branch_name);

    // check global tt uniquness - assume existence, look for "not found" exception
    let exists = true;
    try { nodeTypeReadTree(conf.address) } catch { exists = false; }
    if (exists) {
      this._showMsg(conf.name + " already exists in scope");
      return;
    }

    // put into tree
    this.addresses.push(conf.address);
    nodeTypePutTree(conf, conf.name, this.branch_name, this.type_tree);
    // TODO: sort tree & addresses to have methods displayed after their clsses

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
    this.vtd_lst = this.addresses.map( (itm) => {
      let conf = nodeTypeReadTree(itm, this.type_tree);
      // TODO: throw if not found
      return new ViewTypeDef(conf.name, itm, conf, this.fireClickConf.bind(this), this._tryDeleteCB.bind(this));
    }, this);
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


class CreateNode {
  constructor(basetype, name, clss=null) {
    this.basetype = basetype;
    this.name = name; // can include classname, as in MyCls.someMet
    this.args = [];
  }
  addArg(name, tpe=""){
    this.args.push([name, tpe]);
  }
  getNode(branch_name) {
    let conf = {};
    conf.docstring = "";
    conf.type = this.name;
    conf.address = branch_name + "." + this.name;
    conf.basetype = this.basetype;
    conf.ipars = this.args.map( (itm) => {return itm[0]} );
    conf.itypes = this.args.map( (itm) => {return itm[1]} );
    conf.name = this.name;
    return conf;
  }
}

// a parsed "args" nested list is accumulated into a createnode obj
function recurseArgs(res, cn) {
  if (res.length == 1) {
    cn.addArg(name=res[0]);
    return;
  }
  else if (res.length == 2 && !Array.isArray(res[1])) {
    cn.addArg(name=res[1], tpe=res[0]);
    return;
  }
  else if (res.length == 3 && Array.isArray(res[2])) {
    cn.addArg(name=res[1], tpe=res[0]);
    recurseArgs(res[2], cn);
  }
  else if (res.length == 2 && Array.isArray(res[1])) {
    cn.addArg(name=res[0]);
    recurseArgs(res[1], cn);
  }
  else throw "recursArgs: bad format";
}
