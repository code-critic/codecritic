#!/bin/python3
# author: Jan Hybs

from dataclasses import dataclass
from difflib import HtmlDiff
import html


def get_html_diff(a, b):
    diff = HtmlDiff(4)
    lines_a = list(read_n_lines(a, 100))
    lines_b = list(read_n_lines(b, 100))
    html = diff.make_table(lines_a, lines_b, "Teacher's output", "Student's output")
    print(html)


@dataclass
class DiffResult:
    match: bool
    html: str


def line_by_line_diff(a, b) -> DiffResult:
    class Empty:
        def __repr__(self):
            return '<span class="empty"></span>'

    EMPTY = Empty()
    match = True
    lines_a = list(read_n_lines(a, 100))
    lines_b = list(read_n_lines(b, 100))

    la, lb = len(lines_a), len(lines_b)
    max_lines = max(la, lb)
    lines_a = lines_a + [EMPTY] * (max_lines - la)
    lines_b = lines_b + [EMPTY] * (max_lines - lb)
    fmt = len(str(max_lines))  # use hard-coded value for now

    result = [
        #f'<h1>{a} vs {b}</h1>',
        '<table class="diff">',
        '<tr><th class="res"></th><th class="line">line</th>'
        '<th class="ref">reference</th><th class="student">student</th></tr>'
    ]
    for i in range(max_lines):
        l1, l2 = lines_a[i], lines_b[i]
        if l1 == l2:
            result.append('<tr><td class="res same"><i class="fas fa-check"></i></td>')
        else:
            match = False
            result.append('<tr><td class="res different"><i class="fas fa-times"></i></td>')

        if l1 is not EMPTY:
            l1 = html.escape(l1)
        if l2 is not EMPTY:
            l2 = html.escape(l2)
        result.append(f'<td class="line">{i+1:03d}</td><td class="ref">{l1}</td><td class="gen">{l2}</td></tr>')
    result.append('</table>')

    return DiffResult(
        match=match,
        html='\n'.join(result)
    )


def read_n_lines(f, n=5):
    with open(f, 'r') as fp:
        for x in range(n):
            try:
                yield str(next(fp)).rstrip('\n')
            except:
                # end of file
                pass


f1 = '/home/jan-hybs/projects/cc/codecritic/courses/TGH/2019/results/bohm.lukas/WEBISL/01-101-AT-answer-correct-timeout/output/WEBISL_case_1'
f1b = '/home/jan-hybs/projects/cc/codecritic/courses/TGH/2019/results/bohm.lukas/WEBISL/01-101-AT-answer-correct-timeout/output/WEBISL_case_9'

f2 = '/home/jan-hybs/projects/cc/codecritic/courses/TGH/2019/problems/WEBISL/output/WEBISL_case_1'
f2b = '/home/jan-hybs/projects/cc/codecritic/courses/TGH/2019/problems/WEBISL/output/WEBISL_case_9'

print(line_by_line_diff(f1, f2))
