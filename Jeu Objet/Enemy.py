#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys


class Enemy:
    def __init__(self, x, y, enemy_type=1):
        """
        Crée un ennemi

        Types:
        1: ennemi rouge (standard) - actif en gravité normale
        2: ennemi jaune - actif uniquement en gravité inverse
        """
        self.x = x
        self.y = y
        self.color = "\033[31m" if enemy_type == 1 else "\033[33m"  # Rouge ou Jaune
        self.type = enemy_type  # 1: standard, 2: gravité inverse
        self.state = 0  # 0: état normal, 1: inactif
        self.direction = 1  # 1: droite, -1: gauche
        self.speed = 0.1
        self.movement_counter = 0

    def get_pos(self):
        """
        Récupère les coordonnées de l'ennemi
        """
        return (self.x, self.y)

    def set_pos(self, x, y):
        """
        Positionne un ennemi
        """
        self.x = x
        self.y = y

    def move(self, game_data):
        """
        Déplace l'ennemi
        """
        level = game_data.levels[game_data.level - 1]

        # Vérifier si l'ennemi est actif selon son type et la gravité du joueur
        is_active = True
        if (self.type == 1 and game_data.player.gravity < 0) or (self.type == 2 and game_data.player.gravity > 0):
            is_active = False
            self.state = 1  # Inactif
        else:
            self.state = 0  # Actif

        # Ne déplacer que les ennemis actifs
        if is_active:
            # Mouvement de patrouille simple
            self.movement_counter += self.speed

            if self.movement_counter >= 1:
                self.movement_counter -= 1
                if self.type == 1:
                    # Calculer la nouvelle position potentielle
                    new_x = int(self.x + self.direction)
                    y_int = int(self.y)

                    # Vérifier s'il y a une collision ou un vide en dessous
                    if (new_x < 0 or new_x >= level.width or y_int >= level.height or
                            (y_int < level.height and y_int >= 0 and new_x < len(level.grille[y_int]) and
                             (level.grille[y_int][new_x] == '#' or level.grille[y_int][new_x] == '+'))):
                        # Changer de direction
                        self.direction *= -1
                    else:
                        # Vérifier s'il y a un sol sous l'ennemi
                        if (y_int + 1 >= level.height or
                                (y_int + 1 < level.height and new_x < len(level.grille[y_int + 1]) and
                                 level.grille[y_int + 1][new_x] != '#' and
                                 level.grille[y_int + 1][new_x] != '=')):
                            # Pas de sol, changer de direction
                            self.direction *= -1
                        else:
                            # Déplacer l'ennemi
                            self.x = new_x
                elif self.type == 2:
                    new_x = int(self.x + self.direction)
                    y_int = int(self.y)

                    if (new_x < 0 or new_x >= level.width or y_int >= level.height or
                            (y_int < level.height and y_int >= 0 and new_x < len(level.grille[y_int]) and
                             (level.grille[y_int][new_x] == '#' or level.grille[y_int][new_x] == '+' or
                              level.grille[y_int][new_x] == 'E'))):
                        # Changer de direction
                        self.direction *= -1
                    else:
                        # Vérifier s'il y a un plafond sur l'ennemi
                        if (y_int - 1 >= level.height or
                                (y_int - 1 < level.height and new_x < len(level.grille[y_int - 1]) and
                                 level.grille[y_int - 1][new_x] != '#' and
                                 level.grille[y_int - 1][new_x] != '=')):
                            # Pas de plafond, changer de direction
                            self.direction *= -1
                        else:
                            # Déplacer l'ennemi
                            self.x = new_x

    def test_player_collision(self, player):
        """
        Détecte si l'ennemi touche le joueur
        Les ennemis en état 0 (actifs) sont toujours meurtriers
        Les ennemis en état 1 (inactifs) ne détectent pas de collision
        """
        # Convertir en entiers pour la comparaison
        px, py = int(player.x), int(player.y)
        ex, ey = int(self.x), int(self.y)

        # Si l'ennemi touche le joueur
        return abs(px - ex) < 1 and abs(py - ey) < 1

    def set_speed(self, v):
        """
        Définit la vitesse de l'ennemi
        """
        self.speed = v

    def update(self, game_data):
        """
        Met à jour l'état de l'ennemi
        """
        self.move(game_data)

    def show(self):
        """
        Affiche l'ennemi
        """
        # Convertir en entiers pour l'affichage
        x = int(self.x)
        y = int(self.y)

        # Caractère selon le type d'ennemi
        char = 'E' if self.type == 1 else 'F'  # E pour standard, F pour gravité inverse

        # Ne pas afficher les ennemis inactifs (ou les afficher différemment)
        if self.state == 0:  # Actif
            sys.stdout.write(f"\033[{y + 1};{x + 1}H{self.color}{char}\033[0m")
        else:  # Inactif - afficher en semi-transparent (gris clair)
            sys.stdout.write(f"\033[{y + 1};{x + 1}H\033[37m{char}\033[0m")