from google_alerts import GoogleAlerts

# Create an instance
ga = GoogleAlerts('totallynotabotorscript@gmail.com', '$pVm9RDn_-DNtq$W')
ga.set_log_level('debug')

# Authenticate your user
ga.authenticate()

# List configured monitors
print(len(ga.list()))

ga.create('Google', {'delivery': 'mail'})