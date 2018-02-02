'''
@Author: David Crook
@Copyright: Microsoft 2018
'''
import cntk as C
from cntk.ops.functions import load_model
import json

MODEL_PATH = './assets/simple.dnn'
MODEL = ''

def init():
    global MODEL
    MODEL = load_model(MODEL_PATH)

def pre_process(data):
    return data

def predict(data):
    return data

def post_process(data):
    return data

def run(request):
    try:
        request_json = json.loads(request)
        print(request_json)
        data = pre_process(request_json)
        data = predict(data)
        data = post_process(data)
    except Exception as exc:
        return(str(exc))
    return json.dumps('data from ml module')
