from os import listdir, chdir, path, mkdir, remove
from sys import exit
from subprocess import call
from shutil import copyfile, move
from pki.client import PKIConnection
from pki.cert import CertClient

import tarfile


class OpenVPN:
    def __init__(self, username, directory_easyrsa, directory_client, directory_yealink_pack):
        self.username = username
        self.directory_easyrsa = directory_easyrsa
        self.directory_client = directory_client
        self.directory_yealink_pack = directory_yealink_pack

    def check(self):
        if self.username + '.key' in listdir(self.directory_client):
            print('This certificate is available: %s. See in %s' % (self.username, self.directory_client))
            exit(1)
        elif path.isdir(self.directory_yealink_pack):
            print('This directory is available: %s. See in %s' % (self.username, self.directory_yealink_pack))
            exit(1)
        else:
            mkdir(self.directory_yealink_pack)
            return self.username

    def easy_rsa(self):
        username = self.check()
        chdir(self.directory_easyrsa)
        call('./easyrsa --batch gen-req %s nopass' % username, shell=True)

        request = '/etc/openvpn/easy-rsa/pki/reqs/{0}.req'.format(self.username)

        if path.isfile(request):
            move(self.directory_client + self.username + '.key',  self.directory_yealink_pack)
            return request
        else:
            print('Error! Failed to create request certificate. Something goes wrong')
            exit(1)


class Dogtag:
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
    def __init__(self, client_dir, ca_cert, ta_key, ovpn_config):
        self.client_dir = client_dir
        self.ca_cert = ca_cert
        self.ta_key = ta_key
        self.ovpn_config = ovpn_config
        self.username = client_dir.split('/')[-1]

    def prepare_env(self):
        chdir(self.client_dir)

        copyfile(self.ovpn_config, self.client_dir + '/vpn.cnf')

        f = open(self.client_dir + '/vpn.cnf', 'a')
        f.write('cert /config/openvpn/keys/{0}.crt\nkey /config/openvpn/keys/{0}.key\n'.format(self.username))

        keys = list([self.ca_cert, self.ta_key])

        for i in listdir('.'):
            keys.append(i)

        mkdir('keys')

        for i in keys:
            if i.endswith('ca.crt'):
                copyfile(i, './keys/%s' % i.split('/')[-1])
            elif i.endswith('ta.key'):
                copyfile(i, './keys/%s' % i.split('/')[-1])
            elif i == 'vpn.cnf':
                pass
            else:
                copyfile(i, './keys/%s' % i)

        for i in listdir('.'):
            if path.isdir(i) is True or i == 'vpn.cnf':
                pass
            else:
                remove(i)

    def yealink_tar(self):
        chdir(self.client_dir)

        yealink_tar = tarfile.open('openvpn.tar', 'w')
        for i in listdir('.'):
            if i != '':
                yealink_tar.add(i)
