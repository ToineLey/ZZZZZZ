#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
import termios
import tty
from datetime import datetime


class ScoreManager:
    def __init__(self, scores_file="scores.json"):
        """
        Initialise le gestionnaire de scores
        """
        self.scores_file = scores_file

    def load_scores(self):
        """
        Charge les scores depuis le fichier JSON
        """
        try:
            with open(self.scores_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Si le fichier n'existe pas ou est corrompu, retourner une liste vide
            return []

    def save_scores(self, scores):
        """
        Sauvegarde les scores dans le fichier JSON
        """
        try:
            with open(self.scores_file, 'w', encoding='utf-8') as f:
                json.dump(scores, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde: {e}")
            return False

    def add_score(self, player_name, score, level_reached, victory=False):
        """
        Ajoute un nouveau score au tableau
        """
        scores = self.load_scores()

        new_score = {
            "name": player_name,
            "score": int(score),
            "level": level_reached,
            "victory": victory,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        scores.append(new_score)

        # Trier par score décroissant
        scores.sort(key=lambda x: x["score"], reverse=True)

        # Garder seulement les 10 meilleurs scores
        scores = scores[:10]

        self.save_scores(scores)
        return len(scores)  # Retourne la position dans le classement

    def get_top_scores(self, limit=10):
        """
        Récupère les meilleurs scores
        """
        scores = self.load_scores()
        return scores[:limit]

    def display_scores(self):
        """
        Affiche le tableau des scores à l'écran
        """
        scores = self.get_top_scores()

        if not scores:
            sys.stdout.write("\033[10;30H\033[33mAucun score enregistré\033[0m")
            return

        # Titre du tableau
        sys.stdout.write("\033[8;25H\033[1;36m═══════════════════════════════════════════════════════════════\033[0m")
        sys.stdout.write("\033[9;25H\033[1;36m                    TABLEAU DES SCORES                        \033[0m")
        sys.stdout.write("\033[10;25H\033[1;36m═══════════════════════════════════════════════════════════════\033[0m")

        # En-têtes
        sys.stdout.write("\033[11;25H\033[1;33mPos  Nom             Score    Niveau  Statut     Date\033[0m")
        sys.stdout.write("\033[12;25H\033[33m───  ───             ─────    ──────  ──────     ────\033[0m")

        # Affichage des scores
        for i, score_entry in enumerate(scores):
            row = 13 + i
            pos = f"{i + 1:2d}"
            name = score_entry["name"][:12].ljust(12)  # Limiter à 12 caractères
            score = f"{score_entry['score']:7d}"
            level = f"{score_entry['level']:6d}"
            status = "VICTOIRE" if score_entry["victory"] else "DÉFAITE "
            date = score_entry["date"][:10]  # Seulement la date, pas l'heure

            # Couleur différente pour les victoires
            color = "\033[32m" if score_entry["victory"] else "\033[31m"

            sys.stdout.write(f"\033[{row};25H{color}{pos}   {name} {score}    {level}   {status}   {date}\033[0m")

        sys.stdout.write(
            f"\033[{13 + len(scores) + 1};25H\033[1;36m═══════════════════════════════════════════════════════════════\033[0m")

    def ask_player_name(self):
        """
        Demande le nom du joueur pour enregistrer son score
        Retourne le nom saisi ou None si annulé
        """
        # Afficher la demande
        sys.stdout.write("\033[25;25H\033[1;33mNouveau record! Entrez votre nom (max 12 caractères):\033[0m")
        sys.stdout.write("\033[26;25H\033[1;37m> \033[0m")
        sys.stdout.flush()

        # Sauvegarder les paramètres actuels du terminal
        old_settings = termios.tcgetattr(sys.stdin)

        try:
            # Remettre le terminal en mode normal pour la saisie
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            sys.stdout.write("\033[?25h")  # Afficher le curseur

            # Positionner le curseur après le ">"
            sys.stdout.write("\033[26;28H")
            sys.stdout.flush()

            # Lire le nom caractère par caractère pour éviter les problèmes
            name = ""
            while True:
                char = sys.stdin.read(1)
                if char == '\n' or char == '\r':  # Entrée
                    break
                elif char == '\x7f' or char == '\b':  # Backspace
                    if name:
                        name = name[:-1]
                        sys.stdout.write("\033[26;28H\033[K")  # Effacer la ligne
                        sys.stdout.write(name)
                        sys.stdout.flush()
                elif char == '\x1b':  # Échap
                    name = None
                    break
                elif len(char) == 1 and ord(char) >= 32 and len(name) < 12:  # Caractère imprimable
                    name += char
                    sys.stdout.write(char)
                    sys.stdout.flush()

            # Remettre en mode raw
            tty.setraw(sys.stdin.fileno())
            sys.stdout.write("\033[?25l")  # Cacher le curseur

            # Valider le nom
            if name and name.strip():
                return name.strip()
            else:
                return None

        except (KeyboardInterrupt, EOFError):
            # En cas d'interruption, remettre en mode raw
            tty.setraw(sys.stdin.fileno())
            sys.stdout.write("\033[?25l")
            return None

    def show_score_entry_screen(self, game_data):
        """
        Affiche l'écran d'enregistrement de score
        """
        # Effacer l'écran
        sys.stdout.write("\033[H\033[2J")
        sys.stdout.flush()

        # Afficher le tableau des scores
        self.display_scores()

    def is_score_worthy(self, score):
        """
        Vérifie si le score mérite d'être dans le tableau
        """
        scores = self.load_scores()
        if len(scores) < 10:
            return True

        # Vérifier si le score est supérieur au plus petit score du top 10
        return score > scores[-1]["score"]

    def handle_score_entry(self, game_data):
        """
        Gère l'enregistrement du score automatiquement si il mérite d'être enregistré
        Retourne 'continue', 'restart' ou 'quit'
        """
        # Vérifier si le score mérite d'être enregistré
        if self.is_score_worthy(game_data.score):
            # Score digne du tableau, demander le nom automatiquement
            self.show_score_entry_screen(game_data)

            name = self.ask_player_name()
            if name:
                victory = getattr(game_data, 'victory', False)
                self.add_score(name, game_data.score, game_data.level, victory)

                # Afficher confirmation et tableau mis à jour
                sys.stdout.write("\033[H\033[2J")
                self.display_scores()

                victory_text = "VICTOIRE!" if getattr(game_data, 'victory', False) else "GAME OVER"
                color = "\033[32m" if getattr(game_data, 'victory', False) else "\033[31m"

                sys.stdout.write(f"\033[27;25H\033[1m{color}{victory_text}\033[0m")
                sys.stdout.write(f"\033[28;25H\033[32mScore sauvegardé avec succès!\033[0m")
                sys.stdout.write(f"\033[29;25H\033[1;33m[r]: Recommencer | [Echap]: Quitter\033[0m")
                sys.stdout.flush()
            else:
                # Nom annulé, afficher options sans sauvegarder
                sys.stdout.write("\033[H\033[2J")
                self.display_scores()

                victory_text = "VICTOIRE!" if getattr(game_data, 'victory', False) else "GAME OVER"
                color = "\033[32m" if getattr(game_data, 'victory', False) else "\033[31m"

                sys.stdout.write(f"\033[27;25H\033[1m{color}{victory_text}\033[0m")
                sys.stdout.write(f"\033[28;25HVotre score: {game_data.score}")
                sys.stdout.write(f"\033[29;25H\033[1;33m[r]: Recommencer | [Echap]: Quitter\033[0m")
                sys.stdout.flush()
        else:
            # Score pas assez bon, afficher directement les options
            self.show_score_entry_screen(game_data)

            victory_text = "VICTOIRE!" if getattr(game_data, 'victory', False) else "GAME OVER"
            color = "\033[32m" if getattr(game_data, 'victory', False) else "\033[31m"

            sys.stdout.write(f"\033[27;25H\033[1m{color}{victory_text}\033[0m")
            sys.stdout.write(f"\033[28;25HVotre score: {game_data.score} (pas de nouveau record)")
            sys.stdout.write(f"\033[29;25H\033[1;33m[r]: Recommencer | [Echap]: Quitter\033[0m")
            sys.stdout.flush()

        # Attendre la prochaine action
        while True:
            key = sys.stdin.read(1)
            if key == 'r':
                return 'restart'
            elif key == '\x1b':
                return 'quit'