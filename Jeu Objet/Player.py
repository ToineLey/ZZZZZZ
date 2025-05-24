#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys


class Player:
    def __init__(self, x, y):
        """
        Initialise un joueur
        """
        self.x = x
        self.y = y
        self.color = "\033[32m"  # Couleur verte
        self.speed = 1
        self.velocity_y = 0
        self.gravity = 1  # 1 pour gravité vers le bas, -1 pour gravité vers le haut
        self.on_ground = False
        self.jump_power = -3
        self.jump_cooldown = 0
        self._last_x = None

    def set_pos(self, x, y):
        """
        Définit la position du joueur
        """
        self.x = x
        self.y = y

    def get_pos(self):
        """
        Récupère la position du joueur
        """
        return (self.x, self.y)

    def move_left(self):
        """
        Déplace le joueur à gauche
        """
        self.x -= self.speed
        if self.x < 0:
            self.x = 0

    def move_right(self):
        """
        Déplace le joueur à droite
        """
        self.x += self.speed

    def gravity_change(self):
        """
        Effectue un changement de gravité
        """
        # Inverser la gravité
        self.gravity *= -1

        # Ajuster la vitesse pour un petit effet de poussée dans la nouvelle direction
        self.velocity_y = self.jump_power * self.gravity * 0.5
        self.on_ground = False
        self.jump_cooldown = 5  # Éviter les changements multiples trop rapides

    def pick_key(self, game_data):
        """
        Permet de ramasser la clé
        """
        key = game_data.key

        # Convertir en entiers pour la comparaison
        px, py = int(self.x), int(self.y)
        kx, ky = int(key.x), int(key.y)

        # Si le joueur est à proximité de la clé
        if abs(px - kx) <= 1 and abs(py - ky) <= 1 and not game_data.has_key:
            game_data.has_key = True
            game_data.score += 100 * (game_data.lives / 5)

    def set_speed(self, v):
        """
        Définit la vitesse du joueur
        """
        self.speed = v

    def test_collision(self, x, y, level):
        """
        Teste s'il y a une collision à la position donnée
        """
        # Convertir en entiers pour indexation
        x_int = int(x)
        y_int = int(y)

        if x_int < 0 or y_int < 0 or y_int >= len(level.grille) or x_int >= len(level.grille[y_int]):
            return True

        cell = level.grille[y_int][x_int]
        # Note: '+' (téléporteur) ne bloque pas le mouvement, donc on ne le traite pas comme une collision
        return cell == '#' or cell == '='

    def collide(self, game_data):
        """
        Gère les collisions avec le niveau
        """
        level = game_data.levels[game_data.level - 1]

        # Vérifier la collision dans la direction de la gravité
        test_y = self.y + self.gravity

        if self.test_collision(self.x, test_y, level):
            self.on_ground = True
            self.velocity_y = 0
        else:
            self.on_ground = False

        # Vérifier les collisions verticales (en fonction de la gravité)
        if self.velocity_y != 0:  # Si en mouvement vertical
            next_y = self.y + self.velocity_y
            if not self.test_collision(self.x, next_y, level):
                self.y = next_y
            else:
                # Trouver la position valide la plus proche
                if self.velocity_y > 0:
                    while self.test_collision(self.x, self.y + 0.1, level) == False and abs(self.y - next_y) > 0.1:
                        self.y += 0.1
                else:
                    while self.test_collision(self.x, self.y - 0.1, level) == False and abs(self.y - next_y) > 0.1:
                        self.y -= 0.1
                self.velocity_y = 0

        # Vérifier les collisions horizontales APRÈS le mouvement à gauche/droite
        if self._last_x is not None:
            # Calculer la direction du mouvement
            dx = self.x - self._last_x

            if dx != 0:  # Si un mouvement horizontal a eu lieu
                if self.test_collision(self.x, self.y, level):
                    # En cas de collision, revenir à l'ancienne position
                    self.x = self._last_x

        # Mémoriser la position actuelle pour le prochain cycle
        self._last_x = self.x

        # Vérifier les bords de l'écran
        if self.x < 0:
            self.x = 0
        if self.x > game_data.x_max:
            self.x = game_data.x_max
        if self.y < 0:
            self.y = 0
        if self.y > game_data.y_max - 1:
            self.y = game_data.y_max - 1

    def update(self, game_data):
        """
        Met à jour l'état du joueur
        """
        # Appliquer la gravité
        if not self.on_ground:
            self.velocity_y += 0.5 * self.gravity

        # Limiter la vitesse de chute
        max_fall_speed = 2
        if abs(self.velocity_y) > max_fall_speed:
            self.velocity_y = max_fall_speed * (1 if self.velocity_y > 0 else -1)

        # Décrémenter le compteur de saut
        if self.jump_cooldown > 0:
            self.jump_cooldown -= 1

        # Gérer les collisions
        self.collide(game_data)

    def show(self):
        """
        Affiche le joueur
        """
        # Convertir en entiers pour l'affichage
        x = int(self.x)
        y = int(self.y)

        # Caractère différent selon la direction de la gravité
        char = '?' if self.gravity > 0 else '¿'

        sys.stdout.write(f"\033[{y + 1};{x + 1}H{self.color}{char}\033[0m")