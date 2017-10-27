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

            new_states, reasons = state.get_transitions()

            if verbose:
                print('\n' + '-'*80)
                print(state.description(), end='\n\n')

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

            if verbose:
                nc = len(state.children)
                if nc == 0:
                    print('This is an end state, there are no transitions.')
                else:
                    word = 'state' if nc == 1 else 'states'
                    print('This state transitions to {} {}:'.format(len(state.children), word))

                    for i, s in enumerate(state.children):
                        print('\t{}. State {} (I=[{},{}], V=[{},{}], O=[{},{}]), because:'.format(i+1, s.id,
                                                                                       s.inflow.mag, s.inflow.dev,
                                                                                       s.volume.mag, s.volume.dev,
                                                                                       s.outflow.mag, s.outflow.dev))
                        if i < len(reasons):
                            for r in reasons[i]:
                                print('\t\t{}'.format(r))


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

    def point_transitions(self):
        reasons = []
        states = [State(prev=self)]

        for ns in states:
            # Inflow
            if ns.inflow.mag == '0' and ns.inflow.dev == '+':
                ns.inflow.mag = '+'
                reasons.append('(IM) The inflow magnitude is 0 and the derivative is +, '
                                  'so the inflow magnitude immediately becomes positive')
            elif ns.inflow.mag == '+' and ns.inflow.dev == '0':
                ns.inflow.dev = '-'
                reasons.append('(IM) The inflow magnitude is + and the derivative is 0, so the inflow is at the top '
                                  'of the parabola, and immediately starts decreasing')
            elif ns.inflow.mag == '0' and ns.inflow.dev == '0':
                ns.inflow.dev = '+'
                reasons.append('(IM) The inflow magnitude and derivative are both 0, so the inflow is at the start '
                                  'of the parabola and immediately starts to increase.')

            # Volume
            if ns.volume.mag == '0' and ns.volume.dev == '+':
                ns.volume.mag = '+'
                ns.outflow.mag = '+'  # VC
                reasons.append('(IM) The volume magnitude is 0 and the derivative is +, '
                                  'so the volume magnitude immediately becomes positive')
                reasons.append('(VC) Because of the value correspondences, the outflow magnitude must also increase')

            if ns.volume.mag == 'max' and ns.volume.dev == '-':
                ns.volume.mag = '+'
                ns.outflow.mag = '+'  # VC
                reasons.append('(IM) The volume magnitude is max and the derivative is -, '
                                  'so the volume magnitude changes to max')
                reasons.append('(VC) Because of the value correspondences, the outflow magnitude must also decrease')

            # # Outflow
            # if ns.outflow.mag == '0' and ns.outflow.dev == '+' or ns.outflow.mag == 'max' and ns.outflow.dev == '-':
            #     ns.outflow.mag = '+'
            #     ns.volume.mag = '+'  # VC

            if ns != self:
                return [ns], [reasons]
            else:
                return [], [reasons]


    def dependency_transitions(self):
        reasons = []
        states = []

        # Influence
        if self.inflow.mag != '0' and self.outflow.mag == '0' and self.volume.dev == '0' and self.volume.mag != 'max':
            states.append(State(prev=self, volume=(self.volume.mag, '+')))
            reasons.append(['(I) There is inflow but no outflow, so the volume must be increasing'])

        elif self.inflow.mag == '0' and self.outflow.mag != '0' and self.volume.dev == '+':
            states.append(State(prev=self, volume=(self.volume.mag, '0')))
            reasons.append(['(I) There is outflow but no inflow, so the volume cannot increase'])

        elif self.inflow.mag == '+' and self.outflow.mag != '0' and self.volume.dev == '0':
            if self.volume.mag != 'max' and self.inflow.dev != '-':
                states.append(State(prev=self, volume=(self.volume.mag, '+')))
                reasons.append(['(I) There is inflow and outflow, so the volume could be increasing'])
            if self.volume.mag != '0' and self.inflow.dev != '+':
                states.append(State(prev=self, volume=(self.volume.mag, '-')))
                reasons.append(['(I) There is inflow and outflow, so the volume could be decreasing'])

        if self.inflow.dev == '-' and self.outflow.mag == '+' and self.outflow.dev == '+':
            states.append(State(prev=self, volume=(self.volume.mag, '0')))
            reasons.append(['(I) The inflow may decrease below the level of the outflow, '
                            'causing the volume to stop increasing'])

        if self.inflow.dev == '+' and self.volume.dev == '-':
            states.append(State(prev=self, volume=(self.volume.mag, '0')))
            reasons.append(['(I) The inflow may increase above the level of the outflow, '
                            'causing the volume to stop decreasing'])

        # Proportionality
        for i, state in enumerate(states):
            if state.volume.dev != self.volume.dev:
                state.outflow.dev = state.volume.dev
                word = 'increasing' if state.volume.dev == '+' else 'decreasing' if state.volume.dev == '-' else 'stable'
                reasons[i].append('(P) The volume is {}, so the outflow must be {} too'.format(word, word))
            elif state.outflow.dev != self.outflow.dev:
                word = 'increasing' if state.volume.dev == '+' else 'decreasing' if state.volume.dev == '-' else 'stable'
                reasons[i].append('(P) The outflow is {}, so the outflow must be {} too'.format(word, word))

            # if self.volume.dev == '+' and self.outflow.dev == '0' and state.outflow.mag != 'max':
            #     state.outflow.dev = '+'
            # elif self.volume.dev == '+' and self.outflow.dev == '-':
            #     state.outflow.dev = '0'
            # elif self.volume.dev == '-' and self.outflow.dev == '0':
            #     state.outflow.dev = '-'
            # elif self.volume.dev == '-' and self.outflow.dev == '+':
            #     state.outflow.dev = '0'

        return states, reasons

    def time_transitions(self):
        states = []
        reasons = []

        # Inflow (Exogenous)
        if self.inflow.mag == '+' and self.inflow.dev == '+':
            states.append(State(prev=self, inflow=('+', '0')))
            reasons.append(['(T) The inflow is increasing, so it may reach its maximum'])
        elif self.inflow.mag == '+' and self.inflow.dev == '-':
            states.append(State(prev=self, inflow=('0', '0')))
            reasons.append(['(T) The inflow is decreasing, so it may reach zero'])

        # Volume
        if self.volume.dev == '+' and self.volume.mag == '+':
            states.append(State(prev=self, volume=('max', '0'), outflow=('max', '0')))
            reasons.append(['(T) The volume is increasing, so it may reach its maximum'])
        if self.volume.dev == '-' and self.volume.mag == '+' and self.inflow.mag == '0':
            states.append(State(prev=self, volume=('0', '0'), outflow=('0', '0')))
            reasons.append(['(T) The inflow is decreasing, so it may reach its zero'])

        # Outflow
        if self.outflow.dev == '+' and self.outflow.mag == '+':
            states.append(State(prev=self, volume=('max', '0'), outflow=('max', '0')))
            reasons.append(['(T) The outflow is increasing, so it may reach its maximum'])
        if self.outflow.dev == '-' and self.outflow.mag == '+' and self.inflow.mag == '0':
            states.append(State(prev=self, volume=('0', '0'), outflow=('0', '0')))
            reasons.append(['(T) The outflow is decreasing, so it may reach zero'])

        return states, reasons

    def get_transitions(self):
        # Point transitions
        states, reasons = self.point_transitions()

        if states:
            return states, reasons

        # Dependency transitions
        states, reasons = self.dependency_transitions()

        if states:
            return states, reasons

        # Time transitions
        states, reasons = self.time_transitions()

        return states, reasons

    def description(self):
        rep = 'I=[{},{}], V=[{},{}], O=[{},{}]'.format(self.inflow.mag, self.inflow.dev, self.volume.mag,
                                                       self.volume.dev, self.outflow.mag, self.outflow.dev)
        out = 'Visiting state {} ({})\n'.format(self.id, rep)

        # Inflow
        if self.inflow.mag == '0' and self.inflow.dev == '0':
            inf = 'there is no inflow'
        elif self.inflow.mag == '0' and self.inflow.dev == '+':
            inf = 'there is no inflow, but it is increasing'
        elif self.inflow.mag == '+' and self.inflow.dev == '+':
            inf = 'there is an increasing amount of inflow'
        elif self.inflow.mag == '+' and self.inflow.dev == '0':
            inf = 'the inflow is stable at its maximum'
        elif self.inflow.mag == '+' and self.inflow.dev == '-':
            inf = 'there is a decreasing amount of inflow'
        else:
            inf = 'confused'

        # Volume
        if self.volume.mag == '0' and self.volume.dev == '0':
            pool = 'is empty and not filling'
        elif self.volume.mag == '0' and self.volume.dev == '+':
            pool = 'is empty, but is filling'
        elif self.volume.mag == '+' and self.volume.dev == '+':
            pool = 'has an increasing amount of water'
        elif self.volume.mag == '+' and self.volume.dev == '0':
            pool = 'has a stable amount of water'
        elif self.volume.mag == 'max' and self.volume.dev == '0':
            pool = 'is stable and full'
        elif self.volume.mag == 'max' and self.volume.dev == '-':
            pool = 'is full, but decreasing'
        elif self.volume.mag == '+' and self.volume.dev == '-':
            pool = 'has a decreasing amount of water'
        else:
            pool = 'confused'
            
        # Outflow
        if self.outflow.mag == '0' and self.outflow.dev == '0':
            outf = 'there is no outflow'
        elif self.outflow.mag == '0' and self.outflow.dev == '+':
            outf = 'there is no outflow, but it is increasing'
        elif self.outflow.mag == '+' and self.outflow.dev == '+':
            outf = 'there is an increasing mount of outflow'
        elif self.outflow.mag == '+' and self.outflow.dev == '0':
            outf = 'there is a stable amount of outflow'
        elif self.outflow.mag == 'max' and self.outflow.dev == '0':
            outf = 'the outflow is maximal'
        elif self.outflow.mag == 'max' and self.outflow.dev == '-':
            outf = 'the outflow is maximal, but decreasing'
        elif self.outflow.mag == '+' and self.outflow.dev == '-':
            outf = 'there is a decreasing amount of outflow'
        else:
            outf = 'confused'

        out += 'In this state, {}, the pool {} and {}.'.format(inf, pool, outf)

        return out

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


