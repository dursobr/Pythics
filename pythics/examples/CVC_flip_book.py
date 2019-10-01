# -*- coding: utf-8 -*-
#
# Copyright 2016 Brian R. D'Urso
#
# This file is part of Python Instrument Control System, also known as Pythics.
#
# Pythics is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pythics is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pythics.  If not, see <http://www.gnu.org/licenses/>.
#

def run(result, **kwargs):
    result.value = "Hello, world!"
    

column_1_letters = "bcdjfghklmnprstvwBCDJFGHKLMNPRSTVW"
column_2_letters = "aeiouAEIOU"
column_3_letters = "bcdnglmprstxyBCDNGLMPRSTXY"


def initialize(display, **kwargs):
    display.value = column_1_letters[0] + column_2_letters[0] + column_3_letters[0]


def letter_1_previous(display, **kwargs):
    word = display.value
    i = column_1_letters.find(word[0])
    i = (i - 1) % len(column_1_letters)
    word = column_1_letters[i] + word[1:]
    display.value = word


def letter_1_next(display, **kwargs):
    word = display.value
    i = column_1_letters.find(word[0])
    i = (i + 1) % len(column_1_letters)
    word = column_1_letters[i] + word[1:]
    display.value = word


def letter_2_previous(display, **kwargs):
    word = display.value
    i = column_2_letters.find(word[1])
    i = (i - 1) % len(column_2_letters)
    word = word[0] + column_2_letters[i] + word[2]
    display.value = word


def letter_2_next(display, **kwargs):
    word = display.value
    i = column_2_letters.find(word[1])
    i = (i + 1) % len(column_2_letters)
    word = word[0] + column_2_letters[i] + word[2]
    display.value = word


def letter_3_previous(display, **kwargs):
    word = display.value
    i = column_3_letters.find(word[2])
    i = (i - 1) % len(column_3_letters)
    word = word[0:2] + column_3_letters[i]
    display.value = word


def letter_3_next(display, **kwargs):
    word = display.value
    i = column_3_letters.find(word[2])
    i = (i + 1) % len(column_3_letters)
    word = word[0:2] + column_3_letters[i]
    display.value = word
