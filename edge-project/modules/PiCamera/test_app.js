'use strict';

const Raspistill = require('node-raspistill').Raspistill;
const pixel_getter = require('pixel-getter')

const camera = new Raspistill({ verticalFlip: true,
                                horizontalFlip: true,
                                width: 500,
                                height: 500,
                                encoding: 'jpg',
                                noFileSave: true,
                                time: 5 });

function TakePictureLoop() {
    console.log('taking picture');
    camera.takePhoto().then((photo) => {
        console.log('got photo');
        pixel_getter.get(photo, function(err, pixels) {
            console.log('got pixels');
            console.log(pixels)
            TakePictureLoop();
        });
    });
}

TakePictureLoop();
