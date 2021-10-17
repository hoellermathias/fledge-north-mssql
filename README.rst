==================
fledge-north-mqtt
==================

Fledge North Plugin to send data over MQTT protocol to a MQTT Broker

Installation 
-------------

1. Install MQTT Python Client: ``pip install paho-mqtt`` or run ``python3 -m pip install -r requirements.txt``
2. copy ``mqtt_north`` directory to ``FLEDGE_HOME_DIR/python/fledge/plugins/north/``
3. Test the installation by sending a GET request to ``http://FLEDGE_HOME_URL/fledge/plugins/installed?type=north``. The response is a JSON listing all installed north plugins and should look like: ``{"plugins": [{"name": "mqtt_north", "type": "north", "description": "MQTT North Plugin", "version": "1.0", "installedDirectory": "north/mqtt_north", "packageName": "fledge-north-mqtt-north"}, ...]}``
