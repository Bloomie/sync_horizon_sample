from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client
from novaclient import client as nova_client
from glanceclient import client as glance_client
from neutronclient.v2_0 import client as neutron_client

from http.server import BaseHTTPRequestHandler, HTTPServer
import socketserver


AUTH_URL = "http://10.2.55.20:5000/v3"
USERNAME = "admin"
PASSWORD = "admin"
PROJECT_NAME = "admin"
USER_DOMAIN_ID = "default"
PROJECT_DOMAIN_ID = "default"

def build_novaclient(auth_token):
    return nova_client.Client('2.1',
                           USERNAME,
                           project_name=PROJECT_NAME,
                           project_domain_id=PROJECT_DOMAIN_ID,
                           auth_url=AUTH_URL,
                           auth_token=auth_token)

def build_glanceclient(auth_token):
    return glance_client.Client('2', 'http://10.2.55.31:9292', token=auth_token)

def build_neutronclient(auth_token):
    return neutron_client.Client(token=auth_token, endpoint_url = 'http://10.2.55.31:9696', auth_url = AUTH_URL)


def get_auth_token():
    auth = v3.Password(auth_url=AUTH_URL, username=USERNAME,
                    password=PASSWORD, project_name=PROJECT_NAME,
                    user_domain_id=USER_DOMAIN_ID, project_domain_id=PROJECT_DOMAIN_ID)
    sess = session.Session(auth=auth)
    return sess.get_token()

def get_data():
    auth_token = get_auth_token()

    flavors = build_novaclient(auth_token).flavors.list()
    flavors = [f.name for f in flavors]

    images_iter = build_glanceclient(auth_token).images.list()
    images = list(images_iter)
    images = [i.name for i in images]

    servers = build_novaclient(auth_token).servers.list()
    servers = [s.name for s in servers]

    ports = build_neutronclient(auth_token).list_ports()
    networks = build_neutronclient(auth_token).list_networks()
    fips = build_neutronclient(auth_token).list_floatingips()

    return servers, images, flavors

class S(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        servers, images, flavors = get_data()
        self.wfile.write("Servers: {}\nImages: {}\nFlavors: {}\n".format(servers, images, flavors).encode())

def run(server_class=HTTPServer, handler_class=S, port=80):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

if __name__ == "__main__":
    run()
