from pyxdsm.XDSM import XDSM

x = XDSM()
# Define styles
OPT       = "Optimization"
SUBOPT    = "SubOptimization"
SOLVER    = "MDA"
DOE       = "DOE"
IFUNC     = "ImplicitFunction"
FUNC      = "Function"
GROUP     = "Group"
IGROUP    = "ImplicitGroup"
METAMODEL = "Metamodel"
DataIO    = "DataIO"
DataInter = "DataInter"


x.add_system("opt", OPT, [r"\text{Optimizer}"])
x.add_system("solver", SOLVER, [r"\text{Newton}"])
x.add_system("D1", FUNC, ["Discipline1","y_1=z_1^2+z_2+x_1-0.2y_2"])
x.add_system("D2", FUNC, ["Discipline2","y_2=sqrt(y_1)+z_1+z_2"])
x.add_system("OBJ", FUNC, ["Objective","f=x^2+z_2+y_1+exp(-y_2)"])
x.add_system("G1", FUNC, ["Constraint1","g_1=3.16-y_1"])
x.add_system("G2", FUNC, ["Constraint2","g_2=y_2-24"])

#x.add_input("D1", "x,z_1,z_2")
#x.add_input("D2", "z_1,z_2")
#x.add_input("OBJ", "x,z_2")

x.connect("opt", "D1", "x,z_1,z_2")
x.connect("opt", "D2", "z_1,z_2")
x.connect("opt", "OBJ", "x,z_2")
x.connect("solver", "D1", "y_1")
x.connect("solver", "D2", "y_2")
x.connect("solver", "OBJ", "y_1,y_2")
x.connect("solver", "G1", "y_1")
x.connect("solver", "G2", "y_2")
#x.connect("D1", "D2", "y_1")
#x.connect("D1", "OBJ", "y_1")
#x.connect("D1", "G1", "y_1")
#x.connect("D2", "OBJ", "y_2")
#x.connect("D2", "G2", "y_2")

x.connect("D1", "solver", "y_1")
x.connect("D2", "solver", "y_2")
#x.connect("D2", "D1", "y_2")
x.connect("OBJ", "opt", "f")
x.connect("G1", "opt", "g_1")
x.connect("G2", "opt", "g_2")

x.add_output("opt", "x^*,z_1^*,z_2^*", side="right")
x.add_output("D1", "y_1^*", side="right")
x.add_output("D2", "y_2^*", side="right")
x.add_output("OBJ", "f^*", side="right")
x.add_output("G1", "g_1^*", side="right")
x.add_output("G2", "g_2^*", side="right")


x.write("xdsm_sellar")