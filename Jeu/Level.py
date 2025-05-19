#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys


class Level: pass


def create(filename, offset):
    """
    Charge un niveau depuis un fichier
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        # Si le fichier n'existe pas, créer un niveau par défaut
        lines = [
            "####################################\n",
            "#                    K             #\n",
            "#                                  #\n",
            "#                                  #\n",
            "#                                  #\n",
            "#                                  #\n",
            "#                                  #\n",
            "#                                  #\n",
            "#                                  #\n",
            "#                                  #\n",
            "#                                  #\n",
            "#                                  #\n",
            "#                                  #\n",
            "#                                  #\n",
            "#     @                         S  #\n",
            "####################################\n"
        ]

    # Nettoyer les lignes
    lines = [line.rstrip('\n') for line in lines]

    # Assurons-nous que toutes les lignes ont la même longueur
    max_length = max(len(line) for line in lines)
    lines = [line.ljust(max_length) for line in lines]

    level = {
        'grille': lines,
        'width': max_length,
        'height': len(lines),
        'offset': offset
    }

    return level


def check_exit(l, player, data):
    """
    Vérifie si le joueur atteint la sortie
    """
    x, y = int(player['x']), int(player['y'])

    # S'assurer que les coordonnées sont valides
    if y < 0 or y >= len(l['grille']) or x < 0 or x >= len(l['grille'][y]):
        return False

    # Vérifier si la position contient la sortie (et si le joueur a la clé)
    return l['grille'][y][x] == 'S' and data['has_key']


def change(data, next_level):
    """
    Change de niveau si le joueur atteint la sortie
    """
    import Enemy
    import Player
    import Key

    if next_level:
        data['level'] += 1
        data['has_key'] = False
        data['score'] += 500

        current_level = data['levels'][data['level'] - 1]
        player_pos = None
        key_pos = None
        enemy_positions = []
        inverted_enemy_positions = []  # Pour les ennemis de type 2 (gravité inversée)

        if data['enemies'] != []:
            data['enemies'].clear()

        for y, line in enumerate(current_level['grille']):
            for x, char in enumerate(line):
                if char == '@':
                    player_pos = (x, y)
                elif char == 'K':
                    key_pos = (x, y)
                elif char == 'E':
                    enemy_positions.append((x, y))
                elif char == 'F':  # Nouvel ennemi de type 2 (gravité inversée)
                    inverted_enemy_positions.append((x, y))

        # Créer le joueur à la position extraite du niveau
        if player_pos:
            data['player'] = Player.create(player_pos[0], player_pos[1])
        else:
            data['player'] = Player.create(5, 5)  # Position par défaut

        # Créer la clé à la position extraite du niveau
        if key_pos:
            data['key'] = Key.create(key_pos[0], key_pos[1])
        else:
            data['key'] = Key.create(20, 20)  # Position par défaut

        # Créer les ennemis aux positions extraites du niveau
        if enemy_positions:
            for pos in enemy_positions:
                data['enemies'].append(Enemy.create(pos[0], pos[1], 1))  # Type 1: ennemi standard

        # Créer les ennemis de type 2 (gravité inversée)
        if inverted_enemy_positions:
            for pos in inverted_enemy_positions:
                data['enemies'].append(Enemy.create(pos[0], pos[1], 2))  # Type 2: ennemi gravité inversée


def show(l):
    """
    Affiche le niveau
    """
    for y, line in enumerate(l['grille']):
        sys.stdout.write(f"\033[{y + 1};1H")
        for x, char in enumerate(line):
            if char == '#':
                sys.stdout.write("\033[47m \033[0m")  # Bloc blanc
            elif char == 'S':
                sys.stdout.write("\033[36mS\033[0m")  # Sortie en cyan
            elif char == '=':
                sys.stdout.write("\033[37m=\033[0m")  # Plateforme en gris
            elif char == 'E' or char == 'F':
                # Ne pas afficher les ennemis ici, ils sont gérés par Enemy.show()
                sys.stdout.write(" ")
            elif char == '@':
                # Ne pas afficher le joueur ici, il est géré par Player.show()
                sys.stdout.write(" ")
            elif char == 'K':
                # Ne pas afficher la clé ici, elle est gérée par Key.show()
                sys.stdout.write(" ")
            else:
                sys.stdout.write(" ")  # Espace vide