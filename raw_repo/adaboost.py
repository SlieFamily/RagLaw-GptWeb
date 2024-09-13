import numpy as np


D = np.ones(5) / 5
Y = np.array([1,1,-1,-1,1])
G = np.zeros_like(Y)
f = G.copy()

for i in range(5):

    min_e = 1
    best_threshold = 0.5
    for threshold in [0.5,1.5,2.5,3.5,4.5,5.5]:
        # x < 
        # print(f'G{i}: [+1: x < {threshold};]')
        G_ = np.array([1 if i<threshold else -1 for i in range(1,6)])
        temp = (G_!=Y)
        # print(temp)
        e = (D * temp).sum()
        # print('e:', e)
        min_e = min(e,min_e)
        if e == min_e:
            G = G_
            best_threshold = threshold

        # x > 
        # print(f'G{i}: [+1: x > {threshold};]')
        G_ = np.array([-1 if i<threshold else 1 for i in range(1,6)])
        temp = (G_!=Y)
        # print(temp)
        e = (D * temp).sum()
        # print('e:', e)
        min_e = min(e,min_e)
        if e == min_e:
            G = G_
            best_threshold = threshold

    print(best_threshold,G)
    print('e:',min_e)
    a = 0.5 * np.log((1-min_e)/min_e)
    print('a:', a)
    D = D*np.exp(-a*Y*G)
    D = D/D.sum()

    print('D:',D)

    f = f+a*G
    ff = (np.sign(f)==Y)

    if ff.all(): 
        print('already perfect!')
        break


# G1=np.array([1,1,-1,-1,-1])
# G2=np.array([1,1,1,1,1])
# G3=np.array([-1,-1,-1,-1,1])

# f = 0.693*G1+0.5493*G2+0.8047*G3

# print(np.sign(f))