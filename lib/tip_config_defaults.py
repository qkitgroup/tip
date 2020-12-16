


#
# we define default parameters for the object, which can be overwritten by the config settings
#
_default_thermometer = {
    'type'                        : 'thermometer',
    'active'                      : False,
    'description'                 : 'mixing chamber thermometer',
    # measurement result placeholder(s), what to get from the driver
    'property'                    : 'resistance',
    # scheduler parameter
    'interval'                    : 100.0,
    # device parameter: example resistance bridge
    'device'                      : 'TemplBridge_1',
    'device_channel'              : 0,
    'device_excitation'           : 4,
    'device_range'                : 10,
    'device_integration_time'     : 0.1, # seconds, adds to the total scan interval time
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
    'control_device'              : 'TemplHeater',  # device
    'control_channel'             : 0,              # default channel 
    'control_default_heat'        : 0,              # startup heater value
    'control_resistor'            : 120,            # Ohm
    # web visible
    'webview'                     : True,           # should item be visible in the web ?
    'webview_items'               : 'resistance temperature',  # list of items to be web visible
    'webview_interval'            : 30.0,           # seconds 
}

_default_level = {
    'type'                        : 'level',
    'active'                      : False,
    'description'                 : 'lN2 scale',
    'property'                    : 'weight',
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
    'webview'                     : True,           # should item be visible in the web ?
    'webview_items'               : 'resistance temperature',  # list of items to be web visible
    'webview_interval'            : 30.0,           # seconds 
}

_default_hygrometer = {
    'type'                        : 'hygrometer',
    'active'                      : False,
    'description'                 : 'humidity sensor ',
    'property'                    : 'humidity',
    # scheduler parameter
    'interval'                    : 60, # seconds
    # device parameter: 
    'device'                      : 'TF_humidity', # the instrument to use (driver, TIPDIR/devices/*)
    'device_channel'              : 0,
    'device_excitation'           : 0,
    'device_range'                : 0,
    'device_integration_time'     : 0, # seconds, adds to the total scan interval time
    'device_uid'                  : 'Loy',
}

#
# Instruments 
#

_default_instrument = {
    'type'                        : 'instrument',
    'active'                      : False,
    'description'                 : 'Resistance bridge',
    'device'                      : 'Picowatt_AVS47', # (driver, TIPDIR/device/*) tinkerforge_bricklet_loadcell_2 ,...
    'gpib'                        : 'GPIB::20',
    'com_method'                  : 'ethernet', # could be ethernet, usb, ...
    'address'                     : 'localhost',
    'port'                        : 4223,
    'delay'           		      : 0.2,       # seconds delay between sending end receiving commands
    'timeout'                     : 1.0,       # seconds
}


#
# system defaults
#

_system_defaults = {
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
    "thermometer" : _default_thermometer,
    "scale"       : _default_level,
    "hygrometer"  : _default_hygrometer,
    "instrument"  : _default_instrument,
    "system"      : _system_defaults,
}