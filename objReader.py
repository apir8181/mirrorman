import utils
import pygame
import os, sys
from OpenGL.GL import *
from utils import Timer
import utils

baseDir = "models"

class Object(object):
    def __init__(self, name):
        self.name = name
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.indices = []
        self.material = None
        self.aniMat = utils.eye_glmat4()

    def convert(self):
        self.indices = range(len(self.vertices))
        self.indices = utils.convert_ctypes(
            self.indices, ctypes.c_uint, (len(self.indices), ))
        self.vertices = utils.convert_ctypes(
            self.vertices, ctypes.c_float, (len(self.vertices), 3))
        self.texcoords = utils.convert_ctypes(
            self.texcoords, ctypes.c_float, (len(self.texcoords), 2))
        self.normals = utils.convert_ctypes(
            self.normals, ctypes.c_float, (len(self.normals), 3))

    def draw(self):
        material = self.material
        if material: 
            glEnable(GL_TEXTURE_2D)
            glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)
            
            glMaterialfv(GL_FRONT, GL_AMBIENT, material.ambient)
            glMaterialfv(GL_FRONT, GL_DIFFUSE, material.diffuse)
            glMaterialfv(GL_FRONT, GL_SPECULAR, material.specular)
            glMaterialfv(GL_FRONT, GL_SHININESS, material.shininess)
        else: glDisable(GL_TEXTURE_2D)

        glVertexPointer(3, GL_FLOAT, 0, self.vertices)
        glNormalPointer(GL_FLOAT, 0, self.normals)
        if material:
            glTexCoordPointer(2, GL_FLOAT, 0, self.texcoords)
            glBindTexture(GL_TEXTURE_2D, material.texid)
        glDrawElements(GL_TRIANGLES, len(self.indices),
                       GL_UNSIGNED_INT, self.indices)

        # is these line needed ?
        # glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)
        # glDisable(GL_TEXTURE_2D)

class Model(object):
    def __init__(self, filename):
        tm = Timer()
        self.objects = {}
        self.mtllib = None
        vertices = []
        normals = []
        texcoords = []

        for line in open(os.path.join(baseDir, filename), "r"):
            if line.startswith('#'): continue
            v = line.split()
            if not v: continue

            if v[0] == 'o':
                obj = Object(v[1])
                names = v[1].split('_')
                for name in names:
                    self.objects[name] = obj
            elif v[0] == 'usemtl':
                obj.material = self.mtllib.get(v[1])
            elif v[0] == 'v':
                assert len(v) == 4
                v = map(float, v[1:4])
                vertices.append(v)
            elif v[0] == 'vn':
                assert len(v) == 4
                v = map(float, v[1:4])
                normals.append(v)
            elif v[0] == 'vt':
                assert len(v) == 3
                v = map(float, v[1:3])
                texcoords.append(v)
            elif v[0] == 'mtllib':
                self.mtllib = MaterialLib(v[1])
            elif v[0] == 'f':
                assert len(v) == 4
                for i in range(1, 4):
                    temp = map(int, v[i].split('/'))
                    assert len(temp) == 3, "vertice, normal, texture"
                    obj.vertices.append(vertices[temp[0]-1])
                    obj.texcoords.append(texcoords[temp[1]-1])
                    obj.normals.append(normals[temp[2]-1])

        for obj in self.objects.itervalues():
            obj.convert()

        self.listname = glGenLists(1)
        glNewList(self.listname, GL_COMPILE)
        for obj in self.objects.itervalues():
            obj.draw()
        glEndList()

        print 'object {}, load time: {}'.format(filename, tm.tick())

    def draw(self):
        glCallList(self.listname)
        # for obj in self.objects.itervalues():
        #    obj.draw()

imagenameToTexid = {}

class Material(object):
    def __init__(self, name):
        self.name = name
        self.ambient = (.2, .2, .2)
        self.diffuse = (.8, .8, .8)
        self.specular = (.2, .2, .2)
        self.shininess = 10.
        self.alpha = 1.
        self.texid = 0

    def convert(self):
        self.ambient = utils.convert_ctypes(self.ambient, ctypes.c_float, (3,))
        self.diffuse = utils.convert_ctypes(self.diffuse, ctypes.c_float, (3,))
        self.specular = utils.convert_ctypes(self.specular, ctypes.c_float, (3,))

class MaterialLib(object):
    def __init__(self, filename):
        tm = Timer()
        materials = self.materials = {}

        for line in open(os.path.join(baseDir, filename), "r"):
            if line.startswith('#'): continue
            v = line.split()
            if not v: continue
            if v[0] == 'newmtl':
                name = v[1]
                mtl = Material(name)
                materials[name] = mtl
            elif v[0] == 'Ka':
                mtl.ambient = map(float, v[1:4])
            elif v[0] == 'Kd':
                mtl.diffuse = map(float, v[1:4])
            elif v[0] == 'Ks':
                mtl.specular = map(float, v[1:4])
            elif v[0] == 'Ns':
                mtl.shininess = float(v[1])
            elif v[0] == 'd' or v[0] == 'Tr':
                mtl.alpha = float(v[1])
            elif v[0] == 'map_Kd':
                mtl.texid = glGenTextures(1)
                if v[1] in imagenameToTexid: continue
                imagenameToTexid[v[1]] = mtl.texid
                image = pygame.image.load(os.path.join(baseDir, v[1]))
                w, h = image.get_rect().size
                image = pygame.image.tostring(image, 'RGBA', 1)
                glBindTexture(GL_TEXTURE_2D, mtl.texid)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                                GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER,
                                GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S,
                                GL_MIRRORED_REPEAT)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T,
                                GL_MIRRORED_REPEAT)
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h,
                             0, GL_RGBA, GL_UNSIGNED_BYTE, image)

        for material in materials.itervalues():
            material.convert()
        print 'mtllib {}, load time: {}'.format(filename, tm.tick())

    def get(self, name, default=None):
        return self.materials.get(name, default)

if __name__ == '__main__':
    o = Model('robot.obj')
