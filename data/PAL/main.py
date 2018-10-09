import sys

for pal_raw in sys.stdin.read().splitlines():
    pal = pal_raw.strip().lower().replace(',', '').replace('.', '').replace(' ', '')
    print('[ano] %s' % pal_raw if pal == pal[::-1] else '[ne ] %s' % pal_raw)
