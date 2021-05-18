


function createSubWindow(wname, xpos, ypos, width) {
  let headerheight = 20;
  let container_id = wname + "_container";
  let container = $('<div id="ID">'.replace("ID", container_id))
    .css({
      position : "absolute",
      left : xpos+"px",
      top : ypos+"px",
    })
    .appendTo('body');

  // header
  let header_id = wname + "_header";
  let header = $('<div id="ID">'.replace("ID", header_id))
    .css({
      position : "relative",
      width : width+"px",
      height : headerheight+"px",
      cursor : "grab",
      "background-color" : "#9C9CDE",
      "border-style" : "solid",
      "border-width" : "1px",
      "border-color" : "gray",
      display : "inline-block",
    })
    .appendTo(container)
    .html("")
    .addClass("noselect");

  // close button

  // element
  let closebtn_id = wname + "_closebtn";
  let closebtn = $('<div id="ID">'.replace("ID", closebtn_id))
    .css({
      position : "absolute",
      left : (width-20)+"px",
      top : "0px",
      width : headerheight+"px",
      height : headerheight+"px",
      cursor:"pointer",
      "background-color":"white",
      "border-width":"1px",
      "border-style":"solid",
    })
    .appendTo(container);
  // tooltip
  let closebtn_tooltip = null
  closebtn
    .mouseover(() => {
      closebtn_tooltip = $('<div>close</div>')
        .css({
          position:"absolute",
          top:"-30px",
          left:"-20px",
          width:"50px",
          height:"20px",
          "padding-left":"6px",
          "z-index":"666",
          "background-color":"white",
          "border-width":"1px",
          "border-style":"solid",
          "user-select":"none",
        })
        .appendTo(closebtn)
    })
    .mouseout(() => {
      if (closebtn_tooltip) closebtn_tooltip.remove();
    });
  // event
  $("#"+closebtn_id).click(() => {
    //if (beforeCloseCB != null) beforeCloseCB();
    removeSubWindow(wname);
  });

  // window body area
  let winbody_id = wname + "_body";
  let winbody = $('<div id="ID">'.replace("ID", winbody_id))
    .css({
      "position" : "relative",
      "width" : width + "px",
      "background-color":"white",
      "border-style":"solid",
      "border-width":"1px",
      "border-top":"none",
    })
    .appendTo('#'+container_id)
    .mouseup(() => { if (mouseUpCB != null) mouseUpCB() } );

  // generic mouse events: collapse and close
  $("#"+header_id).dblclick(() => {
      $("#"+winbody_id).toggle();
  });

  // window drag functionality
  var isDragging = false;
  let maybeDragging = false;
  $("#"+container_id)
    .draggable({
      cancel: "#" + winbody_id,
      containment: "body",
    })
    .mousedown(function() {
      isDragging = false;
      maybeDragging = true;
    })
    .mousemove(() => {
      //if (maybeDragging && isDragging && mouseMoveCB != null) mouseMoveCB(); else
      isDragging = true;
    })
    .mouseup(function() {
      maybeDragging = false;
      var wasDragging = isDragging;
      isDragging = false;
      if (!wasDragging) $("#throbble").toggle();
    });

  return [winbody_id, container_id];
}







class IdxEditWindow {
  // This class is a multi-purpose window containing a plotter, a browser, and an index editor all in one.
  constructor(wname, xpos, ypos, titleadd=null) {
    // PlotWindow
    this.sizeCB = this._toggleSizeCB.bind(this);

    this.large = false;
    this.body_container = null;

    // shared
    this.titleadd = titleadd;
    this.sizes = [380, 235, 900, 600];
    this.wname = wname;

    removeSubWindow(this.wname);
    this._createSubWindow(xpos, ypos, this.w);
    this.reDraw();
  }
  // PlotWindow section
  _toggleSizeCB() {
    let prev_w = this.w;
    let prev_h = this.h;
    this.large = !this.large;
    let w = this.w;
    let h = this.h;
    let left = this.left + prev_w/2 - w/2;
    let top = this.top + prev_h/2 - h/2;
    left = Math.max(left, 0);
    top = Math.max(top, 0);

    removeSubWindow(this.wname)
    this._createSubWindow(left, top, w);

    this._update_ui();
  }
  get w() {
    if (this.large) return this.sizes[2]
    return this.sizes[0];
  }
  get h() {
    if (this.large) return this.sizes[3]
    return this.sizes[1];
  }
  get x() {
    let pos = $("#"+this.body_container[1]).position();
    if (pos) return pos.left + this.w/2;
  }
  get y() {
    let pos = $("#"+this.body_container[1]).position();
    if (pos) return pos.top + this.h/2;
  }
  get left() {
    let pos = $("#"+this.body_container[1]).position();
    if (pos) return pos.left;
  }
  get top() {
    let pos = $("#"+this.body_container[1]).position();
    if (pos) return pos.top;
  }
  reDraw() {
    let state = this.model.get_state();
    // nothing to draw - set body size as a window filler / reset body size
    if (state == 0 || state == 3) {
      $("#" + this.body_container[0])
        .css({
          "height" : this.h,
        })
      this._hide_browser();
      return false;
    } else {
      $("#" + this.body_container[0])
        .css({
          "height" : "",
        });
      // reset browser visibility to default
      this._show_browser();
    }

    // get
    let lst = this.model.get_plots();
    let ndims = this.model.get_ndims();
    for (let i=0;i<lst.length;i++) {
      let plotdata = lst[i];
      if (!plotdata) continue;

      // proceed only if ndims match
      if (plotdata.ndims != ndims) continue;

      // plot
      plotdata.title = '';
      plotdata.w = this.w;
      plotdata.h = this.h;

      if (this.plot == null) {
        if (ndims == 1) {
          this.plot = new Plot1D(plotdata, this.plotbranch, this.logscale, this.wname);
          this.plot.rgstrMouseClickPlot(this.clickPlotCB);
        }
        if (ndims == 2) {
          this.plot = new Plot2D(plotdata, this.plotbranch, this.logscale);
        }
      } else {
        if (ndims == 1) this.plot.plotOneMore(plotdata);
        if (ndims == 2) throw "2D multiplot is not supported";
      }
    }

    // update window title
    let ids = this.model.get_plt_node_ids();
    let title = ids[0];
    for (let i=0;i<ids.length-1;i++) {
      title = title + ", " + ids[i+1];
    }
    if (this.titleadd) title = title + ": " + this.titleadd;
    setSubWindowTitle(this.wname, title);
  }

  // IdxEdtWindow section
  _push_tarea_value() {
    // push current value to text area
    let tarea = $('#' + this.wname + "_tarea");
    let newval = this.model.get_value();
    if (newval == null) tarea.val(""); else tarea.val(JSON.stringify(newval, null, 2));
  }
  _pull_tarea_value() {
    // pull current value from text area
    let tarea = $('#'+this.wname+"_tarea");
    let rawval = "" + tarea.val();
    if (rawval == "") rawval = "null";
    let val = null;
    try {
      if (rawval != 0) val = JSON.parse(rawval, null, 2); else val = 0;
    }
    catch {
      console.log("IdxEdt: could not push current non-JSON value: '" + rawval + "'");
      return false;
    }
    // WARNING: js doesn't handle the value 0 very well, because it is the prefix of octals.
    // for some reason, checking val=="" for val==0, trigggers val=""
    if (val != 0 && val == "") val = null;
    this.model.set_value(val);
  }
  _submit() {
    let obj = this.model.try_get_submit_obj();
    if (obj == null) {
      alert('Could not submit values.');
    } else {
      this.node_dataCB(this.model.val_node.id, JSON.stringify(obj));
    }
  }
  // shared
  close() {
    removeSubWindow(this.wname);
    this.body_container = null;
    this._closeOuterCB(this);
  }
  dropNode(n) {
    if (n.type == "idata" || n.type == "ifunc") {
      let ans = this.model.try_add_plt_node(n);
      if (ans == true) {
        this._update_ui();
      }
      return ans;
    }
    else if (n.type == "literal") {
      // data model
      if (!this.model.try_add_val_node(n)) return false;

      // view actions
      this._push_tarea_value();
      this._update_ui();
      return true;
    }
    return false;
  }
  extractNode(nodeid, force=false) {
    if (this.model.try_remove_plt_node(nodeid)) {
      if (this.model.get_num_clients() > 0) this.reDraw();
      return true;
    }
    return false;
  }
  numClients() {
    return this.model.get_num_clients();
  }
  get x() {
    let pos = $("#"+this.body_container[1]).position();
    if (pos) return pos.left + this.w/2;
  }
  get y() {
    let pos = $("#"+this.body_container[1]).position();
    if (pos) return pos.top + this.h/2;
  }
  get left() {
    let pos = $("#"+this.body_container[1]).position();
    if (pos) return pos.left;
  }
  get top() {
    let pos = $("#"+this.body_container[1]).position();
    if (pos) return pos.top;
  }
  _toggleEditor(){
    this._editor = !this._editor;
    this._renderEditor();
  }
  _renderEditor(){
    if (this._editor==true) {
      $("#" + this.wname + "_edtcontainer").show();
    } else {
      $("#" + this.wname + "_edtcontainer").hide();
    }
  }
  _removeEmptySpace() {
    $("#" + this.wname + "_empty").remove();
  }
  _createSubWindow(xpos, ypos, width, height) {
    // standard window
    this.body_container = createSubWindow(
      this.wname, this.mouseupCB, this.dragCB, this.closeCB, xpos, ypos, width, height);
    addHeaderButtonToSubwindow(this.wname, "log", 1, this.logscaleCB, "lightgray");
    addHeaderButtonToSubwindow(this.wname, "size", 2, this.sizeCB, "gray");
    this.btnedt_id = addHeaderButtonToSubwindow(this.wname, "editor", 3, this._toggleEditor.bind(this), "dimgray");

    // header buttons size and log
    let edt_container =
      $("<div id=ID></div>".replace("ID", this.wname + "_edtcontainer"))
      .css({
      });
    let tarea = $('<textarea rows=5 id=ID></textarea>'.replace("ID", this.wname + "_tarea"))
      .css({
        resize: "none",
        width: "99%",
      })
      .appendTo(edt_container)
      .change(this._pull_tarea_value.bind(this));
    let buttons_div = $("<div id=ID></div>".replace("ID", this.wname + "_buttons"))
      .css({
        "margin" : "auto",
        "text-align" : "right",
      })
      .appendTo(edt_container);
    let btn1 = $('<button id="'+ this.wname + '_btn2"' +'>To All</button>')
      .click(this.model.do_copy_to_all.bind(this.model))
      .appendTo(buttons_div);
    let btn2 = $('<button id="'+ this.wname + '_btn"' +'>Submit</button>')
      .click(this._submit.bind(this))
      .appendTo(buttons_div);

    // index browser
    let brws_container = $("<div id=ID></div>".replace("ID", this.wname + "_browsecontainer"))
      .css({
        "margin" : "auto",
        "width" : width,
        "position" : "absolute",
      });
    let brws_div = $("<div id=ID></div>".replace("ID", this.wname + "_browser"))
      .css({
        "margin-top" : "2px",
        "padding-top" : "2px",
        "text-align" : "center",
        "border" : "none",
      })
      .appendTo(brws_container);
    let prev = $("<div id=ID></div>".replace("ID", this.wname + "_prev"))
      .css({
        "width" : "25px",
        "height" : "20px",
        "text-align" : "center",
        "border" : "1px solid blue",
        "display" : "inline-block",
        "cursor" : "pointer",
        "background-color" : "white",
      })
      .html("<")
      .click(this._prev.bind(this))
      .appendTo(brws_div);
    let next = $("<div id=ID></div>".replace("ID", this.wname + "_next"))
      .css({
        "width" : "25px",
        "height" : "20px",
        "text-align" : "center",
        "border" : "1px solid blue",
        "border-left" : "none",
        "display" : "inline-block",
        "cursor" : "pointer",
        "background-color" : "white",
        })
      .html(">")
      .click(this._next.bind(this))
      .appendTo(brws_div);

    // add editor elements
    addElementToSubWindow(this.wname, brws_container);
    addElementToSubWindow(this.wname, edt_container);
    this._renderEditor();

    // update title
    setSubWindowTitle(this.wname, "Right-drag nodes to plot");
  }
  _hide_tarea() {
    $("#" + this.wname + "_edtcontainer").hide();
  }
  _show_tarea() {
    $("#" + this.wname + "_edtcontainer").show();
  }
  _hide_browser() {
    $("#" + this.wname + "_browsecontainer").hide();
  }
  _show_browser() {
    $("#" + this.wname + "_browsecontainer").show();
  }
  _hide_btnedt() {
    $("#" + this.btnedt_id).hide();
  }
}
function removeSubWindow(wname) {
  // this should (also) be called automatically if a user clicks close, after the closeCB has been called
  $("#"+wname+"_container").remove();
}
function setSubWindowTitle(wname, title) {
  $("#"+wname+"_header")
    .html(title);
}
function addHeaderButtonToSubwindow(wname, tooltip, idx, onClick, colour="white") {
  let container = $("#"+wname+"_container");
  let width = container.width();
  let headerheight = $("#"+wname+"_header").height();

  // button
  let btn_id = wname + "_headerbtn_" + idx;
  let btn = $('<div id="ID">'.replace("ID", btn_id))
    .css({
      position : "absolute",
      left : (width-2-20*(idx+1))+"px",
      top : "0px",
      width : headerheight+"px",
      height : headerheight+"px",
      cursor : "pointer",
      "background-color" : colour,
      "border-width" : "1px",
      "border-style" : "solid",
    })
    .appendTo(container);

  // tooltip
  let div_tt = null
  btn
    .mouseover(() => {
      div_tt = $('<div>'+tooltip+'</div>')
        .css({
          position:"absolute",
          top:"-30px",
          left:"-20px",
          width:"50px",
          height:"20px",
          "padding-left":"6px",
          "z-index":"666",
          "background-color":"white",
          "border-width":"1px",
          "border-style":"solid",
          "user-select":"none",
        })
        .appendTo(btn)
    })
    .mouseout(() => {
      if (div_tt) div_tt.remove();
    });

    // click event
    $("#"+btn_id).click(onClick);

    // return the id of said button
    return btn_id;
}
function addElementToSubWindow(wname, element) {
  element
    .appendTo("#" + wname + "_body");
}
