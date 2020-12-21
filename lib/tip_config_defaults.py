
#
# we define default parameters for the object, which can be overwritten by the config settings
#
_default_thermometer = {
    'type'                        : 'thermometer',
    'active'                      : False,
    'description'                 : 'what kind/where',
    # measurement result placeholder(s), what to get from the driver, as in get_'property'()
    'property'                    : 'resistance',
    'unit'                        : 'K',
    # scheduler parameter
    'interval'                    : 100.0, # seconds
    # device parameter: example resistance bridge
    'device'                      : 'Name_of_Instrument', # defined in the instruments section
    'device_channel'              : 0,
    'device_excitation'           : 0,
    'device_range'                : 0,
    'device_integration_time'     : 1, # seconds, adds to the total scan interval time
    # temperature calibration
    'calibration_active'          : False,
    'calibration_description'     : "None",
    'calibration_file'            : 'File_XYZ', #  file path relative to tip/calibrations/
    'calibration_file_order'      : 'TR',                 # TR or RT
    'calibration_interpolation'   : 'linear',
    'calibration_key_format'      : 'R',                 # support for 'R' and 'log10R'
    # feedback loop initial settings; to be changed with a tip client/gui
    'control_active'              : False,
    'control_P'                   : 0.1,
    'control_I'                   : 0.1,
    'control_D'                   : 0.0,
    # control device: example a heater
    'control_device'              : 'Name_of_Instrument',  # defined in the instruments section
    'control_channel'             : 0,              # default channel 
    'control_default_heat'        : 0,              # startup heater value
    'control_resistor'            : 120,            # Ohm
    # web visible
    'webview'                     : True,           # should item be visible in the web ?
    'webview_items'               : 'temperature',  # list (space separated) of items to be web visible, should be items in the config
    'webview_interval'            : -1,             # seconds, only used if > 0
}

_default_levelmeter = {
    'type'                        : 'levelmeter',
    'active'                      : False,
    'description'                 : 'lN2 scale',
    'property'                    : 'weight',
    'unit'                        : '',
    # scheduler parameter
    'interval'                    : 60, # seconds
    # device parameter: 
    'device'                      : 'TF_loadcell', # the instrument to use (driver, TIPDIR/devices/*)
    'device_channel'              : 0,
    'device_excitation'           : 0,
    'device_range'                : 0,
    'device_integration_time'     : 0, # seconds, adds to the total scan interval time
    'device_uid'                  : 'KfH',
    'zero_level'                  : 0, # gram
    'full_level'                  : 24000, # gram, larger than 0!
    # web visible
    'webview'                     : True,              # should item be visible in the web ?
    'webview_items'               : 'relative_level',  # list of items to be web visible
    'webview_interval'            :  -1,               # seconds, only used if > 0
}

_default_hygrometer = {
    'type'                        : 'hygrometer',
    'active'                      : False,
    'description'                 : 'humidity sensor ',
    'property'                    : 'humidity',
    'unit'                        : '%RH',
    # scheduler parameter
    'interval'                    : 60, # seconds
    # device parameter: 
    'device'                      : 'TF_humidity', # the instrument to use (driver, TIPDIR/devices/*)
    'device_channel'              : 0,
    'device_excitation'           : 0,
    'device_range'                : 0,
    'device_integration_time'     : 0, # seconds, adds to the total scan interval time
    'device_uid'                  : 'Loy',
    'webview'                     : True,            # should item be visible in the web ?
    'webview_items'               : 'humidity',      # list of items to be web visible
    'webview_interval'            :  -1,             # seconds, only used if > 0
}

#
# Instruments 
#

_default_instrument = {
    'type'                        : 'instrument',
    'active'                      : False,
    'description'                 : 'The device description, e.g. *IDN?',
    'device'                      : '', # (driver, TIPDIR/device/*) tinkerforge_bricklet_loadcell_2 ,...
    'gpib'                        : '', #'GPIB::20',
    'com_method'                  : '', #'ethernet', # could be ethernet, usb, ...
    'address'                     : 'localhost',
    'port'                        : 9999,
    'delay'           		      : 0.2,       # seconds delay between sending end receiving commands
    'timeout'                     : 1.0,       # seconds
}


#
# system defaults
#

_system_defaults = {
    'type'                       : "system_settings",
    'name'                       : "tip_instance_name",
    'settings_version'           : 2.0,
    'loglevel_console'           : 'INFO',           # one of [DEBUG, INFO, WARNING, ERROR, CRITICAL], default is WARNING
    'loglevel_file'              : 'WARNING',        # one of [DEBUG, INFO, WARNING, ERROR, CRITICAL], default is WARNING
    'zmq_port'                   : 5000,             # zmq server listens here
    # simple IPv4 checking to get rid of the flies ...  
    # space separated list; localhost is always allowed
    'allowed_ips'                : 'localhost',         # "192.168.178.36 192.168.178.34 192.168.178.53",
}


#
# config defaults dict
#

_config_defaults = {
    "thermometer"      : _default_thermometer,
    "levelmeter"       : _default_levelmeter,
    "hygrometer"       : _default_hygrometer,
    "instrument"       : _default_instrument,
    "system_settings"  : _system_defaults,
}