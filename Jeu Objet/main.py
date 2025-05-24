#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from Level import Level
from Player import Player
from Key import Key
from Enemy import Enemy
import sys
import time
import select
import termios
import tty
import threading
import os
from Score import ScoreManager




class GameData:
    def __init__(self):
        """
        Initialise les données du jeu
        """
        self.timeStep = 0.01  # Pas de temps de simulation
        self.show_period = 0.05  # Période d'affichage plus rapide
        self.show_time = 0  # Temps écoulé depuis le dernier affichage
        self.x_min = 0
        self.x_max = 37
        self.y_min = 0
        self.y_max = 24
        self.score = 0
        self.level = 1
        self.lives = 5
        self.levels = []
        self.player = None
        self.enemies = []  # Liste d'ennemis
        self.key = None
        self.running = True
        self.has_key = False
        self.old_settings = None
        self.display_lock = threading.Lock()  # Verrou pour synchroniser l'affichage
        self.victory = False  # indicateur de victoire

        # Variables pour les niveaux secrets
        self.current_is_secret = False
        self.prev_level = None
        self.secret_level = None
        self.saved_level = None

    def load_levels(self):
        """
        Charge tous les niveaux du jeu
        """
        level_files = [
            "niveau-00.txt",
            "niveau-01.txt",
            "niveau-02.txt",
            "niveau-03.txt",
            "niveau-04.txt",
            "niveau-05.txt",
            "niveau-06.txt",
            "niveau-07.txt",
            "niveau-08.txt",
            "niveau-09.txt"
        ]

        for level_file in level_files:
            level = Level(level_file, 0)
            self.levels.append(level)

    def extract_positions_from_level(self, level):
        """
        Extrait les positions des éléments depuis un niveau
        """
        player_pos = None
        key_pos = None
        enemy_positions = []
        inverted_enemy_positions = []

        for y, line in enumerate(level.grille):
            for x, char in enumerate(line):
                if char == '@':
                    player_pos = (x, y)
                elif char == 'K':
                    key_pos = (x, y)
                elif char == 'E':
                    enemy_positions.append((x, y))
                elif char == 'F':  # Ennemi de type 2 (gravité inversée)
                    inverted_enemy_positions.append((x, y))

        return player_pos, key_pos, enemy_positions, inverted_enemy_positions

    def initialize_level_entities(self, level=None):
        """
        Initialise les entités (joueur, clé, ennemis) pour le niveau actuel
        """
        if level is None:
            current_level = self.levels[self.level - 1]
        else:
            current_level = level

        player_pos, key_pos, enemy_positions, inverted_enemy_positions = self.extract_positions_from_level(
            current_level)

        # Créer le joueur
        if player_pos:
            self.player = Player(player_pos[0], player_pos[1])
        else:
            self.player = Player(5, 5)  # Position par défaut

        # Créer la clé
        if key_pos:
            self.key = Key(key_pos[0], key_pos[1])
        else:
            self.key = Key(20, 20)  # Position par défaut

        # Vider la liste des ennemis existants
        self.enemies.clear()

        # Créer les ennemis standard
        for pos in enemy_positions:
            self.enemies.append(Enemy(pos[0], pos[1], 1))

        # Créer les ennemis de gravité inversée
        for pos in inverted_enemy_positions:
            self.enemies.append(Enemy(pos[0], pos[1], 2))

    def change_to_secret_level(self):
        """
        Change vers un niveau secret
        """
        # Sauvegarde le niveau courant pour pouvoir revenir au niveau suivant
        self.prev_level = self.level
        self.has_key = False

        # Charger le niveau secret correspondant au niveau courant
        secret_level_name = f"niveau-secret-{self.level - 1:02d}.txt"

        # Si le niveau secret n'existe pas, utiliser le fichier niveau-secret-01.txt
        try:
            with open(secret_level_name, 'r', encoding='utf-8') as f:
                pass
        except FileNotFoundError:
            secret_level_name = "niveau-secret-01.txt"

        # Créer le niveau secret
        secret_level = Level(secret_level_name, 0)

        # Remplacer temporairement le niveau actuel par le niveau secret
        self.current_is_secret = True
        self.secret_level = secret_level

        # Important: remplacer temporairement le niveau actuel dans la liste des niveaux
        if self.level <= len(self.levels):
            # Sauvegarder le niveau actuel
            self.saved_level = self.levels[self.level - 1]
            # Remplacer par le niveau secret
            self.levels[self.level - 1] = secret_level

        # Initialiser les entités pour le niveau secret
        self.initialize_level_entities(secret_level)

    def change_to_next_level(self):
        """
        Change vers le niveau suivant
        """
        # Si on est dans un niveau secret, aller au niveau suivant celui qui a amené au secret
        if self.current_is_secret:
            self.level = self.prev_level + 1
            self.current_is_secret = False
            self.lives += 5
        else:
            self.level += 1

        self.has_key = False
        self.score += 500

        # Initialiser les entités pour le nouveau niveau
        self.initialize_level_entities()

    def reset_player_position(self):
        """
        Remet le joueur à sa position initiale du niveau
        """
        current_level = self.levels[self.level - 1]
        player_pos, _, _, _ = self.extract_positions_from_level(current_level)

        if player_pos:
            self.player.set_pos(player_pos[0], player_pos[1])
        else:
            self.player.set_pos(5, 5)

        # Réinitialiser la gravité et la vitesse
        self.player.gravity = 1
        self.player.velocity_y = 0


class Game:
    def __init__(self):
        """
        Initialise le jeu
        """
        self.data = GameData()
        self.score_manager = ScoreManager()

    def init(self):
        """
        Initialisation du jeu
        """
        # Charger les niveaux
        self.data.load_levels()

        # Initialiser les entités du premier niveau
        self.data.initialize_level_entities()

        # Configuration du terminal pour la détection des touches sans appuyer sur Entrée
        self.data.old_settings = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin.fileno())

        # Effacer l'écran et cacher le curseur
        sys.stdout.write("\033[2J\033[?25l")
        sys.stdout.flush()

    def is_data(self):
        """
        Indique s'il y a des événements en attente
        """
        return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

    def interact(self):
        """
        Gère les événements clavier
        """
        if self.is_data():
            c = sys.stdin.read(1)
            if c == '\x1b':  # Touche Échap
                self.quit_game()
            elif c == 'a':  # Quitter le jeu (alternative)
                self.quit_game()
            elif c == 'q':  # Déplacer à gauche
                self.data.player.move_left()
                # Afficher immédiatement après le déplacement
                with self.data.display_lock:
                    self.show()
            elif c == 'd':  # Déplacer à droite
                self.data.player.move_right()
                # Afficher immédiatement après le déplacement
                with self.data.display_lock:
                    self.show()
            elif c == 'z' or c == ' ':  # Changer la gravité
                self.data.player.gravity_change()
                # Afficher immédiatement après le changement de gravité
                self.data.score -= 1
                with self.data.display_lock:
                    self.show()
            elif c == 'e':  # Essayer de ramasser la clé
                self.data.player.pick_key(self.data)
                # Afficher immédiatement après la tentative de ramassage
                with self.data.display_lock:
                    self.show()
            elif c == 'r':  # Redémarrer le niveau actuel
                self.data.reset_player_position()
                # Réinitialiser la clé
                self.data.has_key = False
                with self.data.display_lock:
                    self.show()

    def live(self):
        """
        Simule l'évolution du jeu sur un pas de temps
        """
        # Mise à jour du joueur
        self.data.player.update(self.data)

        # Mise à jour des ennemis
        for enemy in self.data.enemies:
            enemy.update(self.data)

        # Vérifier si le joueur a atteint la sortie
        current_level = self.data.levels[self.data.level - 1]
        if current_level.check_exit(self.data.player, self.data):
            if self.data.level < len(self.data.levels):
                self.data.change_to_next_level()
            else:
                self.win()

        # Vérifier si le joueur a atteint la sortie secrète
        if current_level.check_secret_exit(self.data.player, self.data):
            self.data.score += 10000
            self.data.change_to_secret_level()

        # Vérifier les collisions entre le joueur et les ennemis
        for enemy in self.data.enemies:
            if enemy.test_player_collision(self.data.player):
                if enemy.state == 0:  # Ne tester que les ennemis actifs
                    self.game_over()
                    break

    def show(self):
        """
        Fonction d'affichage du jeu
        """
        # Effacer l'écran
        sys.stdout.write("\033[H")

        # Afficher le niveau
        current_level = self.data.levels[self.data.level - 1]
        current_level.show()

        # Afficher la clé si elle n'a pas été ramassée
        if not self.data.has_key:
            self.data.key.show()

        # Afficher les ennemis
        for enemy in self.data.enemies:
            enemy.show()

        # Afficher le joueur (en dernier pour qu'il soit au-dessus)
        self.data.player.show()

        # Afficher les informations du jeu
        sys.stdout.write(f"\033[{self.data.y_max}H\033[K")
        sys.stdout.write(
            f"\033[{self.data.y_max}H\033[KVies: {self.data.lives} | Niveau: {self.data.level} | Score: {int(self.data.score)} | ")
        sys.stdout.write(
            f"Clé: {'Oui' if self.data.has_key else 'Non'} | [q/d]: Déplacer | [z]: Gravité | [e]: Prendre clé | [r]: Restart | [Echap]: Quitter")

        sys.stdout.flush()

    def game_over(self):
        """
        Termine la partie si le joueur meurt
        """
        self.data.lives -= 1
        self.data.score -= 1000

        if self.data.lives <= 0:
            self.data.running = False
            self.data.victory = False  # Défaite

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
            action = self.score_manager.handle_score_entry(self.data)

            if action == 'restart':
                # Restaurer les paramètres du terminal
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.data.old_settings)
                # Réinitialiser et relancer le jeu
                python = sys.executable
                os.execl(python, python, *sys.argv)
            elif action == 'quit':
                self.quit_game()
        else:
            # Réinitialiser la position du joueur
            self.data.reset_player_position()

    def win(self):
        """
        Termine la partie si le joueur gagne
        """
        self.data.running = False
        self.data.victory = True  # Victoire
        self.data.score += int(5000 * (self.data.lives / 5) + 50)  # Bonus de victoire

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
        action = self.score_manager.handle_score_entry(self.data)

        if action == 'restart':
            # Restaurer les paramètres du terminal
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.data.old_settings)
            # Réinitialiser et relancer le jeu
            python = sys.executable
            os.execl(python, python, *sys.argv)
        elif action == 'quit':
            self.quit_game()

    def quit_game(self):
        """
        Quitte l'application
        """
        # Restaurer les paramètres du terminal
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.data.old_settings)

        # Afficher le curseur
        sys.stdout.write("\033[?25h")
        sys.stdout.write("\033[H\033[2J")
        sys.stdout.flush()

        self.data.running = False
        sys.exit(0)

    def display_thread(self):
        """
        Thread dédié à l'affichage
        """
        last_time = time.time()

        while self.data.running:
            current_time = time.time()
            elapsed = current_time - last_time
            last_time = current_time

            # Mettre à jour l'affichage périodiquement
            self.data.show_time += elapsed
            if self.data.show_time >= self.data.show_period:
                with self.data.display_lock:
                    self.show()
                self.data.show_time = 0

            # Pause pour éviter de surcharger le CPU
            time.sleep(0.01)

    def run(self):
        """
        Boucle de simulation avec threading
        """
        # Créer et démarrer le thread d'affichage
        display = threading.Thread(target=self.display_thread)
        display.daemon = True
        display.start()

        # Boucle principale du jeu
        while self.data.running:
            # Gérer les entrées utilisateur
            self.interact()

            # Mettre à jour la simulation
            self.live()

            # Pause pour éviter de surcharger le CPU
            time.sleep(0.01)

    def show_main_menu(self):
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

    def main(self):
        """
        Fonction principale du jeu
        """
        # Configuration du terminal pour la détection des touches
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin.fileno())

        try:
            while True:
                self.show_main_menu()

                # Attendre une action de l'utilisateur
                while True:
                    key = sys.stdin.read(1)
                    if key == '\r':  # Entrée - Jouer
                        # Initialiser et lancer le jeu
                        self.init()
                        self.run()
                        break  # Sortir de la boucle pour revenir au menu principal

                    elif key == 'h':  # Afficher les scores
                        sys.stdout.write("\033[H\033[2J")
                        self.score_manager.display_scores()
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
    game = Game()
    game.main()
