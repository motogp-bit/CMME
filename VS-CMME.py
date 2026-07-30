def CMMC(n, constant):
    qc = QuantumCircuit(n+1)
    ctrl = qc.qubits[0]
    reg = qc.qubits[1:]
    bitmask = 1 ^ constant
    for j in range(n):
        if (bitmask >> j) & 1:
            qc.cx(ctrl, reg[j])
    return qc.to_gate()

