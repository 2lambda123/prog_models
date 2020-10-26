from .. import prognostics_model

import math

class CentrefugalPump(prognostics_model.PrognosticsModel):
    """
    Prognostics model for a centrefugal pump
    """
    events = [
        'ImpellerWearFailure',
        'PumpOilOverheat',
        'RadialBearingOverheat',
        'ThrustBearingOverheat'
    ]
    
    inputs = [
        'Tamb',     # Ambient Temperature (K)
        'V',        # Voltage (V)
        'pdisch',   # Discharge Pressure (Pa)
        'psuc',     # Suction Pressure (Pa)
        'wsync'     # Syncronous Rotational Speed of Supply Voltage (rad/sec)
    ]

    states = [
        'A',
        'Q',
        'To',
        'Tr',
        'Tt',
        'rRadial',
        'rThrust',
        'w',
        'wA',
        'wRadial',
        'wThrust',
        'QLeak'
    ]

    outputs = [
        'Qout',# Discharge Flow (m^3/s)
        'To',  # Oil Temperature (K)
        'Tr',  # Radial Bearing Temperature (K)
        'Tt',  # Thrust Bearing Temperature (K)
        'w'    # Mechanical Rotation (rad/sec)
    ]

    parameters = { # Set to defaults
        'cycleTime': 3600,  # length of a pump usage cycle

        # Environmental parameters
        'pAtm': 101325,     # Atmospheric Pressure (Pa)

        # Torque and pressure parameters
        'a0': 0.00149204,	# empirical coefficient for flow torque eqn
        'a1': 5.77703,		# empirical coefficient for flow torque eqn
        'a2': 9179.4,		# empirical coefficient for flow torque eqn
        'A': 12.7084,		# impeller blade area
        'b': 17984.6,

        # Pump/motor dynamics
        'I': 50,            # impeller/shaft/motor lumped inertia
        'r': 0.008,         # lumped friction parameter (minus bearing friction)
        'R1': 0.36,
        'R2': 0.076,
        'L1': 0.00063,

        # Flow coefficients
        'FluidI': 5,        # pump fluid inertia
        'c': 8.24123e-5,    # pump flow coefficient
        'cLeak': 1,         # internal leak flow coefficient
        'ALeak': 1e-10,     # internal leak area

        # Thrust bearing temperature
        'mcThrust': 7.3,
        'rThrust': 1.4e-6,
        'HThrust1': 0.0034,
        'HThrust2': 0.0026,

        # Radial bearing temperature
        'mcRadial': 2.4,
        'rRadial': 1.8e-6,
        'HRadial1': 0.0018,
        'HRadial2': 0.020,

        # Bearing oil temperature
        'mcOil': 8000,
        'HOil1': 1.0,
        'HOil2': 3.0,
        'HOil3': 1.5,

        # Parameter limits
        'lim': {
            'A': 9.5,
            'Tt': 370,
            'Tr': 370,
            'To': 350
        },

        # Initial state
        'x0': {
            'w': 376.9908, # 3600 rpm (rad/sec)
            'Q': 0,
            'Tt': 290,
            'Tr': 290,
            'To': 290,
            'A': 12.7084,
            'rThrust': 1.4e-6,
            'rRadial': 1.8e-6,
            'wA': 0,
            'wThrust': 0,
            'wRadial': 0
        }
    }

    def initialize(self, u, z):
        x0 = self.parameters['x0']
        x0['QLeak'] = math.copysign(self.parameters['cLeak']*self.parameters['ALeak']*math.sqrt(abs(u['psuc']-u['pdisch'])), u['psuc']-u['pdisch'])
        return x0

    def next_state(self, t, x, u, dt):
        Todot = 1/self.parameters['mcOil'] * (self.parameters['HOil1']*(x['Tt']-x['To']) + self.parameters['HOil2']*(x['Tr']-x['To']) + self.parameters['HOil3']*(u['Tamb']-x['To']))
        Ttdot = 1/self.parameters['mcThrust'] * (x['rThrust']*x['w']*x['w'] - self.parameters['HThrust1']*(x['Tt']-u['Tamb']) - self.parameters['HThrust2']*(x['Tt']-x['To']))
        Adot = -x['wA']*x['Q']*x['Q']
        rRadialdot = x['wRadial']*x['rRadial']*x['w']*x['w']
        rThrustdot = x['wThrust']*x['wThrust']*x['w']*x['w']
        friction = (self.parameters['r']+x['rThrust']+x['rRadial'])*x['w']
        QLeak = math.copysign(self.parameters['cLeak']*self.parameters['ALeak']*math.sqrt(abs(u['psuc']-u['pdisch'])), u['psuc']-u['pdisch'])
        Trdot = 1/self.parameters['mcRadial'] * (x['rRadial']*x['w']*x['w'] - self.parameters['HRadial1']*(x['Tr']-u['Tamb']) - self.parameters['HRadial2']*(x['Tr']-x['To']))
        slipn = (u['wsync']-x['w'])/(u['wsync'])
        ppump = x['A']*x['w']*x['w'] + self.parameters['b']*x['w']*x['Q']
        Qout = max(0,x['Q']-QLeak)
        slip = max(-1,(min(1,slipn)))
        deltaP = ppump+u['psuc']-u['pdisch']
        Te = 3*self.parameters['R2']/slip/(u['wsync']+0.00001)*u['V']**2/((self.parameters['R1']+self.parameters['R2']/slip)**2+(u['wsync']*self.parameters['L1'])**2)
        backTorque = -self.parameters['a2']*Qout**2 + self.parameters['a1']*x['w']*Qout + self.parameters['a0']*x['w']**2
        Qo = math.copysign(self.parameters['c']*math.sqrt(abs(deltaP)), deltaP)
        wdot = (Te-friction-backTorque)/self.parameters['I']
        Qdot = 1/self.parameters['FluidI']*(Qo-x['Q'])
        QLeak = math.copysign(self.parameters['cLeak']*self.parameters['ALeak']*math.sqrt(abs(u['psuc']-u['pdisch'])), u['psuc']-u['pdisch'])


        return {
            'A': x['A'] + Adot*dt,
            'Q': x['Q'] + Qdot*dt, 
            'To': x['To'] + Todot*dt,
            'Tr': x['Tr'] + Trdot*dt,
            'Tt': x['Tt'] + Ttdot*dt,
            'rRadial': x['rRadial'] + rRadialdot*dt,
            'rThrust': x['rThrust'] + rThrustdot*dt,
            'w': x['w']+wdot*dt,
            'wA': x['wA'],
            'wRadial': x['wRadial'],
            'wThrust': x['wThrust'],
            'QLeak': QLeak
        }

    def output(self, t, x):
        Qout = max(0,x['Q']-x['QLeak'])

        return {
            'Qout': Qout,
            'To': x['To'],
            'Tr': x['Tr'],
            'Tt': x['Tt'],
            'w': x['w']
        }

    def event_state(self, t, x):
        return {
            'ImpellerWearFailure': (x['A'] - self.parameters['lim']['A'])/(self.parameters['x0']['A'] - self.parameters['lim']['A']),
            'ThrustBearingOverheat': (self.parameters['lim']['Tt'] - x['Tt'])/(self.parameters['x0']['Tt'] - self.parameters['lim']['Tt']),
            'RadialBearingOverheat': (self.parameters['lim']['Tr'] - x['Tr'])/(self.parameters['x0']['Tr'] - self.parameters['lim']['Tr']),
            'PumpOilOverheat': (self.parameters['lim']['To'] - x['To'])/(self.parameters['x0']['To'] - self.parameters['lim']['To'])
        }

    def threshold_met(self, t, x):
        return {
            'ImpellerWearFailure': x['A'] > self.parameters['lim']['A'],
            'ThrustBearingOverheat': x['Tt'] < self.parameters['lim']['Tt'],
            'RadialBearingOverheat': x['Tr'] < self.parameters['lim']['Tr'],
            'PumpOilOverheat': x['To'] < self.parameters['lim']['To']
        }
