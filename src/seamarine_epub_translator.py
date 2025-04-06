import sys
from PyQt5.QtWidgets import QApplication, QDialog
from settings import load_settings, save_settings
from gui.dialogs import APIKeyDialog, TierSelectionDialog
from gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    settings = load_settings()
    api_key = settings.get("api_key")
    tier = settings.get("tier")

    if not api_key:
        api_dialog = APIKeyDialog()
        if api_dialog.exec_() == QDialog.Accepted:
            api_key = api_dialog.api_key
            settings["api_key"] = api_key
            save_settings(settings)
        else:
            sys.exit(0)

    if not tier:
        tier_dialog = TierSelectionDialog(settings)
        if tier_dialog.exec_() == QDialog.Accepted:
            settings["tier"] = tier_dialog.tier
            save_settings(settings)
        else:
            settings["tier"] = "free"  # or handle as needed

    main_window = MainWindow(settings)
    main_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
