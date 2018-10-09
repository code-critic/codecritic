import sys

for name in sys.stdin.read().splitlines():
    print("Hello, {name}!".format(name=name))
