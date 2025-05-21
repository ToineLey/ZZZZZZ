#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys


class Player: pass


def create(x, y):
    """
    Crée un joueur
    """
    player = {
        'x': x,
        'y': y,
        'color': "\033[32m",  # Couleur verte
        'speed': 1,
        'velocity_y': 0,
        'gravity': 1,  # 1 pour gravité vers le bas, -1 pour gravité vers le haut
        'on_ground': False,
        'jump_power': -3,
        'jump_cooldown': 0
    }
    return player


def set_pos(p, x, y):
    """
    Définit la position du joueur
    """
    p['x'] = x
    p['y'] = y


def get_pos(p):
    """
    Récupère la position du joueur
    """
    return (p['x'], p['y'])


def move_left(p):
    """
    Déplace le joueur à gauche
    """
    p['x'] -= p['speed']
    if p['x'] < 0:
        p['x'] = 0


def move_right(p):
    """
    Déplace le joueur à droite
    """
    p['x'] += p['speed']


def gravity_change(p):
    """
    Effectue un changement de gravité
    """
    # Inverser la gravité
    p['gravity'] *= -1

    # Ajuster la vitesse pour un petit effet de poussée dans la nouvelle direction
    p['velocity_y'] = p['jump_power'] * p['gravity'] * 0.5
    p['on_ground'] = False
    p['jump_cooldown'] = 5  # Éviter les changements multiples trop rapides


def pick_key(data):
    """
    Permet de ramasser la clé
    """

    p = data['player']
    k = data['key']

    # Convertir en entiers pour la comparaison
    px, py = int(p['x']), int(p['y'])
    kx, ky = int(k['x']), int(k['y'])

    # Si le joueur est à proximité de la clé
    if abs(px - kx) <= 1 and abs(py - ky) <= 1 and not data['has_key']:
        data['has_key'] = True
        data['score'] += 100


def set_speed(p, v):
    """
    Définit la vitesse du joueur
    """
    p['speed'] = v


def collide(p, data):
    """
    Gère les collisions avec le niveau
    """

    level = data['levels'][data['level'] - 1]

    # Vérifier la collision dans la direction de la gravité
    test_y = p['y'] + p['gravity']

    if test_collision(p['x'], test_y, level):
        p['on_ground'] = True
        p['velocity_y'] = 0
    else:
        p['on_ground'] = False

    # Vérifier les collisions verticales (en fonction de la gravité)
    if p['velocity_y'] != 0:  # Si en mouvement vertical
        next_y = p['y'] + p['velocity_y']
        if not test_collision(p['x'], next_y, level):
            p['y'] = next_y
        else:
            # Trouver la position valide la plus proche
            if p['velocity_y'] > 0:
                while test_collision(p['x'], p['y'] + 0.1, level) == False and abs(p['y'] - next_y) > 0.1:
                    p['y'] += 0.1
            else:
                while test_collision(p['x'], p['y'] - 0.1, level) == False and abs(p['y'] - next_y) > 0.1:
                    p['y'] -= 0.1
            p['velocity_y'] = 0

    # Vérifier les collisions horizontales APRÈS le mouvement à gauche/droite
    # Cette partie a été ajoutée pour gérer les collisions avec les murs
    if p.get('_last_x', None) is not None:
        # Calculer la direction du mouvement
        dx = p['x'] - p['_last_x']

        if dx != 0:  # Si un mouvement horizontal a eu lieu
            if test_collision(p['x'], p['y'], level):
                # En cas de collision, revenir à l'ancienne position
                p['x'] = p['_last_x']

    # Mémoriser la position actuelle pour le prochain cycle
    p['_last_x'] = p['x']

    # Vérifier les bords de l'écran
    if p['x'] < 0:
        p['x'] = 0
    if p['x'] > data['x_max']:
        p['x'] = data['x_max']
    if p['y'] < 0:
        p['y'] = 0
    if p['y'] > data['y_max'] - 1:
        p['y'] = data['y_max'] - 1


def test_collision(x, y, level):
    """
    Teste s'il y a une collision à la position donnée
    """
    # Convertir en entiers pour indexation
    x_int = int(x)
    y_int = int(y)

    if x_int < 0 or y_int < 0 or y_int >= len(level['grille']) or x_int >= len(level['grille'][y_int]):
        return True

    cell = level['grille'][y_int][x_int]
    # Note: '+' (téléporteur) ne bloque pas le mouvement, donc on ne le traite pas comme une collision
    return cell == '#' or cell == '='


def live(p, data):
    """
    Met à jour l'état du joueur
    """
    # Appliquer la gravité
    if not p['on_ground']:
        p['velocity_y'] += 0.5 * p['gravity']

    # Limiter la vitesse de chute
    max_fall_speed = 2
    if abs(p['velocity_y']) > max_fall_speed:
        p['velocity_y'] = max_fall_speed * (1 if p['velocity_y'] > 0 else -1)

    # Décrémenter le compteur de saut
    if p['jump_cooldown'] > 0:
        p['jump_cooldown'] -= 1

    # Gérer les collisions
    collide(p, data)


def show(p):
    """
    Affiche le joueur
    """
    # Convertir en entiers pour l'affichage
    x = int(p['x'])
    y = int(p['y'])

    # Caractère différent selon la direction de la gravité
    char = '?' if p['gravity'] > 0 else '¿'

    sys.stdout.write(f"\033[{y + 1};{x + 1}H{p['color']}{char}\033[0m")