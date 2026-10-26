"""D159 (2): each measure clamped to its own fold's training range."""
from __future__ import annotations
import numpy as np

def training_range(weather, train):
    raise NotImplementedError

def clamp(weather, low, high):
    raise NotImplementedError

def clamp_to_training(weather, train):
    raise NotImplementedError
