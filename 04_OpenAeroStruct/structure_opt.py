# -*- coding: utf-8 -*-
"""
Created on Fri Oct 16 16:16:11 2020

@author: raulv
"""


import numpy as np

from openaerostruct.geometry.utils import generate_mesh
from openaerostruct.geometry.geometry_group import Geometry
from openaerostruct.transfer.displacement_transfer import DisplacementTransfer
from openaerostruct.structures.struct_groups import SpatialBeamAlone

import openmdao.api as om

## Part-1: Define your lifting surface ------------
# Create a dictionary to store options about the surface
mesh_dict = {'num_y' : 7,
             'wing_type' : 'CRM',
             'symmetry' : True,
             'num_twist_cp' : 5}

mesh, twist_cp = generate_mesh(mesh_dict)

surf_dict = {
            # Wing definition
            'name' : 'wing',        # name of the surface
            'symmetry' : True,     # if true, model one half of wing
                                    # reflected across the plane y = 0
            'fem_model_type' : 'tube',
            'mesh' : mesh,
            # Structural values are based on aluminum 7075
            'E' : 70.e9,            # [Pa] Young's modulus of the spar
            'G' : 30.e9,            # [Pa] shear modulus of the spar
            'yield' : 500.e6 / 2.5, # [Pa] yield stress divided by 2.5 for limiting case
            'mrho' : 3.e3,          # [kg/m^3] material density
            'fem_origin' : 0.35,    # normalized chordwise location of the spar
            't_over_c_cp' : np.array([0.15]),      # maximum airfoil thickness
            'thickness_cp' : np.ones((3)) * .1,
            'wing_weight_ratio' : 2.,
            'struct_weight_relief' : False,    # True to add the weight of the structure to the loads on the structure
            'distributed_fuel_weight' : False,
            'exact_failure_constraint' : False,
            }


## Part-2: Initialize your problem and add flow conditions ------------
# Create the problem and assign the model group
prob = om.Problem()

ny = surf_dict['mesh'].shape[1]
indep_var_comp = om.IndepVarComp()
indep_var_comp.add_output('loads', val=np.ones((ny, 6)) * 2e5, units='N')
indep_var_comp.add_output('load_factor', val=1.)

struct_group = SpatialBeamAlone(surface=surf_dict)

# Add indep_vars to the structural group
struct_group.add_subsystem('indep_vars',indep_var_comp,promotes=['*'])

prob.model.add_subsystem(surf_dict['name'], struct_group)


## Part-3: Add your design variables, constraints, and objective
# Import the Scipy Optimizer and set the driver of the problem to use
# it, which defaults to an SLSQP optimization method
prob.driver = om.ScipyOptimizeDriver()
prob.driver.options['disp'] = True
prob.driver.options['tol'] = 1e-9

recorder = om.SqliteRecorder('struct.db')
prob.driver.add_recorder(recorder)
prob.driver.recording_options['record_derivatives'] = True
prob.driver.recording_options['includes'] = ['*']

# Setup problem and add design variables, constraint, and objective
prob.model.add_design_var('wing.thickness_cp', lower=0.01, upper=0.5, ref=1e-1)
prob.model.add_constraint('wing.failure', upper=0.)
prob.model.add_constraint('wing.thickness_intersects', upper=0.)

# Add design variables, constraisnt, and objective on the problem
prob.model.add_objective('wing.structural_mass', scaler=1e-5)


## Part-4: Set up and run the optimization problem 
# Set up the problem
prob.setup(force_alloc_complex=False)

# prob.run_model()
# prob.check_partials(compact_print=False, method='fd')
# exit()
prob.run_driver()

print('wing.radius:',prob['wing.radius'])
print('Structural_mass (obj):',prob['wing.structural_mass'][0])
print('Thickness_cp (x):',prob['wing.thickness_cp'])


# Part-5: Generate N2 diagram
from openmdao.api import n2; n2(prob)

# Part-6: visualization 
from openaerostruct.utils.plot_wing import disp_plot
args = [[], []]
args[1] = 'struct.db'
disp_plot(args=args)