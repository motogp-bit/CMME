from qiskit import QuantumCircuit
from SMM import QQMM
from AM import RPM
import numpy as np 

def primes(d):
    sqprimes= []
    sqprimes.append(4)
    pprime = 3
    while len(sqprimes) < d:
        prime = 1
        for j in range(3, int(np.sqrt(pprime)),2):
            if pprime % j == 0:
                prime = 0
                break
        if prime:
            sqprimes.append(pprime**2)
        pprime+=2 
    return sqprimes        
            
def CMMC(n, constant):
    qc = QuantumCircuit(n+1)
    ctrl = qc.qubits[0]
    reg = qc.qubits[1:]
    bitmask = 1 ^ constant
    for j in range(n):
        if (bitmask >> j) & 1:
            qc.cx(ctrl, reg[j])
    return qc.to_gate()

def build_tree(qc, regs, n,  N, index, ancilla):
    layers = [regs]
    current_level = regs
    markers = []
    while len(current_level) > 1:
        next_level = []
        tier_size = len(current_level)
        midpoint = tier_size // 2
        
        for i in range(midpoint):
            ln = current_level[i]
            rn = current_level[tier_size - 1 - i]
            out_size = len(ln) + len(rn)
            newreg = qc.qubits[index: index + out_size]
            
            if out_size >= n:
                if out_size % 3 == 0:
                    qc.append(QQMM(n, N, n + 4).inverse(), [*ln, *rn, *newreg, *fc, ancilla[0]])
                else:
                    pass
                qc.append(RPM(len(ln), len(rn)), [*ln, *rn, *newreg, *ancilla[0]])                
            next_level.append(newreg)
            index = index + out_size
        if tier_size % 2 != 0:
            next_level.append(current_level[midpoint])
            
        layers.append(next_level)
        current_level = next_level
        markers.append(tier_size)
    return layers, markers 

def invert_tree(qc, layers, markers, n, N, ancilla):
    depth = len(markers)
    
    for d in range(depth - 1, -1, -1):
        upper_tier = layers[d + 1]
        lower_tier = layers[d]
        
        tier_size = markers[d]
        midpoint = tier_size // 2
        
        for i in range(midpoint - 1, -1, -1):
            ln = lower_tier[i]
            rn = lower_tier[tier_size - 1 - i]
            
            newreg = upper_tier[i]
            out_size = len(ln) + len(rn)
            
            if out_size >= n:
                if out_size % 3 == 0:
                    qc.append(QQMM(n, N, n + 4).inverse(), [*ln, *rn, *newreg, *fc, ancilla[0]])
                else:
                    pass
            else:
                qc.append(RPM(len(ln), len(rn)), [*ln, *rn, *newreg, *ancilla[0]])                
            
def main(sizes, N):
    n = int(np.log2(N))
    d = int(np.sqrt(n))
    qc = QuantumCircuit(total_size * n)
    constants = primes(d)
    total_size = 0
    for i in constants:
        total_size += np.ceil(np.log2(i))
    mark = 0
    regs = []
    for size in sizes:
        regs.append(qc.qubits[mark: mark + size])
        mark = mark + size
    c = qc.qubits[mark: mark + 1]
    for i in range(len(regs)):
        qc.append(CMMC(sizes[i],constants[i]), [*c, regs[i]])
    index = mark + 1
    tree, markers = build_tree(qc, regs, n, N, index, ancilla)
    #accumulator
    invert_tree(qc, tree, markers, n ,N, ancilla)
    
