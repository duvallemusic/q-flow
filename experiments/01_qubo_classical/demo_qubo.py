"""Exemplo didático Q-Flow: 2 veículos, 2 rotas cada. Dados fictícios.
Execute: python demo_qubo.py [--quantum]
Não estima economia real nem comprova vantagem quântica.
"""
import argparse
from itertools import product


def cost(x1, x2):
    # x=0: rota A; x=1: rota B. Ambos em A: congestionamento de R$70.
    return 660 - 50*x1 - 50*x2 + 70*x1*x2


def classical():
    vals = [(x, cost(*x)) for x in product([0, 1], repeat=2)]
    for x, c in vals:
        print(f'{x}: R$ {c}')
    optimum = min(c for _, c in vals)
    assert optimum == 610 and cost(0,0) == 660
    return optimum


def quantum(optimum):
    from qiskit.primitives import StatevectorSampler
    from qiskit_optimization import QuadraticProgram
    from qiskit_optimization.algorithms import MinimumEigenOptimizer
    from qiskit_optimization.minimum_eigensolvers import QAOA
    from qiskit_optimization.optimizers import COBYLA
    qp = QuadraticProgram('qflow_toy')
    qp.binary_var('x1'); qp.binary_var('x2')
    # Scale objective for the variational optimizer; final cost is computed in reais.
    qp.minimize(constant=6.60, linear={'x1': -.50, 'x2': -.50}, quadratic={('x1','x2'):.70})
    qaoa = QAOA(sampler=StatevectorSampler(seed=42, default_shots=4096),
                optimizer=COBYLA(maxiter=120), reps=2,
                initial_point=[0.5, 0.5, 0.5, 0.5])
    result = MinimumEigenOptimizer(qaoa).solve(qp)
    bits = tuple(int(round(v)) for v in result.x)
    value = cost(*bits)
    print(f'QAOA (simulador): {bits}, R$ {value}; gap R$ {value-optimum}')
    print('Amostragem estocástica; sem garantia de ótimo. Nenhum hardware IBM utilizado.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--quantum', action='store_true')
    args = p.parse_args(); optimum = classical()
    if args.quantum:
        quantum(optimum)
