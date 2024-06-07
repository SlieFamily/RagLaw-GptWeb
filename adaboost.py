import numpy as np

D = np.ones(10) / 10
Y = np.array([1,1,1,-1,-1,-1,1,1,1,-1])
G = np.zeros_like(Y)
f = G.copy()

for i in range(5):
    threshold, op = (input()).split(',')
    threshold = np.float32(threshold)
    print(f'G{i}: [+1: x {op} {threshold};]')
    if op == '<':
        G = np.array([1 if (i)<threshold else -1 for i in range(10)])
    if op == '>':
        G = np.array([-1 if (i)<threshold else 1 for i in range(10)])
    temp = (G!=Y)
    print(temp)

    e = (D * temp).sum()
    print('e:', e)
    a = 0.5 * np.log((1-e)/e)
    print('a:', a)
    D = D*np.exp(-a*Y*G)
    D = D/D.sum()

    print('D:',D)

    f = f+a*G

    if (np.sign(f)==Y): 
        print('already perfect!')
        break