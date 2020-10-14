# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 19:21:01 2019
@author: raulv
"""

# Part 1: Import required packages
import openmdao.api as om
import numpy as np

# Part 2: Create new components for Discipline1 and 2
class SellarDis1(om.ExplicitComponent):
    """
    Component containing Discipline 1 -- no derivatives version.
    """
    def setup(self):
        # Global Design Variable
        self.add_input('z', val=np.zeros(2))

        # Local Design Variable
        self.add_input('x', val=0.)

        # Coupling parameter
        self.add_input('y2', val=1.0)

        # Coupling output
        self.add_output('y1', val=1.0)

        # Finite difference all partials.
        self.declare_partials('*', '*', method='fd')

    def compute(self, inputs, outputs):
        """
        Evaluates the equation
        y1 = z1**2 + z2 + x1 - 0.2*y2
        """
        z1 = inputs['z'][0]
        z2 = inputs['z'][1]
        x1 = inputs['x']
        y2 = inputs['y2']

        outputs['y1'] = z1**2 + z2 + x1 - 0.2*y2
        
class SellarDis2(om.ExplicitComponent):
    """
    Component containing Discipline 2 -- no derivatives version.
    """
    def setup(self):
        # Global Design Variable
        self.add_input('z', val=np.zeros(2))

        # Coupling parameter
        self.add_input('y1', val=1.0)

        # Coupling output
        self.add_output('y2', val=1.0)

        # Finite difference all partials.
        self.declare_partials('*', '*', method='fd')

    def compute(self, inputs, outputs):
        """
        Evaluates the equation
        y2 = y1**(.5) + z1 + z2
        """
        z1 = inputs['z'][0]
        z2 = inputs['z'][1]
        y1 = inputs['y1']

        # Note: this may cause some issues. However, y1 is constrained to be
        # above 3.16, so lets just let it converge, and the optimizer will
        # throw it out
        if y1.real < 0.0:
            y1 *= -1

        outputs['y2'] = y1**.5 + z1 + z2
        
# Part 3: Create group SellarMDA
class SellarMDA(om.Group):
    """
    Group containing the Sellar MDA. 
    """
    def setup(self):
        indeps = self.add_subsystem('indeps', om.IndepVarComp(), promotes=['*'])
        indeps.add_output('x', 1.0)
        indeps.add_output('z', np.array([5.0, 2.0]))

        cycle = self.add_subsystem('cycle', om.Group(), promotes=['*'])
        cycle.add_subsystem('d1', SellarDis1(), promotes_inputs=['x', 'z', 'y2'],
                            promotes_outputs=['y1'])
        cycle.add_subsystem('d2', SellarDis2(), promotes_inputs=['z', 'y1'],
                            promotes_outputs=['y2'])

        # Nonlinear Block Gauss Seidel is a gradient free solver
        cycle.nonlinear_solver = om.NonlinearBlockGS(iprint=1)  # try iprint=2

        self.add_subsystem('obj_cmp', om.ExecComp('obj = x**2 + z[1] + y1 + exp(-y2)',
                                                  z=np.array([0.0, 0.0]), x=0.0),
                           promotes=['x', 'z', 'y1', 'y2', 'obj'])

        self.add_subsystem('con_cmp1', om.ExecComp('con1 = 3.16 - y1'), promotes=['con1', 'y1'])
        self.add_subsystem('con_cmp2', om.ExecComp('con2 = y2 - 24.0'), promotes=['con2', 'y2'])
        
        
# Part 4: Setup model and problem 
prob = om.Problem()
prob.model = SellarMDA()
prob.setup()

# Part 5: Provide input to the problem 
prob['x'] = 2.
prob['z'] = [-1., -1.]

prob.run_model()

#  Part 6:  print details
print('\nInput ---')
print('x :',prob['x'])
print('z1 :',prob['z'][0])
print('z2 :',prob['z'][1])

print('\nDiscipline output ---')
print('y1 :',prob['y1'])
print('y2 :',prob['y2'])

print('\nObjective and constraints---')
print('obj :',prob['obj'])
print('con1 :',prob['con1'])
print('con2 :',prob['con2'])
print('\n')

#  Part 7: Optimizing the Problem
prob.driver = om.ScipyOptimizeDriver()
prob.driver.options['optimizer'] = 'SLSQP'
# prob.driver.options['maxiter'] = 100
prob.driver.options['tol'] = 1e-8

prob.model.add_design_var('x', lower=0, upper=10)
prob.model.add_design_var('z', lower=0, upper=10)
prob.model.add_objective('obj')
prob.model.add_constraint('con1', upper=0)
prob.model.add_constraint('con2', upper=0)

# Ask OpenMDAO to finite-difference across the model to compute the gradients for the optimizer
prob.model.approx_totals()

prob.setup()
prob.set_solver_print(level=0)

prob.run_driver()

print('\nminimum found at')
print('x :',prob.get_val('x')[0])
print('z1 :',prob.get_val('z')[0])
print('z2 :',prob.get_val('z')[1])

print('')
print('y1 :',prob.get_val('y1'))
print('y2 :',prob.get_val('y2'))

print('\nminumum objective and constraints')
print('obj :',prob.get_val('obj')[0])
print('con1 :',prob.get_val('con1'))
print('con2 :',prob.get_val('con2'))

# Part 9: Generate N2 diagram
from openmdao.api import n2
n2(prob)
