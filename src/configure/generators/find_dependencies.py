#!/usr/bin/env python3
# -*- encoding: utf8 -*-

import argparse
import re
import subprocess
from os.path import abspath, relpath, dirname, join, exists, isdir, isfile
import multiprocessing
import threading
import time
import queue
import sys

def parse_args():
    parser = argparse.ArgumentParser(
        description="Find C/C++ include dependencies"
    )

    parser.add_argument(
        'sources',
        action = 'append',
        default = [],
        help = "Source file to inspect",
    )

    parser.add_argument(
        '--include-directory', '-I',
        help = 'Include directories',
        default = [],
        action = 'append',
        dest = 'include_directories',
    )

    parser.add_argument(
        '--preprocessor',
        help = 'Prepend system includes used by this preprocessor (usually a binary called "cpp")',
    )

    parser.add_argument(
        '--root',
        help = 'Root directory',
        default = dirname(abspath(__file__)),
    )

    parser.add_argument(
        '--output', '-o',
        help = "Output file",
        action = 'store'
    )

    parser.add_argument(
        '--target', '-t',
        help = "Compilation target",
        action = 'store'
    )
    parser.add_argument(
        '--makefile',
        help = "Generate Makefile dependencies",
        action = 'store_true',
    )

    return parser.parse_args()

INCLUDE_RE = re.compile(b"#\s*include\s*([\"<])(\S+)[\">]\s*$")


def _find_matches(source):
    res = []
    sharp = b'#'[0]
    with open(source, 'rb') as f:
        for line in f:
            line = line.strip()
            if not line or line[0] != sharp:
                continue
            m = INCLUDE_RE.match(line)
            if m:
                res.append((m.group(1), m.group(2).decode('utf8')))
    return res

def _resolve_local_include(source_dir, include_directories, include):
    p = join(source_dir, include)
    if not exists(p):
        return _resolve_global_includes(include_directories, include)
    return p

def _resolve_global_includes(include_directories, include):
    for d in include_directories:
        p = join(d, include)
        if isfile(p):
            return p

def _resolve_includes(source, include_directories):
    source_dir = None
    results = set()
    for c, match in _find_matches(source):
        res = None
        if c == b'"':
            if source_dir is None:
                source_dir = abspath(dirname(source))
            res = _resolve_local_include(source_dir, include_directories, match)
        elif c == b'<':
            res = _resolve_global_includes(include_directories, match)
        else:
            continue
        if res is not None:
            results.add(res)
    return results

class ThreadedIncludeSolver:
    def __init__(self, source, include_directories):
        self.seen = set()
        self.include_directories = include_directories
        self.end_condition = threading.Condition()
        self.workers = []
        self.queue = queue.Queue()
        self.queue.put(source)
        self.nb_threads = multiprocessing.cpu_count()
        for _ in range(self.nb_threads):
            self.workers.append(threading.Thread(target = self.__work))
            self.workers[-1].start()
        self.total = 0

    def __work(self):
        while 1:
            el = self.queue.get()
            if el is None:
                self.queue.task_done()
                break
            results = _resolve_includes(el, self.include_directories)
            for r in results:
                if r not in self.seen:
                    self.seen.add(r)
                    self.queue.put(r, False)
            self.queue.task_done()

    @property
    def result(self):
        self.queue.join()
        for i in range(self.nb_threads):
            self.queue.put(None)
        for w in self.workers: w.join()
        return self.seen

class IncludeSolver:
    def __init__(self, source, include_directories):
        self.seen = set()
        self.include_directories = include_directories
        self.new = {source}

    @property
    def result(self):
        while self.new:
            el = self.new.pop()
            results = _resolve_includes(el, self.include_directories)
            for r in results:
                if r not in self.seen:
                    self.seen.add(r)
                    self.new.add(r)
        return self.seen

def scan_file(source, include_directories):
    import time
    start = time.time()
    result = IncludeSolver(source, include_directories).result
    #print(len(result), "headers found in", time.time() - start, 'secs')
    return result

def main(args):
    if args.makefile:
        if not args.target:
            raise Exception("You should provide a target")

    if args.preprocessor:
        lines = subprocess.check_output(
            '%s -xc++ -v < /dev/null' % args.preprocessor,
            shell = True,
            stderr = subprocess.STDOUT
        ).decode('utf8').split('\n')
        for l in (l.strip().split(' ')[0] for l in lines):
            if l.startswith('/') and isdir(l):
                args.include_directories.insert(0, l)

    for d in args.include_directories:
        if not isdir(d):
            raise Exception("'%s' is not a valid include directory" % d)

    res = set()
    for source in args.sources:
        res.update(
            relpath(include, start = args.root)
            for include in scan_file(source, args.include_directories)
        )

    if args.output:
        out = open(args.output, 'w')
    else:
        out = sys.stdout
    if args.makefile:
        print("Generate header dependencies for", args.target)
        print(args.target + ":", end = '', file = out)
        prev = len(args.target) + 1
        for include in res:
            line = '  %s' % include
            print(' ' * (78 - prev), '\\\n', line, sep = '', end = '', file = out)
            prev = len(line)
        print(file = out)
    if out != sys.stdout:
        out.close()

if __name__ == '__main__':
    try:
        import coverage
        coverage.process_startup()
    except:
        pass
    main(parse_args())
