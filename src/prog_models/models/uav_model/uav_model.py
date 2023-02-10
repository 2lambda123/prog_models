# Copyright © 2021 United States Government as represented by the Administrator of the
# National Aeronautics and Space Administration.  All Rights Reserved.

import numpy as np
import datetime
from warnings import warn
from typing import Callable

from prog_models.prognostics_model import PrognosticsModel
from .vehicles import AircraftModels
from prog_models.aux_fcns.traj_gen_utils import geometry as geom
from prog_models.exceptions import ProgModelInputException

class UAVGen(PrognosticsModel):
    """
    Vectorized prognostics :term:`model` to generate a predicted trajectory for a UAV using a n=6 degrees-of-freedom dynamic model
    with feedback control loop. The model follows the form:
    
    u     = h(x, x_{ref})
    dx/dt = f(x, \theta, u)
    
    where:
      x is a 2n state vector containing position, attitude and corresponding derivatives
      \theta is a vector of model parameters including UAV mass, inertia moment, aerodynamic coefficients, etc
      u is the input vector: thrust along the body vertical axis, and three moments along the UAV body axis to follow the desired trajectory.
      x_{ref} is the desired state vector at that specific time step, with dimension 2n
      f(.) is growth rate function of all vechile state
      h(.) is the feedback-loop control function that returns the necessary thrust and moments (u vector) to cover the error between desired state x_{ref} and current state x
      dx/dt is the state-increment per unit time.

    
    Model generates cartesian positions and velocities, pitch, roll, and yaw, and angular velocities throughout time to satisfy some user-define waypoints. 

    See [0]_ for modeling details. 

    :term:`Events<event>`: (1)
        TrajectoryComplete: All waypoints are completed 
    
    :term:`Inputs/Loading<input>`: (0)
        | User-defined inputs: waypoints plus ETAs or speeds
        | Model-defined inputs: 
            | T: thrust
            | mx: moment in x 
            | my: moment in y
            | mz: moment in z

    :term:`States<state>`: (13)
        | x: first position in cartesian reference frame East-North-Up (ENU), i.e., East in fixed inertia frame, center is at first waypoint
        | y: second position in cartesian reference frame East-North-Up (ENU), i.e., North in fixed inertia frame, center is at first waypoint
        | z: third position in cartesian reference frame East-North-Up (ENU), i.e., Up in fixed inertia frame, center is at first waypoint
        | phi: Euler's first attitude angle
        | theta: Euler's second attitude angle
        | psi: Euler's third attitude angle
        | vx: velocity along x-axis, i.e., velocity along East in fixed inertia frame
        | vy: velocity along y-axis, i.e., velocity along North in fixed inertia frame
        | vz: velocity along z-axis, i.e., velocity Up in fixed inertia frame
        | p: angular velocity around UAV body x-axis
        | q: angular velocity around UAV body y-axis 
        | r: angular velocity around UAV body z-axis 
        | t: time 

    :term:`Outputs<output>`: (12)
        | x: first position in cartesian reference frame East-North-Up (ENU), i.e., East in fixed inertia frame, center is at first waypoint
        | y: second position in cartesian reference frame East-North-Up (ENU), i.e., North in fixed inertia frame, center is at first waypoint 
        | z: third position in cartesian reference frame East-North-Up (ENU), i.e., Up in fixed inertia frame, center is at first waypoint
        | phi: Euler's first attitude angle
        | theta: Euler's second attitude angle
        | psi: Euler's third attitude angle
        | vx: velocity along x-axis, i.e., velocity along East in fixed inertia frame
        | vy: velocity along y-axis, i.e., velocity along North in fixed inertia frame
        | vz: velocity along z-axis, i.e., velocity Up in fixed inertia frame
        | p: angular velocity around UAV body x-axis
        | q: angular velocity around UAV body y-axis 
        | r: angular velocity around UAV body z-axis 

    Keyword Args
    ------------
        process_noise : Optional, float or dict[str, float]
          :term:`Process noise<process noise>` (applied at dx/next_state). 
          Can be number (e.g., .2) applied to every state, a dictionary of values for each 
          state (e.g., {'x1': 0.2, 'x2': 0.3}), or a function (x) -> x
        process_noise_dist : Optional, str
          distribution for :term:`process noise` (e.g., normal, uniform, triangular)
        measurement_noise : Optional, float or dict[str, float]
          :term:`Measurement noise<measurement noise>` (applied in output eqn).
          Can be number (e.g., .2) applied to every output, a dictionary of values for each
          output (e.g., {'z1': 0.2, 'z2': 0.3}), or a function (z) -> z
        measurement_noise_dist : Optional, str
          distribution for :term:`measurement noise` (e.g., normal, uniform, triangular)
        flight_file : Optional, str
          Text file to specify waypoint information. Necessary columns must be in the following
          order with units specified: latitude (labeled 'lat_deg' or 'lat_rad'), longitude 
          (labeled 'lon_deg' or 'lon_rad'), and altitude (labeled 'alt_ft' or 'alt_m'). An 
          additional column for ETAs may be included (labeled 'time_unix). Note that while
          'flight_file' is optional, either 'flight_file' or 'flight_plan' must be specified.
        flight_plan : Optional, dict[str, numpy array]
          Dictionary to specify waypoint information. Necessary keys must include the following
          with units specified: latitude ('lat_deg' or 'lat_rad'), longitude 
          (labeled 'lon_deg' or 'lon_rad'), and altitude (labeled 'alt_ft' or 'alt_m'). An 
          additional key for ETAs may be included (labeled 'time_unix). Each key must correspond
          to a numpy array of values. Note that while 'flight_plan' is optional, either 
          'flight_file' or 'flight_plan' must be specified.
        flight_name : Optional, str
          Optional string to identify flight plan.
        aircraft_name : Optional, str
          Optional string to identify aircraft. 
        dt : Optional, float
          Time step in seconds for trajectory generation
        gravity : Optional, float
          m/s^2, gravity magnitude
        cruise_speed : float
          m/s, avg speed in-between way-points
        ascent_speed : float
          m/s, vertical speed (up)
        descent_speed : float
          m/s, vertical speed (down)
        landing_speed : float
          m/s, landing speed when altitude < 10m
        hovering_time : Optional, float
          s, time to hover between waypoints
        takeoff_time : Optional, float
          s, additional takeoff time 
        landing_time: Optional, float
          s, additional landing time 
        waypoint_weights: Optional, float
          weights of the waypoints in nurbs calculation 
        adjust_eta: Optional, dict 
          Dictionary with keys ['hours', 'seconds'], to adjust route time
        nurbs_basis_length: Optional, float
          Length of the basis function in the nurbs algorithm
        nurbs_order: Optional, int
          Order of the nurbs curve
        final_time_buffer_sec: Optional, float
          s, defines an acceptable time range to reach the final waypoint
        final_space_buffer_m: Optional, float
          m, defines an acceptable distance range to reach final waypoint 
        vehicle_model: Optional, str
          String to specify vehicle type. 'tarot18' and 'djis1000' are supported
        vehicle_payload: Optional, float
          kg, payload mass

    References 
    ----------
        References 
    -------------
     .. [0] M. Corbetta et al., "Real-time UAV trajectory prediction for safely monitoring in low-altitude airspace," AIAA Aviation 2019 Forum,  2019. https://arc.aiaa.org/doi/pdf/10.2514/6.2019-3514
    """
    events = [] # ['TrajectoryComplete']
    inputs = ['T','mx','my','mz']
    states = ['x', 'y', 'z', 'phi', 'theta', 'psi', 'vx', 'vy', 'vz', 'p', 'q', 'r','t']
    outputs = ['x', 'y', 'z', 'phi', 'theta', 'psi', 'vx', 'vy', 'vz', 'p', 'q', 'r']
    is_vectorized = True

    default_parameters = {  # Set to defaults
        # Flight information
        # 'flight_file': None, 
        # 'flight_name': 'flight-1', 
        'aircraft_name': 'aircraft-1', 
        'flight_plan': None,

        # Simulation parameters:
        'dt': 0.1, 
        'gravity': 9.81,
        'cruise_speed': None, 
        'ascent_speed': None, 
        'descent_speed': None,  
        'landing_speed': None, 
        'hovering_time': 0.0,
        'takeoff_time': 0.0, 
        'landing_time': 0.0, 
        # 'waypoint_weights': 10.0, 
        # 'adjust_eta': None, 
        # 'nurbs_basis_length': 2000, 
        # 'nurbs_order': 4, 
        'final_time_buffer_sec': 30, 
        'final_space_buffer_m': 2, 

        # Vehicle parameters:
        'vehicle_model': 'tarot18', 
        'vehicle_payload': 0.0,
    }

    def __init__(self, **kwargs):

      super().__init__(**kwargs)
      
      # Build aircraft model
      # ====================
      # build aicraft, which means create rotorcraft from type (model), initialize state vector, steady-state input (i.e., hover thrust for rotorcraft), controller type 
      # and corresponding setup (scheduled, real-time) and initialization.
      aircraft1 = AircraftModels.build_model(name=self.parameters['aircraft_name'],
                                              model=self.parameters['vehicle_model'],
                                              payload=self.parameters['vehicle_payload'])
      self.vehicle_model = aircraft1 

      self.current_time = 0

      # Initialize vehicle: set initial state and dt for integration.
      # ---------------------------------------------------------------
      # aircraft1.set_state(state=np.concatenate((ref_traj.cartesian_pos[0, :], ref_traj.attitude[0, :], ref_traj.velocity[0, :], ref_traj.angular_velocity[0, :]), axis=0))  # set initial state
      aircraft1.set_state(state=np.array([0,0,0,0,0,0,0,0,0,0,0]))  # set initial state
      aircraft1.set_dt(dt=self.parameters['dt'])  # set dt for simulation

    def initialize(self, u=None, z=None): 
      # Extract initial state from reference trajectory    
      return self.StateContainer({
          'x': 0, # self.ref_traj.cartesian_pos[0, 0],
          'y': 0, #self.ref_traj.cartesian_pos[0, 1],
          'z': 0, #self.ref_traj.cartesian_pos[0, 2],
          'phi': 0, #self.ref_traj.attitude[0, 0],
          'theta': 0, #self.ref_traj.attitude[0, 1],
          'psi': 0, # self.ref_traj.attitude[0, 2],
          'vx': 0, #self.ref_traj.velocity[0, 0],
          'vy': 0, #self.ref_traj.velocity[0, 1],
          'vz': 0, #self.ref_traj.velocity[0, 2],
          'p': 0, #self.ref_traj.angular_velocity[0, 0],
          'q': 0, #self.ref_traj.angular_velocity[0, 1],
          'r': 0, #self.ref_traj.angular_velocity[0, 2],
          't': 0
          })
    
    def dx(self, x : dict, u : dict):

        # Extract useful values
        # ---------------------
        m = self.vehicle_model.mass['total']  # vehicle mass
        Ixx, Iyy, Izz = self.vehicle_model.mass['Ixx'], self.vehicle_model.mass['Iyy'], self.vehicle_model.mass['Izz']    # vehicle inertia
        
        # Input vector
        T  = u['T']   # Thrust (along body z)
        tp = u['mx']  # Moment along body x
        tq = u['my']  # Moment along body y
        tr = u['mz']  # Moment along body z

        # Extract state variables from current state vector
        # -------------------------------------------------
        phi   = x['phi'] 
        theta = x['theta'] 
        psi   = x['psi']
        vx_a = x['vx']
        vy_a = x['vy']
        vz_a = x['vz']
        p = x['p']
        q = x['q']
        r = x['r']

        # Pre-compute Trigonometric values
        # --------------------------------
        sin_phi   = np.sin(phi)
        cos_phi   = np.cos(phi)
        sin_theta = np.sin(theta)
        cos_theta = np.cos(theta)
        tan_theta = np.tan(theta)
        sin_psi   = np.sin(psi)
        cos_psi   = np.cos(psi)
        
        # Compute drag forces
        # -------------------
        v_earth = np.array([vx_a, vy_a, vz_a]).reshape((-1,)) # velocity in Earth-fixed frame
        v_body  = np.dot(geom.rot_eart2body_fast(sin_phi, cos_phi, sin_theta, cos_theta, sin_psi, cos_psi), v_earth)  # Velocity in body-axis
        fb_drag = self.vehicle_model.aero['drag'](v_body)   # drag force in body axis
        fe_drag = np.dot(geom.rot_body2earth_fast(sin_phi, cos_phi, sin_theta, cos_theta, sin_psi, cos_psi), fb_drag) # drag forces in Earth-fixed frame
        fe_drag[-1] = np.sign(v_earth[-1]) * np.abs(fe_drag[-1])  # adjust vertical (z=Up) force according to velocity in fixed frame

        # Update state vector
        # -------------------
        dxdt = np.zeros((len(x),))
        
        dxdt[0] = vx_a    # x-position increment (airspeed along x-direction)
        dxdt[1] = vy_a    # y-position increment (airspeed along y-direction)
        dxdt[2] = vz_a    # z-position increment (airspeed along z-direction)
        
        dxdt[3]  = p + q * sin_phi * tan_theta + r * cos_phi * tan_theta        # Euler's angle phi increment
        dxdt[4]  = q * cos_phi - r * sin_phi                                    # Euler's angle theta increment
        dxdt[5]  = q * sin_phi / cos_theta + r * cos_phi / cos_theta            # Euler's angle psi increment
        
        dxdt[6]  = ((sin_theta * cos_psi * cos_phi + sin_phi * sin_psi) * T - fe_drag[0]) / m   # Acceleration along x-axis
        dxdt[7]  = ((sin_theta * sin_psi * cos_phi - sin_phi * cos_psi) * T - fe_drag[1]) / m   # Acceleration along y-axis
        dxdt[8]  = - self.parameters['gravity'] + (cos_phi * cos_theta  * T - fe_drag[2]) / m   # Acceleration along z-axis

        dxdt[9]  = ((Iyy - Izz) * q * r + tp * self.vehicle_model.geom['arm_length']) / Ixx     # Angular acceleration along body x-axis: roll rate
        dxdt[10] = ((Izz - Ixx) * p * r + tq * self.vehicle_model.geom['arm_length']) / Iyy     # Angular acceleration along body y-axis: pitch rate
        dxdt[11] = ((Ixx - Iyy) * p * q + tr *        1               ) / Izz                   # Angular acceleration along body z-axis: yaw rate
        dxdt[12] = 1                                                                            # Auxiliary time variable

        # Set vehicle state:
        state_temp = np.array([x[iter] for iter in x.keys()])
        self.vehicle_model.set_state(state=state_temp + dxdt*self.parameters['dt'])
        
        # I'd suggest a more compact way of generating the StateContainer
        return self.StateContainer(np.array([np.atleast_1d(item) for item in dxdt]))
    
    def event_state(self, x : dict) -> dict:
        # # Extract next waypoint information 
        # num_wypts = len(self.parameters['waypoints']['waypoints_time']) - 1 # Don't include initial waypoint
        # index_next = self.parameters['waypoints']['next_waypoint']

        # # Check if at intial waypoint. If so, event_state is 1
        # if index_next == 0:
        #     self.parameters['waypoints']['next_waypoint'] = 1
        #     return {
        #         'TrajectoryComplete': 1
        #     }
        # # Check if passed final waypoint. If so, event_state is 0
        # if index_next > num_wypts:
        #     return {
        #         'TrajectoryComplete': 0
        #     }
        
        # t_next = self.parameters['waypoints']['waypoints_time'][index_next]
        # x_next = self.parameters['waypoints']['waypoints_x'][index_next]
        # y_next = self.parameters['waypoints']['waypoints_y'][index_next]
        # z_next = self.parameters['waypoints']['waypoints_z'][index_next]

        # # Define time interval for acceptable arrival at waypoint
        # time_buffer_left = (self.parameters['waypoints']['waypoints_time'][index_next] - self.parameters['waypoints']['waypoints_time'][index_next - 1])/2
        # if index_next == num_wypts:
        #     # Final waypoint, add final buffer time 
        #     time_buffer_right = t_next + self.parameters['final_time_buffer_sec']
        # else: 
        #     time_buffer_right = (self.parameters['waypoints']['waypoints_time'][index_next+1] - self.parameters['waypoints']['waypoints_time'][index_next])/2

        # # Check if next waypoint is satisfied:
        # if x['t'] < t_next - time_buffer_left:
        #     # Not yet within time of next waypoint
        #     return {
        #             'TrajectoryComplete': (num_wypts - (index_next - 1))/num_wypts
        #         }
        # elif t_next - time_buffer_left <= x['t'] <= t_next + time_buffer_right:
        #     # Current time within ETA interval. Check if distance also within acceptable range
        #     dist_now = np.sqrt((x['x']-x_next)**2 + (x['y']-y_next)**2 + (x['z']-z_next)**2)
        #     if dist_now <= self.parameters['final_space_buffer_m']:
        #         # Waypoint achieved
        #         self.parameters['waypoints']['next_waypoint'] += 1
        #         return {
        #             'TrajectoryComplete': (num_wypts - index_next)/num_wypts
        #         }
        #     else:
        #         # Waypoint not yet achieved
        #         return {
        #             'TrajectoryComplete': (num_wypts - (index_next - 1))/num_wypts
        #         }
        # else:
        #     # ETA passed before waypoint reached 
        #     warn("Trajectory may not have reached waypoint associated with ETA of {})".format(t_next))
        #     self.parameters['waypoints']['next_waypoint'] += 1
        #     return {
        #             'TrajectoryComplete': (num_wypts - index_next)/num_wypts
        #         }
        pass
 
    def output(self, x : dict):
        # Output is the same as the state vector, without time 
        return self.OutputContainer(x.matrix[0:-1])


    def threshold_met(self, x : dict) -> dict:
        # t_lower_bound = self.parameters['waypoints']['waypoints_time'][-1] - (self.parameters['waypoints']['waypoints_time'][-1] - self.parameters['waypoints']['waypoints_time'][-2])/2
        # t_upper_bound = self.parameters['waypoints']['waypoints_time'][-1] + self.parameters['final_time_buffer_sec']
        # if x['t'] < t_lower_bound:
        #     # Trajectory hasn't reached final ETA
        #     return {
        #         'TrajectoryComplete': False
        #     }
        # elif t_lower_bound <= x['t'] <= t_upper_bound:
        #     # Trajectory is within bounds of final ETA
        #     dist_now = np.sqrt((x['x']-self.parameters['waypoints']['waypoints_x'][-1])**2 + (x['y']-self.parameters['waypoints']['waypoints_y'][-1])**2 + (x['z']-self.parameters['waypoints']['waypoints_z'][-1])**2)
        #     if dist_now <= self.parameters['final_space_buffer_m']:
        #         return {
        #             'TrajectoryComplete': True
        #         }
        #     else: 
        #         return {
        #             'TrajectoryComplete': False
        #         }
        # else: 
        #     # Trajectory has passed acceptable bounds of final ETA - simulation terminated
        #     warn("Trajectory simulation extends beyond the final ETA. Either the final waypoint was not reached in the alotted time (and the simulation was terminated), or simulation was run for longer than the trajectory length.")
        #     return {
        #         'TrajectoryComplete': True
        #     }
        pass

    def visualize_traj(self, pred):
        """
        This method provides functionality to visualize a predicted trajectory generated, plotted with the reference trajectory and coarse waypoints. 

        Calling this returns a figure with two subplots: 1) latitude (deg) vs longitude (deg), and 2) altitude (m) vs time.

        Parameters
        ----------
        pred : UAVGen model simulation  
               SimulationResults from simulate_to or simulate_to_threshold for a defined UAVGen class

        Returns 
        -------
        fig : Visualization of trajectory generation results 
        """

        import matplotlib.pyplot as plt

        # Conversions
        # -----------
        deg2rad = np.pi/180.0
        rad2deg = 180.0/np.pi
        
        # Extract reference trajectory information
        # ----------------------------------------
        waypoints   = self.ref_traj.route
        eta         = self.ref_traj.route.eta
        depart_time = self.ref_traj.route.departure_time
        time        = self.ref_traj.time
        ref_pos     = self.ref_traj.geodetic_pos

        # Extract predicted trajectory information
        # ----------------------------------------
        pred_time = pred.times
        pred_x = [pred.outputs[iter]['x'] for iter in range(len(pred_time))]
        pred_y = [pred.outputs[iter]['y'] for iter in range(len(pred_time))]
        pred_z = [pred.outputs[iter]['z'] for iter in range(len(pred_time))]

        pred_lat = []
        pred_lon = []
        pred_alt = []

        for iter1 in range(len(pred_time)):
            x_temp, y_temp, z_temp = self.coord_transform.enu2geodetic(pred_x[iter1], pred_y[iter1], pred_z[iter1])
            pred_lat.append(x_temp)
            pred_lon.append(y_temp)
            pred_alt.append(z_temp)
        
        pred_lat_deg = [pred_lat[iter] * rad2deg for iter in range(len(pred_lat))]
        pred_lon_deg = [pred_lon[iter] * rad2deg for iter in range(len(pred_lon))]

        # Initialize Figure
        # ----------------
        params = dict(figsize=(13, 9), fontsize=14, linewidth=2.0, alpha_preds=0.6)
        fig, (ax1, ax2) = plt.subplots(2)

        # Plot trajectory predictions
        # -------------------------
        # First plot waypoints (dots) and reference trajectory (commanded, line)
        ax1.plot(waypoints.lon * rad2deg, waypoints.lat  * rad2deg, 'o', color='tab:orange', alpha=0.5, markersize=10, label='__nolegend__')
        ax1.plot(ref_pos[:, 1] * rad2deg, ref_pos[:, 0] * rad2deg, '--', linewidth=params['linewidth'], color='tab:orange', alpha=0.5, label='traj')
        ax1.plot(pred_lon_deg, pred_lat_deg,'-', color='tab:blue', alpha=params['alpha_preds'], linewidth=params['linewidth'], label='prediction')

        ax1.set_xlabel('longitude, deg', fontsize=params['fontsize'])
        ax1.set_ylabel('latitude, deg', fontsize=params['fontsize'])
        ax1.legend(fontsize=params['fontsize'])

        # Add altitude plot
        # -------------------------------------------------------
        time_vector = [depart_time + datetime.timedelta(seconds=pred_time[ii]) for ii in range(len(pred_time))]
        ax2.plot_date(eta, waypoints.alt, '--o', color='tab:orange', alpha=0.5, linewidth=params['linewidth'], label='__nolegend__')
        ax2.plot(time_vector, pred_alt,'-', color='tab:blue',
                      alpha=params['alpha_preds'], linewidth=params['linewidth'], label='__nolegend__')
        
        ax2.set_xlabel('time stamp, -', fontsize=params['fontsize'])
        ax2.set_ylabel('altitude, m', fontsize=params['fontsize'])

        return fig
