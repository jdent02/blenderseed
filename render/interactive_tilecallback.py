#
# This source file is part of appleseed.
# Visit http://appleseedhq.net/ for additional information and resources.
#
# This software is released under the MIT license.
#
# Copyright (c) 2019 Jonathan Dent, The appleseedhq Organization.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import bpy
import bgl

import numpy
import time

import appleseed as asr
from ..logger import get_logger
from ..utils import util

logger = get_logger()


class AsFrameBuffer(object):
    def __init__(self, engine, depsgraph, resolution):
        self.__resolution = resolution

        buffer_size = self.__resolution[0] * self.__resolution[1] * 4
        self.__as_ogl_image_buffer = bgl.Buffer(bgl.GL_FLOAT, [buffer_size])

        self.__ogl_vertex_buffer = None
        self.__ogl_vertex_array = None
        self.__ogl_texture = None
        self.__ogl_texid = None
        self.__ogl_shader = None

        self.__create_buffer(engine, depsgraph.scene_eval)
        
    def __create_buffer(self, engine, scene):
        self.__ogl_texture = bgl.Buffer(bgl.GL_INT, 1)
        bgl.glGenTextures(1, self.__ogl_texture)
        self.__ogl_texid = self.__ogl_texture[0]

        self.__ogl_shader = bgl.Buffer(bgl.GL_INT, 1)

        self.__ogl_vertex_array = bgl.Buffer(bgl.GL_INT, 1)
        bgl.glGenVertexArrays(1, self.__ogl_vertex_array)
        bgl.glBindVertexArray(self.__ogl_vertex_array[0])

        texturecoord_location = bgl.glGetAttribLocation(self.__ogl_shader[0], "texCoord")
        position_location = bgl.glGetAttribLocation(self.__ogl_shader[0], "pos")

        bgl.glEnableVertexAttribArray(texturecoord_location)
        bgl.glEnableVertexAttribArray(position_location)

        position = [1, 1,
                    self.__resolution[0] + 1, 1,
                    self.__resolution[0] + 1, self.__resolution[1] + 1,
                    1, self.__resolution[1] + 1]
        position = bgl.Buffer(bgl.GL_FLOAT, len(position), position)
        texcoord = [0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0]
        texcoord = bgl.Buffer(bgl.GL_FLOAT, len(texcoord), texcoord)

        self.__ogl_vertex_buffer = bgl.Buffer(bgl.GL_INT, 2)

        bgl.glGenBuffers(2, self.__ogl_vertex_buffer)
        bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.__ogl_vertex_buffer[0])
        bgl.glBufferData(bgl.GL_ARRAY_BUFFER, 32, position, bgl.GL_STATIC_DRAW)
        bgl.glVertexAttribPointer(position_location, 2, bgl.GL_FLOAT, bgl.GL_FALSE, 0, None)

        bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, self.__ogl_vertex_buffer[1])
        bgl.glBufferData(bgl.GL_ARRAY_BUFFER, 32, texcoord, bgl.GL_STATIC_DRAW)
        bgl.glVertexAttribPointer(texturecoord_location, 2, bgl.GL_FLOAT, bgl.GL_FALSE, 0, None)

        bgl.glBindBuffer(bgl.GL_ARRAY_BUFFER, 0)
        bgl.glBindVertexArray(0)

    def update(self, frame):
        pixels = list()
        buffer_size = self.__resolution[0] * self.__resolution[1] * 4
        self.__as_ogl_image_buffer = bgl.Buffer(bgl.GL_FLOAT, [buffer_size], pixels)

    def draw(self):
        pass


class InteractiveTileCallback(asr.ITileCallback):
    def __init__(self):
        self.__is_updated_buffer = False
        self.__buffer = None
        self.__viewport_resolution = list()

    def on_tiled_frame_begin(self, frame):
        pass

    def on_tiled_frame_end(self, frame):
        pass

    def on_tile_begin(self, frame, tile_x, tile_y, thread_index, thread_count):
        pass

    def on_tile_end(self, frame, tile_x, tile_y):
        pass

    def on_progressive_frame_update(self, frame, time, samples, samples_per_pixel, samples_per_second):
        self.__buffer.update(frame)
        self.__is_updated_buffer = True

    def draw_pixels(self, engine, context, depsgraph):
        resolution = util.get_viewport_resolution(depsgraph, context)

        if self.__buffer is None or resolution != self.__viewport_resolution:
            self.__buffer = AsFrameBuffer(engine, depsgraph, resolution)

        while not self.__is_updated_buffer:
            time.sleep(0.1)

        engine.tag_redraw()
        self.__buffer.draw()
        