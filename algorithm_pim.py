class Reasoner:
    stack = []
    states = []

    def __init__(self):
        start = State(inflow=('0', '0'), outflow=('0', '0'), volume=('0', '0'), pi=('-'))
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
        
        # Inflow
        if self.in_dev() == '+' and self.in_mag() == '0':
            if len(states) < 1:
                states.append(State(('+','+'), self.outflow, self.volume, self.previous_inflow))
            else:
                states[0].inflow = ('+','+')
        if self.in_dev() == '-' and self.in_mag() == 'max':
            if len(states) < 1:
                states.append(State(('+','-'), self.outflow, self.volume, self.previous_inflow))
            else:
                states[0].inflow = ('+','-')

        # Volume
        if self.vol_dev() == '+' and self.vol_mag() == '0':
            if len(states) < 1:
                states.append(State(self.inflow, self.outflow, ('+','+'), self.previous_inflow))
            else:
                states[0].volume = ('+','+')
        if self.vol_dev() == '-' and self.vol_mag() == 'max':
            if len(states) < 1:
                states.append(State(self.inflow, self.outflow, ('+', '-'), self.previous_inflow))
            else:
                states[0].volume = ('+','-')

        # Outflow
        if self.out_dev() == '+' and self.out_mag() == '0':
            if len(states) < 1:
                states.append(State(self.inflow, ('+','+'), self.volume, self.previous_inflow))
            else:
                states[0].volume = ('+','+')
        if self.out_dev() == '-' and self.out_mag() == 'max':
            if len(states) < 1:
                states.append(State(self.inflow, ('+','-'), self.volume, self.previous_inflow))
            else:
                states[0].volume = ('+','-')

        if len(states) < 1:
            states.append(State(self.inflow, self.outflow, self.volume, self.previous_inflow))

        extra_states = []
        for state in states:
            # Inflow
            if self.in_dev() == '+' and self.in_mag() == '+':
                extra_states.append(State(('max', '0'), state.outflow, state.volume, state.previous_inflow))
            if self.in_dev() == '-' and self.in_mag() == '+':
                extra_states.append(State(('0', '0'), state.outflow, state.volume, state.previous_inflow))

            # Volume
            if self.vol_dev() == '+' and self.vol_mag() == '+':
                extra_states.append(State(state.inflow, state.outflow, ('max','0'), state.previous_inflow))
            if self.vol_dev() == '-' and self.vol_mag() == '+':
                extra_states.append(State(state.inflow, state.outflow, ('0','0'), state.previous_inflow))
            # Ouflow
            if self.out_dev() == '+' and self.out_mag() == '+':
                extra_states.append(State(state.inflow, ('max','0'), state.volume, state.previous_inflow))
            if self.out_dev() == '-' and self.out_mag() == '+':
                extra_states.append(State(state.inflow, ('0','0'), state.volume, state.previous_inflow))
        
        for state in extra_states:
            states.append(state)

        


        ## Dependency changes
        extra_states = []
        for state in states:
            if self.in_mag() != '0' and self.out_mag() == '0' and self.vol_dev() == '0' and state.vol_mag() != 'max':
                state.volume = (state.vol_mag(), '+')
            if self.in_mag() == '0' and self.out_mag() != '0' and self.vol_dev() == '+':
                state.volume = (state.vol_mag(), '0')
            if self.in_mag() != '0' and self.out_mag() != '0' and self.vol_dev() == '0':
                extra_states.append(State(state.inflow, state.outflow, (state.vol_mag(), '+'), state.previous_inflow))
                extra_states.append(State(state.inflow, state.outflow, (state.vol_mag(), '-'), state.previous_inflow))

        for state in extra_states:
            states.append(state)
         
        for state in states:
            if self.vol_dev() == '+' and self.out_dev() == '0' and state.out_mag() != 'max':
                state.outflow = (state.out_mag(), '+')
            if self.vol_dev() == '+' and self.out_dev() == '-':
                state.outflow = (state.out_mag(), '0')
            if self.vol_dev() == '-' and self.out_dev() == '0':
                state.outflow = (state.out_mag(), '-')
            if self.vol_dev() == '-' and self.out_dev() == '+':
                state.outflow = (state.out_mag(), '0')

        for state in states:
            if state == self:
                states.remove(state)
     
        if len(states) > 0:
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


