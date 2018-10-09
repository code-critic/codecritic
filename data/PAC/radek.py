import fileinput

for line in fileinput.input():
    if line.endswith("\n"):
        line = line[:-1]
    if line == "-1":
        break
    l = len(line)

    if l == 1:
        if line == "9":
            print("11")
            continue
        print(int(line)+1)
        continue
    if l % 2 == 0:
        c = l // 2 - 1
        if line[c+1]<line[c]:
            print(line[:c+1]+reversed(line[c+1:]))
        else:
            x=str(int(line[:c+1])+1)
            print(x+reversed(x))

    else:
        c = l // 2
        if line[c+2]<line[c]:
            print(line[:c+1]+line[c+1]+reversed(line[c+2:]))
        else:
            x=str(int(line[:c+1])+1)
            print(x+line[c+1]+reversed(x))

