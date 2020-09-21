
from pyxdsm.XDSM import XDSM

# Part-1 : Generate XDSM class object 
x = XDSM()

# Part-2 :  Define shape styles used in XDSM
DataIO ='DataIO'
comp2  = 'ImplicitFunction'
group  = 'Metamodel'
func   = 'Function'
OPT = "Optimization"

#  Part-3 : create system 
x.add_system('opt', OPT, r'\text{Optimizer}')
x.add_system('D1', func,( r'Discipline1',r'y_1 = y_2^2' ))
x.add_system('D2', comp2, (r'Discipline2',r'exp(-y_1y_2)-xy_2 = 0 ' ))
x.add_system('F', func, ( r'\text{Model Output}', r'f= y_1^2 - y_2 +3'))

#  Part-4 : Connect systems with variables 
x.connect('opt', 'D2', 'x')
x.connect('D1', 'D2', r'y_1')
x.connect('D1', 'F', r'y_1')
x.connect('D2', 'F', r'y_2')
x.connect('D2', 'D1', r'y_2')
x.connect('F', 'opt', r'f')

x.add_output('opt', 'x^*', side='left')

#  Part-5 : write Sellar.tex, Sellar.tikz, Sellar.pdf files 
x.write('Sellar')
