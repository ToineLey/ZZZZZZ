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
    import Level

    level = data['levels'][data['level'] - 1]

    # Mouvement de patrouille simple
    e['movement_counter'] += e['speed']

    if e['movement_counter'] >= 1:
        e['movement_counter'] -= 1

        # Calculer la nouvelle position potentielle
        new_x = int(e['x'] + e['direction'])
        y_int = int(e['y'])

        # Vérifier s'il y a une collision ou un vide en dessous
        if (new_x < 0 or new_x >= level['width'] or y_int >= level['height'] or
            (y_int < level['height'] and y_int >= 0 and new_x < len(level['grille'][y_int]) and
             level['grille'][y_int][new_x] == '#')):
            # Changer de direction
            e['direction'] *= -1
        else:
            # Vérifier s'il y a un sol sous l'ennemi
            if (y_int + 1 >= level['height'] or
                (y_int + 1 < level['height'] and new_x < len(level['grille'][y_int + 1]) and
                 level['grille'][y_int + 1][new_x] != '#' and
                 level['grille'][y_int + 1][new_x] != '=')):
                # Pas de sol, changer de direction
                e['direction'] *= -1
            else:
                # Déplacer l'ennemi
                e['x'] = new_x


def test_player(e, player):
    """
    Détecte si l'ennemi touche le joueur
    """
    # Convertir en entiers pour la comparaison
    px, py = int(player['x']), int(player['y'])
    ex, ey = int(e['x']), int(e['y'])

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
    # Convertir en entiers pour l'affichage
    x = int(e['x'])
    y = int(e['y'])
    char = 'E'  # Caractère représentant l'ennemi
    sys.stdout.write(f"\033[{y + 1};{x + 1}H{e['color']}{char}\033[0m")