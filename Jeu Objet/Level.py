#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from Player import Player
from Key import Key
from Enemy import Enemy


class Level:
    def __init__(self, filename, offset):
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

        self.grille = lines
        self.width = max_length
        self.height = len(lines)
        self.offset = offset

    def check_exit(self, player, game_data):
        """
        Vérifie si le joueur atteint la sortie
        """
        x, y = int(player.x), int(player.y)

        # S'assurer que les coordonnées sont valides
        if y < 0 or y >= len(self.grille) or x < 0 or x >= len(self.grille[y]):
            return False

        # Vérifier si la position contient la sortie (et si le joueur a la clé)
        return self.grille[y][x] == 'S' and game_data.has_key

    def check_secret_exit(self, player, game_data):
        """
        Vérifie si le joueur atteint la sortie secrète
        """
        x, y = int(player.x), int(player.y)

        # S'assurer que les coordonnées sont valides
        if y < 0 or y >= len(self.grille) or x < 0 or x >= len(self.grille[y]):
            return False

        # Vérifier si la position contient la sortie secrète
        return self.grille[y][x] == '+'

    def check_teleporter(self, player):
        """
        Vérifie si le joueur atteint un téléporteur
        """
        x, y = int(player.x), int(player.y)

        # S'assurer que les coordonnées sont valides
        if y < 0 or y >= len(self.grille) or x < 0 or x >= len(self.grille[y]):
            return False

        # Vérifier si la position contient un téléporteur
        return self.grille[y][x] == '+'

    def show(self):
        """
        Affiche le niveau
        """
        for y, line in enumerate(self.grille):
            sys.stdout.write(f"\033[{y + 1};1H")
            for x, char in enumerate(line):
                if char == '#':
                    sys.stdout.write("\033[47m \033[0m")  # Bloc blanc
                elif char == 'S':
                    sys.stdout.write("\033[36mS\033[0m")  # Sortie en cyan
                elif char == '=':
                    sys.stdout.write("\033[37m=\033[0m")  # Plateforme en gris
                elif char == '+':
                    sys.stdout.write("\033[45m▓\033[0m")  # Téléporteur en magenta
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