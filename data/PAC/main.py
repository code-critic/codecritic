import sys

for s in sys.stdin.read().splitlines():
    l = len(s)
    if s != '-1':
        if l > 1:
            if int(s[int(l / 2) - 1::-1]) > int(s[int(l / 2) + l % 2:]):
                s = s[:int(l / 2) + l % 2] + s[int(l / 2) - 1::-1]
            else:
                s = str(int(s[:int(l / 2) + l % 2]) + 1)
                s = s[:int(l / 2)] + s[::-1]
        else:
            s = int(s) + 1
        print(s)

import sys
is_pal = lambda n: str(n) == str(n)[::-1]
for pal_raw in sys.stdin.read().splitlines():
    number = int(pal_raw)
    if number == -1:
        sys.exit(0)

    number += 1
    while not is_pal(number):
        number += 1
    print(number)
