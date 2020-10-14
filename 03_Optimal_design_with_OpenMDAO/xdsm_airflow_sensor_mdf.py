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
x.add_system("D1", IFUNC, ["Aerodynamic","F=CA_fv^2"])
x.add_system("D2", IFUNC, ["Structural","k\\theta=\\frac{1}{2}\\rho C_D"])
x.add_system("G", FUNC, ["Constraint1","g=F-F_{max}"])
x.add_system("H", FUNC, ["Constraint2","h=lw-A"])
x.add_system("OBJ", FUNC, ["Objective","f=(\\theta-{\\hat \\theta})^2"])

x.add_input("opt", "l^{(0)},w^{(0)}")

x.connect("opt", "D1", "l,w")
x.connect("opt", "D2", "l")
x.connect("opt", "H", "l,w")

x.connect("solver", "G", "F")
x.connect("solver", "OBJ", "\\theta")

x.connect("D1", "solver", "F")
x.connect("D2", "solver", "\\theta")
x.connect("OBJ", "opt", "f")
x.connect("G", "opt", "g")
x.connect("H", "opt", "h")

x.add_output("opt", "l^*,w^*", side="left")
x.add_output("D1", "F^*", side="left")
x.add_output("D2", "\\theta^*", side="left")
x.add_output("G", "g^*", side="left")
x.add_output("H", "h^*", side="left")
x.add_output("OBJ", "f^*", side="left")


x.write("xdsm_airflow_sensor_mdf")