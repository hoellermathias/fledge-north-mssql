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
import pyodbc
import datetime





"""
server = getenv("PYMSSQL_TEST_SERVER")
user = getenv("PYMSSQL_TEST_USERNAME")
password = getenv("PYMSSQL_TEST_PASSWORD")

conn = pymssql.connect(server, user, password, "tempdb")
cursor = conn.cursor()

cursor.executemany(
    "INSERT INTO persons VALUES (%d, %s, %s)",
    [(1, 'John Smith', 'John Doe'),
     (2, 'Jane Doe', 'Joe Dog'),
     (3, 'Mike T.', 'Sarah H.')])
# you must call commit() to persist your data if you don't set autocommit to True
conn.commit()


conn.close()
"""

__license__ = "Apache 2.0"
__version__ = "${VERSION}"

_LOGGER = logger.setup(__name__, level=logging.DEBUG)


mssql_north = None
config = ""

_CONFIG_CATEGORY_NAME = "MSSQL"
_CONFIG_CATEGORY_DESCRIPTION = "MSSQL North Plugin"

_DEFAULT_CONFIG = {
    'plugin': {
         'description': 'MSSQL North Plugin',
         'type': 'string',
         'default': 'mssql_north',
         'readonly': 'true'
    },
    'server': {
        'description': 'MSSQL Server',
        'type': 'string',
        'default': 'testdbserver.at',
        'order': '1',
        'displayName': 'SERVER'
    },
    'port': {
        'description': 'Destination PORT',
        'type': 'integer',
        'default': '1433',
        'order': '2',
        'displayName': 'PORT'
    },
    'db': {
        'description': 'Database Name',
        'type': 'string',
        'default': 'test',
        'order': '3',
        'displayName': 'DB NAME'
    },
    'table': {
        'description': 'Database Table',
        'type': 'string',
        'default': 'test',
        'order': '4',
        'displayName': 'DB TABLE'
    },
    'user': {
        'description': 'Database User',
        'type': 'string',
        'default': 'test',
        'order': '5',
        'displayName': 'DB USER'
    },
    'pwd': {
        'description': 'Database Password',
        'type': 'string',
        'default': 'test',
        'order': '6',
        'displayName': 'DB PWD'
    },
    "source": {
         "description": "Source of data to be sent on the stream. May be either readings or statistics.",
         "type": "enumeration",
         "default": "readings",
         "options": [ "readings", "statistics" ],
         'order': '7',
         'displayName': 'Source'
    },
    "applyFilter": {
        "description": "Should filter be applied before processing data",
        "type": "boolean",
        "default": "false",
        'order': '8',
        'displayName': 'Apply Filter'
    },
    "filterRule": {
        "description": "JQ formatted filter to apply (only applicable if applyFilter is True)",
        "type": "string",
        "default": "[.[]]",
        'order': '9',
        'displayName': 'Filter Rule',
        "validity": "applyFilter == \"true\""
    }
}


def plugin_info():
    return {
        'name': 'mssql',
        'version': '1.0',
        'type': 'north',
        'interface': '1.0',
        'config': _DEFAULT_CONFIG
    }


def plugin_init(data):
    global mssql_north
    mssql_north = MssqlNorthPlugin(data)
    config = data
    return config


async def plugin_send(data, payload, stream_id):
    # stream_id (log?)
    try:
        is_data_sent, new_last_object_id, num_sent = await mssql_north.send_payloads(payload)
    except asyncio.CancelledError:
        _LOGGER.exception('error @ plugin send')
    else:
        return is_data_sent, new_last_object_id, num_sent


def plugin_shutdown(data):
    _LOGGER.debug('shutdown mssql north')
    mssql_north.shutdown() 


def plugin_reconfigure():
    pass

class MssqlNorthPlugin(object):
    """ North Mssql Plugin """

    def __init__(self, config):
        self.event_loop = asyncio.get_event_loop()
        self.server = config['server']['value']
        self.port = config['port']['value']
        self.dbname = config['db']['value']
        self.table = config['table']['value']
        self.user = config['user']['value']
        self.pwd = config['pwd']['value']
        self.dbconn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.server},{self.port};DATABASE={self.dbname};UID={self.user};PWD={self.pwd};')
        self.config = config
        self.dbcursor = self.dbconn.cursor()
        
        #_LOGGER.exception("init mssql north plugin")

    def shutdown(self):
        self.dbconn.close()

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
            send_list = [(p['asset'], p['timestamp'], json.dumps(p['readings']))  for p in payload_block]
            _LOGGER.debug(f'start sending {send_list}')
            self.dbcursor.executemany(
                    f'INSERT INTO {self.table}(asset, date, content) VALUES (?, ?, ?)',
                    [(p['asset'], datetime.datetime.strptime(p['timestamp'], "%Y-%m-%dT%H:%M:%S.%fZ"), json.dumps(p['readings']))  for p in payload_block])
            self.dbcursor.commit()
            
            #if not self.client.is_connected:
            #	self.client.reconnect()
            _LOGGER.debug('finished sending')
        except Exception as ex:
            _LOGGER.exception("Data could not be sent, %s", str(ex))
        else: 
            num_count += len(payload_block)
        return num_count
