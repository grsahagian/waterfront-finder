# Waterfront-Finder

<h3>Overview</h3>

This script queries OpenStreetMap via multiple APIs in order
to find houses within a certain radius of the water 
(i.e. waterfront properties). The script finds all bodies of water
tagged as a lake and creates a coordinate list of their boundaries. Every
10 coordinates in the list is then pinged to see if there are any
nodes that are tagged with a house number and address and adds them to
an ongoing list of dictionaries containing this information
(as well as the nodes OSM reference ID).

To find the full address, search for the address in the OSM database
and if we find a location with a matching reference ID, we then add this address
to our final address book.

The result is a list of all addresses within the given state that are
deemed to be 'Waterfront Property'.

<h3>Usage</h3>
1. Install package dependencies stipulated in requirements.txt file
2. Inside `run.py` change the `state` variable according to preference.
3. <em>(Optional)</em> This script takes a long, long time to run, so you may have to run the script many times with each function isolated, following the correct order of operations: `wpl.get_nodes(), wpl.get_wf(1), wpl.get_wf(2), wpl.get_wf(3), wpl.get_wf(4), wpl.get_full_address()` 
4. Run `python run.py` in terminal 



<h2>Disclaimer</h2>
* I do not promote, encourage, support or excite any illegal activity or hacking without written permission in general. The repo and author of the repo is no way responsible for any misuse of the information.

* "waterfront-finder" is just a terms that represents the name of the repo and is not a repo that provides any illegal information.

* The Software's and Scripts provided by the repo should only be used for EDUCATIONAL PURPOSES ONLY. The repo or the author can not be held responsible for the misuse of them by the users.

* I am not responsible for any direct or indirect damage caused due to the usage of the code provided on this site. All the information provided on this repo are for educational purposes only.




