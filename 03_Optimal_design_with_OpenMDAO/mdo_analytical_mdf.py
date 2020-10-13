# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 19:21:01 2019

@author: raulv
"""
# Part 1: Import required packages
import openmdao.api as om

# Part 2: Create new components for Analysis1 and 2
class Analysis1(om.ExplicitComponent):
    """
    Component containing Discipline1 and Constraint1
    """
    def setup(self):
        # Global Design Variable
        self.add_input('x1', val=0.0)
        self.add_input('x2', val=0.0)

        # Coupling parameter
        self.add_input('y12', val=1.0)

        # Coupling output
        self.add_output('y21', val=1.0)
        self.add_output('g1', val=1.0)

        # Finite difference all partials.
        self.declare_partials('*', '*', method='fd')

    def compute(self, inputs, outputs):
        """
        Evaluate y21, g1 
        """
        x1 = inputs['x1']
        x2 = inputs['x2']
        y12 = inputs['y12']

        outputs['y21'] = x1 + x2 
        outputs['g1']  = y12/2 + 3*x1/4  +1 
        
class Analysis2(om.ExplicitComponent):
    """
    Component containing Discipline2 and Constraint2
    """
    def setup(self):
        # Global Design Variable
        self.add_input('x1', val=0.0)
        self.add_input('x2', val=0.0)
        self.add_input('x3', val=0.0)
        
        # Coupling parameter
        self.add_input('y21', val=1.0)

        # Coupling output
        self.add_output('y12', val=1.0)
        self.add_output('g2',  val=1.0)

        # Finite difference all partials.
        self.declare_partials('*', '*', method='fd')

    def compute(self, inputs, outputs):
        """
        Evaluate y12, g2
        """
        x1 = inputs['x1']
        x2 = inputs['x2']
        x3 = inputs['x3']
        y21 = inputs['y21']

        outputs['y12'] = x1/2 + x2
        outputs['g2'] = -y21 -x1 + x3
        
# Part 3: Create group MDA
class ProcessMDA(om.Group):
    """
    Group containing MDA
    """
    def setup(self):
        indeps = self.add_subsystem('indeps', om.IndepVarComp(), promotes=['*'])
        indeps.add_output('x1', 1.0)
        indeps.add_output('x2', 1.0)
        indeps.add_output('x3', 1.0)

        cycle = self.add_subsystem('cycle', om.Group(), promotes=['*'])
        cycle.add_subsystem('d1', Analysis1(), promotes_inputs=['x1','x2','y12'],promotes_outputs=['y21','g1'])
        cycle.add_subsystem('d2', Analysis2(), promotes_inputs=['x1','x2','x3','y21'],promotes_outputs=['y12','g2'])

        # Nonlinear Block Gauss Seidel is a gradient free solver
        cycle.nonlinear_solver = om.NonlinearBlockGS()

        self.add_subsystem('obj_cmp', om.ExecComp('obj = x1**2 + x2**2 + x3**2 ',
                                                  x1=0.0, x2=0.0, x3=0.0),
                           promotes=['x1','x2','x3','obj'])

        self.add_subsystem('con_cmp1', om.ExecComp('con1 = g1'), promotes=['con1', 'g1'])
        self.add_subsystem('con_cmp2', om.ExecComp('con2 = g2'), promotes=['con2', 'g2'])
        
        
# Part 4: Build the model and problem for optimization
prob = om.Problem()
prob.model = ProcessMDA()

# Part 5: Setup optimizer
prob.driver = om.ScipyOptimizeDriver()
prob.driver.options['optimizer'] = 'SLSQP'
# prob.driver.options['maxiter'] = 100
prob.driver.options['tol'] = 1e-8

# Part 6: Provide bounds and objective function
prob.model.add_design_var('x1', lower=-4, upper=4)
prob.model.add_design_var('x2', lower=-4, upper=4)
prob.model.add_design_var('x3', lower=-4, upper=4)
prob.model.add_objective('obj')
prob.model.add_constraint('con1', upper=0)
prob.model.add_constraint('con2', upper=0)

prob.setup()
prob.set_solver_print(level=0)


# Part 7: Run model with initial values
print('\nSingle evaluation')
prob['x1'] = 2.
prob['x2'] = 2.
prob['x3'] = 2.
prob.run_model()
print('x1 :',prob['x1'])
print('x2 :',prob['x2'])
print('x3 :',prob['x3'])
print('g1 :',prob['g1'])
print('g2 :',prob['g2'])
print('obj :',prob['obj'][0])
print('\n')

# Part 8: Run optimization and print outputs
# Ask OpenMDAO to finite-difference across the model to compute the gradients for the optimizer
prob.model.approx_totals()
prob.run_driver()
# ---------------------------
print('minimum found at')
print('x1 :',prob['x1'])
print('x2 :',prob['x2'])
print('x3 :',prob['x3'])
print('g1 :',prob['g1'])
print('g2 :',prob['g2'])
print('minumum objective')
print('obj :',prob['obj'][0])