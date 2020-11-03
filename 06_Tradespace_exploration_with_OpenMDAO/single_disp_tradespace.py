# -*- coding: utf-8 -*-
"""
Created on Sun Nov  1 18:19:54 2020

@author: raulv
"""

# Part 0: OpenMDAO and component imports
import openmdao.api as om
import copy

# Part 1: Create a new explicit components for f_xy
class Paraboloid(om.ExplicitComponent):
    """
    Evaluates the equation f(x,y) = (x-3)^2 + xy + (y+4)^2 - 3.
    """
    
    def setup(self):
        self.add_input('x', val=0.0)
        self.add_input('y', val=0.0)

        self.add_output('f_xy', val=0.0)

    def setup_partials(self):
        # Finite difference all partials.
        self.declare_partials('*', '*', method='fd')

    def compute(self, inputs, outputs):
        """
        f(x,y) = (x-3)^2 + xy + (y+4)^2 - 3
        Minimum at: x = 6.6667; y = -7.3333
        """
        x = inputs['x']
        y = inputs['y']

        outputs['f_xy'] = (x - 3.0)**2 + x * y + (y + 4.0)**2 - 3.0



# Part 2: Create a group and Paraboloid as subsystem of group
model = om.Group()
model.add_subsystem('parab_comp', Paraboloid())

# Part 3: Create problem from the group and setup the problem
prob = om.Problem(model)
prob.setup()

# Part 4: Provide x and y input to the problem
prob.set_val('parab_comp.x', 3.0)
prob.set_val('parab_comp.y', -4.0)

# Part 5: Run the problem
prob.run_model()

# Part 6: Print the input and output of the problem
print('x =',prob['parab_comp.x'])
print('y =',prob['parab_comp.y'])
print('f_xy =',prob.get_val('parab_comp.f_xy'))

print('\n----------------\n')
# Part 7: Provide new input variables and print output
prob.set_val('parab_comp.x', 5.0)
prob.set_val('parab_comp.y', -2.0)
prob.run_model()
print('x =',prob['parab_comp.x'])
print('y =',prob['parab_comp.y'])
print('f_xy =', prob.get_val('parab_comp.f_xy'))
print('\n----------------\n')
    

# Part 8: Build the model for optimization
prob = om.Problem()
prob.model.add_subsystem('parab', Paraboloid(), promotes_inputs=['x', 'y'])
prob.model.add_subsystem('const', om.ExecComp('g = x + y'), promotes_inputs=['x', 'y'])

# Part 9: Provide initial values to x and y
prob.model.set_input_defaults('x', 3.0)
prob.model.set_input_defaults('y', -4.0)

# Part 10: Setup the optimizer
prob.driver = om.ScipyOptimizeDriver()
prob.driver.options['optimizer'] = 'COBYLA'

# Part 11: Provide bounds and objective function
prob.model.add_design_var('x', lower=-10, upper=10)
prob.model.add_design_var('y', lower=-10, upper=10)


# to add the objective and constraint to the model
prob.model.add_objective('parab.f_xy')
prob.model.add_constraint('const.g', upper=2)

# Part 12: Setup the problem and run
prob.setup()
prob.run_driver()

# Part 13: Print the results
# minimum value
print('f_xy=', prob.get_val('parab.f_xy'))
# location of the minimum
x_opt = copy.deepcopy(prob.get_val('x'))
y_opt = copy.deepcopy(prob.get_val('y'))

print('x=', prob.get_val('x'))
print('y=', prob.get_val('y'))

# Part 14: Generate N2 diagram
# from openmdao.api import n2
# n2(prob)
  

# Part 15: Tradespace Exploration
import numpy as np
import matplotlib.pyplot as plt
n = 100
x1 = np.linspace(-10,10, n)
y1 = np.linspace(-10,10, n)

f= np.zeros([n,n])
c= np.zeros([n,n])
xv, yv = np.meshgrid(x1, y1)

for i in range(n):
    for j in range(n):        
        prob.set_val('parab.x',  xv[i,j])
        prob.set_val('parab.y', yv[i,j])
        prob.run_model()
        
        f[i,j] = prob.get_val('parab.f_xy')
        c[i,j] = prob.get_val('const.g')


# Part 16: plotting 
csfont = {'fontname':'times new roman','fontsize':20}
fig1 = plt.figure(figsize=(7,6),dpi=150)
cs = plt.contour(xv, yv, f, 20)
# c1 = plt.contour(xv, yv, f,10)
plt.clabel(cs, inline=True, fontsize=10,fmt='%1.1f')
contours = plt.contour(xv, yv, c, [0,2,4], colors='r')
plt.scatter(x_opt,y_opt,s=70, c='c',)
# contours = plt.contour(x1v, x3v, ns, [5,20, 40, 60], colors='k')
plt.clabel(contours, inline=True, fontsize=14,fmt='g=%1.1f')
plt.ylabel('y',**csfont)
plt.xlabel('x',**csfont)
plt.xticks(fontsize=16 )
plt.yticks(fontsize=16 )
fig1.tight_layout()
#plt.legend()
fig1.savefig('single_D_trade_anlyt.png', dpi=400)
plt.show()
