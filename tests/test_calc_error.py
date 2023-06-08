# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

import numpy as np
import unittest

from prog_models import *
from prog_models.models import *

class TestCalcError(unittest.TestCase):
    """
    Main Testing class for calc_error.

    Validating that values are correctly being passed into the new calc_error calls and that we are receiving expected results!
    """
    def test_calc_error(self):
        # Note: decreasing dt or increasing the time to simulate to will increase computation time
        m = BatteryElectroChemEOD()

        options = {
            'save_freq': 200, # Frequency at which results are saved
            'dt': 1, # Time step
        }

        def future_loading(t, x=None):
            if (t < 600):
                i = 2
            elif (t < 900):
                i = 1
            elif (t < 1800):
                i = 4
            elif (t < 3000):
                i = 2
            else:
                i = 3
            return m.InputContainer({'i': i})
    
        simulated_results = m.simulate_to(2000, future_loading, **options)

        # Initializing parameters to very erroneous values       
        m.parameters['qMax'] = 4000

        # With our current set parameters, our model goes unstable immediately
        with self.assertRaises(ValueError) as cm:
            m.calc_error(simulated_results.times, simulated_results.inputs, simulated_results.outputs, dt=1)
        self.assertEqual(
            "Model unstable- NAN reached in simulation (t=0.0) before cutoff threshold. Cutoff threshold is 1900.0, or roughly 95.0% of the data",
            str(cm.exception)
        ) 

        # Creating duplicate model to check if consistent results occur
        m1 = BatteryElectroChemEOD()

        # Much bigger parameter initialization
        m.parameters['kp'] = m1.parameters['kp'] = 10000
        m.parameters['kn'] = m1.parameters['kn'] = 1000 
        m.parameters['qpMax'] = m1.parameters['qpMax'] = 4500
        m.parameters['qMax'] = m1.parameters['qMax'] = 9000

        simulated_results = m.simulate_to(2000, future_loading, **options)
        m1_sim_results = m1.simulate_to(2000, future_loading, **options)
        
        # Checks to see if model goes unstable before default stability tolerance is met.
        with self.assertRaises(ValueError) as cm:
            m.calc_error(simulated_results.times, simulated_results.inputs, simulated_results.outputs, dt = 1)
        self.assertEqual(
            "Model unstable- NAN reached in simulation (t=1800.0) before cutoff threshold. Cutoff threshold is 1900.0, or roughly 95.0% of the data",
            str(cm.exception)
        )
        
        # Checks to see if m1 throws the same exception. 
        with self.assertRaises(ValueError):
            m1.calc_error(m1_sim_results.times, m1_sim_results.inputs, m1_sim_results.outputs, dt = 1)
        self.assertEqual(
            "Model unstable- NAN reached in simulation (t=1800.0) before cutoff threshold. Cutoff threshold is 1900.0, or roughly 95.0% of the data",
            str(cm.exception)
        )

        # Checks to see if stability_tolerance throws Warning rather than an Error when the model goes unstable after threshold
        with self.assertWarns(UserWarning) as cm:
            m.calc_error(simulated_results.times, simulated_results.inputs, simulated_results.outputs, 
                     dt = 1, stability_tol=0.7)
        self.assertEqual(
            'Model unstable- NaN reached in simulation (t=1800.0)',
            str(cm.warning)
        )

    def test_MSE(self):
        """
        Base tests that ensure first-level workability within calc_error
        """
        m = ThrownObject()
        m2 = ThrownObject()
        results = m.simulate_to_threshold(save_freq=0.5)
        gt = m.parameters.copy()

        # Arbitrary Test to ensure that both models are behaving the same way
        self.assertEqual(m.calc_error(results.times, results.inputs, results.outputs),
                            m2.calc_error(results.times, results.inputs, results.outputs))
        
        resultsm2 = m2.simulate_to_threshold(save_freq = 0.5)
        m2.parameters['throwing_speed'] = 35
        key = ['throwing_speed']

        previous = m2.calc_error(resultsm2.times, resultsm2.inputs, resultsm2.outputs)

        self.assertNotEqual(m.calc_error(results.times, results.inputs, results.outputs),
                            previous)
        
        m2.estimate_params(times = resultsm2.times, inputs = resultsm2.inputs, outputs = resultsm2.outputs, keys = key, dt = 1)

        for i in key:
            # We can compare with gt because m and m2 originally were the same, and gt was a copy of m.
            self.assertAlmostEqual(m2.parameters[i], gt[i], 2)

        self.assertNotEqual(m.calc_error(results.times, results.inputs, results.outputs),
                    previous)
        
        self.assertLess(m2.calc_error(resultsm2.times, resultsm2.inputs, resultsm2.outputs), previous)

        # By changing the 
        for i in np.arange(0.1, 1, 0.1):
            m.calc_error(results.times, results.inputs, results.outputs, dt=i)

        for i in range(2, 10):
            m.calc_error(results.times, results.inputs, results.outputs, dt=i)

        # Unique Tests for calc_error
        m.parameters['throwing_speed'] = 41
        
        with self.assertRaises(ValueError) as cm:
            m.calc_error(results.times, results.inputs, results.outputs, dt = 0)
        self.assertEqual(
            'Keyword argument \'dt\' must a initialized to a value greater than 0. Currently passed in 0.',
            str(cm.exception)
        )

        with self.assertRaises(TypeError) as cm:
            m.calc_error(results.times, results.inputs, results.outputs, dt = {1})
        self.assertEqual(
            'Keyword argument \'dt\' must be either a int, float, or double.',
            str(cm.exception)
        )

        with self.assertRaises(TypeError) as cm:
            m.calc_error(results.times, results.inputs, results.outputs, x0 = 1)
        self.assertEqual(
            "Keyword argument 'x0' must be initialized to a Dict or StateContainer, not a int.",
            str(cm.exception)
        )

        with self.assertWarns(UserWarning) as cm:
            m.calc_error(results.times, results.inputs, results.outputs, 
                     dt = 1, stability_tol=10)
        self.assertEqual(
            'Configurable cutoff must be some float value in the domain (0, 1]. Received 10. Resetting value to 0.95.',
            str(cm.warning)
        )

        with self.assertRaises(TypeError) as cm:
            m.calc_error(results.times, results.inputs, results.outputs, stability_tol = {1})
        self.assertEqual(
            "Keyword argument 'stability_tol' must be either a int, float, or double.",
            str(cm.exception)
        )

    def test_multiple(self):
        m = ThrownObject()

        # The value of time1, time2, inputs, and outputs are arbitrary values
        times = [[0, 1, 2, 3, 4, 5, 6, 7, 8], [0, 1, 2, 3]]
        inputs = [[{}]*9, [{}]*4]
        outputs = [[{'x': 1.83},
            {'x': 36.95},
            {'x': 62.36},
            {'x': 77.81},
            {'x': 83.45},
            {'x': 79.28},
            {'x': 65.3},
            {'x': 41.51},
            {'x': 7.91},],
            [
                {'x': 1.83},
                {'x': 36.95},
                {'x': 62.36},
                {'x': 77.81},
            ]]
        
        m.calc_error(times, inputs, outputs)

        # Will be testing length errors, will also be providing a 'runs' feedback whenever there are multiple give?
        incorrectTimes = [[0, 1, 2, 3, 4, 5, 6, 7, 8]]

        with self.assertRaises(ValueError) as cm:
            m.calc_error(incorrectTimes, inputs, outputs)
        self.assertEqual(
            "Times, inputs, and outputs must all be the same length. Current lengths: times = 1, inputs = 2, outputs = 2.",
            str(cm.exception)
        )

        incorrectTimes = [[0, 1, 2, 4, 5, 6, 7, 8], [0, 1, 2, 3]]

        # Testing when one of the _runs has a data point of different length
        with self.assertRaises(ValueError) as cm:
            m.calc_error(incorrectTimes, inputs, outputs)
        self.assertEqual(
            "Times, inputs, and outputs must all be the same length. Current lengths at data location (0): times = 8, inputs = 9, outputs = 9.",
            str(cm.exception)
        )

        incorrectTimes = [[0, 1, 2, 4, 5, 6, 7, 8, 9], [0, 1, 2]]

        with self.assertRaises(ValueError) as cm:
            m.calc_error(incorrectTimes, inputs, outputs)
        self.assertEqual(
            "Times, inputs, and outputs must all be the same length. Current lengths at data location (1): times = 3, inputs = 4, outputs = 4.",
            str(cm.exception)
        )

        # More complicated example
        times = [[[1, 2], [1, 2]], [[1, 2], [1, 2]]]
        inputs = [[ [{},{}] for _ in range(2)], [[{}, {}] for _ in range(2)]]
        outputs = [[[{'x': 36.95}, {'x': 62.36}], [{'x': 36.95}, {'x': 62.36}]], 
                   [[{'x': 36.95}, {'x': 62.36}], [{'x': 36.95}, {'x': 62.36}]]]
        
        m.calc_error(times, inputs, outputs)

        incorrectTimes = [[[1, 2], [1]], [[1, 2], [1, 2]]]

        with self.assertRaises(ValueError) as cm:
            m.calc_error(incorrectTimes, inputs, outputs)
        self.assertEqual(
            "Times, inputs, and outputs must all be the same length. Current lengths at data location (0, 1): times = 1, inputs = 2, outputs = 2.",
            str(cm.exception)
        )

        incorrectInputs = [[[{}, {}], [{}]], [[{}, {}], [{}, {}]]]
        incorrectOutputs = [[[{'x': 36.95}, {'x': 62.36}], [{'x': 36.95}]], 
                            [[{'x': 36.95}, {'x': 62.36}], [{'x': 36.95}, {'x': 62.36}]]]
        with self.assertRaises(ValueError) as cm:
            m.calc_error(incorrectTimes, incorrectInputs, incorrectOutputs)
        self.assertEqual(
            "Must provide at least 2 data points for times, inputs, and outputs at data location (0, 1).",
            str(cm.exception)
        )

    def test_errors(self):
        m = ThrownObject()
        results = m.simulate_to_threshold(save_freq=0.5)

        with self.assertRaises(TypeError):
            m.calc_error()

        # With Strings
        with self.assertRaises(TypeError):
            m.calc_error("1, 2, 3", "1, 2, 3", "1, 2, 3")

        # With a list in a string
        with self.assertRaises(TypeError):
            m.calc_error(['1', '2', '3'], ['1', '2', '3'], ['1', '2', '3'])
    
        # Passing in bool values
        with self.assertRaises(TypeError) as cm:
            m.calc_error([False, False, True], [False, False, True], [False, False, True])
        self.assertEqual(
            "Data must be a dictionary or numpy array, not <class 'bool'>",
            str(cm.exception)
        )

        # Passing in tuples where, where inputs and outputs do not contain dicts or StateContainers, rather contain ints
        with self.assertRaises(TypeError) as cm:
            m.calc_error((1, 2, 3), (2, 3, 4), (3, 4, 5))
        self.assertEqual(
            "Data must be a dictionary or numpy array, not <class 'int'>",
            str(cm.exception)
        )

        # Test incorrect Types and to see if error message describes each argument's types
        with self.assertRaises(TypeError) as cm:
            m.calc_error({1, 2, 3}, ({'1': 1}, {'2': 2}, {'3': 3}), ({'1': 1}, {'2': 2}, {'3': 3}))
        self.assertEqual(
            "Types passed in must be from the following: np.ndarray, list, SimResult, or LazySimResult. Current types: times = set, inputs = tuple, and outputs = tuple.",
            str(cm.exception)
        )

        # Puts wrapper around the the incorrectly typed arguments to see if correct error message with runs is invoked.
        with self.assertRaises(TypeError) as cm:
            m.calc_error([{1, 2, 3}, {1, 2, 3}], [({'1': 1}, {'2': 2}, {'3': 3}), ({'1': 1}, {'2': 2}, {'3': 3})],
                         [({'1': 1}, {'2': 2}, {'3': 3}), ({'1': 1}, {'2': 2}, {'3': 3})])
        self.assertEqual(
            "Types passed in must be from the following: np.ndarray, list, SimResult, or LazySimResult. Current types at data location (0): times = set, inputs = tuple, and outputs = tuple.",
            str(cm.exception)
        )

        # Only passing 1 data point and when the lengths of times, inputs, and outputs are the same.
        with self.assertRaises(ValueError) as cm:
            m.calc_error([1], [[{}]], [[{'1':1}]])
        self.assertEqual(
            "Must provide at least 2 data points for times, inputs, and outputs.",
            str(cm.exception)
        )

        # Additional Wrapper 
        with self.assertRaises(ValueError) as cm:
            m.calc_error([[1]], [[[{}]]], [[[{'1':1}]]])
        self.assertEqual(
            "Must provide at least 2 data points for times, inputs, and outputs.",
            str(cm.exception)
        )

        # Tests data point condition with a complicated example to check data location.
        with self.assertRaises(ValueError) as cm:
            m.calc_error([[1], [1, 2]], [[{'1': 1}], [{'1': 1}, {'2': 2}]], 
                         [[{'1': 1}], [{'1': 1}, {'2': 2}]])
        self.assertEqual(
            "Must provide at least 2 data points for times, inputs, and outputs at data location (0).",
            str(cm.exception)
        )

        times = [1, [0, 1, 2, 3]]
        inputs = [{}, [{}]*4]
        outputs = [{'x': 1.83},
            [
                {'x': 1.83},
                {'x': 36.95},
                {'x': 62.36},
                {'x': 77.81},
            ]]

        with self.assertRaises(ValueError) as cm:
            m.calc_error(times, inputs, outputs)
        self.assertEqual(
            "Some, but not all elements, are iterable for argument times.",
            str(cm.exception)
        )

        times = [[0, [1], 2, 3], [0, 1, 2, 3]]
        inputs = [[{}]*4, [{}]*4]
        outputs = [[{'x': 1.83},
                {'x': 36.95},
                {'x': 62.36},
                {'x': 77.81}],
            [
                {'x': 1.83},
                {'x': 36.95},
                {'x': 62.36},
                {'x': 77.81},
            ]]

        with self.assertRaises(ValueError) as cm:
            m.calc_error(times, inputs, outputs)
        self.assertEqual(
            "Some, but not all elements, are iterable for argument times at data location 0.",
            str(cm.exception)
        )

        with self.assertRaises(ProgModelInputException) as cm:
            m.calc_error(results.times, results.inputs, results.outputs, method = "Test")
        self.assertEqual(
            "Error method 'Test' not supported",
            str(cm.exception)
        )

        # Test other valid methods do not raise an exception
        methods = ["max_e", "rmse", "mae", "mape"]
        for method in methods:
            m.calc_error(results.times, results.inputs, results.outputs, method=method)

def run_tests():
    unittest.main()
    
def main():
    l = unittest.TestLoader()
    runner = unittest.TextTestRunner()
    print("\n\nTesting calc_error Feature\n")
    result = runner.run(l.loadTestsFromTestCase(TestCalcError)).wasSuccessful()

    if not result:
        raise Exception("Failed test")

if __name__ == '__main__':
    main()
