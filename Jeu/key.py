#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

class Key: pass

def create(x, y):
    """
    Crée une clé
    """
    key = {
        'x': x,
        'y': y,
        'color': "\033[33m",  # Couleur jaune
    }
    return key

def get_pos(k):
    """
    Récupère les coordonnées de la clé
    """
    return (k['x'], k['y'])

def set_pos(k, x, y):
    """
    Positionne une clé
    """
    k['x'] = x
    k['y'] = y
    return k

def show(k):
    """
    Affiche la clé
    """
    sys.stdout.write(f"\033[{k['y']+1};{k['x']+1}H{k['color']}K\033[0m")
