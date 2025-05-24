#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys


class Key:
    def __init__(self, x, y):
        """
        Crée une clé
        """
        self.x = x
        self.y = y
        self.color = "\033[33m"  # Couleur jaune

    def get_pos(self):
        """
        Récupère les coordonnées de la clé
        """
        return (self.x, self.y)

    def set_pos(self, x, y):
        """
        Positionne une clé
        """
        self.x = x
        self.y = y

    def show(self):
        """
        Affiche la clé
        """
        # Convertir en entiers pour l'affichage
        x = int(self.x)
        y = int(self.y)
        sys.stdout.write(f"\033[{y + 1};{x + 1}H{self.color}K\033[0m")