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
            "#                                  #\n",
            "#                                  #\n",
            "#    @                K            #\n",
            "#################     ##############\n",
            "#                                  #\n",
            "#                                  #\n",
            "#                                  #\n",
            "#                   E              #\n",
            "########    #######################\n",
            "#                                  #\n",
            "#                                  #\n",
            "#                                  #\n",
            "#                                  #\n",
            "#                        S         #\n",
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
    if next_level:
        data['level'] += 1
        data['has_key'] = False
        data['score'] += 500

        # Réinitialiser la position du joueur
        from Player import set_pos
        set_pos(data['player'], 5, 5)


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
            elif char == 'E':
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