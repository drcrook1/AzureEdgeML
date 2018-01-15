'use strict';

var connectionString = 'HostName=iotml.azure-devices.net;DeviceId=camera-1;SharedAccessKey=2Dtt52Rvs7pzZxmV5jRAo6x5AQWEIyF5o7LWxXahEx8=';

var Protocol = require('azure-iot-device-mqtt').Mqtt;
var Client = require('azure-iot-device').Client;
var Message = require('azure-iot-device').Message;
const Raspistill = require('node-raspistill').Raspistill;
const pixel_getter = require('pixel-getter');

const width = 50;
const height = 50;

// fromConnectionString must specify a transport constructor, coming from any transport package.
var client = Client.fromConnectionString(connectionString, Protocol);

const camera = new Raspistill({ verticalFlip: true,
  horizontalFlip: true,
  width: width,
  height: height,
  encoding: 'jpg',
  noFileSave: true,
  time: 5 });

// function PixelsToArray(pixels) {
//   var arr_pixels = '';
//   console.log(pixels);
//   for(var i =0; i < width; i++){
//     for(var j=0; j < height; j++){
//       p = pixels[i][j];
//       arr_pixels += String(p.r) + ',';
//       arr_pixels += String(p.g) + ',';
//       arr_pixels += String(p.b) + ',';
//     }
//   }
//   arr_pixels = arr_pixels.slice(0, -1); //Slice off last comma.
//   return arr_pixels;
// }

function PixelsToArray(pixels){
  var arr_pixels = '';
  Object.keys(pixels).forEach(i => {
    Object.keys(pixels[i]).forEach(j => {
      arr_pixels += pixels[i][j].r + ',';
      arr_pixels += pixels[i][j].g + ',';
      arr_pixels += pixels[i][j].b + ',';
    });
  });
  return arr_pixels.slice(0, -1); //slice off last comma.
}

function TakePictureLoop() {
  console.log('taking picture');
  camera.takePhoto().then((photo) => {
      console.log('got photo');
      pixel_getter.get(photo, function(err, pixels) {
          console.log('got pixels');         
          var pixel_arr = PixelsToArray(pixels);
          console.log(pixel_arr);
          var data = JSON.stringify({ deviceId: 'NODEJS_RPI', image: pixel_arr });
          var message = new Message(data);   
          client.sendEvent(message, printResultFor('send'));  
          TakePictureLoop();
      });
  });
}

var connectCallback = function (err) {
  if (err) {
    console.error('Could not connect: ' + err.message);
    } 
  else {
    console.log('Client connected');
    client.on('message', function (msg) {
      console.log('Id: ' + msg.messageId + ' Body: ' + msg.data);
      client.complete(msg, printResultFor('completed'));
    });

    client.on('error', function (err) {
      console.error(err.message);
    });

    client.on('disconnect', function () {
      clearInterval(sendInterval);
      client.removeAllListeners();
      client.open(connectCallback);
    });

    TakePictureLoop();
  }
};

client.open(connectCallback);

// Helper function to print results in the console
function printResultFor(op) {
  return function printResult(err, res) {
    if (err) console.log(op + ' error: ' + err.toString());
    if (res) console.log(op + ' status: ' + res.constructor.name);
  };
}