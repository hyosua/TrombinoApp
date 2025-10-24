from PySide6.QtWidgets import QListWidget, QAbstractItemView, QWidget, QVBoxLayout, QLabel, QProgressBar, QListWidgetItem
from PySide6.QtCore import Qt, Signal, QSize, QUrl, QMimeData
from PySide6.QtGui import QIcon, QDropEvent, QDragEnterEvent, QDragMoveEvent, QDrag

# --- Widget pour la liste des noms (Source du Drag) ---

class NameListWidget(QListWidget):
    """
    Liste qui contient les noms des étudiants.
    Elle permet de "tirer" (drag) les noms.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuration pour le drag
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSortingEnabled(True)
        
        print("DEBUG: NameListWidget (Source) initialisée. Mode: DragOnly.")
    
    def startDrag(self, supportedActions):
        """
        CRITIQUE: Cette méthode est appelée quand l'utilisateur commence à glisser un item.
        On doit EXPLICITEMENT créer les données MIME.
        """
        item = self.currentItem()
        if not item:
            print("DEBUG SOURCE: Pas d'item sélectionné pour le drag")
            return
        
        print(f"DEBUG SOURCE: startDrag appelé pour '{item.text()}'")
        
        # Créer les données MIME
        mime_data = QMimeData()
        mime_data.setText(item.text())  # Le nom de l'étudiant
        
        # Créer l'objet QDrag
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        
        # Optionnel: définir une icône pour le curseur pendant le drag
        if item.icon():
            drag.setPixmap(item.icon().pixmap(32, 32))
        
        print(f"DEBUG SOURCE: Drag démarré avec le texte: '{mime_data.text()}'")
        
        # Exécuter le drag (bloque jusqu'au drop ou annulation)
        result = drag.exec(Qt.MoveAction)
        
        print(f"DEBUG SOURCE: Drag terminé avec résultat: {result}")

# --- Widget pour la grille des photos (Cible du Drop) ---

class PhotoDropWidget(QListWidget):
    """
    Grille qui reçoit les noms (par drop).
    C'est le composant central de l'association (Page 4).
    """
    itemAssociated = Signal(str, str) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DropOnly) 
        
        self.setViewMode(QListWidget.IconMode)
        self.setResizeMode(QListWidget.Adjust)
        self.setMovement(QListWidget.Static)
        self.setIconSize(QSize(120, 120))
        self.setSpacing(10)
        self.setWordWrap(True)
        
        print("DEBUG: PhotoDropWidget (Cible) initialisée. Drops acceptés.")

    def dragEnterEvent(self, event: QDragEnterEvent):
        """ Appelé quand le glisser ENTRE dans le widget. """
        print(f"DEBUG CIBLE: dragEnterEvent. Données MIME : {event.mimeData().formats()}")
        if event.mimeData().hasText():
            print(f"... C'est du TEXTE: '{event.mimeData().text()}'. J'accepte.")
            event.acceptProposedAction()
            event.accept()  # CRITIQUE: accepter explicitement l'event
        else:
            print("... Ce n'est PAS du texte. Je refuse.")
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        """ Appelé quand le glisser BOUGE dans le widget. """
        # On accepte seulement si c'est du texte
        if event.mimeData().hasText():
            event.acceptProposedAction()
            event.accept()  # CRITIQUE: accepter explicitement l'event
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        """ Appelé quand l'utilisateur LÂCHE la souris. """
        print("DEBUG CIBLE: dropEvent. L'utilisateur a lâché la souris.")
        
        if not event.mimeData().hasText():
            print("... Drop refusé (pas de texte).")
            event.ignore()
            return

        item = self.itemAt(event.position().toPoint())
        
        if item:
            print(f"... Drop sur un item : {item.text()}")
            
            student_name = event.mimeData().text()
            photo_path = item.data(Qt.UserRole) 
            
            item.setText(student_name)
            self.itemAssociated.emit(photo_path, student_name)
            
            source_widget = event.source()
            if isinstance(source_widget, QListWidget):
                items_to_remove = source_widget.findItems(student_name, Qt.MatchExactly)
                if items_to_remove:
                    source_widget.takeItem(source_widget.row(items_to_remove[0]))
            
            event.acceptProposedAction()
            print(f"... Association RÉUSSIE : {student_name} -> {photo_path}")
        else:
            print("... Drop dans le vide (pas sur un item). Action ignorée.")
            event.ignore()

# --- Widget pour la zone de drop de Fichiers (Page 2 et 3) ---

class FileDropZone(QWidget):
    """
    Zone de "Glisser-Déposer" générique pour les fichiers (Excel ou Photos).
    La hitbox couvre maintenant 100% du widget.
    """
    filesDropped = Signal(list) # Émet une liste de chemins de fichiers

    def __init__(self, message="Glissez-déposez les fichiers ici", parent=None):
        super().__init__(parent)
        print("DEBUG: FileDropZone créée avec nouveau style !")
        self.setAcceptDrops(True)
        self.setMinimumHeight(400)
        
        # On donne un ID à notre widget pour le cibler avec CSS
        self.setObjectName("dropZoneWidget")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignCenter)
        # On retire le style du label, on le mettra sur le parent
        
        layout.addWidget(self.label)
        
        self.progressBar = QProgressBar()
        self.progressBar.setVisible(False)
        layout.addWidget(self.progressBar)
        
        # Appliquer le style par défaut au widget parent
        self.setStyleSheet(self._get_default_style())

    def _get_default_style(self):
        """ Retourne le CSS pour l'état normal. """
        return """
            #dropZoneWidget {
                border: 2px dashed #aaa;
                border-radius: 5px; 
                min-height: 4OOpx;
                background-color: transparent;
            }
            #dropZoneWidget QLabel {
                border: none; /* Le label n'a plus de bordure */
                padding: 40px;
                font-size: 14px;
                color: #888;
                background-color: transparent;
            }
        """
        
    def _get_active_style(self):
        """ Retourne le CSS pour l'état "drag-over". """
        return """
            #dropZoneWidget {
                border: 2px dashed #0078d7; /* Bleu */
                border-radius: 5px;
                height: 4OOpx;
                background-color: #f0f8ff; /* Bleu clair */
            }
            #dropZoneWidget QLabel {
                border: none;
                padding: 40px;
                font-size: 14px;
                color: #888;
                background-color: transparent;
            }
        """

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            # Appliquer le style "actif"
            self.setStyleSheet(self._get_active_style())
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        # Revenir au style par défaut
        self.setStyleSheet(self._get_default_style())

    def dropEvent(self, event: QDropEvent):
        # Revenir au style par défaut
        self.setStyleSheet(self._get_default_style())
        
        if event.mimeData().hasUrls():
            file_paths = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_paths.append(url.toLocalFile())
            
            if file_paths:
                self.filesDropped.emit(file_paths)
            event.acceptProposedAction()
        else:
            event.ignore()
    """
    Zone de "Glisser-Déposer" générique pour les fichiers (Excel ou Photos).
    """
    filesDropped = Signal(list) # Émet une liste de chemins de fichiers

    def __init__(self, message="Glissez-déposez les fichiers ici", parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 5px;
                padding: 40px;
                min-height: 4OOpx;
                font-size: 14px;
                color: #888;
            }
        """)
        layout.addWidget(self.label)
        
        self.progressBar = QProgressBar()
        self.progressBar.setVisible(False)
        layout.addWidget(self.progressBar)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.label.setStyleSheet("border: 2px dashed #0078d7; background-color: #f0f8ff;")
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.label.setStyleSheet("""    
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 5px;
                padding: 40px;
                min-height: 4OOpx;
                font-size: 14px;
                color: #888;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        self.dragLeaveEvent(None)
        if event.mimeData().hasUrls():
            file_paths = []
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    file_paths.append(url.toLocalFile())
            
            if file_paths:
                self.filesDropped.emit(file_paths)
            event.acceptProposedAction()
        else:
            event.ignore()