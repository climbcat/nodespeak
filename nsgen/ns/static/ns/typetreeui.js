
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
  constructor(root, addresses, branch_name, type_tree, notbx=false, clickItemCB) {
    this.type_tree = type_tree;
    this.branch_name = branch_name; // this will be prefixed new type words
    this.vtd_lst = [];
    this._clickItemCB = clickItemCB;

    // define base groups for each kind of object
    this.types = root.append("g");
    this.status = root.append("g");

    // create input textbox
    if (!notbx)
      this.types
        .append("div").style("margin-top", "10px")
        .html("| type ")
        .append("input")
        .attr("id", "tbxEnterType")
        .on("change", function(d) {
          let val = d3.select("#tbxEnterType").html();
          console.log("DEBUG:", val);
        });
      // TODO: put docstring as mouse-over or in a label

    // dynamic elements get a subgroup
    this.types = this.types.append("g");

    // get initial objects and sync
    this.vtd_lst = addresses.map( (itm) => {
      let conf = nodeTypeReadTree(itm, this.type_tree);
      // TODO: throw error if conf was not found
      return new ViewTypeDef(conf.name, itm, conf, this._clickItemCB, this._tryDeleteCB);
    }, this);

    // DB
    this._show_msg("DB: test status msg");
  }
  _registerClickConf(cb) {
    this._clickItemCB = cb;
  }
  _tryCreateCB(word) {
    console.log("try create (not impl.)", word);
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
    this.status.selectAll("*").remove();
    this.status.append("div").html(msg);
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
