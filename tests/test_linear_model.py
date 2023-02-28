# Copyright © 2021 United States Government as represented by the Administrator of the National Aeronautics and Space Administration.  All Rights Reserved.

import numpy as np
import unittest
import copy
import pickle
import json
# from prog_models.models.test_models import *
from prog_models.models.test_models.linear_thrown_object import *
from prog_models.models.test_models.linear_models import *


class TestLinearModel(unittest.TestCase):
    def test_linear_model(self):
        m = LinearThrownObject()

        #Checking too see if initalization would error when passing in incorrect parameter forms
        with self.assertRaises(AttributeError):
            b = LinearThrownObject_WrongB()

        m.simulate_to_threshold(lambda t, x = None: m.InputContainer({}))
        # len() = events states inputs outputs
        #         1      2      0      1
        # Matrix overwrite type checking (Can't set attributes for B, D, G; not overwritten)
        # when matrix is not of type NumPy ndarray or standard list

        #INCLUDE TESTS FOR COPY AND DEEPCOPY
            # If they do not work, we implement the functions.
        #Serilization and Deserilization

        # @A
        with self.assertRaises(TypeError):
            m.A = "[[0, 1], [0, 0]]" # string
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.A = None # None
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.A = 0 # int
            m.matrixCheck()
        with self.assertRaises(TypeError):
            m.A = 3.14 # float
            m.matrixCheck()
        with self.assertRaises(TypeError):
            m.A = {} # dict
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.A = () # tuple
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.A = set() # set
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.A = True # boolean
            m.matrixCheck()
        # Matrix Dimension Checking
        # when matrix is not proper dimensional (1-D array = C, D, G; 2-D array = A,B,E; None = F;)
        with self.assertRaises(AttributeError):
            m.A = np.array([0, 1]) # 1-D array
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.A = np.array([[[[0, 1], [0, 0], [1, 0]]]]) # 3-D array
            m.matrixCheck()
        # When Matrix is improperly formed
        with self.assertRaises(AttributeError):
            m.A = np.array([[0, 1, 2, 3], [0, 0, 1, 2]]) # extra column values per row
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.A = np.array([[0], [0]]) # less column values per row
            m.matrixCheck()
        with self.assertRaises(AttributeError): 
            m.A = np.array([[0, 1], [0, 0], [2, 2]]) # extra row
            m.matrixCheck()
        with self.assertRaises(AttributeError): 
            m.A = np.array([[0, 1]]) # less row
            m.matrixCheck()
        # Reset Process
        m.A = np.array([[0, 1], [0, 2]])
        m.matrixCheck()

        # @B
        with self.assertRaises(TypeError):
            m.B = "[[0, 1], [0, 0]]"
            m.matrixCheck()
        with self.assertRaises(TypeError):
            m.B = 0 # int
            m.matrixCheck()
        with self.assertRaises(TypeError):
            m.B = 3.14 # float
            m.matrixCheck()
        with self.assertRaises(TypeError):
            m.B = {} # dict
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.B = () # tuple
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.B = set() # set
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.B = True # boolean
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.B = np.array(2) # 0-D array
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.B = np.array([[0, 0], [1, 1]]) # 2-D array
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.B = np.array([[1, 0, 2]]) # extra column values per row
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.B = np.array([[1]]) # less column values per row
            m.matrixCheck()
        with self.assertRaises(AttributeError): 
            m.B = np.array([[0, 0], [1, 1], [2, 2]]) # extra row
            m.matrixCheck()
        with self.assertRaises(AttributeError): 
            m.B = np.array([[]]) # less row 
            m.matrixCheck()
        m.B = None #sets parameter B to default value
        m.matrixCheck()

        # @C
        with self.assertRaises(TypeError):
            m.C = "[[0, 1], [0, 0]]" # string
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.C = 0 # int
            m.matrixCheck()
        with self.assertRaises(TypeError):
            m.C = 3.14 # float
            m.matrixCheck()
        with self.assertRaises(TypeError):
            m.C = {} # dict
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.C = () # tuple
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.C = set() # set
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.C = True # boolean
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.C = np.array(2) # 0-D array
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.C = np.array([[0, 0], [1, 1]]) # 2-D array
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.C = np.array([[1, 0, 2]]) # extra column values per row
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.C = np.array([[1]]) # less column values per row
            m.matrixCheck()
        with self.assertRaises(AttributeError): 
            m.C = np.array([[0, 0], [1, 1], [2, 2]]) # extra row
            m.matrixCheck()
        with self.assertRaises(AttributeError): 
            m.C = np.array([[]]) # less row 
            m.matrixCheck()
        m.C = np.array([[1, 0]])
        m.matrixCheck()


        with self.assertRaises(TypeError):
            m.D = "[[0, 1], [0, 0]]" # string
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.D = 0 # int
            m.matrixCheck()
        with self.assertRaises(TypeError):
            m.D = 3.14 # float
            m.matrixCheck()
        with self.assertRaises(TypeError):
            m.D = {} # dict
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.D = () # tuple
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.D = set() # set
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.D = True # boolean
            m.matrixCheck()
        # @D 1x
        with self.assertRaises(AttributeError):
            m.D = np.array(1) # 0-D array
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.D = np.array([[2], [1]]) # 2-D array with incorrect values passed in
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.D = np.array([1, 2]) # extra column values per row
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.D = np.array([[]]) # less column values per row
            m.matrixCheck()
        with self.assertRaises(AttributeError): 
            m.D = np.array([[0], [1]]) # extra row
            m.matrixCheck()
        with self.assertRaises(AttributeError): 
            m.D = np.array([[]]) # less row
            m.matrixCheck()
        m.D = np.array([[1]]) # sets to Default Value
        m.matrixCheck()

        # @E
        with self.assertRaises(TypeError):
            m.E = "[[0, 1], [0, 0]]" # string
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.E = 0 # int
            m.matrixCheck()
        with self.assertRaises(TypeError):
            m.E = 3.14 # float
            m.matrixCheck()
        with self.assertRaises(TypeError):
            m.E = {} # dict
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.E = () # tuple
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.E = set() # set
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.E = True # boolean
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.E = np.array([[0]]) # 2-D array
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.E = np.array([[0], [1], [2]]) # 3-D array
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.E = np.array([[0,0], [-9.81, -1]]) # extra column values per row
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.E = np.array([[], []]) # less column values per row
            m.matrixCheck()
        with self.assertRaises(AttributeError): 
            m.E = np.array([[0, 1], [0, 0], [2, 2]]) # extra row
            m.matrixCheck()
        with self.assertRaises(AttributeError): 
            m.E = np.array([[0, 1]]) # less row
            m.matrixCheck()
        m.E = np.array([[0], [-9.81]])
        m.matrixCheck()

        # @F
        with self.assertRaises(TypeError):
            m.F = "[[0, 1], [0, 0]]" # string
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.F = 0 # int
            m.matrixCheck()
        with self.assertRaises(TypeError):
            m.F = 3.14 # float
            m.matrixCheck()
        with self.assertRaises(TypeError):
            m.F = {} # dict
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.F = () # tuple
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.F = set() # set
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.F = True # boolean
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.F = np.array([[0]]) # 2-D array
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.F = np.array([[0], [1], [2]]) # 3-D array
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.F = np.array([[0,0], [-9.81, -1]]) # extra column values per row
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.F = np.array([[], []]) # less column values per row
            m.matrixCheck()
        with self.assertRaises(AttributeError): 
            m.F = np.array([[0, 1], [0, 0], [2, 2]]) # extra row
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            # if F is none, we need to override event_state
            m_noes = FNoneNoEventStateLM()
        #Check when these are true.
        m.F = np.array([[0, 1]]) # less row
        m.matrixCheck()
        m.F = None
        m.matrixCheck()

        #G
        with self.assertRaises(TypeError):
            m.G = "[[0, 1], [0, 0]]" # string
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.G = 0 # int
            m.matrixCheck()
        with self.assertRaises(TypeError):
            m.G = 3.14 # float
            m.matrixCheck()
        with self.assertRaises(TypeError):
            m.G = {} # dict
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.G = () # tuple
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.G = set() # set
            m.matrixCheck() 
        with self.assertRaises(TypeError):
            m.G = True # boolean
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.G = np.array([0]) # 1-D Array
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.G = np.array([[[0], [1], [2]]]) # 3-D array
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.G = np.array([[0,0], [-9.81, -1]]) # extra column values per row
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.G = np.array([[], []]) # less column values per row
            m.matrixCheck()
        with self.assertRaises(AttributeError): 
            m.G = np.array([[0, 1], [0, 0], [2, 2]]) # extra row
            m.matrixCheck()
        with self.assertRaises(AttributeError): 
            m.G = np.array([[0, 1]]) # less row
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.G = np.array([0, 1]) # extra column values per row
            m.matrixCheck()
        with self.assertRaises(AttributeError):
            m.G = np.array([[]]) # less column values per row
            m.matrixCheck()
        with self.assertRaises(AttributeError): 
            m.G = np.array([[0], [1]]) # extra row
            m.matrixCheck()
        with self.assertRaises(AttributeError): 
            m.G = np.array([[]]) # less row
            m.matrixCheck()
        #Correct Testing
        m.G = np.array([[0]]) # 1-D Array
        m.matrixCheck()
        m.G = None # sets to Default Value
        m.matrixCheck()

    def test_copy_linear(self):
        
        m1 = LinearThrownObject()
        copym1 = copy.copy(m1)  
        self.assertTrue(m1 == copym1) #Testing Copy for Linear Model

        # Is simulate to threshold even doing anything in this scenario?
        m1.simulate_to_threshold(lambda t, x = None: m1.InputContainer({}))
        self.assertTrue(m1 == copym1) #Testing Copy for Linear Model

        deepcopym1 = copy.deepcopy(m1)
        deepcopym1.simulate_to_threshold(lambda t, x = None: deepcopym1.InputContainer({}))
        self.assertTrue(m1 == deepcopym1)
 
        self.assertTrue(copym1 == deepcopym1)

        
    def test_linear_pickle(self):
        # future tests can compress, transfer to a file, and see if it still works

        m1 = LinearThrownObject()
        m2 = LinearThrownObject2()

        # Note: dumps = serializing;
        #       loads = deserializing

        bytes_m1 = pickle.dumps(m1) #serializing object 
        loaded_m1 = pickle.loads(bytes_m1) #deserializing the object
        self.assertTrue(m1 == loaded_m1) # see if serializing and deserializing changes original form

        bytes_m2 = pickle.dumps(m2)
        loaded_m2 = pickle.loads(bytes_m2)
        self.assertTrue(m2 == loaded_m2)

        m3 = LinearThrownObject()
        bytes_m3 = pickle.dumps(m3)
        loaded_m3 = pickle.loads(bytes_m3)
        self.assertTrue(m3 == loaded_m3)

        self.assertTrue(bytes_m1 == bytes_m3)
        self.assertTrue(loaded_m3 == loaded_m1)
        self.assertTrue(LinearThrownObject, type(loaded_m3))

# Future implementation includes testing json objects.
# Currently does not work since LinearThrownObject() is not serilizable and needs implmentation

    # def test_linear_json(self):
    #     m1 = LinearThrownObject()
    #     m2 = LinearThrownObject2()

    #     # Note: dumps = serializing;
    #     #       loads = deserializing

    #     bytes_m1 = json.dumps(m1) #serializing object 
    #     loaded_m1 = json.loads(bytes_m1) #deserializing the object
    #     self.assertTrue(m1 == loaded_m1) # see if serializing and deserializing changes original form

    #     bytes_m2 = json.dumps(m2)
    #     loaded_m2 = json.loads(bytes_m2)
    #     self.assertTrue(m2 == loaded_m2)

    #     m3 = LinearThrownObject()
    #     bytes_m3 = json.dumps(m3)
    #     loaded_m3 = json.loads(bytes_m3)
    #     self.assertTrue(m3 == loaded_m3)

    #     self.assertTrue(bytes_m1 == bytes_m3)
    #     self.assertTrue(loaded_m3 == loaded_m1)
    #     self.assertTrue(LinearThrownObject, type(loaded_m3))

    def test_F_property_not_none(self):
        class ThrownObject(LinearThrownObject):
            F = np.array([[1, 0]]) # Will override method

            default_parameters = {
                'thrower_height': 1.83,  # m
                'throwing_speed': 40,  # m/s
                'g': -9.81  # Acceleration due to gravity in m/s^2
            }

        m = ThrownObject()
        m.simulate_to_threshold(lambda t, x = None: m.InputContainer({}))
        m.matrixCheck()
        self.assertIsInstance(m.F, np.ndarray)
        self.assertTrue(np.array_equal(m.F, np.array([[1, 0]])))

    def test_init_matrix_as_list(self):
        # LinearThrown Object defines A, E, C as np arrays, thus we define with python lists instead. 
        
        class ThrownObject(LinearThrownObject):
            A = [[0, 1], [0, 0]]
            E = [[0], [-9.81]]
            C = [[1, 0]]

        m = ThrownObject()
        m.matrixCheck()

        # Testing to see confirm python lists and np arrays have same functionality.
        self.assertIsInstance(m.A, np.ndarray)
        self.assertTrue(np.array_equal(m.A, np.array([[0, 1], [0, 0]])))
        self.assertIsInstance(m.E, np.ndarray)
        self.assertTrue(np.array_equal(m.E, np.array([[0], [-9.81]])))
        self.assertIsInstance(m.C, np.ndarray)
        self.assertTrue(np.array_equal(m.C, np.array([[1, 0]])))

    def test_event_state_function(self):
        class ThrownObject(LinearThrownObject):
            F = None # Will override method
            
            def threshold_met(self, x):
                return {
                    'falling': x['v'] < 0,
                    'impact': x['x'] <= 0
                }
        # Needs more development; test coverage needs testing of event_state not overridden

def run_tests():
    unittest.main()
    
def main():
    l = unittest.TestLoader()
    runner = unittest.TextTestRunner()
    print("\n\nTesting Base Models")
    result = runner.run(l.loadTestsFromTestCase(TestLinearModel)).wasSuccessful()

    if not result:
        raise Exception("Failed test")

if __name__ == '__main__':
    main()
