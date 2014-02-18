federated_openstack_auth
========================

NEW API DOCUMENTATION


1. backend.py --> federated_authenticate()-- super function responsible for the federated authentication, the input parameters passed are the request, tenant, and the realm which authenticates the user and returns a scoped token

2. forms.py --> get_external_auth_services()-- uses the federated api function getRealmList and returns the list of external Idp's that are stored in the Keystone's service catalog

3. utils.py --> get_federated_keystone_url() -- returns the endpoint where the federated keystone service is running

4. utils.py --> get_realm() -- it is responsible for returning the endpoint of the particulat Idp chosen by the user for federated    authentication along with the authentication request message need to be sent to the Idp

5. utils.py --> get_tenant_name() -- handles the response, authentication and attribute assertion message sent from the idp and get the list of tenant the user is already associated with


SET UP THE FEDERATED HORIZON:

   1. Goto devstack VM
   2. git clone https://github.com/deepakselvaraj/federated_openstack_auth.git
   3. cd federated_openstack_auth
   4. vim openstack_auth/utils.py
   5. find the method "get_federated_keystone_url" and change "http://fedkeystone.sec.cs.kent.ac.uk:5000/v2.0/" to "http://IP_OF_YOUR_FEDERATED_KEYSTONE:5000/v2.0/"
   6. sudo python setup.py install

SET UP FEDERATED API 
   
1. git clone https://github.com/deepakselvaraj/federated_api.git
2. cd federated_keystone_auth_module
3. sudo python setup.py install
4. sudo service apache2 restart
5. Goto Horizon UI


Note:

There is a minor bug in the devstack environment when the Horizon client tries opening up the browser for third party 
authentication. Please follow the below steps until the bug is fixed

1. Run the script that holds the endpoint of the IdP
2. Select the endpoint and enter the required credentials, 
3. Then view horizon automatically login the user and changes the dashboard with the default permissions associated with that particular user
