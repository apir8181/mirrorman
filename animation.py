import os, sys
import re
import ctypes
import utils
from objReader import Model
import objReader

baseDir = "models"

class Animation(object):
    """
    Animation file format:
    'ts' timeStep # time between frames, in second
    'n' totalFrames 
    'f' objName frameID matrix... # frames counts from 0
    """
    def __init__(self, filename, sprite):
        self.sprite = sprite
        fullpath = os.path.join(baseDir, filename)
        self.data = {}
        lineID = 0
        for line in open(fullpath, 'r'):
            line = line.split()
            lineID += 1
            opr = line[0]
            if opr == 'f':
                objName = line[1]
                frameID = int(line[2])
                mat = utils.convert_ctypes(map(float, line[3:]), 
                        ctypes.c_float, (16,))
                self.data[objName, frameID] = mat
            elif opr == 'ts':
                self.timeStep = float(line[1])
            elif opr == 'n':
                self.nFrames = int(line[1])
            else:
                print 'In line {}, unknown command "{}"'.format(lineID, opr)

        self.start()

    def step(self):
        fi = self.frame
        data = self.data
        for name, obj in self.sprite.model.objects.iteritems():
            obj.aniMat = data[name, fi]
        self.frame = (self.frame + 1) % self.nFrames

    def draw(self):
        self.sprite.model.draw()

    def start(self):
        self.frame = 0

class Animation2(Animation):
    def __init__(self, aniFolder, sprite):
        self.sprite = sprite
        filenames = os.listdir(os.path.join(objReader.baseDir, aniFolder))
        xs = [(self.extract_num(x),x) for x in filenames if self.extract_num(x) is not None]
        xs.sort()
        self.nFrames = len(xs)
        self.frameModels = []
        # i0 = xs[0][0]
        for i, x in xs:
            model = Model.load(os.path.join(aniFolder, x))
            self.frameModels.append(model)

        self.start()

    def start(self):
        self.frame = 0

    def step(self):
        self.sprite.model = self.model = self.frameModels[self.frame]
        self.frame = (self.frame + 1) % self.nFrames

    def draw(self):
        self.model.draw()

    ExtractPattern = re.compile(r'\w+_(?P<num>\d+)\.obj')
    @staticmethod
    def extract_num(filename):
        mch = Animation2.ExtractPattern.match(filename)
        if mch:
            return int(mch.group('num'))
        else:
            return None