# Copyright © 2021 United States Government as represented by the Administrator of the National Aeronautics and Space Administration.  All Rights Reserved.
# This ensures that the directory containing examples is in the python search directories 

"""
This example demonstrates the Polynomial Choas Expansion (PCE) Surrogate Direct Model functionality. PCE is a method by which the behavior of a model can be approximated by a polynomial. In this case the relationship between future loading and time of event. The result is a direct surrogate model that can be used to estimate time of event given a loading profile, without requiring the original model to be simulated. The resulting estimation is MUCH faster than simulating the model.

In this example, a PCE surrogate model is generated for the BatteryElectroChemEOD model. The surrogate is used to estimate time of event for a number of loading profiles. The result is compared to the actual time of event for the same loading profiles, which were generated by simulating the model.
"""

import chaospy as cp
import matplotlib.pyplot as plt
import numpy as np
from prog_models.models import BatteryElectroChemEOD
from prog_models.data_models import PCE
import scipy as sp

def run_example():
    # First lets define some constants

    # Time step used in simulation
    DT = 0.5 

    # The number of samples to used in the PCE
    # Larger gives a better approximation, but takes longer to generate
    N_SAMPLES = 100  

    # The distribution of the input current
    # This defines the expected values for the input
    # In this case we're saying that the input current can be anything between 3-8 amps
    # With a uniform distribution (i.e., no value in that range is more likely than any other)
    INPUT_CURRENT_DIST = cp.Uniform(3, 8)
    # Note: These discharge rates are VERY high. This is only for demonstration purposes.
    #    The high discharge rate will accelerate the degradation of the battery, 
    #    which will cause the example to run faster

    # Step 1: Define base model
    # First let's define the base model that we're creating a surrogate for.
    m = BatteryElectroChemEOD(process_noise = 0) 
    x0 = m.initialize()  # Initial State
    
    # Step 2: Build surrogate
    # Next we build the surrogate model from the base model
    # To build the model we pass in the distributions of possible values for each input.
    # We also provide the max_time. This is the maximum time that the surrogate will be used for.
    # We dont expect any battery to last more than 4000 seconds given the high discharge curves we're passing in.
    m_surrogate = PCE.from_model(m, x0, {'i': INPUT_CURRENT_DIST}, dt=DT, max_time = 4000, discretization = 5, N=N_SAMPLES)
    # The result (m_surrogate) is a model that can be used to VERY quickly estimate time_of_event for a new loading profile.
 
    # Note: this is only valid for the initial state (x0) of the battery.
    #      To train for another state pass in the parameter x (type StateContainer).
    #      e.g. m_surrogate = PCE.from_model(m, SOME_OTHER_STATE, ...)

    # -------------------------------------------------------------------------
    # Now let's test the surrogate
    # We will do this by generating some new loading profiles
    # then comparing the results to the actual time of event (from simulation)
    N_TEST_CASES = 25  # The number of loading profiles to test

    # some containers for the results
    surrogate_results = np.empty(N_TEST_CASES, dtype=np.float64)
    gt_results = np.empty(N_TEST_CASES, dtype=np.float64)

    # Future loading- interpolates values from randomly sampled values
    def future_loading(t, x=None):
        return m.InputContainer(interpolator(t)[np.newaxis].T)

    TEST_SAMPLES = m_surrogate.parameters['J'].sample(size=N_TEST_CASES, rule='latin_hypercube')
    for i in range(N_TEST_CASES):
        # Generate a new loading profile
        interpolator = sp.interpolate.interp1d(m_surrogate.parameters['times'], TEST_SAMPLES[:, i])
        
        # Estimate time of event from ground truth (original model) and surrogate
        gt_results[i] = m.time_of_event(x0, future_loading, dt = DT)['EOD']
        surrogate_results[i] = m_surrogate.time_of_event(x0, future_loading)['EOD']

    # Plot results
    # Note here that the approximation is very good, but not perfect
    # Approximation would be even better with more samples
    plt.scatter(gt_results, surrogate_results)
    max_val = max(max(gt_results), max(surrogate_results))
    plt.plot([0, max_val], [0, max_val], 'k--')
    plt.xlabel("Ground Truth (s)")
    plt.ylabel("PCE (s)")
    plt.show()

# This allows the module to be executed directly 
if __name__ == '__main__':
    run_example()
