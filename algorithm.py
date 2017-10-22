class Reasoner:
    stack = []
    states = []

    def __init__(self):
        start = State(inflow=('0', '0'), outflow=('0', '0'), volume=('0', '0'), pi='-')
        start.id = 0
        self.stack.append(start)
        self.states.append(start)

    def create_graph(self, verbose=False):
        while self.stack:
            state = self.stack.pop()

            if verbose:
                print(state)

            new_states = state.get_transitions()

            if not new_states:
                print('BACKTRACKING')
            else:
                print(len(new_states))

            for ns in new_states:
                # Check existing states for equality
                existing = False
                for s in self.states:
                    if ns == s:
                        existing = True
                        ns = s
                        break

                if not existing:
                    ns.id = len(self.states)
                    self.states.append(ns)
                    self.stack.append(ns)


class State:
    children = []
    id = None

    def __init__(self, inflow, outflow, volume, pi):
        self.inflow = inflow
        self.outflow = outflow
        self.volume = volume
        self.previous_inflow = pi

    def get_transitions(self):
        states = []

        ## Immediate transitions:

        ns = State(self.inflow, self.outflow, self.volume, self.previous_inflow)

        # Inflow
        if self.in_dev() == '+' and self.in_mag() == '0':
            ns.inflow = ('+', '+')

        # Volume
        if self.vol_dev() == '+' and self.vol_mag() == '0':
            ns.volume = ('+', '+')
        elif self.vol_dev() == '-' and self.vol_mag() == 'max':
            ns.volume = ('+', '-')

        # Outflow
        if self.out_dev() == '+' and self.out_mag() == '0':
            ns.outflow = ('+', '+')
        elif self.out_dev() == '-' and self.out_mag() == 'max':
            ns.outflow = ('+', '-')

        # # VCs
        # if ns.out_mag() == '0':
        #     if ns.vol_dev() == '-':
        #         ns.volume = ('0', '0')
        #     else:
        #         ns.volume = ('0', ns.vol_dev())
        # elif ns.out_mag() == 'max':
        #     if ns.vol_dev() == '+':
        #         ns.volume = ('+', '0')
        #     else:
        #         ns.volume = ('+', ns.vol_dev())
        #
        # if ns.vol_mag() == '0':
        #     if ns.out_dev() == '-':
        #         ns.outflow = ('0', '0')
        #     else:
        #         ns.outflow = ('0', ns.out_dev())
        # elif ns.vol_mag() == 'max':
        #     if ns.out_dev() == '+':
        #         ns.outflow = ('+', '0')
        #     else:
        #         ns.outflow = ('+', ns.out_dev())

        if ns != self:
            return [ns]

        ## Dependency changes

        # I+ (Inflow, Volume), I- (Outflow, Volume)
        if (self.in_mag() == '0' and self.out_mag() == '+') or (self.in_mag() == '0' and self.out_mag() == 'max'):
            if self.vol_dev() != '-' and self.vol_mag() != '0':
                states.append(State(self.inflow, self.outflow, (self.vol_mag(), '-'), self.previous_inflow))
        elif self.in_mag() == '+' and self.out_mag() == '0':
            if self.vol_dev() != '+' and self.vol_mag() != 'max':
                states.append(State(self.inflow, self.outflow, (self.vol_mag(), '+'), self.previous_inflow))
        elif (self.in_mag() == '+' and self.out_mag() == '+') or (self.in_mag() == '+' and self.out_mag() == 'max'):
            if self.vol_dev() != '0':
                states.append(State(self.inflow, self.outflow, (self.vol_mag(), '0'), self.previous_inflow))
            else:
                if self.vol_mag() != '0':
                    states.append(State(self.inflow, self.outflow, (self.vol_mag(), '-'), self.previous_inflow))
                if self.vol_mag() != 'max':
                    states.append(State(self.inflow, self.outflow, (self.vol_mag(), '+'), self.previous_inflow))

        # P+ (Volume, Outflow)
        for state in states:
            state.outflow = (state.out_mag(), state.vol_dev())

        if states:
            return states

        ## Non-immediate Magnitude transitions
        # Inflow
        if self.in_dev() == '-' and self.in_mag() == '+':
            states.append(State(('0', '0'), self.outflow, self.volume, self.previous_inflow))

        # Volume
        if self.vol_dev() == '+' and self.vol_mag() == '+':
            states.append(State(self.inflow, self.outflow, ('max', '0'), self.in_dev()))
        elif self.vol_dev() == '-' and self.vol_mag() == '+':
            states.append(State(self.inflow, self.outflow, ('0', '0'), self.in_dev()))

        if states:
            return states

        # Exogenous transitions
        if self.in_dev() == '0':
            if self.previous_inflow == '+':
                states.append(State((self.in_mag(), '-'), self.outflow, self.volume, self.in_dev()))
            elif self.previous_inflow == '-':
                states.append(State((self.in_mag(), '+'), self.outflow, self.volume, self.in_dev()))
        else:
            states.append(State((self.in_mag(), '0'), self.outflow, self.volume, self.in_dev()))

        return states

    def __str__(self):
        out = 'State {}\n'.format(self.id)
        out += 'Inflow: [{},{}]\n'.format(self.in_mag(), self.in_dev())
        out += 'Volume: [{},{}]\n'.format(self.vol_mag(), self.vol_dev())
        out += 'Outflow: [{},{}]\n'.format(self.out_mag(), self.out_dev())

        return out

    def __eq__(self, other):
        # Check value equality
        if self.inflow != other.inflow or self.outflow != other.outflow or self.volume != other.volume:
            return False

        # Check compatibility for exogenous sinusoidal inflow
        return self.previous_inflow == other.previous_inflow

    def __ne__(self, other):
        return not self == other

    def in_mag(self): return self.inflow[0]

    def in_dev(self): return self.inflow[1]

    def out_mag(self): return self.outflow[0]

    def out_dev(self): return self.outflow[1]

    def vol_mag(self): return self.volume[0]

    def vol_dev(self): return self.volume[1]


