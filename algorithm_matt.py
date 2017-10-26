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

                state.children.append(ns)

        return self.states[0]


class State:
    id = None

    def __init__(self, inflow=None, outflow=None, volume=None, pi=None, prev=None):
        if inflow is not None:
            self.inflow = Quantity(*inflow)
        else:
            self.inflow = Quantity(prev.inflow.mag, prev.inflow.dev)

        if outflow is not None:
            self.outflow = Quantity(*outflow)
        else:
            self.outflow = Quantity(prev.outflow.mag, prev.outflow.dev)

        if volume is not None:
            self.volume = Quantity(*volume)
        else:
            self.volume = Quantity(prev.volume.mag, prev.volume.dev)

        if pi is not None:
            self.previous_inflow = pi
        else:
            self.previous_inflow = prev.previous_inflow

        self.children = []
        self.exogenous = 'increasing'

    @staticmethod
    def point_transitions(states):
        for ns in states:
            # Inflow
            if ns.inflow.mag == '0' and ns.inflow.dev == '+':
                ns.inflow.mag = '+'
            elif ns.inflow.mag == '+' and ns.inflow.dev == '0':
                ns.inflow.dev = '-'
            elif ns.inflow.mag == '0' and ns.inflow.dev == '0':
                ns.inflow.dev = '+'

            # Volume
            if ns.volume.mag == '0' and ns.volume.dev == '+' or ns.volume.mag == 'max' and ns.volume.dev == '-':
                ns.volume.mag = '+'
                ns.outflow.mag = '+'  # VC

            # Outflow
            if ns.outflow.mag == '0' and ns.outflow.dev == '+' or ns.outflow.mag == 'max' and ns.outflow.dev == '-':
                ns.outflow.mag = '+'
                ns.volume.mag = '+'  # VC

    def dependency_transitions(self):
        states = []

        # Influence
        es = []

        if self.inflow.mag != '0' and self.outflow.mag == '0' and self.volume.dev == '0' and self.volume.mag != 'max':
            es.append(State(prev=self, volume=(self.volume.mag, '+')))

        elif self.inflow.mag == '0' and self.outflow.mag != '0' and self.volume.dev == '+':
            es.append(State(prev=self, volume=(self.volume.mag, '0')))

        elif self.inflow.mag != '0' and self.outflow.mag != '0' and self.volume.dev == '0':
            if self.volume.mag != 'max' and self.inflow.dev != '-':
                es.append(State(prev=self, volume=(self.volume.mag, '+')))
            if self.volume.mag != '0' and self.inflow.dev != '+':
                es.append(State(prev=self, volume=(self.volume.mag, '-')))

        states += es

        # Proportionality
        for state in states:
            if state.volume.dev != self.volume.dev:
                state.outflow.dev = state.volume.dev
            if state.outflow.dev != self.outflow.dev:
                state.volume.dev = state.outflow.dev
            # if self.volume.dev == '+' and self.outflow.dev == '0' and state.outflow.mag != 'max':
            #     state.outflow.dev = '+'
            # elif self.volume.dev == '+' and self.outflow.dev == '-':
            #     state.outflow.dev = '0'
            # elif self.volume.dev == '-' and self.outflow.dev == '0':
            #     state.outflow.dev = '-'
            # elif self.volume.dev == '-' and self.outflow.dev == '+':
            #     state.outflow.dev = '0'

        return states

    def time_transitions(self):
        states = []

        # Inflow (Exogenous)
        if self.inflow.mag == '+' and self.inflow.dev == '+':
            states.append(State(prev=self, inflow=('+', '0')))
        elif self.inflow.mag == '+' and self.inflow.dev == '-':
            states.append(State(prev=self, inflow=('0', '0')))

        # Volume
        if self.volume.dev == '+' and self.volume.mag == '+':
            states.append(State(prev=self, volume=('max', '0'), outflow=('max', '0')))
        if self.volume.dev == '-' and self.volume.mag == '+':
            states.append(State(prev=self, volume=('0', '0'), outflow=('0', '0')))

        # Outflow
        if self.outflow.dev == '+' and self.outflow.mag == '+':
            states.append(State(prev=self, volume=('max', '0'), outflow=('max', '0')))
        if self.outflow.dev == '-' and self.outflow.mag == '+':
            states.append(State(prev=self, volume=('0', '0'), outflow=('0', '0')))

        return states

    def get_transitions(self):
        states = [State(prev=self)]

        # Point transitions
        State.point_transitions(states)

        if states[0] != self:
            return states

        # Dependency transitions
        states = self.dependency_transitions()

        if states:
            return states

        # Time transitions
        states = self.time_transitions()

        return states

    def __str__(self):
        out = '{}:\n'.format(self.id)
        out += 'I: [{},{}]\n'.format(self.inflow.mag, self.inflow.dev)
        out += 'V: [{},{}]\n'.format(self.volume.mag, self.volume.dev)
        out += 'O: [{},{}]\n'.format(self.outflow.mag, self.outflow.dev)

        return out

    def __eq__(self, other):
        # Check value equality
        if self.inflow != other.inflow or self.outflow != other.outflow or self.volume != other.volume:
            return False

        # Check compatibility for exogenous sinusoidal inflow
        return self.previous_inflow == other.previous_inflow

    def __ne__(self, other):
        return not self == other


class Quantity:
    def __init__(self, mag, dev):
        self.mag = mag
        self.dev = dev

    def __eq__(self, other):
        return self.mag == other.mag and self.dev == other.dev

    def __ne__(self, other):
        return not self == other

    def set(self, mag, dev):
        self.mag = mag
        self.dev = dev


