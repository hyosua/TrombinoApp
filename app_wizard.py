import sys
import os
import tempfile
from PySide6.QtWidgets import (QWizard, QWidget, QWizardPage, QVBoxLayout, QLineEdit, 
                             QLabel, QListWidget,QListWidgetItem, QAbstractItemView, QSplitter,
                             QComboBox, QFileDialog, QMessageBox, QProgressDialog, QApplication)
from PySide6.QtCore import Qt, QSize, QThread, Signal
from PySide6.QtGui import QIcon

from utils import read_excel, resize_image, create_word_doc, SUPPORTED_FORMATS
from widgets import NameListWidget, PhotoDropWidget, FileDropZone

# --- Thread de Traitement (pour ne pas geler l'UI) ---

class PhotoProcessingThread(QThread):
    """
    Thread pour redimensionner les images en arrière-plan.
    """
    progressUpdated = Signal(int) # Progrès (0-100)
    imageProcessed = Signal(str, str) # Chemin original, chemin traité
    finished = Signal(int, int) # Nombre succès, nombre échecs

    def __init__(self, file_paths, output_dir):
        super().__init__()
        self.file_paths = file_paths
        self.output_dir = output_dir

    def run(self):
        total = len(self.file_paths)
        success_count = 0
        fail_count = 0
        for i, path in enumerate(self.file_paths):
            processed_path = resize_image(path, self.output_dir)
            if processed_path:
                self.imageProcessed.emit(path, processed_path)
                success_count += 1
            else:
                fail_count += 1
            self.progressUpdated.emit(int((i + 1) * 100 / total))
        
        self.finished.emit(success_count, fail_count)

# --- L'Assistant Principal (Wizard) ---

class TrombinoscopeWizard(QWizard):
    """
    L'assistant principal qui guide l'utilisateur à travers les 5 étapes.
    Il stocke également les données partagées entre les pages.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Données partagées
        self.student_list = []
        self.processed_photos = {} # dict {original_path: processed_path}
        self.associations = {} # dict {processed_path: student_name}
        
        # Créer un dossier temporaire pour les images redimensionnées
        self.temp_dir = os.path.join(tempfile.gettempdir(), "TrombinoAppCache")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.addPage(StartPage())
        self.addPage(ExcelPage())
        self.addPage(PhotosPage())
        self.addPage(AssociationPage())
        self.addPage(ExportPage())

        self.setWindowTitle("Assistant Trombinoscope")
        self.setWizardStyle(QWizard.ModernStyle)
        self.setFixedSize(800, 600) # Taille fixe pour la simplicité


# --- Page 1: Démarrer ---

class StartPage(QWizardPage):
    # Fichier: app_wizard.py

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("1. Nouveau Trombinoscope")
        self.setSubTitle("Donnez un nom et une description à votre projet.")
        
        # Layout principal de la page
        main_layout = QVBoxLayout(self)
        
        # Conteneur pour le contenu
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Ajout du contenu
        content_layout.addWidget(QLabel("Nom du trombinoscope (ex: Classe de 3ème A 2024):"))
        self.nameEdit = QLineEdit()
        self.nameEdit.setMaximumWidth(1000) # Empêche le champ de s'étirer trop
        content_layout.addWidget(self.nameEdit, 0, Qt.AlignCenter) # Centre le champ
        
        content_layout.addSpacing(20)
        
        content_layout.addWidget(QLabel("Description (optionnel):"))
        self.descEdit = QLineEdit()
        self.descEdit.setMaximumWidth(1000)
        content_layout.addWidget(self.descEdit, 0, Qt.AlignCenter)

        # Centrer le bloc de contenu dans la page
        main_layout.addStretch(1) # Ressort en haut
        main_layout.addWidget(content_widget, 0, Qt.AlignCenter) # Bloc de contenu
        main_layout.addStretch(1) # Ressort en bas
        
        # Enregistrer les champs
        self.registerField("trombiName*", self.nameEdit)
        self.registerField("trombiDesc", self.descEdit)

# --- Page 2: Importation de la Liste ---

class ExcelPage(QWizardPage):
    # Fichier: app_wizard.py

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("2. Importer la Liste des Étudiants")
        self.setSubTitle("Importez un fichier Excel (.xlsx). La première colonne doit contenir les noms.")
        
        # Layout principal de la page
        main_layout = QVBoxLayout(self)
        
        # Conteneur pour le contenu
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # --- Contenu ---
        self.dropZone = FileDropZone("Glissez-déposez votre fichier Excel ici\nou cliquez pour sélectionner")
        self.dropZone.setMinimumSize(500, 200) # Donne une taille minimale
        content_layout.addWidget(self.dropZone)
        
        self.previewList = QListWidget()
        self.previewList.setVisible(False)
        self.previewList.setMaximumHeight(200) # Limite la hauteur de l'aperçu
        self.previewList.setMinimumWidth(450)
        
        content_layout.addWidget(QLabel("Aperçu de la liste :"), 0, Qt.AlignCenter)
        content_layout.addWidget(self.previewList)
        
        self.statusLabel = QLabel()
        content_layout.addWidget(self.statusLabel, 0, Qt.AlignCenter)
        
        # Connecter les signaux
        self.dropZone.filesDropped.connect(self.handleFileDrop)
        self.dropZone.mousePressEvent = self.openFileDialog
        # --- Fin Contenu ---
        
        # Centrer le bloc de contenu dans la page
        main_layout.addStretch(1)
        main_layout.addWidget(content_widget, 0, Qt.AlignHCenter) # Centre le bloc horizontalement
        main_layout.addStretch(1)

    def openFileDialog(self, event=None):
        path, _ = QFileDialog.getOpenFileName(self, "Sélectionner un fichier Excel", "", "Fichiers Excel (*.xlsx)")
        if path:
            self.handleFileDrop([path])

    def handleFileDrop(self, file_paths):
        if not file_paths:
            return
        
        filepath = file_paths[0]
        if not filepath.endswith('.xlsx'):
            self.statusLabel.setText("<font color='red'>Erreur : Le fichier doit être un .xlsx</font>")
            return
            
        students = read_excel(filepath)
        if students is None:
            self.statusLabel.setText("<font color='red'>Erreur : Impossible de lire le fichier.</font>")
            return
            
        self.wizard().student_list = students
        
        self.previewList.clear()
        self.previewList.addItems(students)
        self.previewList.setVisible(True)
        self.statusLabel.setText(f"<font color='green'>{len(students)} étudiants importés avec succès.</font>")
        
        self.completeChanged.emit() # Signale que la page est "complète"

    def isComplete(self):
        # Le bouton "Suivant" ne s'active que si la liste est chargée
        return len(self.wizard().student_list) > 0

# --- Page 3: Importation des Photos ---

class PhotosPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("3. Importer les Photos")
        self.setSubTitle("Glissez-déposez toutes les photos dans la zone ci-dessous.")
        
        # Layout principal de la page
        main_layout = QVBoxLayout(self)
        
        # Conteneur pour le contenu
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # --- Contenu ---
        self.dropZone = FileDropZone("Glissez-déposez les photos ici (JPG, PNG, ...)")
        self.dropZone.setMinimumSize(500, 200)
        content_layout.addWidget(self.dropZone)
        self.dropZone.filesDropped.connect(self.handlePhotosDrop)
        
        self.statusLabel = QLabel("En attente de photos...")
        content_layout.addWidget(self.statusLabel, 0, Qt.AlignCenter)
        
        self.photoPreview = QListWidget()
        self.photoPreview.setViewMode(QListWidget.IconMode)
        self.photoPreview.setIconSize(QSize(60, 60))
        self.photoPreview.setResizeMode(QListWidget.Adjust)
        self.photoPreview.setMaximumHeight(250)
        self.photoPreview.setMinimumWidth(450)
        content_layout.addWidget(self.photoPreview)
        
        self.processingThread = None
        # --- Fin Contenu ---
        
        # Centrer le bloc de contenu dans la page
        main_layout.addStretch(1)
        main_layout.addWidget(content_widget, 0, Qt.AlignHCenter) # Centre le bloc horizontalement
        main_layout.addStretch(1)

    def handlePhotosDrop(self, file_paths):
        # Filtrer les fichiers supportés
        photo_paths = [p for p in file_paths if os.path.splitext(p)[1].lower() in SUPPORTED_FORMATS]
        
        if not photo_paths:
            self.statusLabel.setText("<font color='red'>Aucun format d'image valide trouvé.</font>")
            return
            
        self.wizard().processed_photos = {} # Réinitialiser
        self.photoPreview.clear()
        
        # Configurer et démarrer le thread de traitement
        output_dir = self.wizard().temp_dir
        self.processingThread = PhotoProcessingThread(photo_paths, output_dir)
        
        # Créer une boîte de dialogue de progression
        self.progressDialog = QProgressDialog("Traitement des images...", "Annuler", 0, 100, self)
        self.progressDialog.setWindowModality(Qt.WindowModal)
        
        self.processingThread.progressUpdated.connect(self.progressDialog.setValue)
        self.processingThread.imageProcessed.connect(self.onImageProcessed)
        self.processingThread.finished.connect(self.onProcessingFinished)
        self.progressDialog.canceled.connect(self.processingThread.terminate) # Permet d'annuler
        
        self.processingThread.start()

    def onImageProcessed(self, original_path, processed_path):
        # Ajouter une miniature à l'aperçu
        icon = QIcon(processed_path)
        item = QListWidgetItem(icon, "") # Pas de texte ici
        self.photoPreview.addItem(item)
        
        # Stocker le résultat
        self.wizard().processed_photos[original_path] = processed_path

    def onProcessingFinished(self, success_count, fail_count):
        self.progressDialog.setValue(100)
        self.progressDialog.close()
        
        self.statusLabel.setText(f"<font color='green'>{success_count} photos traitées.</font> "
                                 f"<font color='red'>{fail_count} échecs.</font>")
        self.completeChanged.emit()

    def isComplete(self):
        return len(self.wizard().processed_photos) > 0

# --- Page 4: Association Nom-Photo (Étape Critique) ---

class AssociationPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("4. Associer Noms et Photos")
        self.setSubTitle("Glissez un nom depuis la liste de gauche sur la photo correspondante à droite.")
        
        layout = QVBoxLayout(self)
        
        # Un 'splitter' permet de redimensionner les deux panneaux
        splitter = QSplitter(Qt.Horizontal)
        
        # Panneau de gauche : Noms
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("Noms à associer :"))
        self.nameList = NameListWidget()
        left_layout.addWidget(self.nameList)
        
        # Panneau de droite : Photos
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel("Photos :"))
        self.photoGrid = PhotoDropWidget()
        self.photoGrid.setAcceptDrops(True)
        self.photoGrid.viewport().setAcceptDrops(True)
        right_layout.addWidget(self.photoGrid)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([200, 600]) # Donner plus de place aux photos
        
        layout.addWidget(splitter)
        
        self.statusLabel = QLabel()
        layout.addWidget(self.statusLabel)
        
        # Connecter le signal d'association
        
        self.photoGrid.itemAssociated.connect(self.onAssociation)

    # Fichier : app_wizard.py
# Classe : AssociationPage

    def initializePage(self):
        """
        Appelée à chaque fois que la page devient active.
        On l'utilise pour charger les données des pages précédentes.
        """
        # --- DEBUG ---
        print("\n--- DEBUG PAGE 4: initializePage DÉMARRE ---")
        # --- FIN DEBUG ---

        self.nameList.clear()
        self.photoGrid.clear()
        self.wizard().associations = {}
        
        # Charger les noms
        students = self.wizard().student_list
        
        # --- DEBUG ---
        print(f"DEBUG PAGE 4: {len(students)} étudiants trouvés dans le wizard.")
        # --- FIN DEBUG ---
        
        self.nameList.addItems(students)
        
        # Charger les photos (uniquement celles qui ont été traitées)
        processed_paths = self.wizard().processed_photos.values()
        
        # --- DEBUG ---
        print(f"DEBUG PAGE 4: {len(processed_paths)} photos trouvées dans le wizard.")
        # --- FIN DEBUG ---
        
        for path in processed_paths:
            icon = QIcon(path)
            item = QListWidgetItem(icon, "[Non associé]") # Texte par défaut
            item.setData(Qt.UserRole, path) # Stocker le chemin de l'image
            item.setTextAlignment(Qt.AlignCenter)
            self.photoGrid.addItem(item)
            
        self.updateStatus()
        
        # --- DEBUG NOUVEAU ---
        # Ajoutez ces lignes à la toute fin de la fonction
        print(f"DEBUG PAGE 4: Vérification finale: Drag activé sur NameList? {self.nameList.dragEnabled()}")
        print(f"DEBUG PAGE 4: Vérification finale: Drops activés sur PhotoGrid? {self.photoGrid.acceptDrops()}")
        # --- FIN DEBUG NOUVEAU ---

        print(f"DEBUG PAGE 4: Listes (Noms: {self.nameList.count()}, Photos: {self.photoGrid.count()}) peuplées.")
        print("--- DEBUG PAGE 4: initializePage TERMINÉ ---\n")
        # --- FIN DEBUG ---
        """
        Appelée à chaque fois que la page devient active.
        On l'utilise pour charger les données des pages précédentes.
        """
        self.nameList.clear()
        self.photoGrid.clear()
        self.wizard().associations = {}
        
        # Charger les noms
        students = self.wizard().student_list
        self.nameList.addItems(students)
        
        # Charger les photos (uniquement celles qui ont été traitées)
        processed_paths = self.wizard().processed_photos.values()
        for path in processed_paths:
            icon = QIcon(path)
            item = QListWidgetItem(icon, "[Non associé]") # Texte par défaut
            item.setData(Qt.UserRole, path) # Stocker le chemin de l'image
            item.setTextAlignment(Qt.AlignCenter)
            self.photoGrid.addItem(item)
            
        self.updateStatus()

    def onAssociation(self, photo_path, student_name):
        # Mettre à jour le modèle de données central
        self.wizard().associations[photo_path] = student_name
        self.updateStatus()

    def updateStatus(self):
        total_photos = self.photoGrid.count()
        total_noms = self.nameList.count()
        self.statusLabel.setText(f"Photos restantes : {total_photos} | Noms restants : {total_noms}")

    def isComplete(self):
        # L'utilisateur peut passer à la suite même si tout n'est pas associé
        return True 

# --- Page 5: Vérification et Exportation ---

class ExportPage(QWizardPage):
    # Fichier: app_wizard.py

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("5. Finaliser et Exporter")
        self.setSubTitle("Vérifiez les associations et exportez au format Word (.docx).")
        
        # Layout principal de la page
        main_layout = QVBoxLayout(self)
        
        # Conteneur pour le contenu
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # --- Contenu ---
        self.summaryLabel = QLabel()
        self.summaryLabel.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.summaryLabel)
        
        content_layout.addSpacing(30)
        
        layout_label = QLabel("Options d'affichage (Photos par page) :")
        layout_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(layout_label)
        
        self.layoutCombo = QComboBox()
        self.layoutCombo.addItems(["3x4 (12)", "4x5 (20)", "5x6 (30)"])
        self.layoutCombo.setMaximumWidth(200)
        content_layout.addWidget(self.layoutCombo, 0, Qt.AlignCenter)
        # --- Fin Contenu ---
        
        # Centrer le bloc de contenu dans la page
        main_layout.addStretch(1)
        main_layout.addWidget(content_widget, 0, Qt.AlignCenter) # Centre le bloc
        main_layout.addStretch(1)
        
        # L'export est géré par le bouton "Finish" du Wizard
        
    def initializePage(self):
        associations = self.wizard().associations
        total_photos = len(self.wizard().processed_photos)
        total_noms = len(self.wizard().student_list)
        
        msg = f"<b>Récapitulatif :</b><br>"
        msg += f"- {len(associations)} associations créées.<br>"
        msg += f"- {total_photos - len(associations)} photos non associées.<br>"
        msg += f"- {total_noms - len(associations)} noms non associés.<br><br>"
        msg += "Prêt à exporter."
        self.summaryLabel.setText(msg)

    def validatePage(self):
        """
        Cette fonction est appelée quand l'utilisateur clique sur "Finish".
        Nous l'utilisons pour déclencher l'exportation.
        """
        save_path, _ = QFileDialog.getSaveFileName(self, "Enregistrer le trombinoscope", 
                                                   f"{self.field('trombiName')}.docx", 
                                                   "Documents Word (*.docx)")
        
        if not save_path:
            return False # Annule la fermeture du Wizard

        layout = self.layoutCombo.currentText().split(" ")[0]
        associations = self.wizard().associations
        
        if not associations:
            QMessageBox.warning(self, "Exportation vide", "Aucune association n'a été faite. L'exportation est annulée.")
            return False

        success = create_word_doc(associations, layout, save_path)
        
        if success:
            QMessageBox.information(self, "Exportation Réussie", f"Le fichier a été sauvegardé ici :\n{save_path}")
            return True # Autorise la fermeture du Wizard
        else:
            QMessageBox.critical(self, "Erreur d'Exportation", "Une erreur est survenue lors de la création du fichier Word.")
            return False # Reste sur la page