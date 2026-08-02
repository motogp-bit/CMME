from qiskit import QuantumCircuit

def CMMC(n, constant):
    qc = QuantumCircuit(n+1)
    ctrl = qc.qubits[0]
    reg = qc.qubits[1:]
    bitmask = 1 ^ constant
    for j in range(n):
        if (bitmask >> j) & 1:
            qc.cx(ctrl, reg[j])
    return qc.to_gate()

def build_tree(circuit, regs, N):
    layers = [regs]
    current_level = regs
    
    while len(current_level) > 1:
        next_level = []
        tier_size = len(current_level)
        midpoint = tier_size // 2
        
        for i in range(midpoint):
            ln = current_level[i]
            rn = current_level[tier_size - 1 - i]
            
            out_size = len(ln) + len(rn)
            new_register = QuantumRegister(out_size)
            circuit.add_register(new_register)
            
            if out_size >= N:
                pass
                # modular
            else:
                pass
                # regular
                
            next_level.append(new_register)
            
        if tier_size % 2 != 0:
            next_level.append(current_level[midpoint])
            
        layers.append(next_level)
        current_level = next_level
        
    return layers

def invert_folding_tree(log):
    
    log.reverse()
    
    for operation in log:
        op_type, ln, rn = operation
        
        if op_type == 1:
            pass
            # modular
        else:
            pass
            #regular
            
            
def main(sizes,total_size, n, N):
    optimal_splits, min_gate_costs = gen_splits(max_bits=32)
    qc = QuantumCircuit(total_size* n)
    constants = []
    mark = 0
    regs = []
    for size in sizes:
        regs.append(qc.qubits[mark: mark + size])
        mark = mark + size
    c = qc.qubits[mark: mark + 1]
    for i in range(len(regs)):
        qc.append(CMMC(sizes[i],constants[i]), [*c, regs[i]])
    final_reg, log = build_tree(qc, regs, n, N)
    
#OUT OF PLACE MULTIPLICATION LOGIC