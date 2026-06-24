# DikTux: Zugriff auf Eingabegeräte einrichten

DikTux verwendet `evdev`, um globale Hotkeys direkt vom Kernel zu lesen.
Dafür muss der Benutzer Mitglied der Gruppe `input` sein.

## Gruppe hinzufügen

```bash
sudo usermod -aG input $USER
```

Danach **abmelden und neu anmelden** (oder Rechner neustarten), damit die
Gruppenmitgliedschaft aktiv wird.

## Prüfen

```bash
groups | grep input
```

Wenn `input` in der Ausgabe erscheint, ist alles bereit.

## Warum ist das nötig?

Eingabegeräte unter `/dev/input/event*` gehören standardmäßig `root:input`.
Ohne Mitgliedschaft in der `input`-Gruppe kann DikTux die Tastaturereignisse
nicht lesen und globale Hotkeys funktionieren nicht.
