from project.problem import Problem
import argparse
from collections import defaultdict, deque


class DfaProblem(Problem):

    def initialize_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument('--check', help='comma-separated words to check')
        parser.add_argument('--det', action='store_true', help='determinize the input automaton')

    def is_chosen_problem(self, args):
        return args.check is not None or args.det

    def run(self, args):
        with open(args.input, 'r', encoding='utf-8') as input_file:
            lines = input_file.read().splitlines()

        if len(lines) < 4:
            raise ValueError('The input must contain at least four lines.')

        states = lines[0].split()
        alphabet = lines[1].split()
        initial_state = lines[2].strip()
        accepting_states = set(lines[3].split())

        if not states or initial_state not in states:
            raise ValueError('The initial state must be listed among the states.')
        if not accepting_states.issubset(states):
            raise ValueError('Every accepting state must be listed among the states.')

        transitions = defaultdict(set)
        for line in lines[4:]:
            parts = line.split()
            if not parts:
                continue
            if len(parts) != 3:
                raise ValueError(f'Invalid transition: {line!r}')
            source, symbol, destination = parts
            if source not in states or destination not in states:
                raise ValueError(f'Transition references an unknown state: {line!r}')
            if symbol not in alphabet:
                raise ValueError(f'Transition uses an unknown symbol: {line!r}')
            transitions[(source, symbol)].add(destination)

        if args.det:
            output = self._determinize(
                alphabet, initial_state, accepting_states, transitions
            )
        else:
            output = self._check_words(
                initial_state, accepting_states, transitions, args.check
            )

        with open(args.output, 'w', encoding='utf-8') as output_file:
            output_file.write('\n'.join(output))

    @staticmethod
    def _determinize(alphabet, initial_state, accepting_states, transitions):
        ordered_alphabet = sorted(alphabet)
        initial_subset = frozenset((initial_state,))
        subsets = [initial_subset]
        subset_ids = {initial_subset: 0}
        subset_transitions = {}
        pending = deque([initial_subset])

        while pending:
            subset = pending.popleft()
            for symbol in ordered_alphabet:
                destination = frozenset(
                    state
                    for source in subset
                    for state in transitions.get((source, symbol), ())
                )
                if not destination:
                    continue
                if destination not in subset_ids:
                    subset_ids[destination] = len(subsets)
                    subsets.append(destination)
                    pending.append(destination)
                subset_transitions[(subset, symbol)] = destination

        # Merge equivalent reachable subset states, retaining partial transitions.
        partitions = []
        for subset in subsets:
            is_accepting = bool(subset & accepting_states)
            for block in partitions:
                if bool(block[0] & accepting_states) == is_accepting:
                    block.append(subset)
                    break
            else:
                partitions.append([subset])

        while True:
            partition_ids = {
                subset: block_id
                for block_id, block in enumerate(partitions)
                for subset in block
            }
            refined = []
            for block in partitions:
                groups = {}
                for subset in block:
                    signature = (
                        bool(subset & accepting_states),
                        tuple(
                            partition_ids.get(
                                subset_transitions.get((subset, symbol))
                            )
                            for symbol in ordered_alphabet
                        ),
                    )
                    groups.setdefault(signature, []).append(subset)
                refined.extend(groups.values())
            if len(refined) == len(partitions):
                partitions = refined
                break
            partitions = refined

        state_to_block = {
            subset: block_id
            for block_id, block in enumerate(partitions)
            for subset in block
        }
        initial_block = state_to_block[initial_subset]
        block_transitions = {}
        for block_id, block in enumerate(partitions):
            representative = block[0]
            for symbol in ordered_alphabet:
                destination = subset_transitions.get((representative, symbol))
                if destination is not None:
                    block_transitions[(block_id, symbol)] = state_to_block[destination]

        # Number quotient states by discovery from the initial state.
        ordered_blocks = [initial_block]
        output_ids = {initial_block: 0}
        pending_blocks = deque([initial_block])
        while pending_blocks:
            block_id = pending_blocks.popleft()
            for symbol in ordered_alphabet:
                destination = block_transitions.get((block_id, symbol))
                if destination is not None and destination not in output_ids:
                    output_ids[destination] = len(ordered_blocks)
                    ordered_blocks.append(destination)
                    pending_blocks.append(destination)

        state_names = [f's{index}' for index in range(len(ordered_blocks))]
        accepting_names = [
            state_names[output_ids[block_id]]
            for block_id in ordered_blocks
            if bool(partitions[block_id][0] & accepting_states)
        ]
        output = [
            ' '.join(state_names),
            ' '.join(ordered_alphabet),
            state_names[0],
            ' '.join(accepting_names),
        ]
        for block_id in ordered_blocks:
            for symbol in ordered_alphabet:
                destination = block_transitions.get((block_id, symbol))
                if destination is not None:
                    output.append(
                        f'{state_names[output_ids[block_id]]} {symbol} '
                        f'{state_names[output_ids[destination]]}'
                    )
        return output

    @staticmethod
    def _check_words(initial_state, accepting_states, transitions, words):
        results = []
        for word in words.split(','):
            current_states = {initial_state}
            for symbol in word:
                current_states = {
                    destination
                    for state in current_states
                    for destination in transitions.get((state, symbol), ())
                }
                if not current_states:
                    break
            results.append('IGEN' if current_states & accepting_states else 'NEM')
        return results
