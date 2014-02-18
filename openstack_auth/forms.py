# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables

from .exceptions import KeystoneAuthException
from .utils import get_federated_keystone_url
from .backend import KeystoneBackend

# make use of the federated api from swift client
import swiftclient
from swiftclient.contrib.federated.federated import getRealmList

LOG = logging.getLogger(__name__)


class Login(AuthenticationForm):
    """ Form used for logging in a user.

    Handles authentication with Keystone by providing the domain name, username
    and password. A scoped token is fetched after successful authentication.

    A domain name is required if authenticating with Keystone V3 running
    multi-domain configuration.

    If the user authenticated has a default project set, the token will be
    automatically scoped to their default project.

    If the user authenticated has no default project set, the authentication
    backend will try to scope to the projects returned from the user's assigned
    projects. The first successful project scoped will be returned.

    Inherits from the base ``django.contrib.auth.forms.AuthenticationForm``
    class for added security features.
    """
    region = forms.ChoiceField(label=_("Region"), required=False)
    external_auth_service = forms.ChoiceField(label=_("Auth Services"), required=True)
    username = forms.CharField(
        label=_("User Name"), required=False, 
        widget=forms.TextInput(attrs={"autofocus": "autofocus"}))
    password = forms.CharField(label=_("Password"), required=False,
                               widget=forms.PasswordInput(render_value=False))

    def __init__(self, *args, **kwargs):
        super(Login, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['external_auth_service', 'username', 'password', 'region']
        self.fields['external_auth_service'].choices = self.get_external_auth_services()
        if getattr(settings,
                   'OPENSTACK_KEYSTONE_MULTIDOMAIN_SUPPORT',
                    False):
            self.fields['domain'] = forms.CharField(label=_("Domain"),
                                                    required=True)
            self.fields.keyOrder = ['external_auth_service', 'domain', 'username', 'password', 'region']
        self.fields['region'].choices = self.get_region_choices()
        if len(self.fields['region'].choices) == 1:
            self.fields['region'].initial = self.fields['region'].choices[0][0]
            self.fields['region'].widget = forms.widgets.HiddenInput()

    @staticmethod
    def get_region_choices():
        default_region = (settings.OPENSTACK_KEYSTONE_URL, "Default Region")
        return getattr(settings, 'AVAILABLE_REGIONS', [default_region])
	
    @staticmethod
    def get_external_auth_services():
        service_list = [("default", "Default")] 
        federated_keystone_url = get_federated_keystone_url()
        realmlist = getRealmList(federated_keystone_url)
        print "=====realmlist=======", realmlist
        if realmlist:
            for item in realmlist.get("realms", []):
                service_list.append((item.get('id'), item.get('name')))      
        return service_list

    @sensitive_variables()
    def clean(self):
        default_domain = getattr(settings,
                                 'OPENSTACK_KEYSTONE_DEFAULT_DOMAIN',
                                 'Default')
        external_auth_service = self.cleaned_data.get('external_auth_service')
        print "======clean====external_auth_service===", external_auth_service
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        region = self.cleaned_data.get('region')
        domain = self.cleaned_data.get('domain', default_domain)

        # if not (username and password):
        #     # Don't authenticate, just let the other validators handle it.
        #     return self.cleaned_data
        print "=============region==========", region
        if external_auth_service not in ['default', None]:
            self.user_cache = KeystoneBackend().federated_authenticate(self.request, external_auth_service, region="RegionOne")

        else:
            try:
                self.user_cache = authenticate(request=self.request,
                                               username=username,
                                               password=password,
                                               user_domain_name=domain,
                                               auth_url=region, 
                                               external_auth_service=external_auth_service)
                msg = 'Login successful for user "%(username)s".' % \
                    {'username': username}
                LOG.info(msg)
            except KeystoneAuthException as exc:
                msg = 'Login failed for user "%(username)s".' % \
                    {'username': username}
                LOG.warning(msg)
                self.request.session.flush()
                raise forms.ValidationError(exc)
        print "===========self.user_cache=======", self.user_cache, type(self.user_cache)       
        self.check_for_test_cookie()
        return self.cleaned_data
