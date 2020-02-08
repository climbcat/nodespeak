var nodetypes_fc = {
  "term_I": {
    "basetype": "term",
    "type": "term_I",
    "address": "flowchart.term_I",
    "ipars": [
      ""
    ],
    "itypes": [],
    "otypes": [
      "flow"
    ],
    "name": "term_I",
    "label": "",
    "docstring": "Terminal enter program/in."
  },
  "term_O": {
    "basetype": "term",
    "type": "term_O",
    "address": "flowchart.term_O",
    "ipars": [
      ""
    ],
    "itypes": [
      "flow"
    ],
    "otypes": [],
    "name": "term_O",
    "label": "",
    "docstring": "Terminal exit program/out."
  },
  "proc": {
    "basetype": "proc",
    "type": "proc",
    "address": "flowchart.proc",
    "ipars": [
      ""
    ],
    "itypes": [
      "flow"
    ],
    "otypes": [
      "flow"
    ],
    "name": "proc",
    "label": "",
    "docstring": "Process. One process, one data graph subtree call."
  },
  "dec": {
    "basetype": "dec",
    "type": "dec",
    "address": "flowchart.dec",
    "ipars": [
      ""
    ],
    "itypes": [
      "flow"
    ],
    "otypes": [
      "flow",
      "flow"
    ],
    "name": "dec",
    "label": "",
    "docstring": "Binary decision. Requires bool/int returning function or value."
  },
}

var nodetypes_dg = {
  "somefunction": {
    "basetype": "function_named",
    "type": "somefunction",
    "address": "datagraph.somefunction",
    "ipars": [
      "a",
      "b"
    ],
    "itypes": [
      "int",
      "int"
    ],
    "otypes": [
      "bool"
    ],
    "name": "func1",
    "label": "func1",
    "docstring": "test function"
  },
  "somefunction_2": {
    "basetype": "function_named",
    "type": "somefunction_2",
    "address": "datagraph.somefunction_2",
    "ipars": [
      "a",
      "b",
      "c"
    ],
    "itypes": [
      "string",
      "int",
      "bool"
    ],
    "otypes": [
      "bool"
    ],
    "name": "func2",
    "label": "func2",
    "docstring": "test function"
  },
  "somefunction_3": {
    "basetype": "function_named",
    "type": "somefunction_3",
    "address": "datagraph.somefunction_3",
    "ipars": [
      "d"
    ],
    "itypes": [
      "bool"
    ],
    "otypes": [
      "string"
    ],
    "name": "func3",
    "label": "func3",
    "docstring": "test function"
  },
  "object": {
    "basetype": "object",
    "type": "object",
    "address": "datagraph.object",
    "ipars": [
      ""
    ],
    "itypes": [
      ""
    ],
    "otypes": [
      ""
    ],
    "name": "object",
    "label": "",
    "docstring": "test object"
  },
  "literal": {
    "basetype": "object_literal",
    "type": "literal",
    "address": "datagraph.literal",
    "ipars": [
      ""
    ],
    "itypes": [
      ""
    ],
    "otypes": [
      ""
    ],
    "name": "literal",
    "label": "",
    "docstring": "test literal"
  },
  "somemethod": {
    "basetype": "method",
    "type": "somemethod",
    "address": "datagraph.somemethod",
    "ipars": [
      ""
    ],
    "itypes": [
      ""
    ],
    "otypes": [],
    "name": "method",
    "label": "somemethod",
    "docstring": "test method"
  }
}

var categories = [
  "flowchart",
  "datagraph"
];

var nodeAddresses = [
  "flowchart.term_I",
  "flowchart.term_O",
  "flowchart.proc",
  "flowchart.dec",
  "datagraph.somefunction",
  "datagraph.somefunction_2",
  "datagraph.somefunction_3",
  "datagraph.object",
  "datagraph.literal",
  "datagraph.somemethod"
];

var nodeTypes = {
  "flowchart": {
    "leaf": null,
    "branch": {
      "term_I": {
        "leaf": {
          "basetype": "term",
          "type": "term_I",
          "address": "flowchart.term_I",
          "ipars": [
            ""
          ],
          "itypes": [],
          "otypes": [
            "flow"
          ],
          "name": "term_I",
          "label": "",
          "docstring": "Terminal enter program/in."
        },
        "branch": {}
      },
      "term_O": {
        "leaf": {
          "basetype": "term",
          "type": "term_O",
          "address": "flowchart.term_O",
          "ipars": [
            ""
          ],
          "itypes": [
            "flow"
          ],
          "otypes": [],
          "name": "term_O",
          "label": "",
          "docstring": "Terminal exit program/out."
        },
        "branch": {}
      },
      "proc": {
        "leaf": {
          "basetype": "proc",
          "type": "proc",
          "address": "flowchart.proc",
          "ipars": [
            ""
          ],
          "itypes": [
            "flow"
          ],
          "otypes": [
            "flow"
          ],
          "name": "proc",
          "label": "",
          "docstring": "Process. One process, one data graph subtree call."
        },
        "branch": {}
      },
      "dec": {
        "leaf": {
          "basetype": "dec",
          "type": "dec",
          "address": "flowchart.dec",
          "ipars": [
            ""
          ],
          "itypes": [
            "flow"
          ],
          "otypes": [
            "flow",
            "flow"
          ],
          "name": "dec",
          "label": "",
          "docstring": "Binary decision. Requires bool/int returning function or value."
        },
        "branch": {}
      }
    }
  },
  "datagraph": {
    "leaf": null,
    "branch": {
      "somefunction": {
        "leaf": {
          "basetype": "function_named",
          "type": "somefunction",
          "address": "datagraph.somefunction",
          "ipars": [
            "a",
            "b"
          ],
          "itypes": [
            "int",
            "int"
          ],
          "otypes": [
            "bool"
          ],
          "name": "func1",
          "label": "func1",
          "docstring": "test function"
        },
        "branch": {}
      },
      "somefunction_2": {
        "leaf": {
          "basetype": "function_named",
          "type": "somefunction_2",
          "address": "datagraph.somefunction_2",
          "ipars": [
            "a",
            "b",
            "c"
          ],
          "itypes": [
            "string",
            "int",
            "bool"
          ],
          "otypes": [
            "bool"
          ],
          "name": "func2",
          "label": "func2",
          "docstring": "test function"
        },
        "branch": {}
      },
      "somefunction_3": {
        "leaf": {
          "basetype": "function_named",
          "type": "somefunction_3",
          "address": "datagraph.somefunction_3",
          "ipars": [
            "d"
          ],
          "itypes": [
            "bool"
          ],
          "otypes": [
            "string"
          ],
          "name": "func3",
          "label": "func3",
          "docstring": "test function"
        },
        "branch": {}
      },
      "object": {
        "leaf": {
          "basetype": "object",
          "type": "object",
          "address": "datagraph.object",
          "ipars": [
            ""
          ],
          "itypes": [
            ""
          ],
          "otypes": [
            ""
          ],
          "name": "object",
          "label": "",
          "docstring": "test object"
        },
        "branch": {}
      },
      "literal": {
        "leaf": {
          "basetype": "object_literal",
          "type": "literal",
          "address": "datagraph.literal",
          "ipars": [
            ""
          ],
          "itypes": [
            ""
          ],
          "otypes": [
            ""
          ],
          "name": "literal",
          "label": "",
          "docstring": "test literal"
        },
        "branch": {}
      },
      "somemethod": {
        "leaf": {
          "basetype": "method",
          "type": "somemethod",
          "address": "datagraph.somemethod",
          "ipars": [
            ""
          ],
          "itypes": [
            ""
          ],
          "otypes": [],
          "name": "method",
          "label": "somemethod",
          "docstring": "test method"
        },
        "branch": {}
      }
    }
  }
};
