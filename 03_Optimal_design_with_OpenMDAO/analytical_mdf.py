# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 19:21:01 2019

@author: raulv
"""
import openmdao.api as om
import numpy as np

class SellarDis1(om.ExplicitComponent):
    """
    Component containing Discipline 1 -- no derivatives version.
    """

    def setup(self):

        # Global Design Variable
        self.add_input('x1x2', val=np.zeros(2))

        # Coupling parameter
        self.add_input('y12', val=1.0)

        # Coupling output
        self.add_output('y21', val=1.0)
        self.add_output('g1', val=1.0)

        # Finite difference all partials.
        self.declare_partials('*', '*', method='fd')

    def compute(self, inputs, outputs):
        """
        Evaluates the equation g1 
        """
        x1 = inputs['x1x2'][0]
        x2 = inputs['x1x2'][1]
        y12 = inputs['y12']

        outputs['y21'] = x1 + x2 
        outputs['g1']  = y12/2 + 3*x1/4  +1 
        
class SellarDis2(om.ExplicitComponent):
    """
    Evaluates the equation g2 
    """

    def setup(self):
        # Global Design Variable
        self.add_input('x1x2', val=np.zeros(2))
        # Global Design Variable
        self.add_input('x3', val=0.)
        # Coupling parameter
        self.add_input('y21', val=1.0)

        # Coupling output
        self.add_output('y12', val=1.0)
        self.add_output('g2',  val=1.0)

        # Finite difference all partials.
        self.declare_partials('*', '*', method='fd')

    def compute(self, inputs, outputs):
        """
        Evaluates the equation
        y2 = y1**(.5) + z1 + z2
        """

        x1 = inputs['x1x2'][0]
        x2 = inputs['x1x2'][1]
        x3 = inputs['x3']
        y21 = inputs['y21']

        # Note: this may cause some issues. However, y1 is constrained to be
        # above 3.16, so lets just let it converge, and the optimizer will
        # throw it out
#        if y1.real < 0.0:
#            y1 *= -1

        outputs['y12'] = x1/2 + x2
        outputs['g2'] = -y21 -x1 + x3
        
        
class SellarMDA(om.Group):
    """
    Group containing the Sellar MDA.
    """

    def setup(self):
        indeps = self.add_subsystem('indeps', om.IndepVarComp(), promotes=['*'])
        indeps.add_output('x3', 1.0)
        indeps.add_output('x1x2', np.array([1.0, 1.0]))

        cycle = self.add_subsystem('cycle', om.Group(), promotes=['*'])
        cycle.add_subsystem('d1', SellarDis1(), promotes_inputs=['x1x2', 'y12'],promotes_outputs=['y21','g1'])
        cycle.add_subsystem('d2', SellarDis2(), promotes_inputs=['x1x2','x3', 'y21'],promotes_outputs=['y12','g2'])

        # Nonlinear Block Gauss Seidel is a gradient free solver
        cycle.nonlinear_solver = om.NonlinearBlockGS()

        self.add_subsystem('obj_cmp', om.ExecComp('obj = x1x2[0]**2 + x1x2[1]**2 + x3**2 ',
                                                  x1x2=np.array([0.0, 0.0]), x3=0.0),
                           promotes=['x1x2', 'x3','obj'])

        self.add_subsystem('con_cmp1', om.ExecComp('con1 = g1'), promotes=['con1', 'g1'])
        self.add_subsystem('con_cmp2', om.ExecComp('con2 = g2'), promotes=['con2', 'g2'])
        
        
        
prob = om.Problem()
prob.model = SellarMDA()

prob.driver = om.ScipyOptimizeDriver()
prob.driver.options['optimizer'] = 'SLSQP'
# prob.driver.options['maxiter'] = 100
prob.driver.options['tol'] = 1e-8

prob.model.add_design_var('x1x2', lower=-4, upper=4)
prob.model.add_design_var('x3', lower=-4, upper=4)
prob.model.add_objective('obj')
prob.model.add_constraint('con1', upper=0)
prob.model.add_constraint('con2', upper=0)

prob.setup()
prob.set_solver_print(level=0)


# ----- Run model with specific inputs 
print('\n Single evaluation')
prob['x3'] = 2.
prob['x1x2'] = [2, 2]
prob.run_model()
print((prob['x1x2'], prob['x3'], prob['obj'][0], prob['con1'][0], prob['con2'][0]))
print('\n')
# ----- Run optimizer

# Ask OpenMDAO to finite-difference across the model to compute the gradients for the optimizer
prob.model.approx_totals()
prob.run_driver()

# ---------------------------
print('minimum found at')
print('x1 , x2 :',prob['x1x2'])
print('x3 :',prob['x3'])
print('g1 :',prob['g1'])
print('g2 :',prob['g2'])
print('minumum objective')
print('obj :',prob['obj'][0])