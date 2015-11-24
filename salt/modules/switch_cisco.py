# -*- coding: utf-8 -*-
from __future__ import absolute_import

# Python libs
import logging
import netmiko
import socket

from netmiko.ssh_exception import NetMikoAuthenticationException, NetMikoTimeoutException

# Salt libs

__proxyenabled__ = ['cisco_ios_switch']

logger = logging.getLogger(__name__)
_conn = None


def _persist(func):
    def inner(self, *args, **kwargs):
        try:
            return super(PersistentConnectHandler, self).func(*args, **kwargs)
        except socket.error as e:
            if e.message == 'Socket is closed' and init(__opts__):
                logger.debug('Reloaded SSH connection')
                self.func(*args, **kwargs)
    return inner


class PersistentConnectHandler(netmiko.ConnectHandler):
    '''
    Overload necessary methods of the base class so that
    the user never gets socket.error exception because of
    an expired connection.
    '''
    @_persist
    def enable(self, *args, **kwargs):
        pass

    @_persist
    def config_mode(self, *args, **kwargs):
        pass

    @_persist
    def send_command(self, *args, **kwargs):
        pass

    @_persist
    def send_config_set(self, *args, **kwargs):
        pass


def __virtual__():
    '''
    There is no way of telling whether the target device is
    a Cisco switch without logging in and inspecting the
    manufacturer. We are therefore assuming that proxy minions
    running this module are communicating with a Cisco box.
    '''
    return 'switch'


def init(opts):
    '''
    Initialize a connection to the switch.
    '''
    ip = opts['proxy'].get('ip')
    username = opts['proxy'].get('username')
    password = opts['proxy'].get('password')

    try:
        _conn = PersistentConnectHandler(ip=ip,
                                         username=username,
                                         password=password,
                                         device_type='cisco_ios')
    except NetMikoAuthenticationException:
        logger.error('Authentication failed with {0} (using username {1})'
                     .format(ip, username))
        return False
    except NetMikoTimeoutException:
        logger.error('Timed out while trying to open SSH connection'
                     'to {0} (using username {1})'.format(ip, username))
        return False
    return True