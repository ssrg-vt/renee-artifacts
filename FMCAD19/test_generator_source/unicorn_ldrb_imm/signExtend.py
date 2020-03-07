from bitstring import BitArray, BitStream, BitString

''' -----------------------------------------------------------------------------------------
    Assumption: 
        N % M == 0

    Parameters:
        length of bit_vector = M
        N = 64
  
    Input and Outputs:
        i/p = 0111
        o/p = 0111 + concat(M-1)th bit of bit_vector till length becomes equal to N
----------------------------------------------------------------------------------------- '''

def signExtendASL(bit_vector, N):
    M = len(bit_vector)
    extending_bit = bit_vector[M-1]
    while(len(bit_vector) < N):
        bit_vector += str(extending_bit)
    
    return bit_vector

ans = signExtendASL('0111', 64)
print("Sign Extended bit vector = ", ans)
a = BitString('0b1111')
b = a.int
# a.in
print(type(b))
print("@@@@", hex(b))

