def do(binary):
    s, e, m = binary[0], binary[1:9], binary[9:]
    sign = int(binary[0])
    expo = list(map(int, binary[1:9]))
    mant = list(map(int, binary[9:]))

    if e == '11111111':
        if m.replace('0', '') == '':
            if s == '0':
                r = 'Infinity'
            else:
                r = '-Infinity'
        else:
            r = 'NaN'

        print('%s' % (r))
    else:

        S = sign
        S_fin = (-1) ** sign
        S_str = '(-1)^%d' % S

        E = [(2 ** (7-i)) * expo[i] for i in range(8)]
        E = sum(E)
        E_fin = 2 ** (E - 127)
        E_str = '2^(%d - 127)' % E

        Q = [(2 ** (-i-1)) * mant[i] for i in range(23)]
        Q = sum(Q)
        Q_fin = (1 + Q)
        Q_str = '(1 + %1.8f)' % Q

        F_str = '%s * %s * %s' % (S_str, E_str, Q_str)
        F = S_fin * E_fin * Q_fin
        print('%s = %1.8f' % (F_str, F))


import sys
for line in sys.stdin.read().splitlines():
    do(line)


#
# t = '''
# -0.00001
# 3.1415926535
# NaN
# Infinity
# 2.3283064E-10
# 1.03126
# -Infinity
# '''.strip()
#
# tt = '''
# 0
# 1.5
# 2
# 3
# 5
# -1
# 8.5
# '''.strip()
# t = '''
# -1
# 8.5
# '''.strip()
# for i in t.splitlines():
#     import bitstring
#     binary = bitstring.BitArray(float=float('infinity'), length=32).bin
#     binary = bitstring.BitArray(float=float(i), length=32).bin
#     print(binary)
#     # do(binary)
#     # print('%10s = 0b%s' % (i, binary))


print('%1.8f' % 1.00000005984651)