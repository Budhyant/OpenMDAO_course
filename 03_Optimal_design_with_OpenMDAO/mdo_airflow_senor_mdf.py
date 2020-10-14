# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 19:21:01 2019

@author: raulv
"""
# Part 1: Import required packages
import openmdao.api as om
import numpy as np

# Part 2: Create new components
class Structures(om.ImplicitComponent):  
    """
    Structures Component
    """
    def setup(self):
        # Global Design Variable
        self.add_input('l', val=0.1)
        
        # Coupling parameter
        self.add_input('F', val=0.1)

        # Coupling output
        self.add_output('theta', val=0.1)

        # Finite difference all partials.
        self.declare_partials('*', '*', method='fd')     
        
    def apply_nonlinear(self, inputs, outputs, residuals):
        """
        Evaluates theta
        """
        l = inputs['l']
        F = inputs['F']
        theta = outputs['theta']
        k = 0.05  #constant          
        residuals['theta'] = k*theta - 1/2*F*l*np.cos(theta)
        # print('residuals',residuals['theta'])

class Aerodynamics(om.ExplicitComponent):
    """
    Aerodynamics Component
    """
    def setup(self):
        # Global Design Variable
        self.add_input('l', val=0.1)
        self.add_input('w', val=0.1)     
                
        # Coupling input
        self.add_input('theta', val=0.5)
        
        # Coupling output
        self.add_output('F', val=3)

        # Finite difference all partials.
        self.declare_partials('*', '*', method='fd')

    def compute(self, inputs, outputs):
        """
        Evaluates F
        """
        l = inputs['l']
        w = inputs['w']
        theta = inputs['theta']
        Cd = 2.0
        rho = 1.0
        v = 40.0  # m/s
        C = 0.5*rho*Cd  # constant
        Af = l*w*np.cos(theta) 
        outputs['F'] = C*Af*v**2 
        # print(outputs['F'])
        
# Part 3: Create group MDA        
class ProcessMDA(om.Group):

    def setup(self):
        indeps = self.add_subsystem('indeps', om.IndepVarComp(), promotes=['*'])
        indeps.add_output('l', 0.01)
        indeps.add_output('w', 0.01)
        
        cycle = self.add_subsystem('cycle', om.Group(), promotes=['*'])
        cycle.add_subsystem('d1', Structures(), promotes_inputs=['l', 'F'], promotes_outputs=['theta'])
        cycle.add_subsystem('d2', Aerodynamics(), promotes_inputs=['l', 'w','theta'], promotes_outputs=['F'])

        ns = cycle.nonlinear_solver = om.NewtonSolver(solve_subsystems=True) 
        ns.options['maxiter'] = 500   

        self.add_subsystem('obj_cmp', om.ExecComp('obj = (theta - 0.250)**2'), promotes=['theta','obj'])       
        self.add_subsystem('con_cmp1', om.ExecComp('con1 = F - 7'), promotes=['con1', 'F'])
        self.add_subsystem('con_cmp2', om.ExecComp('con2 = l*w - 0.01'), promotes=['con2', 'l','w'])
        
# Part 4: Build the model and problem for optimization
prob = om.Problem()
prob.model = ProcessMDA()

# Part 5: Setup optimizer
prob.driver = om.ScipyOptimizeDriver()
prob.driver.options['optimizer'] ='SLSQP'  #'COBYLA' 'SLSQP'
prob.driver.options['maxiter'] = 100
prob.driver.options['tol'] = 1e-5
# prob.driver.options['disp'] = True

# Part 6: Provide bounds and objective function
prob.model.add_design_var('l', lower=0.01, upper=1)
prob.model.add_design_var('w', lower=0.01, upper=1)
prob.model.add_objective('obj')
prob.model.add_constraint('con1', lower=-1e-5, upper=0)
prob.model.add_constraint('con2', equals=0)

prob.setup()
prob.set_solver_print(level=0)


# Part 7: Run model with initial values
print('\nSingle evaluation')
prob['l'] = 0.1
prob['w'] = 0.1
prob.run_model()
print('l=',prob['l'])
print('w=',prob['w'])
print('theta=',prob['theta'])
print('F=',prob['F'])
print('f=',prob['obj'])
print('\n')

# Part 8: Run optimization and print outputs
prob.model.approx_totals()
prob.run_driver()
# ---------------------------
print('minimum found at')
print('l=',prob['l'])
print('w=',prob['w'])
print('theta=',prob['theta'])
print('F=',prob['F'])
print('con1=',prob['con1'])
print('con2=',prob['con2'])
print('minumum objective')
print('f=',prob['obj'])

# Part 9: Generate N2 diagram
from openmdao.api import n2
n2(prob)