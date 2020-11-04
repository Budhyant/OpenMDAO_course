# -*- coding: utf-8 -*-
"""
Created on Mon Nov  2 14:22:41 2020

@author: raulv
"""

################################################################################
# This script runs an aerostructural optimization for the ScanEagle airplane,
# a small drone used for recon missions. The geometry definition comes from
# a variety of sources, including spec sheets and discussions with the
# manufacturer, Insitu.
#
# Results using this model were presented in this paper:
# https://arc.aiaa.org/doi/abs/10.2514/6.2018-1658
# which was presented at AIAA SciTech 2018.
################################################################################

## Part-0: Import required packages
import numpy as np
from openaerostruct.geometry.utils import generate_mesh
from openaerostruct.integration.aerostruct_groups import AerostructGeometry, AerostructPoint
import openmdao.api as om
from openaerostruct.utils.constants import grav_constant

# Total number of nodes to use in the spanwise (num_y) and
# chordwise (num_x) directions. Vary these to change the level of fidelity.
num_y = 21
num_x = 3

# Create a mesh dictionary to feed to generate_mesh to actually create
# the mesh array.
mesh_dict = {'num_y' : num_y,
             'num_x' : num_x,
             'wing_type' : 'rect',
             'symmetry' : True,
             'span_cos_spacing' : 0.5,
             'span' : 3.11,
             'root_chord' : 0.3,
             }

mesh = generate_mesh(mesh_dict)

# Apply camber to the mesh
camber = 1 - np.linspace(-1, 1, num_x) ** 2
camber *= 0.3 * 0.05
for ind_x in range(num_x):
    mesh[ind_x, :, 2] = camber[ind_x]



# Introduce geometry manipulation variables to define the ScanEagle shape
zshear_cp = np.zeros(10)
zshear_cp[0] = .3

xshear_cp = np.zeros(10)
xshear_cp[0] = .15

chord_cp = np.ones(10)
chord_cp[0] = .5
chord_cp[-1] = 1.5
chord_cp[-2] = 1.3

radius_cp = 0.01  * np.ones(10)

# Define wing parameters
surface = {
            # Wing definition
            'name' : 'wing',        # name of the surface
            'symmetry' : True,     # if true, model one half of wing
                                    # reflected across the plane y = 0
            'S_ref_type' : 'wetted', # how we compute the wing area,
                                     # can be 'wetted' or 'projected'
            'fem_model_type' : 'tube',

            'taper' : 0.9,
            'zshear_cp' : zshear_cp,
            'xshear_cp' : xshear_cp,
            'chord_cp' : chord_cp,
            'root_chord' : 1.,      # root chord
            
            
            'sweep' : 20.,
            'twist_cp' : np.array([2.5, 2.5, 5.]),  #np.zeros((3)), twist control points(cp)
            'thickness_cp' : np.ones((3))*.008,     # thickness control points(cp)

            # Give OAS the radius and mesh from before
            'radius_cp' : radius_cp,
            'mesh' : mesh,

            # Aerodynamic performance of the lifting surface at
            # an angle of attack of 0 (alpha=0).
            # These CL0 and CD0 values are added to the CL and CD
            # obtained from aerodynamic analysis of the surface to get
            # the total CL and CD.
            # These CL0 and CD0 values do not vary wrt alpha.
            'CL0' : 0.0,            # CL of the surface at alpha=0
            'CD0' : 0.015,            # CD of the surface at alpha=0

            # Airfoil properties for viscous drag calculation
            'k_lam' : 0.05,         # percentage of chord with laminar
                                    # flow, used for viscous drag
            't_over_c_cp' : np.array([0.12]),      # thickness over chord ratio
            'c_max_t' : .303,       # chordwise location of maximum (NACA0015)
                                    # thickness
            'with_viscous' : True,
            'with_wave' : False,     # if true, compute wave drag

            # Material properties taken from http://www.performance-composites.com/carbonfibre/mechanicalproperties_2.asp
            'E' : 85.e9,
            'G' : 25.e9,
            'yield' : 350.e6,
            'mrho' : 1.6e3,

            'fem_origin' : 0.35,    # normalized chordwise location of the spar
            'wing_weight_ratio' : 1., # multiplicative factor on the computed structural weight
            'struct_weight_relief' : True,    # True to add the weight of the structure to the loads on the structure
            'distributed_fuel_weight' : False,
            # Constraints
            'exact_failure_constraint' : False, # if false, use KS function
            }

#-----------------------------------------------------------------------------------#
## Part-2: Initialize your problem and add flow and structural conditions ------------
# Create the problem and assign the model group
prob = om.Problem()

# Add problem information as an independent variables component
indep_var_comp = om.IndepVarComp()
indep_var_comp.add_output('v', val=22.876, units='m/s')
indep_var_comp.add_output('alpha', val=5., units='deg')
indep_var_comp.add_output('Mach_number', val=0.071)
indep_var_comp.add_output('re', val=1.e6, units='1/m')
indep_var_comp.add_output('rho', val=0.770816, units='kg/m**3')
indep_var_comp.add_output('CT', val=grav_constant * 8.6e-6, units='1/s')
indep_var_comp.add_output('R', val=1800e3, units='m')
indep_var_comp.add_output('W0', val=10.,  units='kg')
indep_var_comp.add_output('speed_of_sound', val=322.2, units='m/s')
indep_var_comp.add_output('load_factor', val=1.)
indep_var_comp.add_output('empty_cg', val=np.array([0.2, 0., 0.]), units='m')

prob.model.add_subsystem('prob_vars',
     indep_var_comp,
     promotes=['*'])

# Add the AerostructGeometry group, which computes all the intermediary
# parameters for the aero and structural analyses, like the structural
# stiffness matrix and some aerodynamic geometry arrays
aerostruct_group = AerostructGeometry(surface=surface)
name = 'wing'

# Add the group to the problem
prob.model.add_subsystem(name, aerostruct_group)

point_name = 'AS_point_0'

# Create the aerostruct point group and add it to the model.
# This contains all the actual aerostructural analyses.
AS_point = AerostructPoint(surfaces=[surface])

prob.model.add_subsystem(point_name, AS_point,
    promotes_inputs=['v', 'alpha', 'Mach_number', 're', 'rho', 'CT', 'R',
        'W0', 'speed_of_sound', 'empty_cg', 'load_factor'])

# Issue quite a few connections within the model to make sure all of the
# parameters are connected correctly.
com_name = point_name + '.' + name + '_perf'
prob.model.connect(name + '.local_stiff_transformed', point_name + '.coupled.' + name + '.local_stiff_transformed')
prob.model.connect(name + '.nodes', point_name + '.coupled.' + name + '.nodes')

# Connect aerodynamic mesh to coupled group mesh
prob.model.connect(name + '.mesh', point_name + '.coupled.' + name + '.mesh')

# Connect performance calculation variables
prob.model.connect(name + '.radius', com_name + '.radius')
prob.model.connect(name + '.thickness', com_name + '.thickness')
prob.model.connect(name + '.nodes', com_name + '.nodes')
prob.model.connect(name + '.cg_location', point_name + '.' + 'total_perf.' + name + '_cg_location')
prob.model.connect(name + '.structural_mass', point_name + '.' + 'total_perf.' + name + '_structural_mass')
prob.model.connect(name + '.t_over_c', com_name + '.t_over_c')


# User defined functions -------------------------------------------------------------#

### Weighted objective function-1 with fuel_burn and structural mass
#indep_var_beta = om.IndepVarComp()
#indep_var_beta.add_output('beta', val=0.5)
#prob.model.add_subsystem('prob_beta', indep_var_beta, promotes=['*'])
#comp = om.ExecComp('f = beta*(FB/5.37070721) + (1-beta)*(Ws/1.83849747)')

#prob.model.add_subsystem('Obj', comp, promotes_outputs=['f'])
#prob.model.connect('AS_point_0.fuelburn', 'Obj.FB')
#prob.model.connect('wing.structural_mass', 'Obj.Ws')
#prob.model.connect('beta', 'Obj.beta')

### Weighted objective function-2 with drag coefficient and structural mass 
indep_var_beta = om.IndepVarComp()
indep_var_beta.add_output('beta', val=0.5)
prob.model.add_subsystem('prob_beta', indep_var_beta, promotes=['*'])
comp = om.ExecComp('f = beta*(Cd/0.04294) + (1-beta)*(Ws/0.06638) ')

prob.model.add_subsystem('Obj', comp, promotes_outputs=['f'])
prob.model.connect('AS_point_0.CD', 'Obj.Cd')
prob.model.connect('wing.structural_mass', 'Obj.Ws')
prob.model.connect('beta', 'Obj.beta')


#-----------------------------------------------------------------------------------#
## Part-3: Setup optimizer, Add your design variables, constraints, and objective
# Set the optimizer type
prob.driver = om.ScipyOptimizeDriver()
prob.driver.options['tol'] = 1e-7

# Record data from this problem so we can visualize it using plot_wing
recorder = om.SqliteRecorder("aerostruct.db")
prob.driver.add_recorder(recorder)
prob.driver.recording_options['record_derivatives'] = True
prob.driver.recording_options['includes'] = ['*']

# Setup problem and add design variables.
# Here we're varying twist, thickness, sweep,taper and alpha.
prob.model.add_design_var('wing.twist_cp', lower=-5., upper=10.)
prob.model.add_design_var('wing.thickness_cp', lower=0.00005, upper=0.01, scaler=1e3)
prob.model.add_design_var('wing.sweep', lower=10., upper=30.)
prob.model.add_design_var('wing.taper', lower=0.25, upper=1.2)
prob.model.add_design_var('alpha', lower=-10., upper= 15.)


# Make sure the spar doesn't fail, we meet the lift needs, and the aircraft
# is trimmed through CM=0.
prob.model.add_constraint('AS_point_0.wing_perf.failure', upper=0.)
prob.model.add_constraint('AS_point_0.wing_perf.thickness_intersects', upper=0.)
prob.model.add_constraint('AS_point_0.L_equals_W', equals=0.)

# Instead of using an equality constraint here, we have to give it a little
# wiggle room to make SLSQP work correctly.
prob.model.add_constraint('AS_point_0.CM', lower=-0.001, upper=0.001)
prob.model.add_constraint('wing.twist_cp', lower=np.array([-1e20, -1e20, 5.]), upper=np.array([1e20, 1e20, 5.]))

# We're trying to minimize fuel burn
# prob.model.add_objective('AS_point_0.fuelburn', scaler=.1)
prob.model.add_objective('f', scaler=.1)

# Set up the problem
prob.setup()

#-----------------------------------------------------------------------------------#
## Part-4: Initial point evaluation
# Use this if you just want to run analysis and not optimization
prob.run_model()
print('\n Initial point ------------')
print('wing.twist_cp',prob['wing.twist_cp'])
print('wing.thickness_cp',prob['wing.thickness_cp'])
print('alpha',prob['alpha'])
print('wing.sweep',prob['wing.sweep'])
print('wing.taper',prob['wing.taper'])
print('AS_point_0.fuelburn',prob['AS_point_0.fuelburn'])
print('wing.structural_mass',prob['wing.structural_mass'])
print('AS_point_0.CD',prob['AS_point_0.CD'])

#-----------------------------------------------------------------------------------#
## Part-5: Set up and run the optimization problem 

prob.set_val('prob_beta.beta',  0.5)   # specify beta for obj fun

prob.run_driver()
print('\n after optimization ------------')
print('prob_beta.beta',prob['prob_beta.beta'])
print('wing.twist_cp',prob['wing.twist_cp'])
print('wing.thickness_cp',prob['wing.thickness_cp'])
print('alpha',prob['alpha'])
print('wing.sweep',prob['wing.sweep'])
print('wing.taper',prob['wing.taper'])
print('\n')
print('AS_point_0.fuelburn',prob['AS_point_0.fuelburn'][0])
print('wing.structural_mass',prob['wing.structural_mass'][0])
print('AS_point_0.CD',prob['AS_point_0.CD'])
print('obj.f',prob['f'])
print('\n')
print('const 1: AS_point_0.wing_perf.failure',prob['AS_point_0.wing_perf.failure'])
print('const 2: AS_point_0.wing_perf.thickness_intersects',prob['AS_point_0.wing_perf.thickness_intersects'])
print('const 3: AS_point_0.L_equals_W',prob['AS_point_0.L_equals_W'])
print('const 4: AS_point_0.CM',prob['AS_point_0.CM'])
print('const 5: wing.twist_cp',prob['wing.twist_cp'])



#-----------------------------------------------------------------------------------#
## Part-6: Generate N2 diagram
# from openmdao.api import n2; n2(prob)

# ## Part-7: visualization 
# from openaerostruct.utils.plot_wing import disp_plot
# args = [[], []]
# args[1] = 'aerostruct.db'
# disp_plot(args=args)


''' Results
beta = [0, 0.25, 0.5, 0.75, 1]
twist=[
       [-5.         -0.61558197  5.    ],
       [4.13349426  3.98879794   5.    ],
       [3.10714353 3.23035414 5.        ],
       [5.58592336 6.42509716 5.        ],
       [ 3.66982238 10.          5.        ]      
  ]
thickness_cp = [
                [5.00000000e-05 5.00000000e-05 3.08271542e-04],
                [5.00000000e-05 5.00000000e-05 3.39248721e-04],
                [5.0000000e-05 5.0000000e-05 4.0662988e-04],
                [5.00000000e-05 5.00000000e-05 4.26502995e-04],
                [1.99382869e-04 7.38663984e-05 7.67964612e-04]
                ]

alpha = [12.077, 8.377 , 6.7533, 5.0378, 2.1493]
sweep = [25.169, 22.427, 18.657, 17.812, 17.3448]
taper=  [0.25  , 0.317 , 1.2   , 1.2   , 1.2]

Ws = [0.0563, 0.0596, 0.0676, 0.070, 0.1378]
Cd = [0.0609, 0.05218, 0.0417, 0.0408, 0.0403]
obj_f = [0.849 ,0.977, 0.995, 0.977, 0.9393]
'''

## Part-8: Plotting 
beta = [0, 0.25, 0.5, 0.75, 1]
Ws = [0.0563, 0.0596, 0.0676, 0.070, 0.1378]
Cd = [0.0609, 0.05218, 0.0417, 0.0408, 0.0403]

import matplotlib.pyplot as plt
from adjustText import adjust_text

# ## Part-9: Plotting
csfont = {'fontname':'times new roman','fontsize':20}
fig1 = plt.figure(figsize=(7,6),dpi=150)
plt.plot(Cd,Ws,'--o', color='r', ms=8 )

plt.xlabel('$C_D$',**csfont)
plt.ylabel('$W_s$',**csfont)
plt.xticks(fontsize=16 )
plt.yticks(fontsize=16 )
# plt.legend(fontsize=16)

texts = [plt.text(Cd[i],Ws[i],r'$\beta$=%s'%(beta[i]), fontsize=14) for i in range(len(beta))]
adjust_text(texts)
    
fig1.tight_layout()
fig1.savefig('ScanE_tradespace.png', dpi=400)
plt.show()

















