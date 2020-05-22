
class ViewTypeDef {
  constructor(text) {
    // TODO: filter here OR filter in the TpeModel try_create functions
    this.text = text;
    this.id = text;
  }
}

class TpeModel {
  constructor() {
    this.types = [];
    this.functions = [];
    this.classes = [];
    this.methods = [];
  }
  get_types() { return this.types; }
  get_functions() { return this.functions; }
  get_classes() { return this.classes; }
  get_methods() { return this.methods; }
  _try_add_to_vtd_lst(lst, word, lstname) {
    if (lst.map(d=>d.text).indexOf(word)==-1) {
      lst.push(new ViewTypeDef(word));
      return "";
    } else {
      return lstname + " " + word + " already exists";
    }
  }
  try_create_type(word) {
    if (/^[a-z][a-zA-Z0-9]*$/.test(word))
      return this. _try_add_to_vtd_lst(this.types, word, "type");
    else
      return "must be single lowercased word containing letters and numbers";
  }
  try_create_function(word) {
    return this. _try_add_to_vtd_lst(this.functions, word, "function");
  }
  try_create_class(word) {
    // TODO: filter word as class
    return this. _try_add_to_vtd_lst(this.classes, word, "class");
  }
  try_create_method(word) {
    // TODO: filter word as method (must append existing classes)
    return this. _try_add_to_vtd_lst(this.methods, word, "method");
  }
  try_del_obj(obj) {
    // returns true on deletion, false otherwise. Deletes by "brute force"
    if(remove(this.types, obj) || remove(this.functions, obj) || remove(this.classes, obj) || remove(this.methods, obj))
      return obj.text + " was deleted";
    return null;
  }
}

class TypeTreeUi {
  constructor(root, tpe_model) {
    this.tpe_model = tpe_model;

    // define base groups for each kind of object
    this.types = root.append("g");
    this.functions = root.append("g");
    this.classes = root.append("g");
    this.methods = root.append("g");
    this.status = root.append("g");

    // create static elements
    this.types
      .append("div").style("margin-top", "10px")
      .html("| type ")
      .append("input")
      .attr("id", "tbxTypes");
    this.functions
      .append("div").style("margin-top", "10px")
      .html("| function ")
      .append("input")
      .attr("id", "tbxFunctions");
    this.classes
      .append("div").style("margin-top", "10px")
      .html("| class ")
      .append("input")
      .attr("id", "tbxClasses");
    this.methods
      .append("div").style("margin-top", "10px")
      .html("| method ")
      .append("input")
      .attr("id", "tbxMethods");

    // let dynamic elements get their own gruop
    this.types = this.types.append("g");
    this.functions = this.functions.append("g");
    this.classes = this.classes.append("g");
    this.methods = this.methods.append("g");

    // put some events into the text boxes using jquery
    this._box_onchange_setup( "#tbxTypes",
      this.types,
      this.tpe_model.try_create_type.bind(this.tpe_model),
      this.tpe_model.get_types.bind(this.tpe_model));
    this._box_onchange_setup( "#tbxFunctions",
      this.functions,
      this.tpe_model.try_create_function.bind(this.tpe_model),
      this.tpe_model.get_functions.bind(this.tpe_model));
    this._box_onchange_setup( "#tbxClasses",
      this.classes,
      this.tpe_model.try_create_class.bind(this.tpe_model),
      this.tpe_model.get_classes.bind(this.tpe_model));
    this._box_onchange_setup( "#tbxMethods",
      this.methods,
      this.tpe_model.try_create_method.bind(this.tpe_model),
      this.tpe_model.get_methods.bind(this.tpe_model));
  }
  _box_onchange_setup(box_id, group, create_fct, get_fct) {
    $(box_id).keypress((event) => {
      if (event.keyCode == 13) {
        let val = $(box_id).val();
        let errmsg = create_fct(val);
        this._show_msg(errmsg);
        if (!errmsg) $(box_id).val(""); // clear the box if no message was returned
        this._sync(group, get_fct());
      }
    });
  }
  _clear_tbx(box_id) {

  }
  _show_msg(msg) {
    if (msg == null) return false;
    this.status.selectAll("*").remove();
    this.status.append("div").html(msg);
  }
  _sync_all() {
    this._sync(this.types, this.tpe_model.get_types());
    this._sync(this.functions, this.tpe_model.get_functions());
    this._sync(this.classes, this.tpe_model.get_classes());
    this._sync(this.methods, this.tpe_model.get_methods());
  }
  _sync(group, vtd_lst) {
    group
      .selectAll("div")
      .remove();
    let containers = group
      .selectAll("div")
      .data(vtd_lst)
      .enter()
      .append("div")
      .attr("id", function(d) { return d.id })
      .style("text-align", "left")
      .style("margin", "auto");
    containers
      .append("div")
      .html(function(d) { return d.text; })
      .style("display", "inline-block");
    containers
      .append("div")
      .style("display", "inline-block")
      .style("margin-left", "25px")
      .style("width", "15px")
      .style("height", "100%")
      .style("background", "white")
      .style("cursor", "pointer")
      .on("click", function(d) {
        let msg = this.tpe_model.try_del_obj(d);
        // TODO: clear the textbox
        this._sync_all();
        this._show_msg(msg);
      }.bind(this))
      .html("x");
  }
}
