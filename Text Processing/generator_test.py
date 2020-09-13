def a_gen(seq):
    for n in seq:
        yield n

def b_gen(seq):
    return (n for n in seq)

seq = range(5)
a = a_gen(seq)
a
b = b_gen(seq)
b
b.__next__()
a.__next__()
