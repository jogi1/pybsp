#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Copyright (C) 2010 Jürgen Legler

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  

See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""

import sys
import array
import re
import os
from stat import *
import getopt
import struct

import cairo
import Image

from OpenGL.GL import *
OpenGL.ERROR_CHECKING = False
from OpenGL.GL.EXT.framebuffer_object import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from cgkit.cgtypes import vec3

only_list = 0

def usage():
	print "pywad.py pakfile \"extraction regexp\""
	print "-l for listing"
	sys.exit(2)


try:
	opts, args = getopt.getopt(sys.argv[1:], 'hl')
except getopt.GetoptError, err:
	print str(err)
	usage()


for o, a in opts:
	if o == "-h":
		usage()
	elif o == "-l":
		list_only = 1
		print "listing files only"
	else :
		print "unknown option %s" % o

if len(args) < 1:
	usage()

ifile = args[0]

class BSP_File:
    def __init__(self, filename):
        self.filename = filename;
        self.invalid = False
        self.header = {} 
        try:
            self.file = open(filename, 'rb')
        except:
            self.invalid = True
            self.error = "could not open file \"%s\"" % filename
            return None
        self.filesize = os.stat(self.filename)[ST_SIZE]
        self.read_header()
        self.read_vertices()
        self.read_edges()
        self.read_ledges()
        self.read_faces()
        self.read_planes()
        self.read_leaves()
        self.read_models()
        self.read_nodes()
        self.get_max()


    def read_long(self):
        return array.array('I', self.file.read(4))[0]

    def read_header(self):
        self.header['version'] = self.read_long()
        self.header['entities'] = {}
        self.header['entities']['offset'] = self.read_long()
        self.header['entities']['size'] = self.read_long()
        self.header['planes'] = {}
        self.header['planes']['offset'] = self.read_long()
        self.header['planes']['size'] = self.read_long()
        self.header['miptex'] = {}
        self.header['miptex']['offset'] = self.read_long()
        self.header['miptex']['size'] = self.read_long()
        self.header['vertices'] = {}
        self.header['vertices']['offset'] = self.read_long()
        self.header['vertices']['size'] = self.read_long()
        self.header['vislist'] = {}
        self.header['vislist']['offset'] = self.read_long()
        self.header['vislist']['size'] = self.read_long()
        self.header['nodes'] = {}
        self.header['nodes']['offset'] = self.read_long()
        self.header['nodes']['size'] = self.read_long()
        self.header['texinfo'] = {}
        self.header['texinfo']['offset'] = self.read_long()
        self.header['texinfo']['size'] = self.read_long()
        self.header['faces'] = {}
        self.header['faces']['offset'] = self.read_long()
        self.header['faces']['size'] = self.read_long()
        self.header['lightmaps'] = {}
        self.header['lightmaps']['offset'] = self.read_long()
        self.header['lightmaps']['size'] = self.read_long()
        self.header['clipnodes'] = {}
        self.header['clipnodes']['offset'] = self.read_long()
        self.header['clipnodes']['size'] = self.read_long()
        self.header['leaves'] = {}
        self.header['leaves']['offset'] = self.read_long()
        self.header['leaves']['size'] = self.read_long()
        self.header['lface'] = {}
        self.header['lface']['offset'] = self.read_long()
        self.header['lface']['size'] = self.read_long()
        self.header['edges'] = {}
        self.header['edges']['offset'] = self.read_long()
        self.header['edges']['size'] = self.read_long()
        self.header['ledges'] = {}
        self.header['ledges']['offset'] = self.read_long()
        self.header['ledges']['size'] = self.read_long()
        self.header['models'] = {}
        self.header['models']['offset'] = self.read_long()
        self.header['models']['size'] = self.read_long()


        s = "fff"
        self.header['vertices']['struct_size'] = struct.calcsize(s)
        self.header['vertices']['num'] = self.header['vertices']['size'] / self.header['vertices']['struct_size']
        self.header['vertices']['struct'] = s

        s = "HH"
        self.header['edges']['struct'] = s
        self.header['edges']['struct_size'] = struct.calcsize(s)
        self.header['edges']['num'] = self.header['edges']['size'] / self.header['edges']['struct_size'];

        s = "hhihhBBBBI"
        self.header['faces']['struct'] = s
        self.header['faces']['struct_size'] = struct.calcsize(s)
        self.header['faces']['num'] = self.header['faces']['size'] / self.header['faces']['struct_size'];

        self.header['ledges']['struct'] = "i"
        self.header['ledges']['struct_size'] = struct.calcsize("i")
        self.header['ledges']['num'] = self.header['ledges']['size'] / self.header['ledges']['struct_size']

        s = "ffffI"
        self.header['planes']['struct'] = s
        self.header['planes']['struct_size'] = struct.calcsize(s)
        self.header['planes']['num'] = self.header['planes']['size'] / self.header['planes']['struct_size']

        s = "llhhhhhhHHcccc"
        self.header['leaves']['struct'] = s
        self.header['leaves']['struct_size'] = struct.calcsize(s)
        self.header['leaves']['num'] = self.header['leaves']['size'] / self.header['leaves']['struct_size']

        s = "fffffffffiiiiiii"
        self.header['models']['struct'] = s
        self.header['models']['struct_size'] = struct.calcsize(s)
        self.header['models']['num'] = self.header['models']['size'] / self.header['models']['struct_size']

        s = "lHHHHHHHHHH"
        self.header['nodes']['struct'] = s
        self.header['nodes']['struct_size'] = struct.calcsize(s)
        self.header['nodes']['num'] = self.header['nodes']['size'] / self.header['nodes']['struct_size']

    def print_header_info(self):
        print "Header Info:"
        for k in self.header:
            if type(self.header[k]) is dict:
                print " %s:" % k
                for i in self.header[k]:
                    print i + ": " +  self.header[k][i]
            else:
                print " " +  k + ": " + "%i" % self.header[k]

    def print_specific_header_info(self, key):
        if type(self.header[key]) is dict:
            print " %s:" % key
            for i in self.header[key]:
                print "  " + i + ": " +  str(self.header[key][i])
        else:
            print " " +  key + ": " + "%i" % self.header[key]

    def read_vertices(self):
        self.file.seek(self.header['vertices']['offset'], os.SEEK_SET)
        limit = self.header['vertices']['num']
        size = self.header['vertices']['struct_size']
        struct_definition = self.header['vertices']['struct']
        self.vertices = []
        for i in range(limit):
            v = struct.unpack(struct_definition, self.file.read(size))
            self.vertices.append((v[0] , v[1] , v[2] ))

    def print_vertices(self):
        limit = self.header['vertices']['num']
        for i in range(limit):
            print "%6i: " % i
            print "       x: " + str(self.vertices[i][0]) + " - y: " + str(self.vertices[i][1]) + " - z: " + str(self.vertices[i][2])


    def read_edges(self):
        self.file.seek(self.header['edges']['offset'], os.SEEK_SET)
        limit = self.header['edges']['num']
        size = self.header['edges']['struct_size']
        struct_definition = self.header['edges']['struct']
        self.edges = []
        for i in range(limit):
            self.edges.append(struct.unpack(struct_definition, self.file.read(size)))


    def print_edges(self):
        limit = self.header['edges']['num']
        for i in range(limit):
            print "%6i: " % i
            print "     0: " + str(self.edges[i][0]) + " - 1: " + str(self.edges[i][1]) 

    def read_ledges(self):
        self.file.seek(self.header['ledges']['offset'], os.SEEK_SET)
        limit = self.header['ledges']['num']
        size = self.header['ledges']['struct_size']
        struct_definition = self.header['ledges']['struct']
        self.ledges = []
        for i in range(limit):
            data = self.file.read(size)
            self.ledges.append(struct.unpack(struct_definition, data))

    def print_ledges(self):
        limit = self.header['ledges']['num']
        for i in range(limit):
            print str(i) + ": " + str(self.ledges[i])

    def read_faces(self):
        self.file.seek(self.header['faces']['offset'], os.SEEK_SET)
        limit = self.header['faces']['num']
        size = self.header['faces']['struct_size']
        struct_definition = self.header['faces']['struct']
        self.faces = []
        for i in range(limit):
            data = struct.unpack(struct_definition, self.file.read(size))
            face = {}
            face['plane_id'] = data[0]
            face['side'] = data[1]
            face['ledge_id'] = data[2]
            face['ledge_num'] = data[3]
            face['texinfo_id'] = data[4]
            face['typelight'] = data[5]
            face['baselight'] = data[6]
            face['light'] = []
            face['light'].append(data[7])
            face['light'].append(data[8])
            face['lightmap'] = data[9]
            face['dont_draw'] = False
            self.faces.append(face)

    def print_faces(self):
        limit = self.header['faces']['num']
        for i in range(limit):
            print "%6i:" % i
            for k in self.faces[i]:
                print " " + k + ": " + str(self.faces[i][k])

    def read_planes(self):
        self.file.seek(self.header['planes']['offset'], os.SEEK_SET)
        limit = self.header['planes']['num']
        size = self.header['planes']['struct_size']
        struct_definition = self.header['planes']['struct']
        self.planes = []
        for i in range(limit):
            data = struct.unpack(struct_definition, self.file.read(size))
            plane = {}
            plane['normal'] = (data[0], data[1], data[2])
            plane['dist'] = data[3]
            plane['type'] = data[4]
            self.planes.append(plane)

    def read_models(self):
        self.file.seek(self.header['models']['offset'], os.SEEK_SET)
        limit = self.header['models']['num']
        size = self.header['models']['struct_size']
        struct_definition = self.header['models']['struct']
        self.models = []
        for i in range(limit):
            data = struct.unpack(struct_definition, self.file.read(size))
            model = {}
            model['bounding_box'] = (vec3(data[0], data[1], data[2]), vec3(data[3], data[4], data[5]))
            model['origin'] = vec3(data[6], data[7], data[8])
            model['node_id0'] = data[9]
            model['node_id1'] = data[10]
            model['node_id2'] = data[11]
            model['node_id3'] = data[12]
            model['numleaves'] = data[13]
            model['face_id'] = data[14]
            model['face_num'] = data[15]
            self.models.append(model)

    def read_leaves(self):
        self.file.seek(self.header['leaves']['offset'], os.SEEK_SET)
        limit = self.header['leaves']['num']
        size = self.header['leaves']['struct_size']
        struct_definition = self.header['leaves']['struct']
        self.leaves = []
        for i in range(limit):
            data = struct.unpack(struct_definition, self.file.read(size))
            leaf = {}
            leaf['type'] = data[0]
            leaf['vistlist'] = data[1]
            #2
            #3
            #4
            #5
            #6
            #7
            leaf['face_id'] = data[8]
            leaf['face_num'] = data[9]
            #and the rest too
            self.leaves.append(leaf)

    def read_nodes(self):
        self.file.seek(self.header['nodes']['offset'], os.SEEK_SET)
        limit = self.header['nodes']['num']
        size = self.header['nodes']['struct_size']
        struct_definition = self.header['nodes']['struct']
        self.nodes = []
        for i in range(limit):
            data = struct.unpack(struct_definition, self.file.read(size))
            node = {}
            node['plane_id'] = data[0]
            node['front'] = data[1]
            node['back'] = data[2]
            node['bounding_box'] = ((data[3], data[4], data[5]), (data[6], data[7], data[8]))
            node['face_id'] = data[9]
            node['face_num'] = data[10]
            self.nodes.append(node)



    def get_max(self):
        limit = self.header['vertices']['num']
        self.minimum = [0, 0, 0]
        self.maximum = [0, 0, 0]
        for i in range(limit):
            for x in range(3):
                if self.vertices[i][x] < self.minimum[x]:
                    self.minimum[x] = self.vertices[i][x]
                if self.vertices[i][x] > self.maximum[x]:
                    self.maximum[x] = self.vertices[i][x]



def check_normal(n):
    n.normalize()
    return True
    if (n[2] == 1):
        return True

    if (n[0] >= -1 and n[0] <= 1):
        if (n[1] >= -1 and n[1] <= 1):
            if (n[2] >= -0.999999 and n[2] <= -0.000001):
                return True
            if (n[2] >= 0.000001 and n[2] <= 0.999999):
                return True

    return False








f = BSP_File(ifile)

if f.invalid == True:
    print f.error
    sys.exit()

print "Filesize: %i" % f.filesize
print f.header['models']['num']

print f.models[0]['bounding_box']
print f.models[0]['origin']


rs = vec3(f.models[0]['bounding_box'][1]) - vec3(f.models[0]['bounding_box'][0])
rs = rs + f.models[0]['origin']
b = f.models[0]['bounding_box'][0]
os = vec3(-b[0], -b[1], -b[2])

print "rs: " + str(rs)
print os

m_max = vec3(-9999, -9999, -9999)
m_min = vec3(9999, 9999, 9999)

min_f = f.models[0]['face_id']
max_f = f.models[0]['face_num'] + min_f
for i in range(min_f, max_f):
    n = vec3(f.planes[f.faces[i]['plane_id']]['normal'])
    if (check_normal(n) and f.faces[i]['side'] == 0):
        y = f.faces[i]['ledge_id']
        for x in range(f.faces[i]['ledge_num'] - 1):
            ledge = abs(f.ledges[x + y][0])
            if (f.ledges[x+y][0] > 0):
                v1 = vec3(f.vertices[f.edges[ledge][0]])
                v2 = vec3(f.vertices[f.edges[ledge][1]])
            else:
                v1 = vec3(f.vertices[f.edges[ledge][1]])
                v2 = vec3(f.vertices[f.edges[ledge][0]])

            for t in range(0, 3):
                if (v1[t] > m_max[t]):
                    m_max[t] = v1[t]
                if (v1[t] < m_min[t]):
                    m_min[t] = v1[t]
                if (v2[t] > m_max[t]):
                    m_max[t] = v2[t]
                if (v2[t] < m_min[t]):
                    m_min[t] = v2[t]

print "max: " + str(m_max)
print "min: " + str(m_min)

os = m_max - m_min

width = os[0]
height = os[1]
scale = os[2]

if width > height:
    size = width
else:
    size = height

size = int(size)

print "width: " + str(width)
print "height: " + str(height)

glutInit(("none"))
glutCreateWindow("test")

# create FBO and bind it (that is, use offscreen render target)
fb = glGenFramebuffersEXT(1)
glBindFramebufferEXT(GL_FRAMEBUFFER_EXT,fb)

# create texture
tex = glGenTextures(1)
glBindTexture(GL_TEXTURE_RECTANGLE_ARB,tex)
glMatrixMode(GL_PROJECTION)
glLoadIdentity()
glViewport(0,0,int(width),int(height))
glOrtho(0,int(width), int(height), 0, -99999, 99999)
glMatrixMode(GL_MODELVIEW)
glLoadIdentity()

# set texture parameters
glTexParameteri(GL_TEXTURE_RECTANGLE_ARB, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
glTexParameteri(GL_TEXTURE_RECTANGLE_ARB, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
glTexParameteri(GL_TEXTURE_RECTANGLE_ARB, GL_TEXTURE_WRAP_S, GL_CLAMP)
glTexParameteri(GL_TEXTURE_RECTANGLE_ARB, GL_TEXTURE_WRAP_T, GL_CLAMP)

# define texture with floating point format
glTexImage2D(GL_TEXTURE_RECTANGLE_ARB,0,GL_RGBA, size,size,0,GL_RGBA,GL_UNSIGNED_BYTE,None)

# attach texture
glFramebufferTexture2DEXT(GL_FRAMEBUFFER_EXT, GL_COLOR_ATTACHMENT0_EXT, GL_TEXTURE_RECTANGLE_ARB,tex,0)
# and read back

glClearColor(0, 0, 0, 0)
glClearDepth(0)
glClear(GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT)
glEnable(GL_BLEND)
glEnable(GL_DEPTH_TEST)
glEnable(GL_ALPHA_TEST)
glDepthFunc(GL_GEQUAL)
glCullFace(GL_FRONT)

glDrawBuffer(GL_COLOR_ATTACHMENT0_EXT)
glReadBuffer(GL_COLOR_ATTACHMENT0_EXT)

glBindTexture(GL_TEXTURE_RECTANGLE_ARB, 0)
glDisable(GL_TEXTURE_2D)

glColor4f(1, 1, 1, 1)

glTranslatef(-m_min[0], -m_min[1], 0)

glLineWidth(4)
for i in range(f.header['edges']['num']-1):
    v1 = vec3(f.vertices[f.edges[i][0]])
    v2 = vec3(f.vertices[f.edges[i][1]])
    a1 = (v1[2] + f.minimum[2])/scale
    a2 = (v2[2] + f.minimum[2])/scale
    a2 = 0;
    a1 = 0;
    glBegin(GL_LINES)
    glColor4f(a1, a1, a1, 1)
    glVertex3f(v1[0], v1[1], v1[2])
    glColor4f(a2, a2, a2, 1)
    glVertex3f(v2[0], v2[1], v2[2])
    glEnd()

"""
glPointSize(5)
glBegin(GL_POINTS)
for i in range(f.header['vertices']['num']):
    v1 = vec3(f.vertices[i])
    a1 = (v1[2] + f.minimum[2])/scale
    dv = v1 + os
    print a1
    print i
    print dv
    glColor4f(a1, a1, a1, 1)
    glVertex4f(dv[0], dv[1], dv[2], a1)
glEnd()
"""

"""
min_l = 0
max_l = f.header['leaves']['num']
for i in range(0, max_l-1):
    min_f = f.leaves[i]['face_id']
    max_f = f.leaves[i]['face_num'] + min_f
    for l in range(min_f, max_f):
        print str(l) + ": " + str(f.faces[l])
"""


min_f = f.models[0]['face_id']
max_f = f.models[0]['face_num'] + min_f

print "size: " + str(size)

m_min = vec3(0, 0, 0)
m_max = vec3(0, 0, 0)

#if 0 :
for i in range(min_f, max_f):
    n = vec3(f.planes[f.faces[i]['plane_id']]['normal'])
    if (check_normal(n) and f.faces[i]['side'] == 0):
        y = f.faces[i]['ledge_id']
        glBegin(GL_POLYGON)
        for x in range(f.faces[i]['ledge_num'] - 1):
            ledge = abs(f.ledges[x + y][0])
            if (f.ledges[x+y][0] > 0):
                v1 = vec3(f.vertices[f.edges[ledge][0]])
                v2 = vec3(f.vertices[f.edges[ledge][1]])
            else:
                v1 = vec3(f.vertices[f.edges[ledge][1]])
                v2 = vec3(f.vertices[f.edges[ledge][0]])

            for t in range(0, 3):
                if (v1[t] > m_max[t]):
                    m_max[t] = v1[t]
                if (v1[t] < m_min[t]):
                    m_min[t] = v1[t]
                if (v2[t] > m_max[t]):
                    m_max[t] = v2[t]
                if (v2[t] < m_min[t]):
                    m_min[t] = v2[t]
            a1 = (v1[2])/scale
            a2 = (v2[2])/scale
            glColor4f(a1, a1, a1, 1)
            glVertex3f(v1[0], v1[1], v1[2])
            glColor4f(a2, a2, a2, 1)
            glVertex3f(v2[0], v2[1], v2[2])
        glEnd()

glFlush();

print m_max
print m_min

data = glReadPixels(0, 0, width, height,GL_RGBA,GL_UNSIGNED_BYTE)
image = Image.fromstring(mode="RGBA", size=(int(width), int(height)), data=data)
image.transpose(Image.FLIP_LEFT_RIGHT)
image.transpose(Image.FLIP_TOP_BOTTOM)
outputfile = ifile[:ifile.find(".")]+".png"
print outputfile 
image.save(outputfile, "PNG")
    

print "test"


sys.exit()



for i in range(f.header['faces']['num'] - 1):
    print "%5i:" % i
    print f.planes[f.faces[i]['plane_id']]['normal']
    y = f.faces[i]['ledge_id']
    print "ledge id: " + str(y)
    print "ledges: " + str(f.ledges[y])
    print "ledges: " + str(abs(f.ledges[y][0]))
    print f.header['edges']['num']
    for x in range(f.faces[i]['ledge_num'] - 1):
        ledge = abs(f.ledges[y][0]) + x
        if (f.ledges[y][0] > 0):
            v1 = f.vertices[f.edges[ledge][0]]
            v2 = f.vertices[f.edges[ledge][1]]
        else:
            v1 = f.vertices[f.edges[ledge][1]]
            v2 = f.vertices[f.edges[ledge][0]]
        print v1
        print v2
        if (x == 0):
            ctx.move_to(os[0] + v1[0], os[1] + v1[1])
        else:
            ctx.line_to(os[0] + v2[0], os[1] + v1[1])

    ctx.close_path()
    print "-----------------"
    ctx.stroke()


surface.write_to_png("test.png")
sys.exit()


surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(width), int(height))
ctx = cairo.Context (surface)

a1 = 1
a2 = 1

os = []
os.append(f.minimum[0] * -1)
os.append(f.minimum[1] * -1)
os.append(f.minimum[2] * -1)



for i in range(f.header['edges']['num']):
    v1 = f.vertices[f.edges[i][0]]
    v2 = f.vertices[f.edges[i][1]]
    ctx.move_to(os[0] + v1[0], os[1] + v1[1])
    ctx.line_to(os[0] + v2[0], os[1] + v2[1])
    a1 = (v1[2] + f.minimum[2])/scale
    a2 = (v2[2] + f.minimum[2])/scale
    linear = cairo.LinearGradient(os[0] + v1[0], os[1] + v1[1], os[0] + v2[0], os[1] + v2[1]);
    linear.add_color_stop_rgb(0, a1, a1, a1)
    linear.add_color_stop_rgb(1, a2, a2, a2)
    ctx.close_path()
    ctx.stroke()

surface.write_to_png("test.png")


sys.exit()

print "opening %s" % ifile
bsp_file = open(ifile, 'rb')
print "filesize: %i" % len(bsp_file.read())
bsp_file.seek(0,0)
version = array.array('I', bsp_file.read(4))[0]
print "header info:"
print " version: %i" % version
entities_offset = array.array('I', bsp_file.read(4))[0]
entities_size = array.array('I', bsp_file.read(4))[0]
print " entities:"
print "  offset: %i" % entities_offset
print "  Size: %i" % entities_size
planes_offset = array.array('I', bsp_file.read(4))[0]
planes_size = array.array('I', bsp_file.read(4))[0]
print " planes:"
print "  offset: %i" % planes_offset
print "  Size: %i" % planes_size

miptex_offset = array.array('I', bsp_file.read(4))[0]
miptex_size = array.array('I', bsp_file.read(4))[0]
print lump_planes
lump_textures_fofs = array.array('I', bsp_file.read(4))[0]
lump_textures_flen = array.array('I', bsp_file.read(4))[0]
print "tfof  : %i" % lump_textures_fofs
print "tflen : %i" % lump_textures_flen


bsp_file.seek(lump_textures_fofs,0)
gpos = bsp_file.tell()

offset_base = bsp_file.tell()
miptx_lump_c = array.array('I', bsp_file.read(4))[0]
miptx_lump = {}

print "mptl  : %i" % miptx_lump_c


index_base = bsp_file.tell()

textures = {}

for i in range(0, miptx_lump_c):
#for i in range(0, miptx_lump_c):
	textures[i] = {} 
	bsp_file.seek(index_base +  i * 4 ,0)
	if i == 2:
		bsp_file.seek(4,1)
	offset = struct.unpack('I', bsp_file.read(4))[0]
	print offset
	#bsp_file.seek(orgpos + i * 4 * 4)
	bsp_file.seek(offset_base + offset)
	print "location %i" % bsp_file.tell()


	textures[i]["name"] = ""
	for x in range(0, 16):
		s = bsp_file.read(1)
		if s:
			if ord(s) < 128 and ord(s) > 32 and s != '/':
				if ord(s) != 42:
					textures[i]["name"] += s;

	textures[i]["name"] = textures[i]["name"][:-4]


	print textures[i]["name"]

	textures[i]["width"] = array.array('I', bsp_file.read(4))[0]
	textures[i]["height"] = array.array('I', bsp_file.read(4))[0]
	print "%i: %s %i %i" % (i,textures[i]["name"], textures[i]["width"], textures[i]["height"])
	local_offset = bsp_file.tell()
	ct_offset=  array.array('I', bsp_file.read(4))[0]
	bsp_file.seek(local_offset + ct_offset, 0)
	try:
		os.mkdir("textures")
	except OSError:
		print "directory already existed"
	name = "textures/" + textures[i]["name"] + ".bmp"
	f = open(name, 'wb')
	f.write("BM")
	#f.write("%d" % 0)
	#f.write("%d" % 0)
	#f.write("%d" % 1076)
	f.write(struct.pack('l', 0))
	f.write(struct.pack('i', 0))
	f.write(struct.pack('l', 1078))
	print f.tell()

	f.write(struct.pack('l', 40))
	f.write(struct.pack('l', textures[i]["width"]))
	f.write(struct.pack('l', textures[i]["height"]))
	f.write(struct.pack('b', 1))
	f.write(struct.pack('b', 0))
	f.write(struct.pack('b', 8))
	f.write(struct.pack('b', 0))
	f.write(struct.pack('l', 0))
	f.write(struct.pack('l', 0))
	f.write(struct.pack('l', 3780))
	f.write(struct.pack('l', 3780))
	f.write(struct.pack('l', 0))
	f.write(struct.pack('l', 0))
	print f.tell()

	pal = open("palette.lmp", 'rb')
	for t in range(0, 256):
		#f.write(pal.read(3))
		r = pal.read(1)
		g = pal.read(1)
		b = pal.read(1)
		f.write(b)
		f.write(g)
		f.write(r)
		f.write('\0')
	print f.tell()

	pal.close()

	

	f.write(bsp_file.read(textures[i]["width"] * textures[i]["height"]))
	f.close()






#bsp_file.fseek()

bsp_file.close()
