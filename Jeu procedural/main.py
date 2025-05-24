#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import select
import termios
import tty
import threading
import os

import Player
import Level
import Enemy
import Key
import Score

''


def init():
    """
    Initialisation du jeu
    """
    data = {
        'timeStep': 0.01,  # Pas de temps de simulation
        'show_period': 0.05,  # Période d'affichage plus rapide
        'show_time': 0,  # Temps écoulé depuis le dernier affichage
        'x_min': 0,
        'x_max': 37,
        'y_min': 0,
        'y_max': 24,
        'score': 0,
        'level': 1,
        'lives': 5,
        'levels': [],
        'player': None,
        'enemies': [],  # Liste d'ennemis
        'key': None,
        'running': True,
        'has_key': False,
        'old_settings': None,
        'display_lock': threading.Lock(),  # Verrou pour synchroniser l'affichage
        'victory': False  # indicateur de victoire
    }

    # Charger les niveaux
    level0 = Level.create("niveau-00.txt", 0)
    level1 = Level.create("niveau-01.txt", 0)
    level2 = Level.create("niveau-02.txt", 0)
    level3 = Level.create("niveau-03.txt", 0)
    level4 = Level.create("niveau-04.txt", 0)
    level5 = Level.create("niveau-05.txt", 0)
    level6 = Level.create("niveau-06.txt", 0)
    level7 = Level.create("niveau-07.txt", 0)
    level8 = Level.create("niveau-08.txt", 0)
    level9 = Level.create("niveau-09.txt", 0)

    data['levels'].append(level0)
    data['levels'].append(level1)
    data['levels'].append(level2)
    data['levels'].append(level3)
    data['levels'].append(level4)
    data['levels'].append(level5)
    data['levels'].append(level6)
    data['levels'].append(level7)
    data['levels'].append(level8)
    data['levels'].append(level9)

    # Extraire les positions initiales des éléments du niveau actuel
    current_level = data['levels'][data['level'] - 1]
    player_pos = None
    key_pos = None
    enemy_positions = []
    inverted_enemy_positions = []  # Pour les ennemis de type 2 (gravité inversée)

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
        if c == '\x1b':  # Touche Échap
            quit_game(data)
        elif c == 'a':  # Quitter le jeu (alternative)
            quit_game(data)
        elif c == 'q':  # Déplacer à gauche
            Player.move_left(data['player'])
            # Afficher immédiatement après le déplacement
            with data['display_lock']:
                show(data)
        elif c == 'd':  # Déplacer à droite
            Player.move_right(data['player'])
            # Afficher immédiatement après le déplacement
            with data['display_lock']:
                show(data)
        elif c == 'z' or c == ' ':  # Changer la gravité
            Player.gravity_change(data['player'])
            # Afficher immédiatement après le changement de gravité
            data['score'] -= 1
            with data['display_lock']:
                show(data)
        elif c == 'e':  # Essayer de ramasser la clé
            Player.pick_key(data)
            # Afficher immédiatement après la tentative de ramassage
            with data['display_lock']:
                show(data)

        elif c == 'r':  # Redémarrer le niveau actuel
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

            # Réinitialiser la gravité et la vitesse
            data['player']['gravity'] = 1
            data['player']['velocity_y'] = 0

            # Réinitialiser la clé
            data['has_key'] = False

            with data['display_lock']:
                show(data)


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

    # Vérifier si le joueur a atteint la sortie secrete
    if Level.check_secret_exit(data['levels'][data['level'] - 1], data['player'], data):
        data['score'] += 10000
        Level.change_to_secret(data, data['level'])

    # Vérifier les collisions entre le joueur et les ennemis
    for enemy in data['enemies']:
        if Enemy.test_player(enemy, data['player']):
            if enemy['state'] == 0:  # Ne tester que les ennemis actifs
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
        f"\033[{data['y_max']}H\033[KVies: {data['lives']} | Niveau: {data['level']} | Score: {int(data['score'])} | ")
    sys.stdout.write(
        f"Clé: {'Oui' if data['has_key'] else 'Non'} | [q/d]: Déplacer | [z]: Gravité | [e]: Prendre clé | [r]: Restart | [Echap]: Quitter")

    sys.stdout.flush()


def game_over(data):
    """
    Termine la partie si le joueur meurt
    """
    data['lives'] -= 1
    data['score'] -= 1000

    if data['lives'] <= 0:
        data['running'] = False
        data['victory'] = False  # Défaite

        # Nettoyer l'écran
        sys.stdout.write("\033[H\033[2J")
        sys.stdout.flush()

        # Déterminer le chemin du fichier fin.txt
        file_paths = ["./fin.txt", "fin.txt", os.path.join(os.path.dirname(__file__), "fin.txt")]
        end_text = None

        for path in file_paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    end_text = f.read()
                    break
            except (FileNotFoundError, IOError):
                continue

        # Afficher le texte de fin
        if end_text:
            lines = end_text.split('\n')
            for i, line in enumerate(lines):
                sys.stdout.write("\033[1;31m" + f"\033[{i + 2};1H{line}" + "\033[0;0m")
        else:
            sys.stdout.write("\033[10;30H\033[31mGAME OVER\033[0m")

        sys.stdout.flush()

        # Petite pause pour laisser voir le message
        time.sleep(1)

        # Gérer l'enregistrement du score
        action = Score.handle_score_entry(data)

        if action == 'restart':
            # Restaurer les paramètres du terminal
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, data['old_settings'])
            # Réinitialiser et relancer le jeu
            python = sys.executable
            os.execl(python, python, *sys.argv)
        elif action == 'quit':
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
    data['running'] = False
    data['victory'] = True  # Victoire
    data['score'] += int(5000 * (data['lives']/5) + 50) # Bonus de victoire et pénalité de mort + score du niveau actuel

    # Nettoyer l'écran
    sys.stdout.write("\033[H\033[2J")
    sys.stdout.flush()

    # Déterminer le chemin du fichier Victoire.txt
    file_paths = ["./Victoire.txt", "Victoire.txt", os.path.join(os.path.dirname(__file__), "Victoire.txt")]
    victory_text = None

    for path in file_paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                victory_text = f.read()
                break
        except (FileNotFoundError, IOError):
            continue

    # Afficher le texte de victoire
    if victory_text:
        lines = victory_text.split('\n')
        for i, line in enumerate(lines):
            sys.stdout.write("\033[1;32m" + f"\033[{i + 2};1H{line}" + "\033[0;0m")
    else:
        sys.stdout.write("\033[1;32m" + "\033[10;30H\033[32mVICTOIRE!\033[0m" + "\033[0;0m")

    sys.stdout.flush()

    # Petite pause pour laisser voir le message
    time.sleep(1)

    # Gérer l'enregistrement du score
    action = Score.handle_score_entry(data)

    if action == 'restart':
        # Restaurer les paramètres du terminal
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, data['old_settings'])
        # Réinitialiser et relancer le jeu
        python = sys.executable
        os.execl(python, python, *sys.argv)
    elif action == 'quit':
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


def display_thread(data):
    """
    Thread dédié à l'affichage
    """
    last_time = time.time()

    while data['running']:
        current_time = time.time()
        elapsed = current_time - last_time
        last_time = current_time

        # Mettre à jour l'affichage périodiquement
        data['show_time'] += elapsed
        if data['show_time'] >= data['show_period']:
            with data['display_lock']:
                show(data)
            data['show_time'] = 0

        # Pause pour éviter de surcharger le CPU
        time.sleep(0.01)


def run(data):
    """
    Boucle de simulation avec threading
    """
    # Créer et démarrer le thread d'affichage
    display = threading.Thread(target=display_thread, args=(data,))
    display.daemon = True
    display.start()

    # Boucle principale du jeu
    while data['running']:
        # Gérer les entrées utilisateur
        interact(data)

        # Mettre à jour la simulation
        live(data)

        # Pause pour éviter de surcharger le CPU
        time.sleep(0.01)


def show_main_menu():
    """
    Affiche le menu principal avec les options
    """
    sys.stdout.write("\033[H\033[2J")

    # Déterminer le chemin du fichier ZZZZZZ.txt
    file_paths = ["./ZZZZZZ.txt", "ZZZZZZ.txt", os.path.join(os.path.dirname(__file__), "ZZZZZZ.txt")]
    intro_text = None

    for path in file_paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                intro_text = f.read()
                break
        except (FileNotFoundError, IOError):
            continue

    # Afficher le texte d'intro
    if intro_text:
        lines = intro_text.split('\n')
        for i, line in enumerate(lines):
            sys.stdout.write("\033[1;36m" + f"\033[{i + 2};1H{line}" + "\033[0;0m")
    else:
        sys.stdout.write("\033[10;30HZZZZZZ")

    # Afficher les instructions
    sys.stdout.write("\033[19;25H\033[1;33m╔════════════════════════════════════════╗\033[0m")
    sys.stdout.write("\033[20;25H\033[1;33m║               INSTRUCTIONS             ║\033[0m")
    sys.stdout.write("\033[21;25H\033[1;33m╚════════════════════════════════════════╝\033[0m")
    sys.stdout.write("\033[23;25H[S]: Sortie | [?/¿]: Joueur | [K]: clé")
    sys.stdout.write("\033[24;25H[E]: Ennemi rouge (actif en gravité normale)")
    sys.stdout.write("\033[25;25H[F]: Ennemi jaune (actif en gravité inversée)")
    sys.stdout.write("\033[27;25H\033[1;32m[Entrée]: Jouer | [h]: Scores | [Echap]: Quitter\033[0m")
    sys.stdout.flush()


def main():
    """
    Fonction principale du jeu
    """
    # Configuration du terminal pour la détection des touches
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setraw(sys.stdin.fileno())

    try:
        while True:
            show_main_menu()

            # Attendre une action de l'utilisateur
            while True:
                key = sys.stdin.read(1)
                if key == '\r':  # Entrée - Jouer
                    # Initialiser et lancer le jeu
                    data = init()
                    run(data)
                    break  # Sortir de la boucle pour revenir au menu principal

                elif key == 'h':  # Afficher les scores
                    sys.stdout.write("\033[H\033[2J")
                    Score.display_scores()
                    sys.stdout.write("\033[30;25H\033[1;33mAppuyez sur une touche pour revenir au menu...\033[0m")
                    sys.stdout.flush()
                    sys.stdin.read(1)  # Attendre une touche
                    break  # Revenir au menu principal

                elif key == '\x1b':  # Échap - Quitter
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                    sys.stdout.write("\033[?25h")  # Afficher le curseur
                    sys.stdout.write("\033[H\033[2J")  # Effacer l'écran
                    sys.stdout.flush()
                    sys.exit(0)

    except KeyboardInterrupt:
        # En cas d'interruption, restaurer le terminal
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        sys.stdout.write("\033[?25h")
        sys.stdout.write("\033[H\033[2J")
        sys.stdout.flush()
        sys.exit(0)


if __name__ == "__main__":
    main()