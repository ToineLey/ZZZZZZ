#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import select
import termios
import tty

import Player
import Level
import Enemy
import Key


def init():
    """
    Initialisation du jeu
    """
    data = {
        'timeStep': 0.1,  # Pas de temps de simulation
        'show_period': 0.2,  # Période d'affichage
        'show_time': 0,  # Temps écoulé depuis le dernier affichage
        'x_min': 0,
        'x_max': 79,
        'y_min': 0,
        'y_max': 24,
        'score': 0,
        'level': 1,
        'lives': 3,
        'levels': [],
        'player': None,
        'enemy': None,
        'key': None,
        'running': True,
        'has_key': False,
        'old_settings': None
    }
    
    # Charger les niveaux
    level1 = Level.create("niveau-02.txt", 0)
    data['levels'].append(level1)
    
    # Créer le joueur
    data['player'] = Player.create(5, 5)
    
    # Créer un ennemi
    data['enemy'] = Enemy.create(15, 10)
    
    # Créer une clé
    data['key'] = Key.create(20, 20)
    
    # Configuration du terminal pour la détection des touches sans appuyer sur Entrée
    data['old_settings'] = termios.tcgetattr(sys.stdin)
    tty.setraw(sys.stdin.fileno())
    
    # Effacer l'écran et cacher le curseur
    sys.stdout.write("\033[2J\033[?25l")
    sys.stdout.flush()
    
    return data

def is_data():
    """
    Indique s'il y a des événements en attente
    """
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

def interact(data):
    """
    Gère les événements clavier
    """
    if is_data():
        c = sys.stdin.read(1)
        if c == 'a':  # Quitter le jeu
            quit_game(data)
        elif c == 'q':  # Déplacer à gauche
            Player.move_left(data['player'])
        elif c == 'd':  # Déplacer à droite
            Player.move_right(data['player'])
        elif c == 'z':  # Changer la gravité (sauter)
            Player.gravity_change(data['player'])
        elif c == 'e':  # Essayer de ramasser la clé
            Player.pick_key(data)

def live(data):
    """
    Simule l'évolution du jeu sur un pas de temps
    """
    # Mise à jour du joueur
    Player.live(data['player'], data)
    
    # Mise à jour des ennemis
    Enemy.live(data['enemy'], data)
    
    # Vérifier si le joueur a atteint la sortie
    if Level.check_exit(data['levels'][data['level']-1], data['player'], data):
        if data['level'] < len(data['levels']):
            Level.change(data, True)
        else:
            win(data)
    
    # Vérifier les collisions entre le joueur et les ennemis
    if Enemy.test_player(data['enemy'], data['player']):
        game_over(data)

def show(data):
    """
    Fonction d'affichage du jeu
    """
    # Effacer l'écran
    sys.stdout.write("\033[H")
    
    # Afficher le niveau
    Level.show(data['levels'][data['level']-1])
    
    # Afficher le joueur
    Player.show(data['player'])
    
    # Afficher l'ennemi
    Enemy.show(data['enemy'])
    
    # Afficher la clé si elle n'a pas été ramassée
    if not data['has_key']:
        Key.show(data['key'])
    
    # Afficher les informations du jeu
    sys.stdout.write(f"\033[{data['y_max']}H\033[KVies: {data['lives']} | Niveau: {data['level']} | Score: {data['score']} | Clé: {'Oui' if data['has_key'] else 'Non'}")
    
    sys.stdout.flush()

def game_over(data):
    """
    Termine la partie si le joueur meurt
    """
    data['lives'] -= 1
    if data['lives'] <= 0:
        sys.stdout.write("\033[H\033[2J")
        sys.stdout.write("\033[10;30HGAME OVER\033[11;25HAppuyez sur une touche pour quitter...")
        sys.stdout.flush()
        sys.stdin.read(1)
        quit_game(data)
    else:
        # Réinitialiser la position du joueur
        Player.set_pos(data['player'], 5, 5)

def win(data):
    """
    Termine la partie si le joueur gagne
    """
    sys.stdout.write("\033[H\033[2J")
    sys.stdout.write("\033[10;30HVICTOIRE!\033[11;25HAppuyez sur une touche pour quitter...")
    sys.stdout.flush()
    sys.stdin.read(1)
    quit_game(data)

def quit_game(data):
    """
    Quitte l'application
    """
    # Restaurer les paramètres du terminal
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, data['old_settings'])
    
    # Afficher le curseur
    sys.stdout.write("\033[?25h")
    sys.stdout.write("\033[H\033[2J")
    sys.stdout.flush()
    
    data['running'] = False
    sys.exit(0)

def run(data):
    """
    Boucle de simulation
    """
    last_time = time.time()
    
    while data['running']:
        current_time = time.time()
        elapsed = current_time - last_time
        last_time = current_time
        
        # Gérer les entrées utilisateur
        interact(data)
        
        # Mettre à jour la simulation
        live(data)
        
        # Mettre à jour l'affichage si nécessaire
        data['show_time'] += elapsed
        if data['show_time'] >= data['show_period']:
            show(data)
            data['show_time'] = 0
        
        # Pause pour éviter de surcharger le CPU
        time.sleep(0.01)

def main():
    """
    Fonction principale du jeu
    """
    # Écran de démarrage
    sys.stdout.write("\033[H\033[2J")
    sys.stdout.write("\033[10;30HZZZZZZ\033[11;25HAppuyez sur Entrée pour commencer...")
    sys.stdout.flush()
    
    # Attendre que l'utilisateur appuie sur Entrée
    sys.stdin.read(1)
    
    # Initialiser le jeu
    data = init()
    
    # Lancer la boucle de simulation
    run(data)

if __name__ == "__main__":
    main()
