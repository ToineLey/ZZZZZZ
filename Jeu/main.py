#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import select
import termios
import tty
import os

import Player
import Level
import Enemy
import Key

''


def load_screen(filename, default_content, center_x=30, center_y=10):
    """
    Charge un écran à partir d'un fichier texte
    Si le fichier n'existe pas, utilise le contenu par défaut
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # Supprimer les sauts de ligne finaux
        lines = [line.rstrip('\n') for line in lines]
        return lines
    except FileNotFoundError:
        return default_content


def display_screen(data, lines, center_y=10, wait_for_key=True, additional_text=None):
    """
    Affiche un écran avec le texte centré
    """
    # Effacer l'écran
    sys.stdout.write("\033[H\033[2J")

    # Afficher le contenu ligne par ligne
    for i, line in enumerate(lines):
        y_pos = center_y + i
        # Centrer le texte
        x_pos = max(1, (data['x_max'] - len(line)) // 2 + 1)
        sys.stdout.write(f"\033[{y_pos};{x_pos}H{line}")

    # Afficher le texte supplémentaire si fourni
    if additional_text:
        for i, line in enumerate(additional_text):
            y_pos = center_y + len(lines) + 2 + i
            x_pos = max(1, (data['x_max'] - len(line)) // 2 + 1)
            sys.stdout.write(f"\033[{y_pos};{x_pos}H{line}")

    # Afficher l'invite pour continuer
    if wait_for_key:
        prompt = "Appuyez sur une touche pour continuer..."
        y_pos = center_y + len(lines) + (4 if additional_text else 2)
        x_pos = max(1, (data['x_max'] - len(prompt)) // 2 + 1)
        sys.stdout.write(f"\033[{y_pos};{x_pos}H{prompt}")

    sys.stdout.flush()

    # Attendre une touche si demandé
    if wait_for_key:
        sys.stdin.read(1)


def init():
    """
    Initialisation du jeu
    """
    data = {
        'timeStep': 0.01,  # Pas de temps de simulation
        'show_period': 0.2,  # Période d'affichage
        'show_time': 0,  # Temps écoulé depuis le dernier affichage
        'x_min': 0,
        'x_max': 37,
        'y_min': 0,
        'y_max': 24,
        'score': 0,
        'level': 1,
        'lives': 3,
        'levels': [],
        'player': None,
        'enemies': [],  # Liste d'ennemis
        'key': None,
        'running': True,
        'has_key': False,
        'old_settings': None
    }

    # Charger les niveaux
    level0 = Level.create("niveau-00.txt", 0)
    level1 = Level.create("niveau-01.txt", 0)
    level2 = Level.create("niveau-02.txt", 0)
    level3 = Level.create("niveau-03.txt", 0)

    data['levels'].append(level0)
    data['levels'].append(level1)
    data['levels'].append(level2)
    data['levels'].append(level3)

    # Extraire les positions initiales des éléments du niveau actuel
    current_level = data['levels'][data['level'] - 1]
    player_pos = None
    key_pos = None
    enemy_positions = []

    for y, line in enumerate(current_level['grille']):
        for x, char in enumerate(line):
            if char == '@':
                player_pos = (x, y)
            elif char == 'K':
                key_pos = (x, y)
            elif char == 'E':
                enemy_positions.append((x, y))

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
            data['enemies'].append(Enemy.create(pos[0], pos[1]))
    else:
        pass

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
        elif c == 'z' or c == ' ':  # Changer la gravité
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
    for enemy in data['enemies']:
        Enemy.live(enemy, data)

    # Vérifier si le joueur a atteint la sortie
    if Level.check_exit(data['levels'][data['level'] - 1], data['player'], data):
        if data['level'] < len(data['levels']):
            Level.change(data, True)
        else:
            win(data)

    # Vérifier les collisions entre le joueur et les ennemis
    for enemy in data['enemies']:
        if Enemy.test_player(enemy, data['player']):
            game_over(data)
            break


def show(data):
    """
    Fonction d'affichage du jeu
    """
    # Effacer l'écran
    sys.stdout.write("\033[H")

    # Afficher le niveau
    Level.show(data['levels'][data['level'] - 1])

    # Afficher la clé si elle n'a pas été ramassée
    if not data['has_key']:
        Key.show(data['key'])

    # Afficher les ennemis
    for enemy in data['enemies']:
        Enemy.show(enemy)

    # Afficher le joueur (en dernier pour qu'il soit au-dessus)
    Player.show(data['player'])

    # Afficher les informations du jeu
    sys.stdout.write(f"\033[{data['y_max']}H\033[K")
    sys.stdout.write(
        f"\033[{data['y_max']}H\033[KVies: {data['lives']} | Niveau: {data['level']} | Score: {data['score']} | ")
    sys.stdout.write(
        f"Clé: {'Oui' if data['has_key'] else 'Non'} | [q/d]: Déplacer | [z]: Gravité | [e]: Prendre clé | [a]: Quitter")

    sys.stdout.flush()


def game_over(data):
    """
    Termine la partie si le joueur meurt
    """
    data['lives'] -= 1
    data['score'] -= 1000

    if data['lives'] <= 0:
        # Charger l'écran de fin de partie depuis un fichier
        default_game_over = [
            "GAME OVER",
            "Vous avez perdu toutes vos vies!",
            f"Score final: {data['score']}"
        ]

        game_over_screen = load_screen("fin.txt", default_game_over)

        # Ajouter le score si nécessaire (si pas déjà dans le fichier)
        additional_text = [f"Score final: {data['score']}"] if not any(
            "Score" in line for line in game_over_screen) else None

        display_screen(data, game_over_screen, additional_text=additional_text)
        quit_game(data)
    else:
        # Réinitialiser la position du joueur
        current_level = data['levels'][data['level'] - 1]
        player_pos = None

        for y, line in enumerate(current_level['grille']):
            for x, char in enumerate(line):
                if char == '@':
                    player_pos = (x, y)
                    break
            if player_pos:
                break

        if player_pos:
            Player.set_pos(data['player'], player_pos[0], player_pos[1])
        else:
            Player.set_pos(data['player'], 5, 5)

        # Réinitialiser la gravité
        data['player']['gravity'] = 1
        data['player']['velocity_y'] = 0


def win(data):
    """
    Termine la partie si le joueur gagne
    """
    # Charger l'écran de victoire depuis un fichier
    default_victory = [
        "VICTOIRE!",
        "Félicitations, vous avez terminé tous les niveaux!"
    ]

    victory_screen = load_screen("Victoire.txt", default_victory)

    # Ajouter le score si nécessaire (si pas déjà dans le fichier)
    additional_text = [f"Score final: {data['score']}"] if not any("Score" in line for line in victory_screen) else None

    display_screen(data, victory_screen, additional_text=additional_text)
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
    # Définir l'écran titre par défaut au cas où le fichier n'existe pas
    default_title = [
        "ZZZZZZ",
        "Jeu de plateforme avec gravité inversée",
        "",
        "[q/d]: Déplacer | [z]: Gravité | [e]: Prendre clé | [a]: Quitter"
    ]

    # Créer un dictionnaire pour init(), même si on n'a pas encore appelé init()
    # Juste pour passer à la fonction display_screen
    temp_data = {'x_max': 37, 'y_max': 24}

    # Charger et afficher l'écran titre
    title_screen = load_screen("ZZZZZZ.txt", default_title)
    display_screen(temp_data, title_screen)

    # Initialiser le jeu
    data = init()

    # Lancer la boucle de simulation
    run(data)


if __name__ == "__main__":
    main()