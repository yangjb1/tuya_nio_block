'''
from threading import Event
from requests.exceptions import ConnectionError
from unittest.mock import patch, MagicMock
from nio.block.terminals import DEFAULT_TERMINAL
#from nio.signal.base import Signal
from nio import Signal
from nio.testing.block_test_case import NIOBlockTestCase
from ..tuya_base import TuYaBase, TuYaDevice
from ..tuya_insight_block import TuYaInsight

class EventTuYaDiscovery(TuYaInsight):

    def __init__(self, event, *args, **kwargs):
        self.event = event
        super().__init__(*args, **kwargs)

    def _discover(self):
        super()._discover()
        # Set the event after discovery happens
        self.event.set()

@patch(TuYaBase.__module__ + '.pytuya')
class TestTuYaBase(NIOBlockTestCase):

    def setUp(self):
        super().setUp()
        self.mock_insight = TuYaDevice('host', 'mac')
        self.mock_insight_2 = TuYaDevice('host', 'mac2')
        self.device = TuYaDevice('host', 'mac')


    def test_process_signals(self, mock_discover):
        """ Params are read from an Insight device for every signal list
        processed and each signal is enriched with the contents."""

        self.device.signal = {'pi': 3.14}

        mock_discover.return_value = [self.mock_insight]
        discover_event = Event()
        blk = EventTuYaDiscovery(discover_event)
        #blk.device = self.mock_insight
        self.configure_block(blk, {'enrich': {'exclude_existing': False}})
        blk.update_tuya_device_signal({'pi': 3.14})
        #self.device.signal = {'pi':3.14}
        self.assertTrue(discover_event.wait(2))
        blk.start()
        #self.assertTrue(discover_event.wait(1))
        self.assertEqual(mock_discover.call_count, 0)
        blk.process_signals([Signal({'foo': 'bar'}), Signal({'foo': 'baz'})])
        #blk.process_signals([Signal()])
        #blk.process_signals([{}])

        '''
        '''
            #Signal({'foo': 'bar'})
            #Signal({'foo': 'baz'})
            ])
        '''
        '''
        #self.assertEqual(mock_discover.call_count, 2)
        #self.assert_num_signals_notified(2)
        self.assertDictEqual(
                self.last_notified[DEFAULT_TERMINAL][0].to_dict(),
                {'pi': 3.14, 'foo': 'bar'})
        self.assertDictEqual(
                self.last_notified[DEFAULT_TERMINAL][1].to_dict(),
                {'pi': 3.14, 'foo': 'baz'})
        blk.stop()

    def test_rediscovery(self, mock_discover, *args):
        """ Retry discovery if it has failed."""
        self.mock_insight.signal = {'pi': 3.14}
        #mock_discover.side_effect = [ConnectionError, [self.mock_insight]]

        mock_discover.side_effect = [ConnectionRefusedError, [self.mock_insight]]

        #self.mock_insignt.insight_params = {'pi': 3.14}
        #mock_discover.return_value = [self.mock_insight]

        discover_event = Event()
        blk = EventTuYaDiscovery(discover_event)
        self.configure_block(blk, {})
        self.assertTrue(discover_event.wait(2))
        #self.assertEqual(mock_discover.call_count, 1)
        self.assertFalse(blk._discovering)
        self.assertIsNotNone(blk.device)
        discover_event.clear()
        blk.start()
        # ConnectionError raised, discovery aborted

        blk.process_signals([Signal()])
        #self.assertTrue(discover_event.wait(1))
        #self.assertEqual(mock_discover.call_count, 2)
        # device discovered
        #self.assertEqual(blk.device, self.mock_insight)
        #self.assertIsNone(blk.device)
        # signal was dropped, so no params retrieved from device
        #self.assertEqual(self.mock_insight.update_insight_params.call_count, 0)
        # and nothing notified
        #self.assert_num_signals_notified(0)
        f = open('device.txt', 'r+')
        content = f.read()
        token = content.split(',')
        self.assertEqual(blk.device.mac, token[2])
        self.assertEqual(blk.device.ip, token[1])
        self.assertEqual(blk.device.deviceID, token[0])
        

        # now we have a device
        blk.process_signals([Signal()])
        #self.assertEqual(mock_discover.call_count, 2)
        #self.assertEqual(self.mock_insight.update_insight_params.call_count, 1)
        self.assertIsNotNone(blk.device)
        #self.assert_num_signals_notified(1)
        blk.stop()


    #def test_rediscover_cmd(self, mock_discover, *args):

'''