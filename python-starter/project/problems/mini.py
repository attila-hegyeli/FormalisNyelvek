from project.problem import Problem
import argparse
import re
from collections import deque


def _natural_key(name):
    return [int(p) if p.isdigit() else p for p in re.split(r'(\d+)', name)]


def _new_name(name):
    if re.search(r'\d', name):
        return re.sub(r'^\D+', 's', name)
    return 's' + name


class MiniProblem(Problem):

    def initialize_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument('--mini', action='store_true', help='minimize the input DFA')

    def is_chosen_problem(self, args):
        return bool(args.mini)

    def run(self, args):
        with open(args.input, 'r', encoding='utf-8') as input_file:
            lines = input_file.read().splitlines()

        if len(lines) < 4:
            raise ValueError('The input must contain at least four lines.')

        states = lines[0].split()
        alphabet = lines[1].split()
        initial = lines[2].strip()
        accepting = set(lines[3].split())

        if initial not in states:
            raise ValueError('The initial state must be listed among the states.')
        if not accepting.issubset(states):
            raise ValueError('Every accepting state must be listed among the states.')

        delta = {}
        for line in lines[4:]:
            parts = line.split()
            if not parts:
                continue
            if len(parts) != 3:
                raise ValueError(f'Invalid transition: {line!r}')
            src, sym, dst = parts
            if src not in states or dst not in states:
                raise ValueError(f'Transition references an unknown state: {line!r}')
            if sym not in alphabet:
                raise ValueError(f'Transition uses an unknown symbol: {line!r}')
            if delta.get((src, sym), dst) != dst:
                raise ValueError(f'The automaton is not deterministic: {line!r}')
            delta[(src, sym)] = dst

        symbols = sorted(set(alphabet))

        # Keep only the states reachable from the initial state.
        reachable = {initial}
        queue = deque([initial])
        while queue:
            cur = queue.popleft()
            for sym in symbols:
                nxt = delta.get((cur, sym))
                if nxt is not None and nxt not in reachable:
                    reachable.add(nxt)
                    queue.append(nxt)
        live = sorted(reachable, key=_natural_key)

        # Partition refinement (Moore); a missing transition counts as "no block".
        block = {s: int(s in accepting) for s in live}
        count = len(set(block.values()))
        while True:
            sigs = {
                s: (block[s], tuple(block.get(delta.get((s, a))) for a in symbols))
                for s in live
            }
            ids = {}
            new_block = {}
            for s in live:
                new_block[s] = ids.setdefault(sigs[s], len(ids))
            block = new_block
            if len(ids) == count:
                break
            count = len(ids)

        # Representative = smallest name in each class.
        rep = {}
        for s in live:
            rep.setdefault(block[s], s)
        name = {s: _new_name(rep[block[s]]) for s in live}

        reps = sorted(rep.values(), key=_natural_key)
        out_states = [name[r] for r in reps]
        out_finals = [name[r] for r in reps if r in accepting]

        transitions = set()
        for s in live:
            for a in symbols:
                d = delta.get((s, a))
                if d is not None:
                    transitions.add((name[s], a, name[d]))
        transitions = sorted(
            transitions,
            key=lambda t: (_natural_key(t[0]), t[1], _natural_key(t[2])),
        )

        output = [
            ' '.join(out_states),
            ' '.join(symbols),
            name[initial],
            ' '.join(out_finals),
        ] + [f'{a} {b} {c}' for a, b, c in transitions]

        with open(args.output, 'w', encoding='utf-8') as output_file:
            output_file.write('\n'.join(output))
