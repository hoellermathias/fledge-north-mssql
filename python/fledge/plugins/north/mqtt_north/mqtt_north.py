# -*- coding: utf-8 -*-

# FLEDGE_BEGIN
# See: http://fledge-iot.readthedocs.io/
# FLEDGE_END

""" MQTT North plugin"""

import aiohttp
import asyncio
import json
import logging

from fledge.common import logger
from fledge.plugins.north.common.common import *
import paho.mqtt.client as mqtt

__author__ = "Ashish Jabble, Praveen Garg"
__copyright__ = "Copyright (c) 2018 Dianomic Systems"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

_LOGGER = logger.setup(__name__, level=logging.INFO)


mqtt_north = None
config = ""

_CONFIG_CATEGORY_NAME = "MQTT"
_CONFIG_CATEGORY_DESCRIPTION = "MQTT North Plugin"

_DEFAULT_CONFIG = {
    'plugin': {
         'description': 'MQTT North Plugin',
         'type': 'string',
         'default': 'mqtt_north',
         'readonly': 'true'
    },
    'host': {
        'description': 'Destination HOST or IP',
        'type': 'string',
        'default': 'test.mosquitto.org',
        'order': '1',
        'displayName': 'HOST/IP'
    },
    'port': {
        'description': 'Destination PORT',
        'type': 'integer',
        'default': '1883',
        'order': '2',
        'displayName': 'PORT'
    },
    'topic': {
        'description': 'Publishing Topic',
        'type': 'string',
        'default': 'test',
        'order': '3',
        'displayName': 'TOPIC'
    },
    "source": {
         "description": "Source of data to be sent on the stream. May be either readings or statistics.",
         "type": "enumeration",
         "default": "readings",
         "options": [ "readings", "statistics" ],
         'order': '4',
         'displayName': 'Source'
    },
    "applyFilter": {
        "description": "Should filter be applied before processing data",
        "type": "boolean",
        "default": "false",
        'order': '5',
        'displayName': 'Apply Filter'
    },
    "filterRule": {
        "description": "JQ formatted filter to apply (only applicable if applyFilter is True)",
        "type": "string",
        "default": "[.[]]",
        'order': '6',
        'displayName': 'Filter Rule',
        "validity": "applyFilter == \"true\""
    }
}


def plugin_info():
    return {
        'name': 'mqtt',
        'version': '1.0',
        'type': 'north',
        'interface': '1.0',
        'config': _DEFAULT_CONFIG
    }


def plugin_init(data):
    global mqtt_north
    mqtt_north = MqttNorthPlugin(data)
    config = data
    return config


async def plugin_send(data, payload, stream_id):
    # stream_id (log?)
    try:
        is_data_sent, new_last_object_id, num_sent = await mqtt_north.send_payloads(payload)
    except asyncio.CancelledError:
        _LOGGER.exception('error @ plugin send')
    else:
        return is_data_sent, new_last_object_id, num_sent


def plugin_shutdown(data):
    _LOGGER.debug('shutdown mqtt north')
    mqtt_north.shutdown() 


# TODO: North plugin can not be reconfigured? (per callback mechanism)
def plugin_reconfigure():
    pass

class MqttNorthPlugin(object):
    """ North HTTP Plugin """

    def __init__(self, config):
        self.event_loop = asyncio.get_event_loop()
        self.client = mqtt.Client()
        self.host = config['host']['value']
        self.port = int(config['port']['value'])
        self.topic = config['topic']['value']
        self.client.connect(self.host, self.port, 30)
        self.client.loop_start()
        self.config = config
        
        #_LOGGER.exception("init mqtt north plugin")

    def shutdown(self):
        self.client.loop_stop()
        self.client.disconnect()

    async def send_payloads(self, payloads):
        is_data_sent = False
        last_object_id = 0
        num_sent = 0
        if len(payloads) == 0:
            _LOGGER.debug("no data")
        try:
            payload_block = list()

            for p in payloads:
                last_object_id = p["id"]
                read = dict()
                read["asset"] = p['asset_code']
                read["readings"] = p['reading']
                read["timestamp"] = p['user_ts']
                payload_block.append(read)

            num_sent = await self._send_payloads(payload_block)
            _LOGGER.debug("Data sent, %s", str(num_sent))
            is_data_sent = True
        except Exception as ex:
            _LOGGER.exception("Data could not be sent, %s", str(ex))

        return is_data_sent, last_object_id, num_sent

    async def _send_payloads(self, payload_block):
        """ send a list of block payloads"""
        num_count = 0
        try:
            _LOGGER.debug('start sending')
            for p in payload_block:
            	self.client.publish(f'{self.topic}/{p["asset"]}', json.dumps(p)).wait_for_publish()
            #if not self.client.is_connected:
            #	self.client.reconnect()
            _LOGGER.debug('finished sending')
        except Exception as ex:
            _LOGGER.exception("Data could not be sent, %s", str(ex))
        else: 
            num_count += len(payload_block)
        return num_count
