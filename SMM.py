import numpy as np
from math import inf
from qiskit import QuantumCircuit,QuantumRegister
from qiskit.circuit.library import QFT
from .gates import IP_adder,cuccaro_1,cuccaro_2,cuccaro_inv,correction_g

def QQM(n: int, N: int) -> QuantumCircuit:
    x = QuantumRegister(n)
    y = QuantumRegister(n)
    w = QuantumRegister(2*n)
    qc = QuantumCircuit(4 * n)
    
    qc.append(QFT(num_qubits=2*n, do_swaps=True).to_gate(), [*w])
    PTP(qc, 2 * np.pi / N, x, y, w, n)
    qc.append(QFT(num_qubits=2*n, do_swaps=True).inverse().to_gate(), [*w])
    
    return qc.to_gate()

def PTP(qc: QuantumCircuit, phi: float, x, y, z,  n: int, cutoff: int = 4):
    if n <= cutoff:
        for i in range(n):
            for j in range(n):
                for k in range(len(z)):
                    qc.mcp(
                        phi * (2**(i+j+k)), 
                        control_qubits=[x[i], y[j]], 
                        target_qubit=z[k]
                    )
        #fix base case multiplication
        return qc.to_gate(label="PTP")

    q = 3 * k - 2
    m = n // 3
    
    xc = [x[i*m : (i+1)*m] for i in range(3)]
    yc = [y[i*m : (i+1)*m] for i in range(3)]
    zc = [z[i*m : (i+1)*m] for i in range(3)]
    
    points = [0, inf, 1, -1, 2, -2, -0.5]
    phases = interpol_phases(phi, points, m) 
    
    add_g = IP_adder(m, m)
    sub_g = IP_adder(m, m).inverse()
    for l in range(q):
            pt = points[l]
            phi_l = phases[l]
            
            if pt == 0:
                PTP(qc, phi_l, xc, yc, zc, m, cutoff)
                
            elif pt == float('inf'):
                PTP(qc, phi_l, xc[2], yc[2], zc[2], m, cutoff)
                
            elif pt == 1:
                q_add(qc, xc[1], xc[0])  
                q_add(qc, xc[1], xc[2])  
            
                q_add(qc, yc[1], yc[0])  
                q_add(qc, yc[1], yc[2])  
            
                q_add(qc, zc[1], zc[0]) 
                q_add(qc, zc[1], zc[2]) 
                sub_ptpc = QuantumCircuit(6 * m)
                PTPC(sub_ptpc, m, phi_l, cutoff)
                qc.append(sub_ptpc.to_gate(label="PTPC"), [
                *xc, *xc[1],
                *yc, *yc[1],
                *zc, *zc[1]
                ])
                
                q_sub(qc, zc[1], zc[2])  
                q_sub(qc, zc[1], zc[0])  
            
                q_sub(qc, yc[1], yc[2]) 
                q_sub(qc, yc[1], yc[0])  
            
                q_sub(qc, xc[1], xc[2])  
                q_sub(qc, xc[1], xc[0])  
    return qc.to_gate(label="PTP")


def PTPC(qc, m: int, phi: float, cutoff: int = 4):
    
    rx0 = qc.qubits[0 : m]
    rx1 = qc.qubits[m : 2 * m]
    ry0 = qc.qubits[2 * m : 3 * m]
    ry1 = qc.qubits[3 * m : 4 * m]
    rz0 = qc.qubits[4 * m : 5 * m]
    rz1 = qc.qubits[5 * m : 6 * m]

    dcx_in, dcy_in, dcz_in = rx0[m-1], ry0[m-1], rz0[m-1]
    dcx_out, dcy_out = rx1[m-1], ry1[m-1]
    qc.append(correction_g(m, phi), [*rx0, *rx1, *ry0, *ry1, *rz0, *rz1])
    

    qc.append(cuccaro_1(m-1), [*rx0[:m-1], *rx1[:m-1], dcx_in])
    qc.append(cuccaro_1(m-1), [*ry0[:m-1], *ry1[:m-1], dcy_in])
    qc.append(cuccaro_1(m-1), [*rz0[:m-1], *rz1[:m-1], dcz_in])
    carry_x = rx0[m-2]
    carry_y = ry0[m-2]
    
    for i in range(m-1):
        for j in range(m-1):
            wt = phi * (2**(m-1 + i + j))
            qc.mcp(wt, control_qubits=[carry_x, ry1[i]], target_qubit=rz1[j])
            qc.mcp(wt, control_qubits=[carry_y, rx1[i]], target_qubit=rz1[j])
            qc.mcp(wt, control_qubits=[dcx_out, ry1[i]], target_qubit=rz1[j])
            qc.mcp(wt, control_qubits=[dcy_out, rx1[i]], target_qubit=rz1[j])
            
    qc.append(cuccaro_2(m-1), [*rx0[:m-1], *rx1[:m-1], dcx_in])
    qc.append(cuccaro_2(m-1), [*ry0[:m-1], *ry1[:m-1], dcy_in])
    qc.append(cuccaro_2(m-1), [*rz0[:m-1], *rz1[:m-1], dcz_in])
    PTP(qc, phi, rx1[:m-1], ry1[:m-1], rz1[:m-1], m - 1, cutoff)
    qc.append(cuccaro_inv(m-1), [*rz0[:m-1], *rz1[:m-1], dcz_in])
    qc.append(cuccaro_inv(m-1), [*ry0[:m-1], *ry1[:m-1], dcy_in])
    qc.append(cuccaro_inv(m-1), [*rx0[:m-1], *rx1[:m-1], dcx_in])
    
    return qc.to_gate(label="PTPC")


