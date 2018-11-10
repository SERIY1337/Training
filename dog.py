import tarfile
import os
import sys
import subprocess
import shutil
from pki.client import PKIConnection
from pki.cert import CertClient


class EasyRsa:
    """How to use this:

    :param username: type: str, certificate name to create
    :param directory_easyrsa: type: str, path to directory when contain easyrsa program
    :param directory_client: type: str, path to directory where the newly created client private keys lie
    :param directory_yealink: type: str, path to directory in which the ready 'openvpn.tar' will lie
    """
    def __init__(self, username, directory_easyrsa, directory_client, directory_yealink):
        self.username = username
        self.directory_easyrsa = directory_easyrsa
        self.directory_client = directory_client
        self.directory_yealink = directory_yealink

    def check(self):
        error_certificate = 'This certificate is available: {0}. See in {1}'
        error_directory = 'This directory is available: {0}. See in {1}'
        
        client_key = self.username + '.key'

        if client_key in os.listdir(self.directory_client):
            sys.exit(error_certificate.format(self.username, self.directory_client))
        elif os.path.isdir(self.directory_yealink):
            sys.exit(error_directory.format(self.username, self.directory_yealink))
        else:
            os.mkdir(self.directory_yealink)
            return self.username

    def easy_rsa(self):
        client_req = '/etc/openvpn/easy-rsa/pki/reqs/{0}.req'
        client_key = self.username + '.key'

        username = self.check()

        os.chdir(self.directory_easyrsa)
        subprocess.call('./easyrsa --batch gen-req %s nopass' % username, shell=True)

        request = client_req.format(self.username)

        if os.path.isfile(request):
            shutil.move(self.directory_client + client_key,  self.directory_yealink)
            return request
        else:
            sys.exit('Error! Failed to create request certificate. Something goes wrong')


class DogApi:
    """How to use this:

    :param protoctol: type: str, protocol type (schema) - http or https
    :param hostname: type: str, dogtag ca hostname (example.com)
    :param port: type: str, 80 or 443 or some other port
    :param cert: type: str, path to authentication certificate for access to dogtag api
    """
    def __init__(self, protocol, hostname, port, cert):
        self.protocol = protocol
        self.hostname = hostname
        self.cert = cert
        self.port = port

    def connection(self):
        connection = PKIConnection(protocol=self.protocol, hostname=self.hostname, port=self.port)
        connection.set_authentication_cert(self.cert)

        client = CertClient(connection)
        return client

    def enroll(self, cert_req, cn, cert_sign):
        certificate_request = open(cert_req, 'r')
        certificate_signed = open(cert_sign, 'w')

        inputs = dict()
        inputs['cert_request_type'] = 'pkcs10'
        inputs['cert_request'] = certificate_request.read()
        inputs['sn_uid'] = 'V1-{0}'.format(cn)
        inputs['sn_e'] = '{0}@sigbind.internal'.format(cn)
        inputs['sn_cn'] = cn

        connection = self.connection()
        enroll_certificate = connection.enroll_cert('caUserCert', inputs)
        certificate_signed.write(enroll_certificate[0].cert.encoded)
        return enroll_certificate[0].cert.encoded


class YeaLink:
    """How to use this:

    :param client_dir: type: str, path to client directory where 'openvpn.tar' will be created
    :param ca_cert: type: str, path to dogtag ca certificate
    :param ta_key: type: str, path to 'ta.key'
    :param ovpn_config: type: str, path to client openvpn configuration file
    """
    def __init__(self, client_dir, ca_cert, ta_key, ovpn_config):
        self.client_dir = client_dir
        self.ca_cert = ca_cert
        self.ta_key = ta_key
        self.ovpn_config = ovpn_config
        self.username = client_dir.split('/')[-1]

    def prepare_env(self):
        os.chdir(self.client_dir)
        shutil.copyfile(self.ovpn_config, self.client_dir + '/vpn.cnf')

        f = open(self.client_dir + '/vpn.cnf', 'a')
        f.write('cert /config/openvpn/keys/{0}.crt\nkey /config/openvpn/keys/{0}.key\n'.format(self.username))

        keys = [
            self.ca_cert,
            self.ta_key,
        ]

        for i in os.listdir('.'):
            keys.append(i)

        os.mkdir('keys')

        for i in keys:
            if i.endswith('ca.crt') or i.endswith('ta.key'):
                shutil.copyfile(i, './keys/%s' % i.split('/')[-1])
            elif i == 'vpn.cnf':
                pass
            else:
                shutil.copyfile(i, './keys/%s' % i)

        for i in os.listdir('.'):
            if os.path.isdir(i) is True or i == 'vpn.cnf':
                pass
            else:
                os.remove(i)

    def tar_certificates(self):
        os.chdir(self.client_dir)

        yealink_tar = tarfile.open('openvpn.tar', 'w')
        for i in os.listdir('.'):
            if i != '':
                yealink_tar.add(i)
