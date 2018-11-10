#!/usr/bin/env python2
import argparse
import dog


def parse():
    parser = argparse.ArgumentParser(prog='./create-certificate.py',
                                     description='This program create certificate for openvpn client')
    parser.add_argument('username', type=str,
                        help='Client username, example: Help_Mobile')
    args = parser.parse_args()
    return args.username


def main():
    directory_easyrsa = '/etc/openvpn/easy-rsa/'
    directory_client = '/etc/openvpn/easy-rsa/pki/private/'
    directory_yealink = '/etc/openvpn/client-keys/'
    ca_certificate = '/etc/openvpn/ca.crt'
    ta_key = '/etc/openvpn/ta.key'
    openvpn_config = '/etc/openvpn/python/ovpn.template'
    dogtag_schema = 'https'
    dogtag_hostname = 'sigbind.internal'
    dogtag_port = '8443'
    dogtag_auth_certificate = '/opt/test.pem'

    username = parse()

    directory_yealink_client = directory_yealink + username + '/'
    signed_certificate = directory_yealink_client + username + '.crt'

    creation = dog.EasyRsa(username, directory_easyrsa, directory_client, directory_yealink_client)
    creation_certificate = creation.easy_rsa()

    conn = dog.DogApi(dogtag_schema, dogtag_hostname, dogtag_port, dogtag_auth_certificate)
    conn.enroll(creation_certificate, username, signed_certificate)

    yealink = dog.YeaLink(directory_yealink_client, ca_certificate, ta_key, openvpn_config)
    yealink.prepare_env()
    yealink.tar_certificates()


main()
