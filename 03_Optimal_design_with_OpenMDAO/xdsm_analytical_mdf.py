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
x.add_system("solver", SOLVER, [r"\text{MDA}"])
x.add_system("D1", FUNC, ["Discipline1","y_{21}=x_1+x_2"])
x.add_system("D2", FUNC, ["Discipline2","y_{12}=x_1/2+x_2"])
x.add_system("OBJ", FUNC, ["Objective","f=x_1^2+x_2^2+x_3^2"])
x.add_system("G1", FUNC, ["Constraint1","g_1=y_{12}^t/2+3x_1/4+1"])
x.add_system("G2", FUNC, ["Constraint2","g_2=-y_{21}^t-x_1+x_3"])

x.add_input("opt", "x_1^{(0)},x_2^{(0)},x_3^{(0)}")

x.connect("opt", "D1", "x_1,x_2")
x.connect("opt", "D2", "x_1,x_2")
x.connect("opt", "OBJ", "x_1,x_2,x_3")
x.connect("opt", "G1", "x_1")
x.connect("opt", "G2", "x_1,x_3")
x.connect("solver", "G1", "y_{12}^t")
x.connect("solver", "G2", "y_{21}^t")

x.connect("D1", "solver", "y_{21}")
x.connect("D2", "solver", "y_{12}")
x.connect("OBJ", "opt", "f")
x.connect("G1", "opt", "g_1")
x.connect("G2", "opt", "g_2")

x.add_output("opt", "x_1^*,x_2^*,x_3^*", side="left")
x.add_output("D1", "y_{21}^*", side="left")
x.add_output("D2", "y_{12}^*", side="left")
x.add_output("OBJ", "f^*", side="left")
x.add_output("G1", "g_1^*", side="left")
x.add_output("G2", "g_2^*", side="left")


x.write("xdsm_analytical_mdf")