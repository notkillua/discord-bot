# Read environment variables
file = open('.env', 'r')
variables = file.readlines()
env = {}
for variable in variables:
    variable = variable.split('=')
    key = variable[0]
    variable.pop(0)
    value = '='.join(variable)
    env[key] = value
