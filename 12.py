for i in range(1, 10):
    if i == 4:
        continue
    print(i)

for j in range(1, 10):
    print(j)
    if 4 == j:
        break

a = 0
while a < 10:
    a += 1
    print(a)