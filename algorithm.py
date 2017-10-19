class Reasoner:
    stack = []
    states = []

    def __init__(self):
        start = State(inflow=('0', '0'), outflow=('0', '0'), volume=('0', '0'))
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


class State:
    parents = []
    children = []
    id = None

    def __init__(self, inflow, outflow, volume):
        self.inflow = inflow
        self.outflow = outflow
        self.volume = volume

    def get_transitions(self):
        if self.in_dev() == '0':
            return [State(('0', '+'), self.outflow, self.volume)]

        return []

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

        # Check parent compatibility for exogenous sinusoidal inflow
        for parent in self.parents:
            if (other.in_dev() == '-' and parent.in_dev() == '+') or (other.in_dev() == '+' and parent.in_dev() == '-'):
                return False

        return True

    def __ne__(self, other):
        return not self == other

    def in_mag(self): return self.inflow[0]

    def in_dev(self): return self.inflow[1]

    def out_mag(self): return self.outflow[0]

    def out_dev(self): return self.outflow[1]

    def vol_mag(self): return self.volume[0]

    def vol_dev(self): return self.volume[1]


