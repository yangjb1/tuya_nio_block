import pytuya
from time import sleep
import subprocess
import requests
import os
from nio import Block
from nio.block.mixins.enrich.enrich_signals import EnrichSignals
from nio.command import command
from nio.properties import StringProperty
from nio.util.threading import spawn
from nio.util.discovery import not_discoverable

@command('rediscover')
@not_discoverable
class TuYaBase(Block, EnrichSignals):

    device_mac = StringProperty(title='MAC Address of Target Device',
                                allow_none=True)
   
    x_api_key = StringProperty(title='X API Key',
                                allow_none=False)
                                
    api_endpoint = StringProperty(title='API Endpoint',
                                allow_none=False)
   
   
    def __init__(self):
        super().__init__()
        self.device = None
        self._thread = None
        self._discovering = False
        self._updating = False
        self.ip = None
        self.mac = None
        self.deviceID = None
        #self.signal = '' 

    def configure(self, context):
        super().configure(context)
        self._thread = spawn(self._discover)

    def process_signals(self, signals):
        if not self.device:
            self.logger.warning(
                    'No TuYa device connected, dropping {} signals'.format(
                        len(signals)))
            if self._discovering:
                return
            else:
                self._thread = spawn(self._discover)
                return
        outgoing_signals = []
        for signal in signals:
            new_signal = self.get_output_signal(
                    self.execute_tuya_command(signal), signal)
            outgoing_signals.append(new_signal)

        self.notify_signals(outgoing_signals)

    def execute_tuya_command(self, signal):
        return {}

    def rediscover(self):
        self.logger.info('Rediscover command recived!')
        if self._discovering:
            status = 'Discover already in progress'
        else:
            status = 'OK'
            if self.device:
                status += ', dropped device \"{}\" with MAC {}'\
                        .format(self.ip, self.mac)
            self.device = None
            self._thread = spawn(self._discover)
        self.logger.info(status)
        return {'status': status}

    def is_valid_device(self, mac):
        """ Override to determine whether the device should be considered
        Can check device type, device MAC address, etc
        This parent function will check that the MAC address matches if it
        was specified in the block parameters
        Return a boolean for whether it is valid
        """
        if self.device_mac():
            return mac == self.device_mac()
        # If no MAC specified consider it valid
        return True


    def _discover(self):
        self._discovering = True
        self.device = None
        while not self.device:
            self.logger.debug('Discovering TuYa devices on network...')
            try:
                devices = self.discover_devices()
            except:
                self.logger.error('Error discovering devices, aborting')
                self._discovering = False
                return
            self.logger.debug('Found {} TuYa devices'.format(len(devices)))
            for device in devices:
                self.logger.debug('Checking device {}'.format(device))
                if self.is_valid_device(device):
                    self.ip = device.ip
                    self.mac = device.mac
                    self.deviceID = self.get_deviceID()
                    self.device = pytuya.OutletDevice(self.deviceID, self.ip, '1')
                    break

            else:
                self.logger.debug('No valid devices, trying again in 1 second')
                sleep(1)
        self.logger.info('Selected device \"{}\" with MAC {}'.format(
            self.ip, self.mac))
        self._discovering = False

    
    def discover_devices(self):
        arp = subprocess.check_output('arp', universal_newlines=True)

        arp_str = arp.split('\n')

        devices = []

        for arp in arp_str:
            if '84:0d:8e' in arp:
                arp = ' '.join(arp.split())
                token = arp.split(' ')
                device = TuYaDevice(token[0], token[2])
                devices.append(device)
        return devices

    def get_deviceID(self):
        response = requests.get(
                self.api_endpoint(),
                params = {'macid' : self.mac},
                headers = {'x-api-key' : self.x_api_key()}
                )
        try:
            return response.json()['deviceID']
        
        except:
            self.logger.error('Error discovering devices, aborting')
            return
            

    def stop(self):
        # End the discovery thread if it's running
        if self._thread:
            self._thread.join(0.2)
            super().stop()


class TuYaDevice():

    def __init__(self, ip, mac, deviceID='', signal={}, tuya=None):
        self.ip = ip
        self.mac = mac
        self.deviceID = deviceID
        self.signal = signal
        self.tuya = tuya 

    def update_signal(self, signal):
        if self.tuya:
            self.signal = Signal(self.tuya.status())
        else:
            self.signal = signal

