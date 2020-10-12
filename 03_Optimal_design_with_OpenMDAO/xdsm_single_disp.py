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
x.add_system("D1", FUNC, ["Discipline1","f(x,y)=(x-3)^2+xy+(y+4)^2-3"])

x.add_input("opt", "x^{(0)},y^{(0)}")

x.connect("opt", "D1", "x,y")

x.connect("D1", "opt", "f")

x.add_output("opt", "x^*,y^*", side="left")
x.add_output("D1", "f^*", side="left")

x.write("xdsm_single_disp")