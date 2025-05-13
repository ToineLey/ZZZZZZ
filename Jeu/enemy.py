#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

class Enemy: pass

def create(x, y):
    """
    Crée un ennemi
    """
    enemy = {
        'x': x,
        'y': y,
        'color': "\033[31m",  # Couleur rouge
        'type': 1,  # 1: ennemi de base
        'state': 0,  # 0: état normal
        'direction': 1,  # 1: droite, -1: gauche
        'speed': 0.5,
        'movement_counter': 0
    }
    return enemy

def get_pos(e):
    """
    Récupère les coordonnées de l'ennemi
    """
    return (e['x'], e['y'])

def set_pos(e, x, y):
    """
    Positionne un ennemi
    """
    e['x'] = x
    e['y'] = y
    return e

def move(e, data):
    """
    Déplace l'ennemi
    """
    from level import Level
    
    level = data['levels'][data['level']-1]
    
    # Mouvement de patrouille simple
    e['movement_counter'] += e['speed']
    
    if e['movement_counter'] >= 1:
        e['movement_counter'] -= 1
        
        # Calculer la nouvelle position potentielle
        new_x = e['x'] + e['direction']
        
        # Vérifier s'il y a une collision ou un vide en dessous
        if (new_x < 0 or new_x >= len(level['grille'][0]) or
            level['grille'][e['y']][new_x] == '#' or
            (e['y'] + 1 < len(level['grille']) and level['grille'][e['y'] + 1][new_x] == ' ')):
            # Changer de direction
            e['direction'] *= -1
        else:
            # Déplacer l'ennemi
            e['x'] = new_x

def test_player(e, player):
    """
    Détecte si l'ennemi touche le joueur
    """
    from player import get_pos
    
    px, py = get_pos(player)
    ex, ey = get_pos(e)
    
    # Si l'ennemi touche le joueur
    return abs(px - ex) < 1 and abs(py - ey) < 1

def set_speed(e, v):
    """
    Définit la vitesse de l'ennemi
    """
    e['speed'] = v

def live(e, data):
    """
    Met à jour l'état de l'ennemi
    """
    move(e, data)

def show(e):
    """
    Affiche l'ennemi
    """
    char = 'E'  # Caractère représentant l'ennemi
    sys.stdout.write(f"\033[{e['y']+1};{e['x']+1}H{e['color']}{char}\033[0m")
