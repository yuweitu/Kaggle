
from util import *
import numpy as NP
import numpy.random as RNG
from deepdist import DeepDist

sc, sqlContext = init_spark(verbose_logging='INFO', show_progress=False)
sc.addPyFile('deepdist.py')
sc.addPyFile('rwlock.py')

xneg = RNG.multivariate_normal([-1.5,-1.5],NP.eye(2),size=50)
xpos = RNG.multivariate_normal([1.5,1.5],NP.eye(2),size=50)
x = NP.concatenate([xneg, xpos])
y = NP.array([-1] * 50 + [1] * 50)
dataset = sc.parallelize(zip(x, y))

w = RNG.uniform(-1, 1, 2)
b = RNG.uniform(-1, 1)
model = {'w': w, 'b': b}

def grad(model, data):
    dataX = NP.array(data.map(lambda r: r[0]).collect())
    dataY = NP.array(data.map(lambda r: r[1]).collect())
    pred = NP.dot(dataX, model['w']) + model['b']
    gw = NP.dot((pred - dataY), dataX) / 100
    gb = (pred - dataY).sum() / 100
    return {'w': gw, 'b': gb}

def desc(model, update):
    model['w'] -= 0.01 * update['w']
    model['b'] -= 0.01 * update['b']

print model
with DeepDist(model, master=None) as dd:
    dd.train(dataset, grad, desc)
    print model
