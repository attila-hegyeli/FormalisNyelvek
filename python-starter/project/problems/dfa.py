from project.problem import Problem
import argparse


class DfaProblem(Problem):

    def initialize_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument('--check', help='comma-separated words to check')

    def is_chosen_problem(self, args):
        return args.check is not None

    def run(self, args):
        with open(args.input, 'r', encoding='utf-8') as input_file:
            lines = input_file.read().splitlines()

        initial_state = lines[2].strip()
        accepting_states = set(lines[3].split())
        transitions = {}

        for line in lines[4:]:
            source, symbol, destination = line.split()
            transitions[(source, symbol)] = destination

        results = []
        for word in args.check.split(','):
            state = initial_state
            for symbol in word:
                next_state = transitions.get((state, symbol))
                if next_state is None:
                    break
                state = next_state
            else:
                results.append('IGEN' if state in accepting_states else 'NEM')
                continue

            results.append('NEM')

        with open(args.output, 'w', encoding='utf-8') as output_file:
            output_file.write('\n'.join(results))
