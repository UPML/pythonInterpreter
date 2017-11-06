def f(x):
    return x

p = f
p.s = 30
p.y = 23
print(p.s)
delattr(p, 'y')