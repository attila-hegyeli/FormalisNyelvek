from project.problem import Problem
import argparse
import re

# Egy logcat sor szerkezete (a feladat által javasolt kifejezés):
# 1: teljes dátum+idő, 2: dátum+idő, 3: pid, 4: tid, 5: szint, 6: tag, 7: üzenet
LINE = re.compile(r'(([0-9-]+ [0-9:.]+) +([0-9]+) +([0-9]+) ([IDVEFAW]) (.+?):(?: (.+))?)')

H = r'^[0-9-]+ [0-9:.]+ +[0-9]+ +[0-9]+ '  # a sor fejléce a szintig

COUNT_PATTERNS = [
    re.compile(r'^10-15 '),
    re.compile(r'^10-15 10:18:51\.'),
    re.compile(r'^[0-9-]+ [0-9]{2}:[0-9]{2}:51\.'),
    re.compile(r'lowmemorykiller'),
    re.compile(r'^[0-9-]+ 10:18:51\.[0-9]+ +221 '),
    re.compile(H + r'E '),
    re.compile(H + r'W PackageManager\b'),
    re.compile(H + r'D ExoPlayer'),
    re.compile(H + r'[EW] .*\.java:'),
]
THREAD = re.compile(r'Thread')
JAVA_FILE = re.compile(r'[\w$-]+\.java(?=:)')


 
class RgxProblem(Problem):

    def initialize_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument('--rgx', type=int, help='task number of the regex exercise')

    def is_chosen_problem(self, args):
        return args.rgx is not None

    def run(self, args):
        with open(args.input, 'r', encoding='utf-8', errors='replace') as f:
            lines = [l.rstrip('\r\n') for l in f]

        solvers = {1: self._task1, 2: self._task2, 3: self._task3,
                   4: self._task4, 5: self._task5}
        if args.rgx not in solvers:
            raise ValueError(f'Unknown regex task: {args.rgx}')
        output = solvers[args.rgx](lines)

        with open(args.output, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(output))

    @staticmethod
    def _parsed(lines):
        for line in lines:
            m = LINE.match(line)
            if m:
                yield m

    @staticmethod
    def _task1(lines):
        counts = [sum(1 for l in lines if p.search(l)) for p in COUNT_PATTERNS]
        # 10. pont: a Thread szó az üzenetben (nem a tagben) szerepel
        counts.append(sum(
            1 for m in RgxProblem._parsed(lines)
            if m.group(7) and THREAD.search(m.group(7))
        ))
        return [str(c) for c in counts]

    @staticmethod
    def _task2(lines):
        result = []
        for m in RgxProblem._parsed(lines):
            if m.group(5) == 'E':
                result.extend(JAVA_FILE.findall(m.group(1)))
        return result

    @staticmethod
    def _task3(lines):
        seen = []
        for m in RgxProblem._parsed(lines):
            if m.group(3) not in seen:
                seen.append(m.group(3))
        return seen

    @staticmethod
    def _task4(lines):
        counts = {}
        for m in RgxProblem._parsed(lines):
            if m.group(5) == 'E':
                counts[m.group(3)] = counts.get(m.group(3), 0) + 1
        if not counts:
            return []
        best = max(counts, key=lambda pid: counts[pid])  # döntetlennél az első
        return [f'PID={best} ({counts[best]} errors)']

    @staticmethod
    def _task5(lines):
        main = re.compile(H.replace(r'+[0-9]+ +[0-9]+ ', r'+([0-9]+) +\1 ') + r'E ')
        return [str(sum(1 for l in lines if main.search(l)))]
