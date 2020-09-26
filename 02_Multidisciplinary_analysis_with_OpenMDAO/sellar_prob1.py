#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct  3 10:42:11 2019
@author: vvssraul
"""

"""
Sellar Problem 
input: x
Min : f = (y1)**2 - y2 + 3
Discipline1 : y1 = (y2)**2 
Discipline2 : exp(-y1 y2) - x y1 = 0 

""" 

# Block 1: OpenMDAO and component imports
import numpy as np
from openmdao.api import Problem , Group , ScipyOptimizeDriver
from openmdao.api import IndepVarComp , ExecComp
from openmdao.api import NewtonSolver , DirectSolver
from openmdao . api import ExplicitComponent , ImplicitComponent


class Discipline1( ExplicitComponent ) :
    def setup(self):
        self.add_input( 'y2' )
        self.add_output('y1')
        self.declare_partials('y1','y2')
        
    def compute( self , inputs , outputs ) :
    	outputs[ 'y1' ] = inputs[ 'y2' ]**2

    def compute_partials(self, inputs, partials):
        partials[ 'y1' , 'y2' ] = 2 * inputs[ 'y2' ]


class Discipline2( ImplicitComponent ) :
    def setup(self):
        self.add_input('x')
        self.add_input('y1')
        self.add_output('y2')
        self.declare_partials('y2' , 'x')
        self.declare_partials('y2' , 'y1')
        self.declare_partials('y2' , 'y2')
        
    def apply_nonlinear(self, inputs, outputs, residuals):
        residuals[ 'y2' ] = ( np.exp(-inputs[ 'y1' ] * outputs[ 'y2' ] ) - inputs[ 'x' ] * outputs[ 'y2' ] )
        
    def linearize(self, inputs, outputs, partials ):
        partials['y2' , 'x' ] = -outputs['y2']
        partials['y2' , 'y1' ] = (-outputs['y2'] * np.exp(-inputs['y1'] * outputs['y2']) )
        partials['y2' , 'y2' ] = (-inputs['y1'] * np.exp(-inputs['y1'] * outputs['y2']) - inputs['x'] )
        

# Block 2: creation of all the components and groups
# except the top -level group
input_comp = IndepVarComp('x')

states_group = Group()
states_group.add_subsystem( 'discipline1_comp' , Discipline1() )
states_group.add_subsystem( 'discipline2_comp' , Discipline2() )
states_group.connect( 'discipline1_comp.y1' , 'discipline2_comp.y1' )
states_group.connect( 'discipline2_comp.y2' , 'discipline1_comp.y2' )
states_group.nonlinear_solver = NewtonSolver( iprint = 0 )
states_group.linear_solver = DirectSolver( iprint = 0 )
output_comp = ExecComp( 'f=y1**2 - y2 + 3' )

# Block 3: creation of the top -level group
model = Group()
model.add_subsystem( 'input_comp' , input_comp )
model.add_subsystem( 'states_group' , states_group )
model.add_subsystem( 'output_comp' , output_comp )
model.connect( 'input_comp.x' , 'states_group.discipline2_comp.x' )
model.connect( 'states_group.discipline1_comp.y1' , 'output_comp.y1' )
model.connect( 'states_group.discipline2_comp.y2' , 'output_comp.y2' )

# Block 4: specification of the model input (design variable)
#and model output (objective)
model.add_design_var( 'input_comp.x' )
model.add_objective( 'output_comp.f' )

# Block 5: creation of the problem and setup
prob = Problem()
prob.model = model
prob.driver = ScipyOptimizeDriver()
prob.setup()

# Block 6: set a model input; run the model; and print a model output
prob[ 'input_comp.x' ] = 1 
prob.run_model ( )
print( prob [ 'output_comp.f' ] )

# Block 7: solve the optimization problem and print the results
prob.run_driver ( )
print( 'x = {} \nf = {} '.format(prob [ 'input_comp.x' ] , prob [ 'output_comp.f' ]) )
#print( 'y1 = {} \ny2 = {}'.format(prob['output_comp.y1'],prob['output_comp.y2']) )

