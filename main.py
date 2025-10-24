import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from app_wizard import TrombinoscopeWizard

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # ===== AMÉLIORATION DE L'UI =====
    
    # 1. Police par défaut plus grande
    default_font = QFont()
    default_font.setPointSize(12)  # Texte plus grand (était ~9 par défaut)
    app.setFont(default_font)
    
    # 2. Styles personnalisés pour des composants plus gros et lisibles
    custom_style = """
        /* Boutons plus gros et visibles */
        QPushButton {
            min-height: 40px;
            min-width: 120px;
            font-size: 14px;
            padding: 8px 16px;
            border-radius: 5px;
        }
        
        /* Champs de texte plus larges */
        QLineEdit, QTextEdit, QPlainTextEdit {
            min-height: 35px;
            font-size: 13px;
            min-width: 220px;
            padding: 6px;
        }
        
        /* SpinBox et ComboBox plus hauts */
        QSpinBox, QComboBox {
            min-height: 35px;
            font-size: 13px;
            padding: 4px;
            min-width: 200px;
            font-size: 16px;

        }
        
        /* Labels lisibles */
        QLabel {
            font-size: 18px;
        }
        
        /* Items de liste plus espacés */
        QListWidget {
            font-size: 16px;
            padding: 4px;
        }
        
        QListWidget::item {
            padding: 6px;
            min-height: 30px;
        }
        
        /* CheckBox et RadioButton */
        QCheckBox, QRadioButton {
            font-size: 16px;
            spacing: 8px;
        }
    """
    
    # 3. Appliquer le style (avec ou sans qdarkstyle)
    try:
        import qdarkstyle
        # Combiner qdarkstyle avec nos styles personnalisés
        app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyside6') + custom_style)
        # Si qdarkstyle n'est pas installé : uv pip install qdarkstyle
    except ImportError:
        # Utiliser seulement nos styles personnalisés
        app.setStyleSheet(custom_style)
    
    # ===== FIN AMÉLIORATION UI =====

    wizard = TrombinoscopeWizard()
    
    # Fenêtre plus grande par défaut
    wizard.resize(1000, 700)
    
    wizard.show()
    
    sys.exit(app.exec())