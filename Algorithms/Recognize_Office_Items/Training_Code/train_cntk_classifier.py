#
# @Author: DaCrook 
# Train an image classifier in CNTK for usage in an edge module
# Actual training is done via Azure ML Workbench & Microsoft Azure's Batch AI
#

#Start with our import statements
#from azureml.logging import get_azureml_logger
import cntk as C
from cntk.io import transforms as xforms
from azure.storage.blob import BlockBlobService
import os
import pickle
import time

#NEURAL NET PARAMS
IMAGE_HEIGHT = 224
IMAGE_WIDTH = 224
IN_SHAPE = (3, IMAGE_WIDTH, IMAGE_HEIGHT)

MINIBATCH_SIZE = 50
EPOCH_SIZE = 120
MAX_DATA_PASSES = 100
LOG_FREQ = 10
TEST_SAMPLES = 120

#DATA LOCATION PARAMS
DOWNLOAD_DIR = 'C:/data/Office_Supplies/'
MAP_FILE_PATH = DOWNLOAD_DIR + 'mapfile.txt'
CLASS_MAPPING_FILE = DOWNLOAD_DIR + 'class_mapping.pkl'
BLOB_ACCOUNT = 'iotmlreceiving'
BLOB_KEY = 'Rg/wEKqkhPAso5FqvgtAQrYBP0dTFcYQc35LhZRvNBEUQE8y7HXf+MAd9rUrk2lSR4eqSZULOAvDZ1YFItg4RA=='

#Global variables that change
NUM_OUTPUTS = 7

def download_and_prep_data():
    '''Downloads data from blob, create image map file & a pickled class mapping'''
    bbs = BlockBlobService(account_name = BLOB_ACCOUNT, account_key = BLOB_KEY)
    classes = []
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
    with open(MAP_FILE_PATH, 'w') as file:        
        for cont in bbs.list_containers():
            classes.append(cont.name)
            if not os.path.exists(DOWNLOAD_DIR + cont.name):
                os.makedirs(DOWNLOAD_DIR + cont.name)
            for blob in bbs.list_blobs(cont.name):
                dest = DOWNLOAD_DIR + cont.name + '/' + blob.name
                bbs.get_blob_to_path(
                    cont.name,
                    blob.name,
                    dest
                )
                file.write(dest + '\t' + str(classes.index(cont.name)) + '\n')
    with open(CLASS_MAPPING_FILE, 'wb') as p_file:
        pickle.dump(classes, p_file)
    global NUM_OUTPUTS 
    NUM_OUTPUTS = len(classes)
    return classes

def create_minibatch_source(map_file, is_training, num_outputs):
    '''Create a minibatch source'''
    transforms = []     
    # train uses data augmentation (translation only)
    if is_training:
        transforms += [xforms.crop(crop_type='randomside', side_ratio=0.8)  ]
    transforms += [xforms.scale(width=IMAGE_WIDTH, height=IMAGE_HEIGHT, channels=3, interpolations='linear')]
    data_source = C.io.ImageDeserializer(MAP_FILE_PATH, C.io.StreamDefs(
        image = C.io.StreamDef(field='image', transforms=transforms),
        label = C.io.StreamDef(field='label', shape=num_outputs)
    ))
    return C.io.MinibatchSource([data_source], randomize=is_training)

def create_model(x):
    '''Create a standard convolutional model'''
    with C.layers.default_options(init = C.layers.glorot_uniform(), activation = C.relu):
        h = x
        #layer 1
        h = C.layers.Convolution2D(filter_shape=(3,3), num_filters=32, strides=(2,2), pad=True)(h)
        h = C.layers.MaxPooling(filter_shape=(2,2), strides=(2,2))(h)

        #layer 2
        h = C.layers.Convolution2D(filter_shape=(3,3), num_filters=32, strides=(2,2), pad=True)(h)
        h = C.layers.MaxPooling(filter_shape=(2,2), strides=(2,2))(h)

        #layer 3
        h = C.layers.Convolution2D(filter_shape=(3,3), num_filters=64, strides=(2,2), pad=True)(h)
        h = C.layers.MaxPooling(filter_shape=(2,2), strides=(2,2))(h)

        #Dense & Output
        h = C.layers.Dense(100)(h)
        h = C.layers.Dropout(0.5)(h)
        h = C.layers.Dense(NUM_OUTPUTS, activation=None, name="prediction")(h)
        return h

def create_criterion(model, labels):
    loss = C.losses.cross_entropy_with_softmax(model, labels)
    error = C.classification_error(model, labels)
    return loss, error

def moving_average(a, w=5):
    if len(a) < w:
        return a[:]    # Need to send a copy of the array
    return [val if idx < w else sum(a[(idx-w):idx])/w for idx, val in enumerate(a)]

def print_training_progress(trainer, mb, frequency, verbose=1):
    training_loss = "NA"
    eval_error = "NA"

    if mb%frequency == 0:
        training_loss = trainer.previous_minibatch_loss_average
        eval_error = trainer.previous_minibatch_evaluation_average
        if verbose:
            print ("Minibatch: {0}, Loss: {1:.4f}, Error: {2:.2f}%".format(mb, training_loss, eval_error*100))
    return mb, training_loss, eval_error

def train_test(train_reader, test_reader, num_sweeps = 10):
    loss, label_error = create_criterion(model, y)
    # Instantiate the trainer object to drive the model training
    learning_rate = [0.01]*100 + [0.001]*100 + [0.0001]
    lr_schedule = C.learning_rate_schedule(learning_rate, C.UnitType.minibatch)
    learner = C.sgd(model.parameters, lr_schedule)
    trainer = C.Trainer(model, (loss, label_error), [learner])

    num_minibatches = (EPOCH_SIZE * num_sweeps) / MINIBATCH_SIZE

    train_map = {
        y : train_reader.streams.label,
        x : train_reader.streams.image
    }

    start = time.time()

    for i in range(0, int(num_minibatches)):
        data = train_reader.next_minibatch(MINIBATCH_SIZE, input_map = train_map)
        trainer.train_minibatch(data)
        print_training_progress(trainer, i, LOG_FREQ)
    
    print("Training took {:.1f} sec".format(time.time() - start))

    #
    # Start Testing
    #
    test_map = {
        y : test_reader.streams.label,
        x : test_reader.streams.image
    }

    test_result = 0.0
    num_test_minibatches = TEST_SAMPLES // MINIBATCH_SIZE

    print(num_test_minibatches)

    for i in range(num_test_minibatches):
        data = test_reader.next_minibatch(MINIBATCH_SIZE, input_map = test_map)
        eval_error = trainer.test_minibatch(data)
        test_result += eval_error
    print("Average test error: {0:.2f}%".format(test_result*100 / num_test_minibatches))

classes = download_and_prep_data()
print(NUM_OUTPUTS)
x = C.input_variable(IN_SHAPE)
y = C.input_variable(NUM_OUTPUTS)
model = create_model(x / 255)

print('attempting train')

train_reader = create_minibatch_source(MAP_FILE_PATH, True, NUM_OUTPUTS)
test_reader = create_minibatch_source(MAP_FILE_PATH, True, NUM_OUTPUTS)

train_test(train_reader, test_reader, num_sweeps = 100)
