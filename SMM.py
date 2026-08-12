import numpy as np
from math import inf
from qiskit import QuantumCircuit
from qiskit.circuit import Gate
from qiskit.circuit.library import QFT

def QQM(n: int) -> QuantumCircuit:
    qc = QuantumCircuit(4 * n)
    
    # Slice the circuit's qubits directly into lists of Qubit objects
    x = qc.qubits[0:n]
    y = qc.qubits[n:2 * n]
    w = qc.qubits[2 * n:4 * n]
    
    # Pass the unpacked list of qubits directly to the gate
    qc.append(QFT(num_qubits=2*n, do_swaps=True).to_gate(), [*w])
    PTP(qc, 2 * np.pi / (2 ** (2 * n)), x, y, w, n)
    qc.append(QFT(num_qubits=2*n, do_swaps=True).inverse().to_gate(), [*w])
    
    return qc

def PTP(n: int, n_z: int, phi: float, cutoff: int = 4):

    qc = QuantumCircuit(2 * n + n_z)
    
    rx = qc.qubits[0 : n]
    ry = qc.qubits[n : 2 * n]
    rz = qc.qubits[2 * n : 2 * n + n_z]

    if n <= cutoff:
        for i in range(n):
            for j in range(n):
                for k in range(n_z):
                    qc.mcp(
                        phi * (2**(i+j+k)), 
                        control_qubits=[rx[i], ry[j]], 
                        target_qubit=rz[k]
                    )
        return qc.to_gate(label="PTP")

    m = n // 3
    
    xc = [rx[i*m : (i+1)*m] for i in range(3)]
    yc = [ry[i*m : (i+1)*m] for i in range(3)]
    zc = [rz[i*m : (i+1)*m] for i in range(3)]
    
    points = [0, inf, 1, -1, 2, -2, -0.5]
    phases = [phi * (i + 1) for i in range(7)] 
    
    add_g = IP_adder(m, m)
    sub_g = IP_adder(m, m).inverse()

    for pt, phi_l in zip(points, phases):
        if pt == 0:
            qc.append(PTP(m, m, phi_l, cutoff), [*xc[0], *yc[0], *zc[0]])
        elif pt == inf:
            qc.append(PTP(m, m, phi_l, cutoff), [*xc[2], *yc[2], *zc[2]])
        elif pt == 1:
            for reg in (xc, yc, zc): 
                qc.append(add_g, [*reg[0], *reg[1], reg[2][0]])
                qc.append(add_g, [*reg[2], *reg[1], reg[0][0]])
            
            qc.append(PTPC(m, phi_l, cutoff), [*xc[1], *yc[1], *zc[1]])
            
            for reg in (zc, yc, xc): 
                qc.append(sub_g, [*reg[2], *reg[1], reg[0][0]])
                qc.append(sub_g, [*reg[0], *reg[1], reg[2][0]])
        elif pt == -1:
            qc.append(sub_g, [*xc[0], *xc[1], xc[2][0]])
            qc.append(add_g, [*xc[2], *xc[1], xc[0][0]])
            qc.append(PTPC(m, phi_l, cutoff), [*xc[1], *yc[1], *zc[1]])
            
    return qc.to_gate(label="PTP")


def PTPC(m: int, phi: float, cutoff: int = 4):

    qc = QuantumCircuit(6 * m)
    
    # 2. Slice Qubit Registers
    rx0 = qc.qubits[0 : m]
    rx1 = qc.qubits[m : 2 * m]
    ry0 = qc.qubits[2 * m : 3 * m]
    ry1 = qc.qubits[3 * m : 4 * m]
    rz0 = qc.qubits[4 * m : 5 * m]
    rz1 = qc.qubits[5 * m : 6 * m]

    dcx_in, dcy_in, dcz_in = rx0[m-1], ry0[m-1], rz0[m-1]
    dcx_out, dcy_out = rx1[m-1], ry1[m-1]
    
    carry_x = rx0[m-2]
    carry_y = ry0[m-2]
    
    qc.append(correction_g(m, phi), [*rx0, *rx1, *ry0, *ry1, *rz0, *rz1])
    

    qc.append(cuccaro_1(m), [*rx0[:m-1], *rx1[:m-1], dcx_in])
    qc.append(cuccaro_1(m), [*ry0[:m-1], *ry1[:m-1], dcy_in])
    qc.append(cuccaro_1(m), [*rz0[:m-1], *rz1[:m-1], dcz_in])
    
    for i in range(m-1):
        for j in range(m-1):
            wt = phi * (2**(m-1 + i + j))
            

            qc.mcp(wt, control_qubits=[carry_x, ry1[i]], target_qubit=rz1[j])
            qc.mcp(wt, control_qubits=[carry_y, rx1[i]], target_qubit=rz1[j])
            qc.mcp(wt, control_qubits=[dcx_out, ry1[i]], target_qubit=rz1[j])
            qc.mcp(wt, control_qubits=[dcy_out, rx1[i]], target_qubit=rz1[j])
            
    qc.append(cuccaro_2(m), [*rx0[:m-1], *rx1[:m-1], dcx_in])
    qc.append(cuccaro_2(m), [*ry0[:m-1], *ry1[:m-1], dcy_in])
    qc.append(cuccaro_2(m), [*rz0[:m-1], *rz1[:m-1], dcz_in])
    
    qc.append(PTP(m-1, m-1, phi, cutoff), [*rx1[:m-1], *ry1[:m-1], *rz1[:m-1]])
    
    qc.append(cuccaro_inv(m), [*rz0[:m-1], *rz1[:m-1], dcz_in])
    qc.append(cuccaro_inv(m), [*ry0[:m-1], *ry1[:m-1], dcy_in])
    qc.append(cuccaro_inv(m), [*rx0[:m-1], *rx1[:m-1], dcx_in])
    
    return qc.to_gate(label="PTPC")






def cuccaro_inv(m: int) -> Gate:
    return Gate('cuccaro_inverse', num_qubits=m, params=[])

def correction_g(m: int, phi: float) -> Gate:
    return Gate('dirty_carry_correction', num_qubits=3*m, params=[phi])