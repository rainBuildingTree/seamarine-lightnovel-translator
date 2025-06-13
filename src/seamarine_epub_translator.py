import sys
from PyQt5.QtWidgets import QApplication, QDialog
from settings import load_settings, save_settings
from gui.dialogs import APIKeyDialog, TierSelectionDialog
from gui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    settings = load_settings()
    # Check if authentication is configured (either API key or Vertex AI)
    auth_configured = False
    if settings.get("use_vertex_ai", False):
        # For Vertex AI, project_id and location are essential. SA key is optional (for ADC).
        if settings.get("gcp_project_id") and settings.get("gcp_location"):
            auth_configured = True
    elif settings.get("api_key"):
        auth_configured = True
    if not auth_configured:
        api_dialog = APIKeyDialog(settings) # Pass settings to the dialog
        
        if api_dialog.exec_() == QDialog.Accepted:
            # Settings are modified in-place by APIKeyDialog
            save_settings(settings) # Save the updated settings        
        else:
            sys.exit(0)

    # Show TierSelectionDialog only if API key is used and tier is not set
    if not settings.get("use_vertex_ai") and not settings.get("tier"):        
        tier_dialog = TierSelectionDialog(settings)
        if tier_dialog.exec_() == QDialog.Accepted:
            # TierSelectionDialog saves settings internally
            pass
        else:
            settings["tier"] = "free"  # Default to free if cancelled
            save_settings(settings)

    main_window = MainWindow(settings)
    main_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
