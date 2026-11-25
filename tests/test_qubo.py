import unittest
from itertools import product
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path

spec = spec_from_file_location("demo", Path(__file__).resolve().parents[1] / "experiments/01_qubo_classical/demo_qubo.py")
demo = module_from_spec(spec)
spec.loader.exec_module(demo)

class TestQubo(unittest.TestCase):
    def test_cost(self):
        self.assertEqual([demo.cost(*x) for x in product([0,1], repeat=2)], [660,610,610,630])
    def test_ising(self):
        for a,b in product([0,1], repeat=2):
            z1,z2=1-2*a,1-2*b
            self.assertEqual(demo.cost(a,b),627.5+7.5*z1+7.5*z2+17.5*z1*z2)
