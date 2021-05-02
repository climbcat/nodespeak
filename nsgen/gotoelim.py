'''
Goto elimination algorithm.

Follows Erosa/Hendren'94, with a reduced detail level owing to the reduced complexity of 
goto's generate from flow-charts (we have no else-branches).
'''
from queue import LifoQueue
from simplegraph import *
from ast import *


class LogASTs:
    '''
    Apply to study the evolution of the AST through the goto-elim process.
    '''
    def __init__(self, enable=True):
        self.enable = enable
        self.idx = -1
        self.messages = []
        self.clones = []
    def log(self, message, ast):
        if self.enable is False:
            return
        self.messages.append(message)
        self.clones.append(AST_clone_tree(ast))
    def next(self):
        self.idx += 1
        if self.idx >= len(self.messages):
            return None, None
        return self.messages[self.idx], self.clones[self.idx]
    def last_ast(self):
        return self.clones[-1]
    def first_ast(self):
        return self.clones[0]
    def steps(self):
        return len(self.clones)


def goto_elimination_alg(gotos, lbls, ast, log_enable=True, allnodes=None):
    '''
    Goto-elimination procedure. Returns step-py-step 
    '''
    # TODO: intialize logical vars for evey label (initialized to false), AND initialized to false before the label
    init_logical_labelvars_start(gotos, lbls, ast)
    reinit_logical_labelvars(gotos, lbls)

    log_evlolution = LogASTs(log_enable)
    log_evlolution.log("initial state:", ast)

    # select goto/lbl pair
    for goto in gotos:
        lbl = lbls[goto]

        while indirectly_related(goto, lbl):
            move_out_of_loop_or_if(goto)
            log_evlolution.log("move_out_of_loop_or_if:", ast)

        while directly_related(goto, lbl):
            if level(goto) > level(lbl):
                move_out_of_loop_or_if(goto)
                log_evlolution.log("move_out_of_loop_or_if:", ast)
            else:
                lblstm = find_directly_related_lblstm(goto, lbl)
                if offset(goto) > offset(lblstm):
                    lift_above_lblstm(goto, lblstm)
                    log_evlolution.log("lift_above_lblstm:", ast)
                else:
                    move_into_loop_or_if(goto, lbl)
                    log_evlolution.log("move_into_loop_or_if:", ast)

        if siblings(goto, lbl):
            if offset(goto) < offset(lbl):
                eliminate_by_cond(goto, lbl)
                log_evlolution.log("eliminate_by_cond:", ast)
            else:
                eliminate_by_dowhile(goto, lbl)
                log_evlolution.log("eliminate_by_while:", ast)
        else:
            raise Exception("elimination fail")

    return log_evlolution

def reinit_logical_labelvars(gotos, lbls):
    ''' (Re-)init a boolean variable "goto_i" to false exactly at every goto '''
    for getter in gotos:
        lbl = lbls[getter]
        init_to_false = AST_bassign(AST_bvar("goto_%d" % getter.index), AST_false())
        _insert_before(node=init_to_false, before=lbl)

def init_logical_labelvars_start(gotos, lbls, ast):
    ''' Create a boolean var "goto_i" initialized to false for every goto, just after the ast root '''
    if type(ast) is not AST_root:
        raise Exception("init_logical_labelvars_start required: ast is root")
    for getter in gotos:
        lbl = lbls[getter]
        init_to_false = AST_bassign(AST_bvar("goto_%d" % getter.index), AST_false())
        _insert_before(node=init_to_false, before=ast.block)

def find_directly_related_lblstm(blocknode, lbl) -> AST_STM:
    ''' find stm in block containing, or being, lbl. Assumnes level(blocknode) <= level(lbl) and directly related '''
    lvldiff = level(lbl) - level(blocknode)
    node = lbl
    if lvldiff < 0:
        raise Exception("find_lblstm fail: l(g) must be < l(l)")
    if lvldiff == 0:
        return lbl # here we assume directly related(!)
    while lvldiff > 0:
        while node.prev != None and node.up == None:
            node = node.prev
        if node.up != None:
            node = node.up
            lvldiff = lvldiff -1
        if lvldiff == 0 and issubclass(type(node), AST_FORK):
            return node
    raise Exception("find_directly_related_lblstm: find_lblstm fail: did not converge, are blocknode and lbl directly related?")

def indirectly_related(goto, lbl) -> bool:
    if siblings(goto, lbl):
        return False
    elif directly_related(goto, lbl):
        return False
    else:
        return True
def directly_related(goto, lbl) -> bool:
    lvlgoto = level(goto)
    lvllbl = level(lbl)
    if lvlgoto == lvllbl:
        # must be siblings or indirectly related
        return False
    else:
        # can be directly or indirectly related
        n1 = goto
        n2 = lbl
        goto_parents = []
        common_parent = None

        # map all nodes above goto, return if lbl is encountered
        while type(n1) != AST_root:
            if n1.prev != None:
                n1 = n1.prev
            elif n1.up != None:
                n1 = n1.up
            if n1 == lbl:
                return True
            goto_parents.append(n1)

        # search above lbl for any marked, return if goto is encountered
        while common_parent == None:
            if n2.prev != None:
                n2 = n2.prev
            elif n2.up != None:
                n2 = n2.up
            if n2 == goto:
                return True
            elif n2 in goto_parents:
                common_parent = n2

        # common parent must be on level with goto or lbl
        lvlcommon = level(common_parent)
        if lvlcommon == lvlgoto or lvlcommon == lvllbl:
            return True
        else:
            return False
def siblings(goto, lbl) -> bool:
    ogoto = offset(goto)
    olbl = offset(lbl)
    node = None
    node2 = None
    if ogoto < olbl:
        node = lbl
        node2 = goto
    else:
        node = goto
        node2 = lbl

    while node != node2:
        if node.prev != None:
            node = node.prev
        else:
            return False
    return True

def level(node) -> int:
    lvl = -1
    while type(node) != AST_root:
        while node.prev != None:
            node = node.prev
        if node.up != None: # node.up could be root, since this is how root is attached
            lvl = lvl + 1
            node = node.up
    return lvl
def offset(node) -> int:
    ''' returns the offset/index within the current block '''
    offset = 0
    while node.prev != None:
        node = node.prev
        offset = offset + 1
    return offset
def is_in_loop(node) -> bool:
    ''' is node in the block of a while or dowhile '''
    while node.prev != None:
        node = node.prev
    if node.up == None:
        raise Exception("is_in_loop: node.up xor node.prev must be set")
    if type(node.up) in (AST_while, AST_dowhile):
        return True
    else:
        return False
def is_in_if(node) -> bool:
    ''' is node in the block of an if '''
    while node.prev != None:
        node = node.prev
    if node.up == None:
        raise Exception("is_in_if: node.up xor node.prev must be set")
    if type(node.up) == AST_if:
        return True
    else:
        return False

def move_out_of_loop_or_if(goto):
    # map goto context
    node = goto
    loop = None
    while node.prev != None:
        node = node.prev
    if node.up:
        loop = node.up # the while, dowhile or if containing the goto
    else:
        raise Exception("move_out_of_loop_or_if: loop/if not found")
    stm_after_goto = goto.next
    stm_before_goto = goto.prev
    org_goto_ifcond = goto.ifcond

    # create replacing nodes
    bvar = AST_bvar("goto_%s" % goto.index)
    bass = AST_bassign(bvar, goto.ifcond)
    if_replacing_goto = AST_if(AST_not(bvar))

    # first, extract, redefine and re-insert the goto after the loop
    _remove(goto)
    goto.ifcond = bvar
    _insert_after(goto, loop)

    # repair the hole where the goto was
    if stm_after_goto != None:
        # there is some statement after the goto
        _insert_before(bass, stm_after_goto)
        _insert_loop_or_if_above(if_replacing_goto, stm_after_goto) # the block tail carries over
    elif stm_before_goto != None:
        # there are only statements before the goto
        _insert_after(bass, stm_before_goto)
    else:
        # the block consists only of the goto
        if type(loop) in (AST_if, AST_while, ):
            goto.ifcond = AST_and(org_goto_ifcond, loop.condition)
        _remove(loop)
def eliminate_by_cond(goto, lbl):
    ''' use when o(g) < o(l) '''
    # trivial case: just remove the goto
    if lbl.prev == goto:
        # untested
        _remove(goto)
        raise Exception("eliminate_by_cond: untested branch notification")

    if_elim = AST_if(AST_not(goto.ifcond))
    block_first = goto.next
    block_last = lbl.prev

    _remove(goto)
    _insert_loop_or_if_above(if_elim, block_first)
    block_last.next = None
    if_elim.next = lbl
    lbl.prev = if_elim
def eliminate_by_dowhile(goto, lbl):
    ''' use when o(g) > o(l) '''
    while_elim = AST_dowhile(goto.ifcond)
    block_last = goto.prev

    _remove(goto)
    _insert_loop_or_if_above(while_elim, lbl)
    if block_last.next:
        while_elim.next = block_last.next
        block_last.next.prev = while_elim
    block_last.next = None
def move_into_loop_or_if(goto, lbl):
    ''' move goto into the loop/if that contains lbl (or the statement containing lbl) '''
    loop = find_directly_related_lblstm(goto, lbl)
    if not type(loop) in (AST_if, AST_while, AST_dowhile):
        raise Exception("move_into_loop_or_if assert: loop must be a loop type")
    lblstm = find_directly_related_lblstm(loop.block, lbl) # in loop
    stm1 = None
    if goto.next != loop:
        stm1 = goto.next

    # create replacing nodes
    bvar = AST_bvar("goto_%s" % goto.index)
    bass_initial = AST_bassign(bvar, goto.ifcond)
    bass_final = AST_bassign(bvar, AST_false())

    # modify loop and goto conditions
    loop.condition = AST_or(bvar, loop.condition)
    goto.ifcond = bvar
    
    # modify AST
    if stm1 != None:
        # untested branch
        if_replacing_goto = AST_if(AST_not(bvar))
        # stms between the goto and the loop
        _insert_loop_or_if_above(if_replacing_goto, stm1)
        # repair the tail
        loop.prev.next = None
        loop.prev = if_replacing_goto
    _remove(goto)
    _insert_before(bass_initial, loop)
    _insert_before(goto, loop.block)
    _insert_before(bass_final, lblstm)
def lift_above_lblstm(goto, lblstm):
    ''' assuming, of course, that o(g) > o(l) '''
    # map goto context
    stm_after_goto = goto.next # could be None
    stm_before_goto = goto.prev # must not be None
    if stm_before_goto == None:
        raise Exception("lift_above_lblstm: stm_before_goto must not be None")

    # create replacing nodes
    bvar = AST_bvar("goto_%s" % goto.index)
    bass_initial = AST_bassign(bvar, AST_false())
    bass_dolast = AST_bassign(bvar, goto.ifcond)
    dowhile_replacing_goto = AST_dowhile(bvar)

    # extract and redefine the goto
    _remove(goto)
    goto.ifcond = bvar

    # reorganize the ast
    _insert_before(goto, lblstm)
    _insert_before(bass_initial, goto)
    _insert_loop_or_if_above(dowhile_replacing_goto, goto)

    # insert that goto-var end condition
    _insert_after(bass_dolast, stm_before_goto)

    # limit the dowhile block - UNTESTED
    if stm_after_goto != None:
        # TODO: this will not work
        _remove(stm_after_goto)
        _insert_after(stm_after_goto, dowhile_replacing_goto) 

def _remove(node):
    ''' Removes and stiches the graph. NOTE: Removing a branch removes its block with it '''
    if node.prev:
        if node.next:
            node.next.prev = node.prev
            node.prev.next = node.next
        else:
            node.prev.next = None
    elif node.up:
        if node.next:
            node.up.block = node.next
            node.next.prev = None
            node.next.up = node.up
        else:
            node.up.block = AST_pass()
    else:
        raise Exception("_remove assert: (node.up xor node.prev) must be true")
    node.next = None
    node.prev = None
    node.up = None
def _insert_loop_or_if_above(loop, node):
    ''' insert loop/if "loop" above "node" '''
    # set prev.next to be the loop
    if node.prev != None:
        loop.prev = node.prev
        node.prev.next = loop
        node.prev = None
    elif node.up != None:
        loop.up = node.up
        node.up.block = loop
        node.up = None
    # set node and loop relations
    node.up = loop
    loop.block = node
def _insert_after(node, after):
    ''' insert item "node" after "after" '''
    # set next.prev to node
    if after.next != None:
        after.next.prev = node
        node.next = after.next
    # set next to node
    after.next = node
    node.prev = after
def _insert_before(node, before):
    ''' insert item "node" before "before" '''
    # set prev.next to node
    if before.prev != None:
        before.prev.next = node
        node.prev = before.prev
    # reset up from before to node
    elif before.up != None:
        before.up.block = node
        node.up = before.up
        before.up = None
    # set direct relations
    before.prev = node
    node.next = before

