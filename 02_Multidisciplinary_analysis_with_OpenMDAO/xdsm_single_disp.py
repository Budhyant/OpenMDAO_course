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


x.add_system("D1", FUNC, ["Discipline1","f(x,y)=(x-3)^2+xy+(y+4)^2-3"])

x.add_input("D1", "x,y")

x.add_output("D1", "f", side="right")

x.write("xdsm_single_disp")