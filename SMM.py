import numpy as np
from math import inf
from qiskit import QuantumCircuit,QuantumRegister
from qiskit.circuit.library import QFT,DraperQFTAdder
from .gates import IP_adder,cuccaro_1,cuccaro_2,cuccaro_inv,correction_g,q_add,q_sub, interpol_phases

def QQM(n: int, N: int) -> QuantumCircuit:
    x = QuantumRegister(n)
    y = QuantumRegister(n)
    w = QuantumRegister(n)
    anc = QuantumRegister(1)
    qc = QuantumCircuit(x, y, w, anc)
    qc.append(QFT(num_qubits=n, do_swaps=True).to_gate(), [*w])
    PTP(qc, 2 * np.pi / N, x, y, w, anc, n)    
    qc.append(QFT(num_qubits=n, do_swaps=True).inverse().to_gate(), [*w])

    return qc.to_gate()

def PTP(qc: QuantumCircuit, phi: float, x, y, z, anc,  n: int, cutoff: int = 4):
    if n <= cutoff:        
        for i in range(n):
            for j in range(n):
                for k in range(len(z)):
                    qc.mcp(
                        phi * (2**(i+j+k)), 
                        control_qubits=[x[i], y[j]], 
                        target_qubit=z[k]
                    )
                    
        return

    k = 3
    q = 3 * k - 2
    m = n // 3
    
    xc = [x[i*m : (i+1)*m] for i in range(3)]
    yc = [y[i*m : (i+1)*m] for i in range(3)]
    zc = [z[i*m : (i+1)*m] for i in range(3)]
    
    points = [0, inf, 1, -1, 2, -2, -0.5]
    phases = interpol_phases(phi, points, m) 
    

    for l in range(q):
            pt = points[l]
            phi_l = phases[l]
            
            if pt == 0:
                PTP(qc, phi_l, xc[0], yc[0], zc[0], anc, m, cutoff)
                
            elif pt == float('inf'):
                PTP(qc, phi_l, xc[2], yc[2], zc[2], anc, m, cutoff)
                
            elif pt == 1:
                qc.append(q_add(), [*xc[1], *xc[0], anc])
                qc.append(q_add(), [*xc[1], *xc[2], anc])
                qc.append(q_add(), [*yc[1], *yc[0], anc]) 
                qc.append(q_add(), [*yc[1], *yc[2], anc])
                qc.append(q_add(), [*zc[1], *zc[0], anc]) 
                qc.append(q_add(), [*zc[1], *zc[2], anc])
                sub_ptpc = QuantumCircuit(6 * m + 1) 
                local_xc = [sub_ptpc.qubits[0 : m], sub_ptpc.qubits[m : 2*m]]
                local_yc = [sub_ptpc.qubits[2*m : 3*m], sub_ptpc.qubits[3*m : 4*m]]
                local_zc = [sub_ptpc.qubits[4*m : 5*m], sub_ptpc.qubits[5*m : 6*m]]
                local_anc = sub_ptpc.qubits[6 * m]
                PTPC(sub_ptpc, m, phi_l, local_anc, local_xc, local_yc, local_zc, cutoff)
                qc.append(sub_ptpc.to_gate(label="PTPC"), [
                *xc[0], *xc[1],
                *yc[0], *yc[1],
                *zc[0], *zc[1], anc
            ])
                qc.append(q_sub(), [*zc[1], *zc[2], anc])
                qc.append(q_sub(), [*zc[1], *zc[0], anc]) 
                qc.append(q_sub(), [*yc[1], *yc[2], anc])
                qc.append(q_sub(), [*yc[1], *yc[0], anc]) 
                qc.append(q_sub(), [*xc[1], *xc[2], anc])
                qc.append(q_sub(), [*xc[1], *xc[0], anc])
            elif pt == -1:
                qc.append(q_sub(), [*xc[1], *xc[1], anc])
                qc.append(q_sub(), [*xc[1], *xc[1], anc])
                qc.append(q_add(), [*xc[1], *xc[0], anc])
                qc.append(q_add(), [*xc[1], *xc[2], anc])
                qc.append(q_sub(), [*yc[1], *yc[1], anc])
                qc.append(q_sub(), [*yc[1], *yc[1], anc])
                qc.append(q_add(), [*yc[1], *yc[0], anc])
                qc.append(q_add(), [*yc[1], *yc[2], anc])
                qc.append(q_sub(), [*zc[1], *zc[1], anc])
                qc.append(q_sub(), [*zc[1], *zc[1], anc])
                qc.append(q_add(), [*zc[1], *zc[0], anc])
                qc.append(q_add(), [*zc[1], *zc[2], anc])
                sub_ptpc = QuantumCircuit(6 * m + 1)
                local_xc = [sub_ptpc.qubits[0 : m], sub_ptpc.qubits[m : 2*m]]
                local_yc = [sub_ptpc.qubits[2*m : 3*m], sub_ptpc.qubits[3*m : 4*m]]
                local_zc = [sub_ptpc.qubits[4*m : 5*m], sub_ptpc.qubits[5*m : 6*m]]
                local_anc = sub_ptpc.qubits[6 * m]
                PTPC(sub_ptpc, m, phi_l, local_anc, local_xc, local_yc, local_zc, cutoff)
                qc.append(sub_ptpc.to_gate(label="PTPC_neg1"), [
                    *xc[0], *xc[1],
                    *yc[0], *yc[1],
                    *zc[0], *zc[1],
                    anc
                ])
                qc.append(q_sub(), [*zc[1], *zc[2], anc])
                qc.append(q_sub(), [*zc[1], *zc[0], anc])
                qc.append(q_add(), [*zc[1], *zc[1], anc])
                qc.append(q_add(), [*zc[1], *zc[1], anc])            
                qc.append(q_sub(), [*yc[1], *yc[2], anc])
                qc.append(q_sub(), [*yc[1], *yc[0], anc])
                qc.append(q_add(), [*yc[1], *yc[1], anc])
                qc.append(q_add(), [*yc[1], *yc[1], anc])
                qc.append(q_sub(), [*xc[1], *xc[2], anc])
                qc.append(q_sub(), [*xc[1], *xc[0], anc])
                qc.append(q_add(), [*xc[1], *xc[1], anc])
                qc.append(q_add(), [*xc[1], *xc[1], anc])
            elif pt == -2:
                qc.append(q_sub(), [*xc[1][1:], *xc[0][:m-1], anc])
                qc.append(q_sub(), [*xc[1][2:], *xc[2][:m-2], anc])
                
                qc.append(q_sub(), [*yc[1][1:], *yc[0][:m-1], anc])
                qc.append(q_sub(), [*yc[1][2:], *yc[2][:m-2], anc])
                
                qc.append(q_sub(), [*zc[1][1:], *zc[0][:m-1], anc])
                qc.append(q_sub(), [*zc[1][2:], *zc[2][:m-2], anc])
                sub_ptpc = QuantumCircuit(6 * m + 1)
                local_xc = [sub_ptpc.qubits[0 : m], sub_ptpc.qubits[m : 2*m]]
                local_yc = [sub_ptpc.qubits[2*m : 3*m], sub_ptpc.qubits[3*m : 4*m]]
                local_zc = [sub_ptpc.qubits[4*m : 5*m], sub_ptpc.qubits[5*m : 6*m]]
                local_anc = sub_ptpc.qubits[6 * m]
                
                PTPC(sub_ptpc, m, -phi_l, local_anc, local_xc, local_yc, local_zc, cutoff)
                
                qc.append(sub_ptpc.to_gate(label="PTPC_neg2"), [
                    *xc[0], *xc[1],
                    *yc[0], *yc[1],
                    *zc[0], *zc[1],
                    anc
                ])
                qc.append(q_add(), [*zc[1][2:], *zc[2][:m-2], anc])
                qc.append(q_add(), [*zc[1][1:], *zc[0][:m-1], anc])
                qc.append(q_add(), [*yc[1][2:], *yc[2][:m-2], anc])
                qc.append(q_add(), [*yc[1][1:], *yc[0][:m-1], anc])
                qc.append(q_add(), [*xc[1][2:], *xc[2][:m-2], anc])
                qc.append(q_add(), [*xc[1][1:], *xc[0][:m-1], anc])
                
            elif pt == 2:
                qc.append(q_add(), [*xc[1][1:], *xc[0][:m-1], anc])
                qc.append(q_add(), [*xc[1][2:], *xc[2][:m-2], anc])
                qc.append(q_add(), [*yc[1][1:], *yc[0][:m-1], anc])
                qc.append(q_add(), [*yc[1][2:], *yc[2][:m-2], anc])
                qc.append(q_add(), [*zc[1][1:], *zc[0][:m-1], anc])
                qc.append(q_add(), [*zc[1][2:], *zc[2][:m-2], anc])
                sub_ptpc = QuantumCircuit(6 * m + 1)
                local_xc = [sub_ptpc.qubits[0 : m], sub_ptpc.qubits[m : 2*m]]
                local_yc = [sub_ptpc.qubits[2*m : 3*m], sub_ptpc.qubits[3*m : 4*m]]
                local_zc = [sub_ptpc.qubits[4*m : 5*m], sub_ptpc.qubits[5*m : 6*m]]
                local_anc = sub_ptpc.qubits[6 * m]
                
                PTPC(sub_ptpc, m, phi_l, local_anc, local_xc, local_yc, local_zc, cutoff)
                qc.append(sub_ptpc.to_gate(), [
                    *xc[0], *xc[1],
                    *yc[0], *yc[1],
                    *zc[0], *zc[1],
                    anc
                ])
                qc.append(q_sub(), [*zc[1][2:], *zc[2][:m-2], anc])
                qc.append(q_sub(), [*zc[1][1:], *zc[0][:m-1], anc])
                qc.append(q_sub(), [*yc[1][2:], *yc[2][:m-2], anc])
                qc.append(q_sub(), [*yc[1][1:], *yc[0][:m-1], anc])
                qc.append(q_sub(), [*xc[1][2:], *xc[2][:m-2], anc])
                qc.append(q_sub(), [*xc[1][1:], *xc[0][:m-1], anc])
            elif pt == 0.5:
                qc.append(q_sub(), [*xc[1][2:], *xc[0][:m-2], anc])
                qc.append(q_sub(), [*xc[1], *xc[2], anc])
                qc.append(q_sub(), [*yc[1][2:], *yc[0][:m-2], anc])
                qc.append(q_sub(), [*yc[1], *yc[2], anc])
                qc.append(q_sub(), [*zc[1][2:], *zc[0][:m-2], anc])
                qc.append(q_sub(), [*zc[1], *zc[2], anc])
                sub_ptpc = QuantumCircuit(6 * m + 1)
                local_xc = [sub_ptpc.qubits[0 : m], sub_ptpc.qubits[m : 2*m]]
                local_yc = [sub_ptpc.qubits[2*m : 3*m], sub_ptpc.qubits[3*m : 4*m]]
                local_zc = [sub_ptpc.qubits[4*m : 5*m], sub_ptpc.qubits[5*m : 6*m]]
                local_anc = sub_ptpc.qubits[6 * m]
                PTPC(sub_ptpc, m, -phi_l, local_anc, local_xc, local_yc, local_zc, cutoff)
                qc.append(sub_ptpc.to_gate(label="PTPC_neg2"), [
                    *xc[0], *xc[1],
                    *yc[0], *yc[1],
                    *zc[0], *zc[1],
                    anc
                ])
                qc.append(q_add(), [*zc[1], *zc[2], anc])
                qc.append(q_add(), [*zc[1][2:], *zc[0][:m-2], anc])
                qc.append(q_add(), [*yc[1], *yc[2], anc])
                qc.append(q_add(), [*yc[1][2:], *yc[0][:m-2], anc])
                qc.append(q_add(), [*xc[1], *xc[2], anc])
                qc.append(q_add(), [*xc[1][2:], *xc[0][:m-2], anc])


    return 


def PTPC(qc, m: int, phi: float, anc, xc, yc, zc, cutoff: int = 4):
    
    rx0 = xc[0]
    rx1 = xc[1]
    ry0 = yc[0]
    ry1 = yc[1]
    rz0 = zc[0]
    rz1 = zc[1]

    dcx_in, dcy_in, dcz_in = rx0[m-1], ry0[m-1], rz0[m-1]
    dcx_out, dcy_out, dcz_out = rx1[m-1], ry1[m-1], rz1[m-1] # FIXED: Added dcz_out
    qc.append(correction_g(m, phi), [*rx0, *rx1, *ry0, *ry1, *rz0, *rz1])
    

    qc.append(cuccaro_1(m-1), [*rx0[:m-1], *rx1[:m-1], dcx_in])
    qc.append(cuccaro_1(m-1), [*ry0[:m-1], *ry1[:m-1], dcy_in])
    qc.append(cuccaro_1(m-1), [*rz0[:m-1], *rz1[:m-1], dcz_in])
    carry_x = rx0[m-2]
    carry_y = ry0[m-2]
    carry_z = rz0[m-2] 


    for i in range(m-1):
        for j in range(m-1):
            wt = phi * (2**(m-1 + i + j))
            qc.mcp(wt, control_qubits=[carry_x, ry1[i]], target_qubit=rz1[j])
            qc.mcp(wt, control_qubits=[carry_y, rx1[i]], target_qubit=rz1[j])
            qc.mcp(wt, control_qubits=[rx1[i], ry1[j]], target_qubit=carry_z) 
            qc.mcp(wt, control_qubits=[dcx_out, ry1[i]], target_qubit=rz1[j])
            qc.mcp(wt, control_qubits=[dcy_out, rx1[i]], target_qubit=rz1[j])
            qc.mcp(wt, control_qubits=[rx1[i], ry1[j]], target_qubit=dcz_out) 

    qc.append(cuccaro_2(m-1), [*rx0[:m-1], *rx1[:m-1], dcx_in])
    qc.append(cuccaro_2(m-1), [*ry0[:m-1], *ry1[:m-1], dcy_in])
    qc.append(cuccaro_2(m-1), [*rz0[:m-1], *rz1[:m-1], dcz_in])
    PTP(qc, phi, rx1[:m-1], ry1[:m-1], rz1[:m-1], anc, m - 1, cutoff)
    qc.append(cuccaro_inv(m-1), [*rz0[:m-1], *rz1[:m-1], dcz_in])
    qc.append(cuccaro_inv(m-1), [*ry0[:m-1], *ry1[:m-1], dcy_in])
    qc.append(cuccaro_inv(m-1), [*rx0[:m-1], *rx1[:m-1], dcx_in])
    
    return 


