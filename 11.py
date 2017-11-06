a = 12
print(True and 0)
print(0 or True)

#TODO здесь не вызывается JUMP_IF_FALSE_OR_POP=(
if True and 1:
    print(a + 1)
else:
    print(a - 1)

if False and 1:
    print(a + 1)
else:
    print(a - 1)

if 1 and True:
    print(a + 1)
else:
    print(a - 1)

if 1 and False:
    print(a + 1)
else:
    print(a - 1)