Modules that get deployed onto physical gateway or edge devices

To update the runtime.json file on an individual device; currently, you must copy the runtime.json file to the device and execute the commands:

sudo iotedgectl setup --config-file runtime.json
sudo iotedgectl start

