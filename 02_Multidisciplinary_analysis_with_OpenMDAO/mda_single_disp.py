
"""
Demonstration of a model using the Paraboloid component.
Link: http://openmdao.org/twodocs/versions/latest/basic_guide/first_analysis.html
"""

# Part 0: OpenMDAO and component imports
import openmdao.api as om

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


if __name__ == "__main__":    
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