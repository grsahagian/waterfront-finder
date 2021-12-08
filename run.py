from main import WaterfrontPropertyLocator
import os


path = 'wf_data'
f_exists = os.path.exists(path)
if not f_exists:
    os.makedirs(path)


state = 'Connecticut' # full name of any State
wpl = WaterfrontPropertyLocator(state) # instantiate class w/ specified state

# Find all boundary node coordinates of lakes in region
wpl.get_nodes() # --> to CSV

# Get all incomplete addresses of house nodes within 200m of waterfront
wpl.get_wf(1) # broken down into 4 pieces due to high number of API calls
wpl.get_wf(2)
wpl.get_wf(3)
wpl.get_wf(4)

# Search for full addresses (matches reference ID found in previous function)
wpl.get_full_address() #  Reads all 4 pieces of previous function call -> only call this once

