
class ViewTypeDef {
  constructor(text, address, conf, clickCB, delCB) {
    this.text = text;
    this.id = text;
    this.address = address; // passed with del cb
    this.conf = conf; // passed with click cb
    this.clickCB = clickCB;
    this.delCB = delCB;
  }
  wordClicked() { this.clickCB(this.conf); }
  deleteClicked() { this.delCB(this.address); }
}

class TypeTreeUi {
  // addresses: the only ones object this instance of ttui should worry about!
  // type_tree: the actual, entire type tree (global addressing used for now)
  constructor(root, addresses, branch_name, type_tree, clickItemCB, notbx=false) {
    this.type_tree = type_tree;
    this.branch_name = branch_name; // this will be prefixed new type words
    this.vtd_lst = [];
    this._clickItemCB = clickItemCB;

    // define base groups for each kind of object
    this.typegrp = root.append("g");
    this.statusgrp = root.append("g");

    // create input textbox
    if (!notbx) {
      this.typegrp
        .append("div").style("margin-top", "10px")
        .html("| type ")
        .append("input")
        .attr("id", "tbxEnterType")
        .on("change", function(d) {
          let val = d3.select("#tbxEnterType").property("value");
          this._tryCreateType(val);
        }.bind(this));
      // TODO: put docstring as mouse-over or in a label
    }

    // dynamic elements get a subgroup (so we can use delete *)
    this.typegrp = this.typegrp.append("g");

    // get initial objects and sync
    this.vtd_lst = addresses.map( (itm) => {
      let conf = nodeTypeReadTree(itm, this.type_tree);
      // TODO: throw error if conf was not found
      return new ViewTypeDef(conf.name, itm, conf, this._clickItemCB, this._tryDeleteCB);
    }, this);
    this._sync(this.typegrp, this.vtd_lst);
  }
  _registerClickConf(cb) {
    this._clickItemCB = cb;
  }
  _tryCreateType(word) {
    console.log("try create:", word);
    // TODO: parse word -> status and return if error
    // TODO: prefix branch name to create new address
    // TODO: check global tt uniquness -> status and return if error
    // TODO: create conf and enter into tree
    //          -> this requires functionality for doing this, copy from Python
    // TODO: create menu item with appropriate cbs etc.
  }
  _tryDeleteCB(addr) {
    console.log("try delete (not impl.)", addr);
    // returns true on deletion, false otherwise. Deletes by "brute force"
    // TODO: del from tt
    // TODO: del from html
    // TODO: call intface cleanup
  }
  _show_msg(msg) {
    if (msg == null) return false;
    this.statusgrp.selectAll("*").remove();
    this.statusgrp.append("div").html(msg);
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
      .attr("id", function(d) { return d.id })
      .style("text-align", "left")
      .style("margin", "auto");
    containers
      // text element
      .append("div")
      .style("display", "inline-block")
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
