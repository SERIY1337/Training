from dog import Dogtag, OpenVPN, YeaLink
from argparse import ArgumentParser


def parse():
    parser = ArgumentParser(prog='./create-certificate.py',
                            description='This program create certificate for openvpn client')
    parser.add_argument('username', type=str,
                        help='Client username, example: Help_Mobile')
    args = parser.parse_args()
    return args.username


def main():
    directory_easyrsa = '/etc/openvpn/easy-rsa/'
    directory_client = '/etc/openvpn/easy-rsa/pki/private/'
    directory_yealink_storage = '/etc/openvpn/client-keys/'
    ca_cert = '/etc/openvpn/ca.crt'
    ta_key = '/etc/openvpn/ta.key'
    openvpn_config = '/etc/openvpn/python/ovpn.template'
    dogtag_schema = 'https'
    dogtag_hostname = 'sigbind.internal'
    dogtag_port = '8443'
    dogtag_auth_certificate = '/opt/test.pem'

    username = parse()

    directory_yealink_pack = directory_yealink_storage + username
    signed_certificate = directory_yealink_pack + '/' + username + '.crt'

    creation = OpenVPN(username, directory_easyrsa, directory_client, directory_yealink_pack)
    request_certificate = creation.easy_rsa()

    conn = Dogtag(dogtag_schema, dogtag_hostname, dogtag_port, dogtag_auth_certificate)
    conn.enroll(request_certificate, username, signed_certificate)

    yealink = YeaLink(directory_yealink_pack, ca_cert, ta_key, openvpn_config)
    yealink.prepare_env()
    yealink.yealink_tar()


main()
