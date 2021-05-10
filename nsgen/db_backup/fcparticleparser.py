'''
Flowchart based particle parser.
'''
import re
from .instrgeom import RayBundle, ParticleStory, ParticleCompGroup, ParticleState
from .flowchart import FCNTerminal, FCNDecisionBool, FCNDecisionMulti, FCNProcess, FlowChartControl

# terminal nodes implementation
def t_begin(args):
    print("starting particle parsing")

def t_end(args):
    print("ended particle parsing")

def t_error(args):
    print(args['linegetter'].current())
    raise Exception("error")

def t_error2(args):
    print(args['linegetter'].current())
    raise Exception("error2")

def t_error3(args):
    print(args['linegetter'].current())
    raise Exception("error3")

def t_error4(args):
    print(args['linegetter'].current())
    raise Exception("error4")

def t_error5(args):
    print(args['linegetter'].current())
    raise Exception("error5")

# decision nodes implementation
def d_isenter(args):
    m = re.match('ENTER:', args['linegetter'].current())
    return m is not None

def d_done(args):
    return args['linegetter'].isempty()

def d_isstate(args):
    m = re.match('STATE:', args['linegetter'].current())
    return m is not None

def d_isscatter(args):
    m = re.match('SCATTER:', args['linegetter'].current())
    return m is not None

def d_iscomp(args):
    m = re.match('COMP:', args['linegetter'].current())
    return m is not None

def d_isleave(args):
    m = re.match('LEAVE:', args['linegetter'].current())
    return m is not None

def d_iskeywd(args):
    line = args['linegetter'].current()
    m0 = re.match('COMP:', line)
    if m0:
        return 0 
    m1 = re.match('SCATTER:', line)
    if m1:
        return 1
    m2 = re.match('ABSORB:', line)
    if m2:
        return 2
    m3 = re.match('LEAVE:', line)
    if m3:
        return 3
    m4 = re.match('STATE:', line)
    if m4:
        return 4

    raise Exception("wrong line: %s" % line)

# process nodes implementation  --- NOTE: all process nodes increment line idx by one
def p_newparticle(args):
    args['weaver'].new_story()
    
    args['linegetter'].inc()

def p_ignoreline(args):
    args['linegetter'].inc()

def p_addcomp(args):
    linegetter = args['linegetter']
    
    weaver = args['weaver']
    weaver.close_comp()
    weaver.new_comp(_get_compname(linegetter.current()))
    
    linegetter.inc()

def p_addpoint(args):
    linegetter = args['linegetter']
    args['weaver'].new_point(_get_strcoords(linegetter.current()))
    
    linegetter.inc()

def p_addpointclose(args):
    linegetter = args['linegetter']
    args['weaver'].new_point(_get_strcoords(linegetter.current()))
    
    weaver = args['weaver']
    weaver.close_comp()
    weaver.close_story()
    
    linegetter.inc()

# helper functions implementation
def _get_strcoords(line):
    m = re.match('\w+: ([\d\.\+\-e]+), ([\d\.\+\-e]+), ([\d\.\+\-e]+), ([\d\.\+\-e]+), ([\d\.\+\-e]+), ([\d\.\+\-e]+), ([\d\.\+\-e]+), ([\d\.\+\-e]+), ([\d\.\+\-e]+), ([\d\.\+\-e]+), ([\d\.\+\-e]+)', line)
    if m is None:
        print("m is None!")
    return [m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), m.group(6), m.group(7), m.group(8), m.group(9), m.group(10), m.group(11)]

def _get_compname(line):
    m = re.match('COMP: \"(\w+)\"', line)
    return m.group(1)

# action code helper classes
class ParticleBundleWeaver(object):
    ''' creates the particle ray data structure by aid of a bunch of functions that can be called in succession '''
    def __init__(self):
        self._rays = []
        self._bundle = RayBundle(self._rays)
        self._compgroup = None
        self._story = None
    
    def new_story(self):
        if self._story is not None:
            raise Exception("Close the current story before adding a new one.")
        self._story = ParticleStory()
        self._rays.append(self._story)
    
    def new_comp(self, compname):
        if self._story is None:
            raise Exception("You must add a particle story before adding a compgroup.")
        if self._compgroup is not None:
            raise Exception("Close the current compgroup before adding a new one.")
        self._compgroup = ParticleCompGroup(compname)
        self._story.add_group(self._compgroup)

    def new_point(self, point_str):
        if self._compgroup is None:
            raise Exception("You must add a compgroup before adding points.")
        point = ParticleState(point_str)
        self._compgroup.add_event(point)
    
    def close_comp(self):
        self._compgroup = None
    
    def close_story(self):
        self._story = None
    
    def get_particles(self):
        if self._story == None and self._compgroup == None: 
            return self._bundle
        else:
            raise Exception("Close compgroup and story before fetching the particle bundle.")

class LineGetter(object):
    def __init__(self, text):
        self.lines = text.splitlines()
        self.idx = 0
    
    def current(self):
        if not self.idx >= len(self.lines):
            return self.lines[self.idx]

    def prev(self):
        if not self.idx == 0:
            return self.lines[self.idx-1]

    def next(self):
        if not self.idx == len(self.lines) - 1:
            return self.lines[self.idx+1]

    def inc(self):
        self.idx += 1
    
    def isempty(self):
        return self.idx >= len(self.lines)

# flowchart assembly and execution
class FlowChartParticleTraceParser(object):
    def __init__(self):
        # terminal nodes
        t1 = FCNTerminal(key="begin", fct=t_begin)
        t2 = FCNTerminal(key="end", fct=t_end)
        t3 = FCNTerminal(key="error", fct=t_error)
        t4 = FCNTerminal(key="error2", fct=t_error2)
        t5 = FCNTerminal(key="error3", fct=t_error3)
        t6 = FCNTerminal(key="error4", fct=t_error4)
        t7 = FCNTerminal(key="error5", fct=t_error5)
        
        # decision nodes
        d0 = FCNDecisionBool(fct=d_done)
        d1 = FCNDecisionBool(fct=d_isenter)
        d2 = FCNDecisionBool(fct=d_isstate)
        d3 = FCNDecisionMulti(fct=d_iskeywd)
        d4 = FCNDecisionBool(fct=d_isstate)
        d5 = FCNDecisionBool(fct=d_isstate)
        d5_b = FCNDecisionBool(fct=d_isscatter)
        d5_c = FCNDecisionBool(fct=d_iscomp)
        d6 = FCNDecisionBool(fct=d_isstate)
        d7 = FCNDecisionBool(fct=d_isstate)
        d8 = FCNDecisionBool(fct=d_isleave)
        
        # process nodes
        p1 = FCNProcess(fct=p_newparticle)
        p2 = FCNProcess(fct=p_ignoreline)
        p3 = FCNProcess(fct=p_addcomp)
        p4 = FCNProcess(fct=p_addpoint)
        p5 = FCNProcess(fct=p_addpoint)
        p6 = FCNProcess(fct=p_ignoreline)
        p7 = FCNProcess(fct=p_ignoreline)
        p8 = FCNProcess(fct=p_addpoint)
        p9 = FCNProcess(fct=p_ignoreline)
        p10 = FCNProcess(fct=p_addpointclose)
        p12 = FCNProcess(fct=p_ignoreline)

        # assemble the flowchart from top
        t1.set_nodenext(node_next=d0)
        d0.set_nodes(node_T=t2, node_F=d1)
        d1.set_nodes(node_T=p1, node_F=t3)
        p1.set_nodenext(node_next=d2)
        d2.set_nodes(node_T=p2, node_F=t4)
        p2.set_nodenext(node_next=d3)
        d3.set_node_lst(node_lst=[p3, p5, p7, p9, p12])

        p3.set_nodenext(node_next=d4)
        d4.set_nodes(node_T=p4, node_F=t5)
        p4.set_nodenext(node_next=d3)

        p5.set_nodenext(node_next=d5)
        d5.set_nodes(node_T=p6, node_F=d5_b)
        d5_b.set_nodes(node_T=p5, node_F=d5_c)
        d5_c.set_nodes(node_T=d3, node_F=t6)
        p6.set_nodenext(node_next=d3)

        p7.set_nodenext(node_next=d6)
        d6.set_nodes(node_T=p8, node_F=d3)
        p8.set_nodenext(node_next=d8) # <-- this event rarely happens for most instruments!
        d8.set_nodes(node_T=p7, node_F=d3)

        p9.set_nodenext(node_next=d7)
        d7.set_nodes(node_T=p10, node_F=t7)
        p10.set_nodenext(node_next=d0)

        p12.set_nodenext(node_next=d3)
        
        self.rootnode = t1

    def nsgen_alternative(self, args):

        def eq_zero(args):
            return d_iskeywd(args) == 0
        def eq_one(args):
            return d_iskeywd(args) == 1
        def eq_two(args):
            return d_iskeywd(args) == 2
        def eq_three(args):
            return d_iskeywd(args) == 3


        goto_8 = False
        goto_7 = False
        goto_6 = False
        goto_5 = False
        goto_4 = False
        goto_3 = False
        goto_2 = False
        goto_1 = False
        goto_0 = False
        t_begin(args)
        while True:
            goto_1 = False
            if d_done(args): ## lbl_1
                t_end(args)
                return
            if d_isenter(args):
                p_newparticle(args)
                if d_isstate(args):
                    p_ignoreline(args)
                    while True:
                        goto_0 = False
                        while True:
                            goto_2 = False
                            while True:
                                goto_3 = False
                                while True:
                                    goto_5 = False
                                    while True:
                                        goto_7 = False
                                        while True:
                                            goto_8 = False
                                            if eq_zero(args): ## lbl_8
                                                p_addcomp(args)
                                                if d_isstate(args):
                                                    p_addpoint(args)
                                                    goto_8 = True
                                                if not goto_8:
                                                    t_error3(args)
                                                    return
                                            if not goto_8:
                                                break
                                        if eq_one(args):
                                            p_addpoint(args)
                                            if d_isstate(args):
                                                p_ignoreline(args)
                                                goto_7 = True
                                            if not goto_7:
                                                if not goto_6:
                                                    goto_5 = True and d_iscomp(args)
                                                goto_6 = True and d_isscatter(args)
                                                if goto_6 or not goto_5:
                                                    goto_6 = False
                                                    t_error4(args) ## lbl_6
                                                    return
                                        if not goto_7:
                                            break
                                    if not goto_5:
                                        break
                                if eq_two(args):
                                    while True:
                                        goto_4 = False
                                        p_ignoreline(args) ## lbl_4
                                        if d_isstate(args):
                                            p_addpoint(args)
                                            goto_4 = True and d_isleave(args)
                                            if not goto_4:
                                                goto_3 = True
                                        if not goto_4:
                                            break
                                    if not goto_3:
                                        goto_2 = True
                                if not goto_3:
                                    break
                            if not goto_2:
                                break
                        if eq_three(args):
                            p_ignoreline(args)
                            if d_isstate(args):
                                p_addpointclose(args)
                                goto_1 = True
                            if not goto_1:
                                t_error5(args)
                                return
                        if not goto_1:
                            p_ignoreline(args)
                        if not True:
                            break
                if not goto_1:
                    t_error2(args)
                    return
            if not goto_1:
                break
        t_error(args)
        return





    def execute(self, text, madness=False):
        # set args according to the above implementation and execute the flowchart
        args = {}
        args['linegetter'] = LineGetter(text)
        weaver = ParticleBundleWeaver()
        args['weaver'] = weaver

        if madness == True:
            self.nsgen_alternative(args)
        else:
            flowchart = FlowChartControl(self.rootnode)
            flowchart.process(args)

        return weaver.get_particles()

