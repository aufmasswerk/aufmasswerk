
import sys, os, sqlite3, ast, operator, re, zipfile, shutil, subprocess
from urllib.parse import urlencode
from xml.etree import ElementTree as ET
from pathlib import Path
from datetime import datetime, date

from PySide6.QtCore import Qt, QDate, QRectF, QUrl, QEvent, QSettings, QTimer, QSize, QByteArray, QObject
from PySide6.QtGui import QImage, QPdfWriter, QPainter, QFont, QColor, QBrush, QPageSize, QPageLayout, QDesktopServices, QPixmap, QPalette, QRegion, QIcon
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QMenu,
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QStackedWidget, QLabel, QPushButton, QLineEdit, QTableWidget as _QtTableWidget, QTableWidgetItem,
    QMessageBox, QFormLayout, QDialog, QDialogButtonBox, QTextEdit, QSplitter,
    QAbstractItemView, QComboBox, QDoubleSpinBox, QSpinBox, QGroupBox, QCheckBox,
    QDateEdit, QFileDialog, QGridLayout, QInputDialog, QStyledItemDelegate, QAbstractItemDelegate,
    QStyle, QHeaderView, QFrame, QScrollArea, QColorDialog, QToolButton, QSizePolicy, QAbstractButton, QTreeWidget, QTreeWidgetItem
)

APP_NAME = "Aufmaßwerk"
APP_SUBTITLE = "das Programm fürs Handwerk"
APP_VERSION = "0.9.1"
# Das Programm hieß früher Aufmaßwerk. Wer es schon benutzt, behält seine Ordner;
# neue Installationen verwenden „Aufmasswerk“.
def _app_folder(base, new_name, old_name):
    return old_name if (base / old_name).exists() else new_name
DATA_FOLDER_NAME = _app_folder(Path.home() / ".local" / "share", "Aufmasswerk", "HandwerkPro")
CONFIG_FOLDER_NAME = _app_folder(Path.home() / ".config", "Aufmasswerk", "HandwerkPro")
if os.environ.get("HANDWERKPRO_DATA_DIR") and not os.environ.get("AUFMASSWERK_DATA_DIR"):
    os.environ["AUFMASSWERK_DATA_DIR"] = os.environ["HANDWERKPRO_DATA_DIR"]
def db_file_name(root):
    """Datenbankdatei eines Datenordners: eine vorhandene ältere Datei bleibt in Gebrauch."""
    return "handwerkpro.db" if (Path(root) / "handwerkpro.db").is_file() else "aufmasswerk.db"

# Die Oberflächensprache ist bewusst von den Geschäftsdokumenten getrennt.
# Rechnungen, Angebote und Mahnungen werden weiterhin mit ihren deutschen
# Vorlagentexten erzeugt. Dieser erste Prototyp übersetzt Navigation und Kunden.
UI_LANGUAGE = "de"
UI_TEXTS = {
    "de": {
        "language_title":"Sprache der Bedienoberfläche",
        "language_question":"Welche Sprache möchtest du für die Bedienung verwenden?",
        "language_note":"Geschäftsdokumente werden unabhängig davon weiterhin auf Deutsch erstellt.",
        "continue":"Weiter",
        "nav": ["🏠  Dashboard","👥  Kunden && Projekte","🧰  Leistungen","📋  Angebot && Aufmaß","🧾  Rechnungen","⚙  Einstellungen"],
        "customers_title":"Kunden & Projekte","customers_search":"Kunden suchen …",
        "customer_new":"Neuen Kunden hinzufügen","customer_edit":"Kunde bearbeiten","customer_delete":"Kunde löschen",
        "customer_select":"Bitte einen Kunden auswählen.","customer_number":"Kundennummer",
        "customer_headers":["Nr.","Firma / Name","Ansprechpartner","Ort","Telefon"],
        "project_headers":["Nr.","Projekt","Baustelle","Status"],
        "customer_new_title":"Neuer Kunde","customer_edit_title":"Kunde bearbeiten",
        "customer_fields":["Firma / Name *","Ansprechpartner","Straße / Hausnummer","PLZ","Ort","Telefon","E-Mail","Notizen"],
        "required_title":"Pflichtfeld","required_customer":"Bitte Firma oder Namen eintragen.",
        "select_customer_edit":"Bitte zuerst einen Kunden auswählen.",
        "not_possible":"Nicht möglich","customer_has_projects":"Dieser Kunde hat {count} Projekt(e).",
        "save":"Speichern","cancel":"Abbrechen",
        "ui_language":"Sprache der Bedienoberfläche","restart_language":"Die neue Sprache wird beim nächsten Programmstart verwendet.",
        "status": {"Offen":"Offen","In Arbeit":"In Arbeit","Wartet":"Wartet","Abgeschlossen":"Abgeschlossen","Storniert":"Storniert"},
    },
    "ar": {
        "language_title":"لغة واجهة المستخدم",
        "language_question":"ما اللغة التي تريد استخدامها لواجهة البرنامج؟",
        "language_note":"ستبقى عروض الأسعار والفواتير والمستندات التجارية باللغة الألمانية.",
        "continue":"متابعة",
        "nav": ["🏠  لوحة المعلومات","👥  العملاء","🧰  الخدمات","📋  عروض الأسعار","🧾  الفواتير","⚙  الإعدادات"],
        "customers_title":"إدارة العملاء","customers_search":"البحث عن عميل …",
        "customer_new":"إضافة عميل جديد","customer_edit":"تعديل بيانات العميل","customer_delete":"حذف العميل",
        "customer_select":"يرجى اختيار عميل.","customer_number":"رقم العميل",
        "customer_headers":["الرقم","الشركة / الاسم","جهة الاتصال","المدينة","الهاتف"],
        "project_headers":["الرقم","المشروع","موقع العمل","الحالة"],
        "customer_new_title":"عميل جديد","customer_edit_title":"تعديل بيانات العميل",
        "customer_fields":["الشركة / الاسم *","جهة الاتصال","الشارع / رقم المنزل","الرمز البريدي","المدينة","الهاتف","البريد الإلكتروني","ملاحظات"],
        "required_title":"حقل مطلوب","required_customer":"يرجى إدخال اسم الشركة أو اسم العميل.",
        "select_customer_edit":"يرجى اختيار عميل أولاً.",
        "not_possible":"غير ممكن","customer_has_projects":"لدى هذا العميل {count} مشروع/مشاريع مرتبطة.",
        "save":"حفظ","cancel":"إلغاء",
        "ui_language":"لغة واجهة المستخدم","restart_language":"سيتم استخدام اللغة الجديدة عند تشغيل البرنامج مرة أخرى.",
        "status": {"Offen":"مفتوح","In Arbeit":"قيد التنفيذ","Wartet":"في الانتظار","Abgeschlossen":"مكتمل","Storniert":"ملغى"},
    },
    "en": {
        "language_title":"User Interface Language",
        "language_question":"Which language would you like to use for the interface?",
        "language_note":"Business documents will continue to be generated in German regardless.",
        "continue":"Continue",
        "nav": ["🏠  Dashboard","👥  Customers && Projects","🧰  Services","📋  Quotes && Measurements","🧾  Invoices","⚙  Settings"],
        "customers_title":"Customers & Projects","customers_search":"Search customers …",
        "customer_new":"Add new customer","customer_edit":"Edit customer","customer_delete":"Delete customer",
        "customer_select":"Please select a customer.","customer_number":"Customer ID",
        "customer_headers":["No.","Company / Name","Contact Person","City","Phone"],
        "project_headers":["No.","Project","Site","Status"],
        "customer_new_title":"New Customer","customer_edit_title":"Edit Customer",
        "customer_fields":["Company / Name *","Contact Person","Street / House Number","ZIP Code","City","Phone","Email","Notes"],
        "required_title":"Required Field","required_customer":"Please enter a company or name.",
        "select_customer_edit":"Please select a customer first.",
        "not_possible":"Not possible","customer_has_projects":"This customer has {count} linked project(s).",
        "save":"Save","cancel":"Cancel",
        "ui_language":"User Interface Language","restart_language":"The new language will be used the next time the program starts.",
        "status": {"Offen":"Open","In Arbeit":"In Progress","Wartet":"Waiting","Abgeschlossen":"Completed","Storniert":"Cancelled"},
    }
}

def ui(key):
    return UI_TEXTS.get(UI_LANGUAGE,UI_TEXTS["de"]).get(key,UI_TEXTS["de"].get(key,key))

def ui_status(value):
    return ui("status").get(value,value)

def set_ui_language(language):
    global UI_LANGUAGE
    UI_LANGUAGE=language if language in UI_TEXTS else "de"
    app=QApplication.instance()
    if app:app.setLayoutDirection(Qt.RightToLeft if UI_LANGUAGE=="ar" else Qt.LeftToRight)

# Zentrale Übersetzung der Aktionsknöpfe. Sie verändert ausschließlich sichtbare
# Qt-Elemente, niemals Datenbankwerte oder Texte in Geschäftsdokumenten.
AR_ACTIONS = {
    "+ Ausgleich":"+ تسوية","+ Manuelle Position":"+ بند يدوي","+ Neues Angebot":"+ عرض سعر جديد",
    "+ Position aus Leistung übernehmen":"+ إضافة بند من الخدمات","+ Textblock":"+ فقرة نصية",
    "Abschließen":"إكمال","Alle auswählen":"تحديد الكل","Keine auswählen":"إلغاء تحديد الكل",
    "Angebot als PDF-Vorschau öffnen":"فتح معاينة عرض السعر PDF","Angebot aus Auswahl erstellen":"إنشاء عرض سعر من التحديد",
    "Angebot ausgeben":"إخراج عرض السعر","Angebot bearbeiten":"تعديل عرض السعر","Angebot löschen":"حذف عرض السعر",
    "Angebot per E-Mail senden":"إرسال عرض السعر بالبريد الإلكتروني","Angebotsauswahl anzeigen ▾":"إظهار قائمة عروض الأسعار ▾",
    "Angebotsauswahl ausblenden ▴":"إخفاء قائمة عروض الأسعار ▴","Angebotsformel speichern":"حفظ معادلة عرض السعر",
    "Positionen aus Angebot auswählen ▾":"اختيار بنود من عرض السعر ▾","Positionen aus Angebot ausblenden ▴":"إخفاء بنود عرض السعر ▴",
    "+ Markierte Positionen zum Aufmaß hinzufügen":"+ إضافة البنود المحددة إلى قياس الكميات",
    "Angebotsposition bearbeiten":"تعديل بند عرض السعر","Angebotsposition hinzufügen":"إضافة بند إلى عرض السعر",
    "Angebotsposition kopieren":"نسخ بند عرض السعر","Angebotsposition löschen":"حذف بند عرض السعر",
    "Archivieren":"أرشفة","Aufmaß als PDF speichern":"حفظ قياس الكميات بصيغة PDF",
    "Aufmaß als PDF-Vorschau öffnen":"فتح معاينة قياس الكميات PDF","Aufmaß anzeigen":"عرض قياس الكميات",
    "Aufmaß per E-Mail senden":"إرسال قياس الكميات بالبريد الإلكتروني","Aufmaß-Historie":"سجل قياس الكميات",
    "Aufmaßansicht schließen":"إغلاق عرض قياس الكميات","Aufmaßformel speichern":"حفظ معادلة القياس",
    "Aufmaßposition bearbeiten":"تعديل بند القياس","Aufmaßposition hinzufügen":"إضافة بند قياس",
    "Aufmaßzeile bearbeiten":"تعديل سطر القياس","Aufmaßzeile löschen":"حذف سطر القياس",
    "Ausgewählte Positionen übernehmen":"اعتماد البنود المحددة","Ausgewählte übernehmen":"اعتماد المحدد",
    "Auswahl als neues Angebot":"إنشاء عرض سعر جديد من التحديد","Auswahl aufheben":"إلغاء التحديد","Auswahl leeren":"مسح التحديد",
    "Backup löschen":"حذف النسخة الاحتياطية","Backup-Ordner öffnen":"فتح مجلد النسخ الاحتياطية",
    "Bearbeitung abbrechen":"إلغاء التعديل","Bearbeitungsleiste schließen":"إغلاق شريط التعديل",
    "Brutto aus Netto und MwSt. berechnen":"حساب الإجمالي من الصافي وضريبة القيمة المضافة",
    "Details ausblenden ▴":"إخفاء التفاصيل ▴","Dokument hinzufügen":"إضافة مستند","Dokument löschen":"حذف المستند",
    "Dokument öffnen":"فتح المستند","Dokumentbeschreibung speichern":"حفظ وصف المستند","Dokumente":"المستندات",
    "Dokumentenfenster schließen":"إغلاق نافذة المستندات","Dokumentordner öffnen":"فتح مجلد المستندات",
    "Entwurf aus Aufmaß aktualisieren":"تحديث المسودة من قياس الكميات","Farbe auswählen …":"اختيار اللون …",
    "Firmenangaben speichern":"حفظ بيانات الشركة","Freie Rechnung":"فاتورة حرة",
    "Fällige Rechnungen prüfen":"فحص الفواتير المستحقة","LV importieren (ODS/PDF)":"استيراد جدول الكميات (ODS/PDF)",
    "LV-Positionen ergänzen":"إضافة بنود جدول الكميات","Leistung bearbeiten":"تعديل الخدمة","Leistung kopieren":"نسخ الخدمة",
    "Leistung löschen":"حذف الخدمة","Leistungsformel speichern":"حفظ معادلة الخدمة","Logo auswählen …":"اختيار الشعار …",
    "Logo entfernen":"إزالة الشعار","Mahnung":"إنذار دفع","Mahnung erstellen":"إنشاء إنذار دفع",
    "Mahnung für Auswahl":"إنذار دفع للمحدد","Mahnungen aktualisieren":"تحديث الإنذارات","Mahnungsfenster schließen":"إغلاق نافذة الإنذار",
    "Manuelles Backup erstellen":"إنشاء نسخة احتياطية يدوياً","Markierte aus Auswahl entfernen":"إزالة المحدد من الاختيار",
    "Neue Leistung hinzufügen":"إضافة خدمة جديدة","Neues Projekt hinzufügen":"إضافة مشروع جديد",
    "Nummernkreise speichern":"حفظ تسلسل الأرقام","Offenen Rest als Skonto übernehmen":"اعتماد المبلغ المتبقي كخصم سداد",
    "Ohne Skonto vollständig bezahlt":"مدفوع بالكامل دون خصم","Original-PDF auswählen":"اختيار ملف PDF الأصلي",
    "Position aus Angebot ins Aufmaß übernehmen":"نقل بند من عرض السعر إلى قياس الكميات",
    "+ Position aus Angebot hinzufügen":"+ إضافة بند من عرض السعر",
    "+ Aufmaßzeile hinzufügen":"+ إضافة سطر قياس",
    "Details zur ausgewählten Position anzeigen ▾":"إظهار تفاصيل البند المحدد ▾",
    "Details zur ausgewählten Position ausblenden ▴":"إخفاء تفاصيل البند المحدد ▴",
    "Position aus Aufmaß entfernen":"إزالة البند من قياس الكميات","Position aus Rechnungsentwurf entfernen":"إزالة البند من مسودة الفاتورة",
    "Position in Angebot kopieren":"نسخ البند إلى عرض السعر","Projekt bearbeiten":"تعديل المشروع","Projekt löschen":"حذف المشروع",
    "Projektabrechnung auf 0 setzen":"تصفير حساب المشروع","Projektdokument öffnen oder Vorschau anzeigen":"فتح مستند المشروع أو معاينته",
    "Rechnung als PDF ausgeben":"إخراج الفاتورة بصيغة PDF","Rechnung aus Aufmaß erstellen":"إنشاء فاتورة من قياس الكميات",
    "Rechnung aus Aufmaß erzeugen":"إنشاء فاتورة من قياس الكميات","Rechnung freigeben":"اعتماد الفاتورة",
    "Rechnung per E-Mail senden":"إرسال الفاتورة بالبريد الإلكتروني","Rechnungsentwurf bearbeiten":"تعديل مسودة الفاتورة",
    "Rechnungsentwurf löschen":"حذف مسودة الفاتورة","Rechnungsvorschau öffnen":"فتح معاينة الفاتورة",
    "Standardrot":"الأحمر القياسي","Vorhandenen Beleg übernehmen":"إدخال مستند سابق","Vorschau & Freigabe":"المعاينة والاعتماد",
    "Weitere Aufmaßzeile hinzufügen":"إضافة سطر قياس آخر","Wiederherstellen":"استعادة","Zahlungsbuchung löschen":"حذف قيد الدفع",
    "Zahlungseingang":"دفعة واردة","Zahlungseingang hinzufügen":"إضافة دفعة واردة","Zurück zum Rechnungsentwurf":"العودة إلى مسودة الفاتورة",
    "Änderungen an Rechnungsposition speichern":"حفظ تعديلات بند الفاتورة","↑ Nach oben":"↑ إلى الأعلى","↓ Nach unten":"↓ إلى الأسفل",
    "Speichern":"حفظ","Abbrechen":"إلغاء","Save":"حفظ","Cancel":"إلغاء","Close":"إغلاق","OK":"موافق",
    "Angebot anlegen":"إنشاء عرض السعر","Neues Angebot erstellen":"إنشاء عرض سعر جديد","Projekt auswählen":"اختيار المشروع",
    "Position kopieren":"نسخ البند","Ausgabeformat wählen:":"اختيار صيغة الإخراج:","Formel prüfen":"فحص المعادلة",
}

def translate_widget_tree(root):
    """Übersetzt bestehende und dynamisch geöffnete Aktionsschaltflächen."""
    if UI_LANGUAGE!="ar" or root is None:return
    buttons=[]
    if isinstance(root,QAbstractButton):buttons.append(root)
    if isinstance(root,QWidget):buttons.extend(root.findChildren(QAbstractButton))
    for button in buttons:
        text=button.text()
        translated=AR_ACTIONS.get(text)
        if translated is None:translated=AR_ACTIONS.get(text.replace("&",""))
        if translated is not None:button.setText(translated)
        tip=button.toolTip()
        if tip in AR_ACTIONS:
            button.setToolTip(AR_ACTIONS[tip]);button.setAccessibleName(AR_ACTIONS[tip])

class UiTranslationFilter(QObject):
    def eventFilter(self,obj,event):
        if UI_LANGUAGE=="ar" and event.type() in (QEvent.Show,QEvent.ShowToParent):
            QTimer.singleShot(0,lambda target=obj:translate_widget_tree(target))
        return False

THEMES = {
    "klassisch": {"label":"Klassisch Blau", "accent":"#1f5f8b", "delete":"#d9475c"},
    "skandinavisch": {"label":"Skandinavisch Hell", "accent":"#1f5f8b", "delete":"#d9475c"},
    "dark_bernstein": {"label":"Dark Bernstein", "accent":"#ffb347", "delete":"#ff6474"},
    "cyber": {"label":"Cyber Neon", "accent":"#ff2bd6", "delete":"#ff4d7d"},
    "schiefer_salbei": {"label":"Schiefer & Salbei", "accent":"#8fbc8f", "delete":"#d47c7c"},
}
DEFAULT_THEME = "schiefer_salbei"

# Einheitliche Symbolsprache fuer kompakte Standardaktionen. QIcon.fromTheme
# nutzt das Desktop-Theme; das Qt-Standardsymbol verhindert leere Schaltflaechen
# auf Systemen mit unvollstaendigen Icon-Themes.
ACTION_ICONS = {
    "new": (("list-add", "document-new"), QStyle.SP_FileDialogNewFolder),
    "edit": (("document-edit", "edit-rename"), QStyle.SP_FileDialogDetailedView),
    "delete": (("edit-delete", "user-trash"), QStyle.SP_TrashIcon),
    "preview": (("document-preview", "view-preview"), QStyle.SP_FileDialogContentsView),
    "pdf": (("application-pdf", "document-export"), QStyle.SP_DialogSaveButton),
    "print": (("document-print", "printer"), QStyle.SP_DialogSaveButton),
    "email": (("mail-send", "document-send"), QStyle.SP_ArrowForward),
    "save": (("document-save",), QStyle.SP_DialogSaveButton),
    "cancel": (("dialog-cancel", "go-previous"), QStyle.SP_DialogCancelButton),
    "back": (("go-previous", "edit-undo"), QStyle.SP_ArrowBack),
    "open": (("document-open",), QStyle.SP_DialogOpenButton),
    "copy": (("edit-copy",), QStyle.SP_FileDialogListView),
    "refresh": (("view-refresh",), QStyle.SP_BrowserReload),
}

# Eigene kontrastreiche SVG-Pfade: unabhängig von Theme, Symbolfarbe und
# AppImage-Umgebung. Die Formen folgen der üblichen Desktop-Symbolsprache.
ACTION_SVGS = {
    "new": '<path d="M12 5v14M5 12h14"/>',
    "edit": '<path d="M4 20l4.7-1 10-10-3.7-3.7-10 10L4 20zm9.6-13.3 3.7 3.7"/>',
    "delete": '<path d="M5 7h14M9 7V4h6v3m2 0-1 13H8L7 7m3 3v7m4-7v7"/>',
    "preview": '<path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6z"/><circle cx="12" cy="12" r="2.8"/>',
    "pdf": '<path d="M6 2h8l4 4v16H6zM14 2v5h4M8 17h8M8 13h8"/>',
    "print": '<path d="M7 9V3h10v6M7 18H4V10h16v8h-3M7 15h10v6H7z"/>',
    "email": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M4 7l8 6 8-6"/>',
    "save": '<path d="M4 3h14l2 2v16H4zM8 3v6h8V3M8 21v-7h8v7"/>',
    "cancel": '<path d="M6 6l12 12M18 6 6 18"/>',
    "back": '<path d="M10 5l-7 7 7 7M4 12h17"/>',
    "open": '<path d="M3 7h7l2 2h9l-3 11H4zM3 7v13"/>',
    "copy": '<rect x="8" y="8" width="12" height="12" rx="1"/><path d="M16 8V4H4v12h4"/>',
    "refresh": '<path d="M20 7v5h-5M4 17v-5h5M19 12a7 7 0 00-12-5L4 10M5 12a7 7 0 0012 5l3-3"/>',
}

def bundled_action_icon(action):
    app=QApplication.instance();theme=(app.property("appTheme") if app else None) or DEFAULT_THEME
    colors=THEMES.get(theme,THEMES[DEFAULT_THEME])
    color=colors["delete"] if action=="delete" else colors["accent"]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
           f'fill="none" stroke="{color}" stroke-width="1.9" '
           f'stroke-linecap="round" stroke-linejoin="round">{ACTION_SVGS[action]}</svg>')
    renderer=QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap=QPixmap(24,24);pixmap.fill(Qt.transparent)
    painter=QPainter(pixmap);renderer.render(painter);painter.end()
    return QIcon(pixmap)

def action_icon(action):
    """Kontrastreiches eingebettetes SVG mit Qt-Fallback liefern."""
    icon=bundled_action_icon(action)
    if not icon.isNull():return icon
    return QApplication.style().standardIcon(ACTION_ICONS[action][1])

def icon_button(action, tooltip, slot=None, parent=None):
    """Eindeutige Textaktion; nur Löschen und E-Mail bleiben als Symbol."""
    if action in {"delete", "email"}:
        button = QToolButton(parent)
        button.setIcon(action_icon(action))
        button.setIconSize(QSize(16, 16))
        button.setFixedSize(QSize(26, 24))
        button.setAutoRaise(False)
    else:
        button = QPushButton(tooltip, parent)
    button.setToolTip(tooltip)
    button.setAccessibleName(tooltip)
    button.setAccessibleDescription(tooltip)
    button.setProperty("standardAction", action)
    if slot is not None:
        button.clicked.connect(slot)
    return button

def compact_hint(text="", parent=None):
    """Einheitliche platzsparende Hinweiszeile ohne kleinere Schrift."""
    label=QLabel(text,parent)
    label.setWordWrap(True)
    label.setContentsMargins(0,0,0,0)
    label.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Maximum)
    label.setObjectName("compactHint")
    label.setStyleSheet("padding:0; margin:0;")
    return label

BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
IS_PACKAGED = bool(os.environ.get("APPIMAGE")) or bool(getattr(sys, "frozen", False))
# Mehrere Firmen: Jede Firma hat einen eigenen Datenordner. Die Liste steht in
# ~/.config/Aufmaßwerk/firmen.json, die zuletzt benutzte Firma wird geöffnet.
COMPANY_REGISTRY = Path.home() / ".config" / CONFIG_FOLDER_NAME / "firmen.json"
DEFAULT_DATA_ROOT = Path.home() / ".local" / "share" / DATA_FOLDER_NAME
NEW_COMPANY_MARKER = ".neue_firma"

def load_company_registry():
    import json
    try:data=json.loads(COMPANY_REGISTRY.read_text(encoding="utf-8"))
    except Exception:data={}
    companies=[c for c in data.get("companies",[]) if isinstance(c,dict) and c.get("path")]
    if not any(Path(c["path"]).expanduser()==DEFAULT_DATA_ROOT for c in companies):
        companies.insert(0,{"path":str(DEFAULT_DATA_ROOT),"name":""})
    return {"companies":companies,"last":data.get("last") or str(DEFAULT_DATA_ROOT)}

def save_company_registry(data):
    import json
    COMPANY_REGISTRY.parent.mkdir(parents=True,exist_ok=True)
    COMPANY_REGISTRY.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")

if not os.environ.get("AUFMASSWERK_DATA_DIR"):
    _last=Path(load_company_registry()["last"]).expanduser()
    if _last!=DEFAULT_DATA_ROOT and _last.is_dir():os.environ["AUFMASSWERK_DATA_DIR"]=str(_last)

DATA_ROOT = Path(os.environ.get("AUFMASSWERK_DATA_DIR", "")).expanduser() if os.environ.get("AUFMASSWERK_DATA_DIR") else (
    Path.home() / ".local" / "share" / DATA_FOLDER_NAME
)
DATA_ROOT.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_ROOT / db_file_name(DATA_ROOT)
if not DB_PATH.exists() and not (DATA_ROOT / NEW_COMPANY_MARKER).exists():
    migration_candidates = []
    if os.environ.get("AUFMASSWERK_MIGRATION_SOURCE"):
        migration_candidates.append(Path(os.environ["AUFMASSWERK_MIGRATION_SOURCE"]).expanduser())
    source_db = next((p for p in migration_candidates if p.is_file() and p.resolve() != DB_PATH.resolve()), None)
    if source_db:
        shutil.copy2(source_db, DB_PATH)
BACKUP_DIR = DATA_ROOT / "backups"
BACKUP_DIR.mkdir(exist_ok=True)
DOCUMENT_ROOT = DATA_ROOT / "documents"
DOCUMENT_DIR = DOCUMENT_ROOT / "Rechnungen"
DOCUMENT_DIR.mkdir(parents=True, exist_ok=True)
REMINDER_DOCUMENT_DIR = DOCUMENT_ROOT / "Mahnungen"
REMINDER_DOCUMENT_DIR.mkdir(parents=True, exist_ok=True)
PREVIEW_DIR = DOCUMENT_ROOT / "Vorschau"
PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
OFFER_DOCUMENT_DIR = DOCUMENT_ROOT / "Angebote"
OFFER_DOCUMENT_DIR.mkdir(parents=True, exist_ok=True)
MEASUREMENT_DOCUMENT_DIR = DOCUMENT_ROOT / "Aufmass"
MEASUREMENT_DOCUMENT_DIR.mkdir(parents=True, exist_ok=True)
PROJECT_DOCUMENT_DIR = DOCUMENT_ROOT / "Projekte"
PROJECT_DOCUMENT_DIR.mkdir(parents=True, exist_ok=True)
LETTER_DOCUMENT_DIR = DOCUMENT_ROOT / "Briefe"
LETTER_DOCUMENT_DIR.mkdir(parents=True, exist_ok=True)
HISTORICAL_INVOICE_DIR = DOCUMENT_ROOT / "Historische_Belege"
HISTORICAL_INVOICE_DIR.mkdir(parents=True, exist_ok=True)
(DATA_ROOT / "settings").mkdir(parents=True, exist_ok=True)


def apply_application_theme(app,theme_name):
    """Zentrales QSS laden; bei unbekannter Auswahl sicher auf Salbei fallen."""
    theme_name=theme_name if theme_name in THEMES else DEFAULT_THEME
    path=BASE_DIR/"themes"/f"{theme_name}.qss"
    if not path.is_file():
        return False
    app.setProperty("appTheme",theme_name)
    app.setStyleSheet(path.read_text(encoding="utf-8")+"""
QLineEdit#cellEditor, QComboBox#cellEditor { margin:0; padding:0 4px; min-height:0; border:1px solid palette(highlight); border-radius:0; }
QComboBox#cellEditor QLineEdit { margin:0; padding:0; min-height:0; border:none; }
""")
    return True


def current_theme_color(role="accent"):
    app=QApplication.instance();theme=(app.property("appTheme") if app else None) or DEFAULT_THEME
    return THEMES.get(theme,THEMES[DEFAULT_THEME])[role]


def desktop_process_environment():
    """Umgebung fuer Systemprogramme ausserhalb des AppImage bereinigen."""
    env=os.environ.copy()
    for key in ("LD_LIBRARY_PATH","PYTHONHOME","PYTHONPATH","QT_PLUGIN_PATH",
                "QML2_IMPORT_PATH","QML_IMPORT_PATH"):
        env.pop(key,None)
    return env


def open_desktop_url(url,parent=None,title="Öffnen"):
    """Desktop-Aufrufe zentral und außerhalb der AppImage-Bibliotheksumgebung."""
    def failed():
        if parent is not None:
            QMessageBox.warning(parent,title,
                "Die Standardanwendung konnte nicht geöffnet werden. "
                "Bitte prüfen Sie die Zuordnung in den Systemeinstellungen.")
    if sys.platform.startswith("linux") and os.environ.get("LD_LIBRARY_PATH"):
        opener=shutil.which("xdg-open")
        if not opener:
            failed();return False
        target=url.toLocalFile() if url.isLocalFile() else url.toString(QUrl.FullyEncoded)
        try:
            process=subprocess.Popen([opener,target],env=desktop_process_environment(),
                start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        except OSError:
            failed();return False
        # Fehler auch nach erfolgreichem Prozessstart melden. Der Dateibetrachter
        # bleibt unabhängig geöffnet, wenn Aufmaßwerk später beendet wird.
        timer=QTimer(parent or QApplication.instance());timer.setInterval(150)
        def check_result():
            code=process.poll()
            if code is None:return
            timer.stop();timer.deleteLater()
            if code!=0:failed()
        timer.timeout.connect(check_result);timer.start()
        return True
    if QDesktopServices.openUrl(url):return True
    failed();return False


def open_desktop_file(path,parent=None,title="PDF-Vorschau"):
    """Vorhandene Datei oder Ordner mit der Standardanwendung öffnen."""
    target=Path(path).expanduser().resolve()
    if not target.exists():
        if parent is not None:
            QMessageBox.warning(parent,title,f"Die Datei oder der Ordner wurde nicht gefunden:\n\n{target}")
        return False
    return open_desktop_url(QUrl.fromLocalFile(str(target)),parent,title)


def mail_send_dir(env=None):
    """Dedizierter, fuer Mailprogramme freigebbarer Versandordner."""
    env=env or desktop_process_environment()
    documents_dir=Path.home()/"Dokumente"
    xdg_user_dir=shutil.which("xdg-user-dir")
    if xdg_user_dir:
        try:
            configured=subprocess.run([xdg_user_dir,"DOCUMENTS"],env=env,text=True,
                capture_output=True,check=True).stdout.strip()
            if configured:documents_dir=Path(configured).expanduser()
        except (OSError,subprocess.SubprocessError):
            pass
    return documents_dir/_app_folder(documents_dir,"Aufmasswerk-Versand","HandwerkPro-Versand")


def installed_flatpak_thunderbirds(flatpak,env=None):
    """Installierte Thunderbird-Flatpaks erkennen (App-IDs sind case-sensitive)."""
    env=env or desktop_process_environment()
    try:
        output=subprocess.run([flatpak,"list","--app","--columns=application"],env=env,
            text=True,capture_output=True,check=True).stdout
        installed={line.strip() for line in output.splitlines() if line.strip()}
    except (OSError,subprocess.SubprocessError):
        installed=set()
    candidates=("org.mozilla.thunderbird","org.mozilla.Thunderbird","net.thunderbird.Thunderbird")
    return [app_id for app_id in candidates if app_id in installed]


def default_mail_client_id(env=None):
    """Desktop-Datei des eingestellten mailto-Handlers ermitteln."""
    env=env or desktop_process_environment()
    queries=(("xdg-mime","query","default","x-scheme-handler/mailto"),
             ("xdg-settings","get","default-url-scheme-handler","mailto"))
    for command in queries:
        executable=shutil.which(command[0])
        if not executable:continue
        try:
            output=subprocess.run([executable,*command[1:]],env=env,text=True,
                capture_output=True,check=True).stdout
        except (OSError,subprocess.SubprocessError):
            continue
        # Manche xdg-settings-Versionen schreiben zusaetzlich "handler is".
        for line in reversed(output.splitlines()):
            value=line.strip()
            if value.lower().endswith(".desktop"):
                return value
    return ""


def is_thunderbird_mail_client(desktop_id):
    return "thunderbird" in (desktop_id or "").lower()


def is_kmail_mail_client(desktop_id):
    return "kmail" in (desktop_id or "").lower()


def flatpak_has_read_access(flatpak,app_id,directory,env=None):
    """Pruefen, ob genau der Versandordner bereits mindestens lesbar ist."""
    env=env or desktop_process_environment();directory=str(Path(directory).resolve())
    outputs=[]
    for args in (("override","--user","--show",app_id),("info","--show-permissions",app_id)):
        try:
            outputs.append(subprocess.run([flatpak,*args],env=env,text=True,
                capture_output=True,check=True).stdout)
        except (OSError,subprocess.SubprocessError):
            pass
    entries=[]
    for output in outputs:
        for line in output.splitlines():
            if line.startswith("filesystems="):
                entries.extend(line.partition("=")[2].rstrip(";").split(";"))
    return any(entry.split(":",1)[0] in (directory,"home","host","host-os")
               for entry in entries if entry and not entry.startswith("!"))


def ensure_flatpak_send_access(parent,flatpak,app_id,send_dir,env=None):
    """Mit Zustimmung nur den Versandordner read-only fuer Thunderbird freigeben."""
    env=env or desktop_process_environment()
    if flatpak_has_read_access(flatpak,app_id,send_dir,env):return True
    answer=QMessageBox.question(parent,"Thunderbird-Zugriff einrichten",
        "Thunderbird ist als Flatpak abgeschirmt und benötigt Leserechte auf den "
        "Aufmaßwerk-Versandordner.\n\nAufmaßwerk kann jetzt ausschließlich diesen Ordner "
        "schreibgeschützt für Thunderbird freigeben:\n\n"+str(send_dir)+
        "\n\nEs wird kein Zugriff auf das übrige Benutzerverzeichnis erteilt.",
        QMessageBox.Yes|QMessageBox.No,QMessageBox.Yes)
    if answer!=QMessageBox.Yes:return False
    try:
        subprocess.run([flatpak,"override","--user",f"--filesystem={send_dir}:ro",app_id],
            env=env,text=True,capture_output=True,check=True)
        return flatpak_has_read_access(flatpak,app_id,send_dir,env)
    except (OSError,subprocess.SubprocessError):
        return False


def file_generated_document(db,project_id,source,name,description):
    """Kopie eines erzeugten Dokuments in der Projektablage ablegen. Gleicher
    Name ersetzt die ältere Fassung. Fehler hier dürfen nie den eigentlichen
    Vorgang (PDF, E-Mail) verhindern."""
    try:
        project=db.project(project_id) if project_id else None;src_path=Path(source)
        if not project or not src_path.is_file():return
        folder=PROJECT_DOCUMENT_DIR/str(project["number"]);folder.mkdir(parents=True,exist_ok=True)
        name=re.sub(r"[^A-Za-z0-9ÄÖÜäöüß._ -]+","_",name).strip() or src_path.name
        target=folder/name
        if src_path.resolve()!=target.resolve():shutil.copy2(src_path,target)
        relative=target.relative_to(DATA_ROOT).as_posix();now=datetime.now().isoformat(timespec="seconds")
        row=db.conn.execute("SELECT id FROM project_documents WHERE project_id=? AND filepath=?",(project_id,relative)).fetchone()
        if row:db.conn.execute("UPDATE project_documents SET description=?,created_at=? WHERE id=?",(description,now,row["id"]))
        else:db.conn.execute("""INSERT INTO project_documents(project_id,filename,filepath,description,created_at)
                                VALUES(?,?,?,?,?)""",(project_id,target.name,relative,description,now))
        db.conn.commit()
    except Exception:
        pass

def today_de():
    return date.today().strftime("%d.%m.%Y")

def assign_existing_documents(db):
    """Einmalig: bereits erzeugte PDFs anhand der Nummer im Dateinamen dem
    Projekt zuordnen. Liefert (zugeordnet, nicht zuordenbar)."""
    marker=DATA_ROOT/"settings"/"dokumente_den_projekten_zugeordnet"
    if marker.exists():return 0,[]
    offers={r["number"]:r for r in db.conn.execute("SELECT number,project_id FROM offers").fetchall()}
    invoices={r["number"]:r for r in db.conn.execute("SELECT number,project_id,invoice_type,source_pdf FROM invoices").fetchall()}
    projects={r["number"]:r for r in db.conn.execute("SELECT id,number FROM projects").fetchall()}
    by_source={Path(r["source_pdf"]).name:r for r in invoices.values() if r["source_pdf"]}
    assigned=0;unknown=[]
    def mtime(f):return datetime.fromtimestamp(f.stat().st_mtime).strftime("%d.%m.%Y")
    for folder,kind in [(OFFER_DOCUMENT_DIR,"Angebot"),(DOCUMENT_DIR,"Rechnung"),(REMINDER_DOCUMENT_DIR,"Mahnung"),
                        (MEASUREMENT_DOCUMENT_DIR,"Aufmaß"),(HISTORICAL_INVOICE_DIR,"Altbeleg")]:
        if not folder.is_dir():continue
        for f in sorted(folder.iterdir()):
            if not f.is_file():continue
            number=f.stem.split("_",1)[0];pid=None;desc=""
            if kind=="Angebot" and number in offers:
                pid=offers[number]["project_id"];desc=f"Angebot {number} – erstellt am {mtime(f)}"
            elif kind in ("Rechnung","Mahnung") and number in invoices:
                pid=invoices[number]["project_id"]
                m=re.match(r"^[^_]+_(.+)_(\d{4}-\d{2}-\d{2})$",f.stem)
                desc=(f"{m.group(1).replace('_',' ')} zu Rechnung {number} vom {de_date(m.group(2))}" if kind=="Mahnung" and m
                      else f"Mahnung zu Rechnung {number} – erstellt am {mtime(f)}" if kind=="Mahnung"
                      else f"{invoices[number]['invoice_type']} {number} – erstellt am {mtime(f)}")
            elif kind=="Aufmaß":
                m=re.match(r"Aufmass_(.+?)(?:_\d{4}-\d{2}-\d{2})?$",f.stem)
                if m and m.group(1) in projects:pid=projects[m.group(1)]["id"];desc=f"Aufmaß – erstellt am {mtime(f)}"
            elif kind=="Altbeleg" and f.name in by_source:
                r=by_source[f.name];pid=r["project_id"];desc=f"{r['invoice_type']} {r['number']} – übernommener Originalbeleg"
            if pid:file_generated_document(db,pid,f,f.name,desc);assigned+=1
            else:unknown.append(f"{folder.name}/{f.name}")
    marker.parent.mkdir(parents=True,exist_ok=True)
    marker.write_text(f"{datetime.now().isoformat(timespec='seconds')}: {assigned} zugeordnet, {len(unknown)} nicht zuordenbar\n"
                      +"\n".join(unknown),encoding="utf-8")
    return assigned,unknown

def compose_email_with_pdf(parent,pdf_path,recipient,subject,body):
    """Mailentwurf ohne Zugangsdaten oeffnen; Anhang mit klarem Fallback."""
    pdf_path=Path(pdf_path).expanduser().resolve();recipient=(recipient or "").strip()
    env=desktop_process_environment()
    mail_client=default_mail_client_id(env)

    # Nur wenn Thunderbird tatsaechlich Standard ist, wird seine spezielle
    # Anhang-Schnittstelle verwendet. Thunderbird als Flatpak sieht den
    # Aufmaßwerk-Datenordner nicht direkt.
    # Das Dokument-Portal laesst sich bei Thunderbirds -compose-Schnittstelle
    # nicht verlaesslich uebergeben. Daher wird nur ein eigener Versandordner
    # read-only freigegeben; niemals das gesamte Home-Verzeichnis.
    flatpak=shutil.which("flatpak")
    if is_thunderbird_mail_client(mail_client) and flatpak:
        for thunderbird_app in installed_flatpak_thunderbirds(flatpak,env):
            try:
                send_dir=mail_send_dir(env);send_dir.mkdir(parents=True,exist_ok=True)
                if not ensure_flatpak_send_access(parent,flatpak,thunderbird_app,send_dir,env):
                    QMessageBox.warning(parent,"Thunderbird-Zugriff fehlt",
                        "Die PDF wurde erstellt, Thunderbird darf den Versandordner aber nicht lesen. "
                        "Die E-Mail wird deshalb ohne automatischen Anhang geöffnet; bitte hängen Sie "
                        "die angezeigte Datei manuell an.")
                    break
                attachment_path=send_dir/pdf_path.name
                shutil.copy2(pdf_path,attachment_path)
                def tb_value(value):
                    return str(value or "").replace("\\","\\\\").replace("'","\\'")
                compose=",".join([
                    f"to='{tb_value(recipient)}'",f"subject='{tb_value(subject)}'",
                    f"body='{tb_value(body)}'",f"attachment='{tb_value(attachment_path.as_uri())}'"])
                subprocess.Popen([flatpak,"run",thunderbird_app,"-compose",compose],env=env,
                    start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                QMessageBox.information(parent,"E-Mail vorbereiten",
                    "Thunderbird wurde mit der PDF als Anhang geöffnet. Bitte prüfen "
                    "Sie Empfänger, Text und Anhang vor dem Senden.\n\nVersandkopie: "+str(attachment_path))
                return True
            except (OSError,subprocess.SubprocessError,IndexError,shutil.Error):
                continue

    thunderbird=shutil.which("thunderbird")
    if is_thunderbird_mail_client(mail_client) and thunderbird:
        try:
            def tb_value(value):
                return str(value or "").replace("\\","\\\\").replace("'","\\'")
            compose=",".join([f"to='{tb_value(recipient)}'",f"subject='{tb_value(subject)}'",
                f"body='{tb_value(body)}'",f"attachment='{tb_value(pdf_path.as_uri())}'"])
            subprocess.Popen([thunderbird,"-compose",compose],env=env,start_new_session=True,
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            QMessageBox.information(parent,"E-Mail vorbereiten",
                "Thunderbird wurde mit der PDF als Anhang geöffnet. Bitte prüfen "
                "Sie Empfänger, Text und Anhang vor dem Senden.\n\nPDF: "+str(pdf_path))
            return True
        except OSError:
            pass

    # KMail verarbeitet Anhaenge ueber seine Composer-Schnittstelle direkt.
    # Das umgeht fehlerhafte kde-open/kdialog-Zwischenschritte einzelner
    # Distributionen, respektiert KMail aber nur, wenn es Standardclient ist.
    if is_kmail_mail_client(mail_client):
        kmail=shutil.which("kmail")
        if kmail:
            args=[kmail,"--composer","--subject",subject,"--body",body,
                  "--attach",pdf_path.as_uri()]
            if recipient:args.append(recipient)
            try:
                subprocess.Popen(args,env=env,start_new_session=True,
                    stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                QMessageBox.information(parent,"E-Mail vorbereiten",
                    "KMail wurde mit der PDF als Anhang geöffnet. Bitte prüfen "
                    "Sie vor dem Senden Empfänger, Text und PDF-Anhang.\n\nPDF: "+str(pdf_path))
                return True
            except OSError:
                pass

    # Fuer alle anderen Clients entscheidet die Linux-Desktopzuordnung.
    xdg_email=shutil.which("xdg-email")
    if xdg_email:
        args=["--subject",subject,"--body",body,"--attach",str(pdf_path)]
        if recipient:args.append(recipient)
        try:
            subprocess.Popen([xdg_email,*args],env=env,start_new_session=True,
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            QMessageBox.information(parent,"E-Mail vorbereiten",
                "Das Standard-Mailprogramm wurde geöffnet. Bitte prüfen Sie vor "
                "dem Senden Empfänger, Text und PDF-Anhang.\n\nPDF: "+str(pdf_path))
            return True
        except OSError:
            pass
    query=urlencode({"subject":subject,"body":body})
    mail_opened=open_desktop_url(QUrl(f"mailto:{recipient}?{query}"),parent,"E-Mail öffnen")
    open_desktop_file(pdf_path.parent,parent,"PDF-Ordner öffnen")
    QMessageBox.information(parent,"PDF bitte manuell anhängen",
        "Der Mailentwurf wurde ohne automatisch angehängte Datei geöffnet, weil "
        "der Desktop keinen zuverlässigen Anhang-Aufruf bereitstellt. Der Ordner "
        "mit der PDF wurde ebenfalls geöffnet. Bitte hängen Sie diese Datei an:\n\n"
        +str(pdf_path))
    return mail_opened


class PlainTextPasteEdit(QTextEdit):
    """Mehrzeiliges Textfeld, das beim Einfuegen nur sichtbaren Text annimmt."""
    def insertFromMimeData(self,source):
        if source and source.hasText():
            text=source.text().replace("\r\n","\n").replace("\r","\n")
            self.textCursor().insertText(text)
            return
        super().insertFromMimeData(source)


class QTableWidget(_QtTableWidget):
    """Einheitliche, persistente Spaltenverwaltung fuer alle Tabellen.

    Die bestehende Anwendung kann weiterhin unveraendert ``QTableWidget``
    verwenden. Beim ersten Anzeigen wird die Tabelle anhand ihrer Seite, ihres
    Attributnamens und ihrer Ueberschriften eindeutig identifiziert.
    """
    SETTINGS_FILE = DATA_ROOT / "settings" / "column_layouts.ini"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._column_settings_key = None
        self._column_layout_restored = False
        self._restoring_columns = False
        self._columns_locked = False

        header = self.horizontalHeader()
        header.setSectionsMovable(True)
        header.setSectionsClickable(True)
        self.verticalHeader().setMinimumWidth(30)
        header.sectionResized.connect(self._schedule_column_layout_save)
        header.sectionMoved.connect(self._schedule_column_layout_save)

        self._column_save_timer = QTimer(self)
        self._column_save_timer.setSingleShot(True)
        self._column_save_timer.setInterval(250)
        self._column_save_timer.timeout.connect(self._save_column_layout)

        # Der Schalter sitzt kompakt in der ohnehin freien Ecke zwischen
        # Zeilen- und Spaltenkopf. So verdeckt er keine Spaltenueberschrift.
        self._column_lock_button = QPushButton("🔓", self)
        self._column_lock_button.setObjectName("columnLockButton")
        self._column_lock_button.setToolTip(
            "Spaltenbreiten und -reihenfolge gegen versehentliche Aenderungen sperren"
        )
        self._column_lock_button.clicked.connect(self.toggle_columns_locked)

    def _settings(self):
        self.SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        return QSettings(str(self.SETTINGS_FILE), QSettings.IniFormat)

    def _owner_and_attribute(self):
        owner = self.parentWidget()
        while owner is not None and type(owner).__module__ != __name__:
            owner = owner.parentWidget()
        if owner is None:
            owner = self.window()
        attribute = next(
            (name for name, value in vars(owner).items() if value is self), "table"
        )
        return type(owner).__name__, attribute

    def _layout_key(self):
        if self._column_settings_key:
            return self._column_settings_key
        owner, attribute = self._owner_and_attribute()
        labels = []
        for column in range(self.columnCount()):
            item = self.horizontalHeaderItem(column)
            labels.append(item.text().strip() if item else str(column))
        # Schraegstriche sind in QSettings Gruppentrenner und werden ersetzt.
        identity = "|".join((owner, attribute, *labels))
        self._column_settings_key = "tables/" + re.sub(r"[^A-Za-z0-9_.-]+", "_", identity)
        return self._column_settings_key

    def showEvent(self, event):
        super().showEvent(event)
        if not self._column_layout_restored:
            self._restore_column_layout()
        self._position_column_lock_button()
        self._column_lock_button.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_column_lock_button()

    def _position_column_lock_button(self):
        if not hasattr(self, "_column_lock_button"):
            return
        vertical_header = self.verticalHeader()
        horizontal_header = self.horizontalHeader()
        self._column_lock_button.setGeometry(
            vertical_header.geometry().x(), horizontal_header.geometry().y(),
            vertical_header.width(), horizontal_header.height()
        )

    def _schedule_column_layout_save(self, *_args):
        if self._column_layout_restored and not self._restoring_columns and not self._columns_locked:
            self._column_save_timer.start()

    def _save_column_layout(self):
        if not self._column_layout_restored or self._restoring_columns:
            return
        settings = self._settings()
        key = self._layout_key()
        settings.setValue(key + "/header_state", self.horizontalHeader().saveState())
        settings.setValue(key + "/locked", self._columns_locked)
        settings.sync()

    def _restore_column_layout(self):
        self._restoring_columns = True
        try:
            settings = self._settings()
            key = self._layout_key()
            state = settings.value(key + "/header_state")
            if state:
                self.horizontalHeader().restoreState(state)
            locked = settings.value(key + "/locked", False, type=bool)
            self._apply_columns_locked(locked)
            self._column_layout_restored = True
        finally:
            self._restoring_columns = False

    def _apply_columns_locked(self, locked):
        self._columns_locked = bool(locked)
        header = self.horizontalHeader()
        header.setSectionsMovable(not self._columns_locked)
        header.setSectionResizeMode(
            QHeaderView.Fixed if self._columns_locked else QHeaderView.Interactive
        )
        self._column_lock_button.setText("🔒" if self._columns_locked else "🔓")
        self._column_lock_button.setToolTip(
            "Spalten wieder anpassbar machen" if self._columns_locked else
            "Spaltenbreiten und -reihenfolge gegen versehentliche Aenderungen sperren"
        )

    def set_columns_locked(self, locked):
        """Oeffentliche Schnittstelle, auch fuer Tests und kuenftige Module."""
        if not self._column_layout_restored:
            self._restore_column_layout()
        self._apply_columns_locked(locked)
        self._save_column_layout()

    def toggle_columns_locked(self):
        self.set_columns_locked(not self._columns_locked)

def de_num(v, decimals=2):
    return f"{float(v or 0):,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X",".")

def money(v):
    return de_num(v) + " €"

def parse_de_number(value):
    s=str(value or "").replace("€","").replace(" ","").strip()
    if "," in s:s=s.replace(".","").replace(",",".")
    return float(s or 0)

def de_date(value):
    if not value:
        return ""
    s=str(value)[:10]
    try:
        return datetime.strptime(s,"%Y-%m-%d").strftime("%d.%m.%Y")
    except Exception:
        return s

def one_line(value):
    """Zeilenumbrüche und mehrfache Leerzeichen für kompakte UI-Texte glätten."""
    return " ".join(str(value or "").split())

def draw_pdf_logo(painter, logo_path, x, y, max_w, max_h):
    """Firmenlogo ohne Qualitätsverlust und transparente Außenränder zeichnen."""
    path=Path(str(logo_path or "")).expanduser()
    if not path.is_file():return 0
    pixmap=QPixmap(str(path))
    if pixmap.isNull():return 0
    # Bildgeneratoren und Grafikprogramme lassen häufig viel unsichtbare
    # Leinwand um ein Logo stehen. Für die Skalierung zählt nur der tatsächlich
    # sichtbare Bereich, sonst wird besonders der Folgeseitenkopf unnötig klein.
    source=QRegion(pixmap.mask()).boundingRect() if pixmap.hasAlphaChannel() else pixmap.rect()
    if source.isEmpty():source=pixmap.rect()
    ratio=source.width()/max(1,source.height())
    target_w=min(float(max_w),float(max_h)*ratio)
    target_h=target_w/ratio
    target=QRectF(float(x),float(y)+(float(max_h)-target_h)/2,target_w,target_h)
    # Nicht vorab auf 96 Bildschirmpixel verkleinern: QPdfWriter erhält das
    # hochauflösende Original und kann es beim Drucken scharf wiedergeben.
    painter.save();painter.setRenderHint(QPainter.SmoothPixmapTransform,True)
    painter.drawPixmap(target,pixmap,QRectF(source));painter.restore()
    return target_w

LETTERHEAD_KINDS=[("offer","Angebote"),("invoice","Rechnungen"),("reminder","Mahnungen"),("measurement","Aufmaß"),("letter","Briefe")]

def letterhead_settings():
    return QSettings(str(DATA_ROOT/"settings"/"briefbogen.ini"),QSettings.IniFormat)

class Letterhead:
    """Briefbogen einer Firma als Seitenhintergrund (Seite 1, optional Folgeseite)."""
    def __init__(self,kind,writer):
        s=letterhead_settings();self.writer=writer
        self.first=str(s.value("first","") or "");self.follow=str(s.value("follow","") or "") or self.first
        self.active=bool(self.first and Path(self.first).is_file() and s.value(f"use/{kind}",True,type=bool))
        self.top_mm=float(s.value("top_mm",45) or 45);self.bottom_mm=float(s.value("bottom_mm",30) or 30)
        layout=writer.pageLayout();res=writer.resolution()
        self.full=layout.fullRectPixels(res);self.paint=layout.paintRectPixels(res);self._images={}
    def _px(self,mm):return mm/25.4*self.writer.resolution()
    def content_top(self,default):
        return max(default,self._px(self.top_mm)-self.paint.y()) if self.active else default
    def limit(self,default):
        """Unterste nutzbare y-Position (Platz für „Seite n“ bleibt frei)."""
        return min(default,self.full.height()-self._px(self.bottom_mm)-self.paint.y()-18) if self.active else default
    def page_number_y(self):
        return self.full.height()-self._px(self.bottom_mm)-self.paint.y()-16
    def _image(self,path):
        if path not in self._images:
            document=QPdfDocument();document.load(path);image=QImage()
            if document.pageCount()>0:
                size=document.pagePointSize(0)
                image=document.render(0,QSize(int(size.width()/72*200),int(size.height()/72*200)))
            self._images[path]=image
        return self._images[path]
    def draw(self,painter,first=True):
        if not self.active:return
        image=self._image(self.first if first else self.follow)
        if not image.isNull():
            painter.drawImage(QRectF(-self.paint.x(),-self.paint.y(),self.full.width(),self.full.height()),image)

def draw_pdf_brand(painter, logo_path, company_name, x, y, max_w, max_h,
                   text_size=18, text_width=None):
    """Logo oder textbasierten Firmennamen zeichnen, niemals beides zugleich."""
    logo_w=draw_pdf_logo(painter,logo_path,x,y,max_w,max_h)
    if logo_w:return logo_w
    box=QRectF(float(x),float(y),float(text_width or max_w),float(max_h))
    name=str(company_name or APP_NAME);size=float(text_size)
    while size>7:
        font=QFont("DejaVu Sans");font.setPointSizeF(size);font.setBold(True);painter.setFont(font)
        needed=painter.boundingRect(box,Qt.AlignLeft|Qt.AlignVCenter|Qt.TextWordWrap,name)
        if needed.height()<=box.height() and needed.width()<=box.width()+1:break
        size-=0.5
    painter.drawText(
        box,
        Qt.AlignLeft|Qt.AlignVCenter|Qt.TextWordWrap,
        name)
    return 0


class StatusColorDelegate(QStyledItemDelegate):
    """Hebt bekannte Statuswerte dezent hervor, ohne Daten oder Bedienung zu ändern."""
    COLORS = {
        "offen": ("#e7f4ec", "#21643b"),
        "aktiv": ("#e7f4ec", "#21643b"),
        "in arbeit": ("#e7f4ec", "#21643b"),
        "teilbezahlt": ("#e8f1f8", "#285d82"),
        "entwurf": ("#fff4d8", "#795d12"),
        "wartet": ("#fff4d8", "#795d12"),
        "abgeschlossen": ("#e9eef3", "#485866"),
        "bezahlt": ("#e9eef3", "#485866"),
        "ausgeglichen": ("#e9eef3", "#485866"),
        "archiviert": ("#eceff2", "#66717a"),
        "storniert": ("#f5e9e9", "#824747"),
        "abgelehnt": ("#f5e9e9", "#824747"),
        "überfällig": ("#f5e9e9", "#824747"),
    }

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        colors=self.COLORS.get(str(index.data() or "").strip().lower())
        if colors and not (option.state & QStyle.State_Selected):
            option.backgroundBrush=QBrush(QColor(colors[0]))
            option.palette.setColor(QPalette.ColorRole.Text,QColor(colors[1]))

OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}


def _xml_escape(text):
    return (str(text or "").replace("&","&amp;").replace("<","&lt;")
            .replace(">","&gt;").replace('"',"&quot;").replace("'","&apos;"))

def offer_tax_lines(offer,net):
    """Summenblock eines Angebots: [(Text, Betrag oder "", fett)]."""
    keys=offer.keys()
    mode=(offer["tax_mode"] or "") if "tax_mode" in keys else ""
    if mode.startswith("Steuerschuldnerschaft"):
        return [("Angebotssumme netto",money(net),True),
                ("Steuerschuldnerschaft des Leistungsempfängers (§ 13b UStG): "
                 "Die Umsatzsteuer schuldet der Leistungsempfänger.","",False)]
    rate=float(offer["vat_rate"]) if "vat_rate" in keys and offer["vat_rate"] is not None else 19.0
    if rate<=0:
        return [("Angebotssumme netto",money(net),True)]
    vat=net*rate/100.0
    return [("Summe netto",money(net),False),
            (f'zzgl. {("%g"%rate).replace(".",",")} % MwSt.',money(vat),False),
            ("Angebotssumme brutto",money(net+vat),True)]

def create_simple_offer_odt(path, offer, positions, company):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)

    def cval(k):
        try:
            return (company[k] or "") if company else ""
        except Exception:
            return ""

    total=sum(float(p["quantity"] or 0)*float(p["unit_price"] or 0) for p in positions)

    def para(text, style="TextBody"):
        return '<text:p text:style-name="%s">%s</text:p>' % (style, _xml_escape(text))

    paras=[]
    paras.append(para(cval("company_name") or APP_NAME,"Title"))
    sender=" · ".join(x for x in [cval("street"),(cval("zip")+" "+cval("city")).strip(),cval("phone"),cval("email")] if x)
    if sender: paras.append(para(sender,"Small"))
    paras.append(para(""))
    for x in [offer["company"],offer["customer_contact"],offer["customer_street"],
              f'{offer["customer_zip"] or ""} {offer["customer_city"] or ""}'.strip()]:
        if x: paras.append(para(x))
    paras.append(para(""))
    paras.append(para(f'Angebot {offer["number"]}',"Heading1"))
    paras.append(para(f'Projekt: {offer["project_number"]} - {offer["project_name"]}'))
    if offer["site"]: paras.append(para(f'Baustelle: {offer["site"]}'))
    if offer["title"]: paras.append(para(f'Bezeichnung: {offer["title"]}'))
    paras.append(para(f'Datum: {de_date(offer["created_at"])}'))
    paras.append(para(""))

    table_rows=[]
    headers=["Pos.","Beschreibung","Menge","Einheit","EP","Gesamt"]
    table_rows.append("<table:table-row>"+"".join(
        f'<table:table-cell><text:p>{_xml_escape(h)}</text:p></table:table-cell>' for h in headers
    )+"</table:table-row>")

    last_title=None;last_sub=None
    for pos in positions:
        tno,tt,sno,st=lv_group_values(pos)
        if tno and (tno,tt)!=last_title:
            table_rows.append('<table:table-row><table:table-cell table:number-columns-spanned="6"><text:p text:style-name="Heading1">'
                              +_xml_escape(f"TITEL {tno} – {tt}")+'</text:p></table:table-cell></table:table-row>')
            last_title=(tno,tt);last_sub=None
        if sno and (sno,st)!=last_sub:
            table_rows.append('<table:table-row><table:table-cell table:number-columns-spanned="6"><text:p><text:span>'
                              +_xml_escape(f"Untertitel {sno} – {st}")+'</text:span></text:p></table:table-cell></table:table-row>')
            last_sub=(sno,st)
        desc=pos["short_text"] or ""
        longtext=(pos["long_text"] or "").strip()
        if longtext and longtext!=desc:
            desc += " - " + longtext
        line=float(pos["quantity"] or 0)*float(pos["unit_price"] or 0)
        vals=[pos["position_no"],desc,de_num(pos["quantity"],3),pos["unit"],
              money(pos["unit_price"]),money(line)]
        table_rows.append("<table:table-row>"+"".join(
            f'<table:table-cell><text:p>{_xml_escape(v)}</text:p></table:table-cell>' for v in vals
        )+"</table:table-row>")

    if offer["notes"]:
        paras.append(para(""))
        paras.append(para("Hinweise:","Heading1"))
        paras.append(para(offer["notes"]))

    content = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-content
 xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
 xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
 xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
 office:version="1.2">
 <office:automatic-styles>
  <style:style style:name="Title" style:family="paragraph"><style:text-properties fo:font-size="18pt" fo:font-weight="bold"/></style:style>
  <style:style style:name="Heading1" style:family="paragraph"><style:text-properties fo:font-size="13pt" fo:font-weight="bold"/></style:style>
  <style:style style:name="Small" style:family="paragraph"><style:text-properties fo:font-size="8pt"/></style:style>
  <style:style style:name="TextBody" style:family="paragraph"><style:text-properties fo:font-size="10pt"/></style:style>
 </office:automatic-styles>
 <office:body><office:text>
 %s
 <table:table table:name="Angebotspositionen">
  <table:table-column table:number-columns-repeated="6"/>
  %s
 </table:table>
 %s
 </office:text></office:body>
</office:document-content>""" % ("".join(paras), "".join(table_rows),
        "".join(para(f"{text}: {amount}" if amount else text,"Heading1" if bold else "TextBody")
                for text,amount,bold in offer_tax_lines(offer,total)))

    styles = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles
 xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
 xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
 office:version="1.2">
 <office:styles>
  <style:default-style style:family="paragraph">
   <style:paragraph-properties fo:margin-bottom="0.08in"/>
   <style:text-properties fo:font-family="DejaVu Sans" fo:font-size="10pt"/>
  </style:default-style>
 </office:styles>
</office:document-styles>"""

    meta = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-meta
 xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
 office:version="1.2">
 <office:meta><meta:generator>Aufmaßwerk 0.8.7.0</meta:generator></office:meta>
</office:document-meta>"""

    manifest = """<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest
 xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"
 manifest:version="1.2">
 <manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.text"/>
 <manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
 <manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>
 <manifest:file-entry manifest:full-path="meta.xml" manifest:media-type="text/xml"/>
</manifest:manifest>"""

    with zipfile.ZipFile(path,"w") as z:
        z.writestr("mimetype","application/vnd.oasis.opendocument.text",compress_type=zipfile.ZIP_STORED)
        z.writestr("content.xml",content,compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("styles.xml",styles,compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("meta.xml",meta,compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("META-INF/manifest.xml",manifest,compress_type=zipfile.ZIP_DEFLATED)



def lv_group_values(row):
    """Liefert Titel/Untertitel. Bei alten Daten wird nur eine neutrale Titelnummer abgeleitet."""
    def get(name):
        try:return (row[name] or "").strip()
        except:return ""
    tno=get("title_no");tt=get("title_text")
    sno=get("subtitle_no");st=get("subtitle_text")
    pos=get("position_no")
    if not tno and "." in pos:
        first=pos.split(".",1)[0].strip()
        if first:
            tno=first
            tt=f"Titel {first}"
    if tno and not tt:tt=f"Titel {tno}"
    if sno and not st:st=f"Untertitel {sno}"
    return tno,tt,sno,st

def eval_formula(text):
    s = (text or "").strip().lower().replace("×","*").replace("x","*").replace(",",".")
    if not s:
        return 0.0
    if not re.fullmatch(r"[0-9\.\+\-\*\/\(\)\s]+", s):
        raise ValueError("Erlaubt sind nur Zahlen, +, -, *, / und Klammern.")
    node = ast.parse(s, mode="eval")
    def ev(n):
        if isinstance(n, ast.Expression): return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int,float)): return float(n.value)
        if isinstance(n, ast.BinOp) and type(n.op) in OPS: return OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in OPS: return OPS[type(n.op)](ev(n.operand))
        raise ValueError("Ungültige Formel.")
    return float(ev(node))

BACKUP_NAME_RE=re.compile(r"^(?:aufmasswerk|handwerkpro)_(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})_(.+)\.db$")

def backup_info(path):
    """(Zeitpunkt, Anlass) einer Sicherungsdatei."""
    m=BACKUP_NAME_RE.match(path.name)
    if m:
        try:return datetime.strptime(m.group(1)+" "+m.group(2),"%Y-%m-%d %H-%M-%S"),m.group(3)
        except ValueError:pass
    return datetime.fromtimestamp(path.stat().st_mtime),""

def prune_backups():
    """Gestaffelt aufbewahren: 2 Tage alle, 30 Tage eine pro Tag, 6 Monate eine pro
    Woche, danach eine pro Monat. Manuelle Sicherungen bleiben immer."""
    now=datetime.now();kept=set();keep=[]
    files=sorted([p for p in BACKUP_DIR.glob("*.db") if BACKUP_NAME_RE.match(p.name)],key=lambda p:backup_info(p)[0],reverse=True)
    for index,p in enumerate(files):
        when,reason=backup_info(p);age=(now-when).days
        if reason.startswith("manuell") or index<20 or age<2:keep.append(p);continue
        if age<30:bucket=("d",when.date())
        elif age<183:bucket=("w",)+tuple(when.isocalendar()[:2])
        else:bucket=("m",when.year,when.month)
        if bucket in kept:
            try:p.unlink()
            except Exception:pass
        else:kept.add(bucket);keep.append(p)

BACKUP_WORDS={"aufmass":"Aufmaß","aufmasszeile":"Aufmaßzeile","aufmassposition":"Aufmaßposition","uebernahme":"Übernahme",
    "leistungsuebernahme":"Leistungsübernahme","loeschen":"löschen","aenderung":"Änderung","hinzufuegen":"hinzufügen",
    "aendern":"ändern","null":"0","inline":"","tabzeile":"neue Zeile"}
def backup_label(reason):
    fixed={"start":"Programmstart","ende":"Programmende","manuell":"Manuelle Sicherung"}
    if reason in fixed:return fixed[reason]
    words=[BACKUP_WORDS.get(w,w) for w in reason.split("_")]
    text=" ".join(w for w in words if w)
    return "vor "+text[4:5].upper()+text[5:] if text.startswith("vor ") else text

class DB:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.init()

    def init(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS customers(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          number TEXT UNIQUE NOT NULL,
          company TEXT NOT NULL,
          contact TEXT, street TEXT, zip TEXT, city TEXT, phone TEXT, email TEXT, notes TEXT
        );
        CREATE TABLE IF NOT EXISTS projects(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          number TEXT UNIQUE NOT NULL,
          customer_id INTEGER NOT NULL,
          name TEXT NOT NULL,
          site TEXT,
          status TEXT DEFAULT 'Offen',
          notes TEXT,
          FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE RESTRICT
        );
        CREATE TABLE IF NOT EXISTS project_lv_sources(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          project_id INTEGER NOT NULL,
          source_name TEXT,
          imported_at TEXT NOT NULL,
          notes TEXT,
          FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS project_documents(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          project_id INTEGER NOT NULL,
          filename TEXT NOT NULL,
          filepath TEXT NOT NULL,
          description TEXT,
          created_at TEXT NOT NULL,
          FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_project_documents_project_id
          ON project_documents(project_id);
        CREATE TABLE IF NOT EXISTS letters(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          customer_id INTEGER NOT NULL,
          project_id INTEGER,
          letter_date TEXT NOT NULL,
          subject TEXT NOT NULL,
          filename TEXT NOT NULL,
          filepath TEXT NOT NULL,
          created_at TEXT NOT NULL,
          FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE RESTRICT,
          FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS idx_letters_customer_id ON letters(customer_id);
        CREATE INDEX IF NOT EXISTS idx_letters_project_id ON letters(project_id);
        CREATE TABLE IF NOT EXISTS project_lv_positions(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          source_id INTEGER NOT NULL,
          project_id INTEGER NOT NULL,
          position_no TEXT NOT NULL,
          short_text TEXT NOT NULL,
          long_text TEXT,
          quantity REAL NOT NULL DEFAULT 0,
          unit TEXT NOT NULL,
          source_unit_price REAL NOT NULL DEFAULT 0,
          sort_order INTEGER NOT NULL DEFAULT 0,
          title_no TEXT, title_text TEXT,
          subtitle_no TEXT, subtitle_text TEXT,
          FOREIGN KEY(source_id) REFERENCES project_lv_sources(id) ON DELETE CASCADE,
          FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS project_lv_selection(
          project_id INTEGER NOT NULL,
          lv_position_id INTEGER NOT NULL,
          created_at TEXT NOT NULL,
          PRIMARY KEY(project_id,lv_position_id),
          FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
          FOREIGN KEY(lv_position_id) REFERENCES project_lv_positions(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS services(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          number TEXT UNIQUE NOT NULL,
          short_text TEXT NOT NULL,
          long_text TEXT,
          unit TEXT NOT NULL DEFAULT 'Stk.',
          purchase_price REAL NOT NULL DEFAULT 0,
          sales_price REAL NOT NULL DEFAULT 0,
          wage_share REAL NOT NULL DEFAULT 0,
          material_share REAL NOT NULL DEFAULT 0,
          active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS offers(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          number TEXT UNIQUE NOT NULL,
          project_id INTEGER NOT NULL,
          title TEXT,
          status TEXT DEFAULT 'Entwurf',
          created_at TEXT NOT NULL,
          notes TEXT,
          FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS offer_positions(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          offer_id INTEGER NOT NULL,
          service_id INTEGER,
          position_no TEXT NOT NULL,
          short_text TEXT NOT NULL,
          long_text TEXT,
          formula TEXT,
          quantity REAL NOT NULL DEFAULT 0,
          unit TEXT NOT NULL,
          unit_price REAL NOT NULL DEFAULT 0,
          sort_order INTEGER NOT NULL DEFAULT 0,
          source_type TEXT NOT NULL DEFAULT 'Manuell',
          title_no TEXT, title_text TEXT,
          subtitle_no TEXT, subtitle_text TEXT,
          FOREIGN KEY(offer_id) REFERENCES offers(id) ON DELETE CASCADE,
          FOREIGN KEY(service_id) REFERENCES services(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS measure_history(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          project_id INTEGER NOT NULL,
          offer_position_id INTEGER,
          formula TEXT,
          quantity REAL NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL,
          note TEXT,
          FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
          FOREIGN KEY(offer_position_id) REFERENCES offer_positions(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS measurement_positions(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          project_id INTEGER NOT NULL,
          offer_position_id INTEGER NOT NULL UNIQUE,
          created_at TEXT NOT NULL,
          billed_quantity REAL NOT NULL DEFAULT 0,
          location TEXT,
          FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
          FOREIGN KEY(offer_position_id) REFERENCES offer_positions(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS measurement_snapshots(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          measurement_position_id INTEGER NOT NULL,
          total_quantity REAL NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL,
          note TEXT,
          FOREIGN KEY(measurement_position_id) REFERENCES measurement_positions(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS invoices(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          number TEXT UNIQUE NOT NULL,
          project_id INTEGER NOT NULL,
          invoice_type TEXT NOT NULL DEFAULT 'Teilrechnung',
          installment_no INTEGER NOT NULL DEFAULT 1,
          deduct_previous INTEGER NOT NULL DEFAULT 1,
          title TEXT,
          status TEXT NOT NULL DEFAULT 'Entwurf',
          created_at TEXT NOT NULL,
          due_date TEXT,
          vat_rate REAL NOT NULL DEFAULT 19,
          tax_mode TEXT NOT NULL DEFAULT 'Regelbesteuerung',
          performance_from TEXT,
          performance_to TEXT,
          skonto_percent REAL NOT NULL DEFAULT 0,
          skonto_due_date TEXT,
          security_enabled INTEGER NOT NULL DEFAULT 0,
          security_percent REAL NOT NULL DEFAULT 0,
          construction_enabled INTEGER NOT NULL DEFAULT 0,
          construction_percent REAL NOT NULL DEFAULT 0,
          construction_label TEXT NOT NULL DEFAULT 'Bauwesen',
          net_total REAL NOT NULL DEFAULT 0,
          gross_total REAL NOT NULL DEFAULT 0,
          payable_total REAL NOT NULL DEFAULT 0,
          notes TEXT,
          is_historical INTEGER NOT NULL DEFAULT 0,
          source_pdf TEXT,
          imported_at TEXT,
          FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE RESTRICT
        );
        CREATE TABLE IF NOT EXISTS company_settings(
          id INTEGER PRIMARY KEY CHECK(id=1),
          company_name TEXT, street TEXT, zip TEXT, city TEXT, phone TEXT, email TEXT, website TEXT,
          tax_no TEXT, vat_id TEXT, registry TEXT, managing_director TEXT,
          bank TEXT, iban TEXT, bic TEXT, footer_note TEXT, logo_path TEXT,
          invoice_header_color TEXT NOT NULL DEFAULT '#a40000'
        );
        CREATE TABLE IF NOT EXISTS number_ranges(
          range_key TEXT PRIMARY KEY,
          label TEXT NOT NULL,
          table_name TEXT,
          prefix TEXT NOT NULL DEFAULT '',
          next_value INTEGER NOT NULL DEFAULT 1,
          digits INTEGER NOT NULL DEFAULT 4,
          use_year INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS invoice_positions(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          invoice_id INTEGER NOT NULL,
          measurement_position_id INTEGER,
          offer_position_id INTEGER,
          position_no TEXT NOT NULL,
          short_text TEXT NOT NULL,
          unit TEXT NOT NULL,
          unit_price REAL NOT NULL DEFAULT 0,
          cumulative_quantity REAL NOT NULL DEFAULT 0,
          previously_billed_quantity REAL NOT NULL DEFAULT 0,
          new_quantity REAL NOT NULL DEFAULT 0,
          line_total REAL NOT NULL DEFAULT 0,
          FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
          FOREIGN KEY(measurement_position_id) REFERENCES measurement_positions(id) ON DELETE SET NULL,
          FOREIGN KEY(offer_position_id) REFERENCES offer_positions(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS invoice_position_exclusions(
          invoice_id INTEGER NOT NULL,
          measurement_position_id INTEGER NOT NULL,
          created_at TEXT NOT NULL,
          PRIMARY KEY(invoice_id,measurement_position_id),
          FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
          FOREIGN KEY(measurement_position_id) REFERENCES measurement_positions(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS payments(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          invoice_id INTEGER NOT NULL,
          payment_date TEXT NOT NULL,
          paid_amount REAL NOT NULL DEFAULT 0,
          discount_amount REAL NOT NULL DEFAULT 0,
          adjustment_amount REAL NOT NULL DEFAULT 0,
          adjustment_type TEXT,
          adjustment_reason TEXT,
          created_at TEXT NOT NULL,
          FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS reminders(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          invoice_id INTEGER NOT NULL,
          reminder_level INTEGER NOT NULL DEFAULT 1,
          reminder_date TEXT NOT NULL,
          new_due_date TEXT,
          amount_due REAL NOT NULL DEFAULT 0,
          status TEXT NOT NULL DEFAULT 'Offen',
          note TEXT,
          created_at TEXT NOT NULL,
          FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS measurement_lines(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          measurement_position_id INTEGER NOT NULL,
          description TEXT,
          sheet TEXT,
          room TEXT,
          formula TEXT NOT NULL,
          quantity REAL NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL,
          FOREIGN KEY(measurement_position_id) REFERENCES measurement_positions(id) ON DELETE CASCADE
        );
        """)
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS incoming_invoices(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          project_id INTEGER NOT NULL,
          supplier TEXT NOT NULL,
          invoice_no TEXT,
          invoice_date TEXT NOT NULL,
          category TEXT NOT NULL DEFAULT 'Material',
          net_amount REAL NOT NULL DEFAULT 0,
          vat_rate REAL NOT NULL DEFAULT 19,
          gross_amount REAL NOT NULL DEFAULT 0,
          due_date TEXT,
          paid_date TEXT,
          note TEXT,
          document_id INTEGER,
          created_at TEXT NOT NULL,
          FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_incoming_invoices_project_id ON incoming_invoices(project_id);
        """)
        cols=[r[1] for r in self.conn.execute("PRAGMA table_info(measurement_positions)").fetchall()]
        if cols and "billed_quantity" not in cols:
            self.conn.execute("ALTER TABLE measurement_positions ADD COLUMN billed_quantity REAL NOT NULL DEFAULT 0")
        if cols and "location" not in cols:
            self.conn.execute("ALTER TABLE measurement_positions ADD COLUMN location TEXT")
        ml_cols=[r[1] for r in self.conn.execute("PRAGMA table_info(measurement_lines)").fetchall()]
        if ml_cols and "sheet" not in ml_cols:
            self.conn.execute("ALTER TABLE measurement_lines ADD COLUMN sheet TEXT")
        if ml_cols and "room" not in ml_cols:
            self.conn.execute("ALTER TABLE measurement_lines ADD COLUMN room TEXT")
            self.conn.execute("""UPDATE measurement_lines SET room=description,description=''
              WHERE TRIM(COALESCE(description,''))<>''
                AND description<>'Aus Angebotsformel übernommen'""")
        customer_cols=[r[1] for r in self.conn.execute("PRAGMA table_info(customers)").fetchall()]
        for name in ("vat_id","buyer_reference"):
            if customer_cols and name not in customer_cols:
                self.conn.execute(f"ALTER TABLE customers ADD COLUMN {name} TEXT")
        if cols and "sort_order" not in cols:
            self.conn.execute("ALTER TABLE measurement_positions ADD COLUMN sort_order REAL")
        self.number_new_measurement_positions()
        lv_cols=[r[1] for r in self.conn.execute("PRAGMA table_info(project_lv_positions)").fetchall()]
        for name in ("title_no","title_text","subtitle_no","subtitle_text"):
            if lv_cols and name not in lv_cols:
                self.conn.execute(f"ALTER TABLE project_lv_positions ADD COLUMN {name} TEXT")
        op_cols=[r[1] for r in self.conn.execute("PRAGMA table_info(offer_positions)").fetchall()]
        if op_cols and "source_type" not in op_cols:
            self.conn.execute("ALTER TABLE offer_positions ADD COLUMN source_type TEXT NOT NULL DEFAULT 'Manuell'")
        op_cols=[r[1] for r in self.conn.execute("PRAGMA table_info(offer_positions)").fetchall()]
        for name in ("title_no","title_text","subtitle_no","subtitle_text"):
            if op_cols and name not in op_cols:
                self.conn.execute(f"ALTER TABLE offer_positions ADD COLUMN {name} TEXT")
        service_cols=[r[1] for r in self.conn.execute("PRAGMA table_info(services)").fetchall()]
        if service_cols and "category" not in service_cols:
            self.conn.execute("ALTER TABLE services ADD COLUMN category TEXT NOT NULL DEFAULT 'Allgemein'")
        if service_cols and "source" not in service_cols:
            self.conn.execute("ALTER TABLE services ADD COLUMN source TEXT")
        project_cols=[r[1] for r in self.conn.execute("PRAGMA table_info(projects)").fetchall()]
        if project_cols and "status_before_archive" not in project_cols:
            self.conn.execute("ALTER TABLE projects ADD COLUMN status_before_archive TEXT")
        line_cols=[r[1] for r in self.conn.execute("PRAGMA table_info(measurement_lines)").fetchall()]
        if line_cols and "sort_order" not in line_cols:
            # Ohne Wert gilt die bisherige Reihenfolge (nach Anlage).
            self.conn.execute("ALTER TABLE measurement_lines ADD COLUMN sort_order REAL")
        offer_cols=[r[1] for r in self.conn.execute("PRAGMA table_info(offers)").fetchall()]
        if offer_cols and "tax_mode" not in offer_cols:
            self.conn.execute("ALTER TABLE offers ADD COLUMN tax_mode TEXT DEFAULT 'Normale Umsatzsteuer'")
        if offer_cols and "vat_rate" not in offer_cols:
            self.conn.execute("ALTER TABLE offers ADD COLUMN vat_rate REAL DEFAULT 19")
        inv_cols=[r[1] for r in self.conn.execute("PRAGMA table_info(invoices)").fetchall()]
        for name,sqltype,default in [
            ("tax_mode","TEXT","'Regelbesteuerung'"),("performance_from","TEXT","NULL"),
            ("performance_to","TEXT","NULL"),("skonto_percent","REAL","0"),("skonto_due_date","TEXT","NULL"),
            ("security_enabled","INTEGER","0"),("security_percent","REAL","0"),
            ("construction_enabled","INTEGER","0"),("construction_percent","REAL","0"),
            ("construction_label","TEXT","'Bauwesen'"),("payable_total","REAL","0")]:
            if inv_cols and name not in inv_cols:
                self.conn.execute(f"ALTER TABLE invoices ADD COLUMN {name} {sqltype} DEFAULT {default}")
        inv_cols=[r[1] for r in self.conn.execute("PRAGMA table_info(invoices)").fetchall()]
        if "installment_no" not in inv_cols:
            self.conn.execute("ALTER TABLE invoices ADD COLUMN installment_no INTEGER NOT NULL DEFAULT 1")
        if "deduct_previous" not in inv_cols:
            self.conn.execute("ALTER TABLE invoices ADD COLUMN deduct_previous INTEGER NOT NULL DEFAULT 1")
        inv_cols=[r[1] for r in self.conn.execute("PRAGMA table_info(invoices)").fetchall()]
        if "is_historical" not in inv_cols:
            self.conn.execute("ALTER TABLE invoices ADD COLUMN is_historical INTEGER NOT NULL DEFAULT 0")
        if "source_pdf" not in inv_cols:
            self.conn.execute("ALTER TABLE invoices ADD COLUMN source_pdf TEXT")
        if "imported_at" not in inv_cols:
            self.conn.execute("ALTER TABLE invoices ADD COLUMN imported_at TEXT")
        company_cols=[r[1] for r in self.conn.execute("PRAGMA table_info(company_settings)").fetchall()]
        if company_cols and "logo_path" not in company_cols:
            self.conn.execute("ALTER TABLE company_settings ADD COLUMN logo_path TEXT")
        if company_cols and "invoice_header_color" not in company_cols:
            self.conn.execute("ALTER TABLE company_settings ADD COLUMN invoice_header_color TEXT NOT NULL DEFAULT '#a40000'")
        # Bestehende Rechnungen aus älteren Versionen: Zahlbetrag entspricht zunächst Brutto.
        self.conn.execute("""UPDATE invoices SET payable_total=gross_total
          WHERE (payable_total IS NULL OR ABS(payable_total)<0.000001) AND ABS(gross_total)>0.000001""")
        self.conn.execute("""INSERT OR IGNORE INTO company_settings
          (id,company_name,street,zip,city,phone,email,website,tax_no,vat_id,registry,managing_director,bank,iban,bic,footer_note)
          VALUES(1,'','','','','','','','','','','','','','','')""")
        defaults=[
          ("customers","Kunden","customers","K",4,0),
          ("projects","Projekte","projects","P",4,0),
          ("offers","Angebote","offers","A",4,0),
          ("invoices","Rechnungen","invoices","R",4,0),
          ("reminders","Mahnungen",None,"M",4,0),
        ]
        for key,label,table,prefix,digits,use_year in defaults:
            next_value=1
            if table:
                row=self.conn.execute(f"SELECT number FROM {table} ORDER BY id DESC LIMIT 1").fetchone()
                if row:
                    m=re.search(r"(\d+)$",row["number"] or "")
                    if m: next_value=int(m.group(1))+1
            self.conn.execute("""INSERT OR IGNORE INTO number_ranges
              (range_key,label,table_name,prefix,next_value,digits,use_year)
                VALUES(?,?,?,?,?,?,?)""",(key,label,table,prefix,next_value,digits,use_year))
        self.conn.commit()

        # Reparatur für bereits mit 0.8.6.4 übernommene Aufmaßpositionen:
        # Existiert noch keine Aufmaßzeile, wird eine gültige Angebotsformel
        # einmalig als erster kumulierter Stand nachgetragen.
        missing=self.conn.execute("""SELECT mp.id,op.formula
          FROM measurement_positions mp
          JOIN offer_positions op ON op.id=mp.offer_position_id
          WHERE TRIM(COALESCE(op.formula,''))<>''
            AND NOT EXISTS (SELECT 1 FROM measurement_lines ml
                            WHERE ml.measurement_position_id=mp.id)""").fetchall()
        for row in missing:
            formula=(row["formula"] or "").strip()
            try:
                quantity=eval_formula(formula)
            except Exception:
                continue
            self.add_measurement_line(
                row["id"],"Aus Angebotsformel übernommen",formula,quantity
            )

        # Reparatur älterer Projektwechsel: Die fachliche Projektzuordnung einer
        # Aufmaßposition folgt immer dem Angebot. Früher blieb project_id beim
        # Verschieben eines Angebots unverändert; dadurch war das Aufmaß unsichtbar,
        # blockierte aber weiterhin korrekt das Löschen des Angebots.
        self.conn.execute("""UPDATE measurement_positions
          SET project_id=(SELECT o.project_id FROM offer_positions op
                          JOIN offers o ON o.id=op.offer_id
                          WHERE op.id=measurement_positions.offer_position_id)
          WHERE EXISTS (SELECT 1 FROM offer_positions op JOIN offers o ON o.id=op.offer_id
                        WHERE op.id=measurement_positions.offer_position_id
                          AND o.project_id<>measurement_positions.project_id)""")
        self.conn.commit()

    def next_number(self, table, prefix):
        # 0.8.4: zentrale Nummernkreise. Bestehende Aufrufe bleiben kompatibel.
        key={"customers":"customers","projects":"projects","offers":"offers",
             "invoices":"invoices"}.get(table)
        if not key:
            row=self.conn.execute(f"SELECT number FROM {table} ORDER BY id DESC LIMIT 1").fetchone()
            n=1
            if row:
                m=re.search(r"(\d+)$",row["number"] or "")
                if m:n=int(m.group(1))+1
            return f"{prefix}{n:04d}"
        r=self.conn.execute("SELECT * FROM number_ranges WHERE range_key=?",(key,)).fetchone()
        if not r:
            return f"{prefix}0001"
        n=max(1,int(r["next_value"] or 1))
        p=(r["prefix"] or "")
        digits=max(1,min(10,int(r["digits"] or 4)))
        year=(datetime.now().strftime("%Y")+"-") if int(r["use_year"] or 0) else ""
        number=f"{p}{year}{n:0{digits}d}"
        # Eine historische Originalnummer darf den Aufmaßwerk-Zähler nicht
        # verschieben. Trifft der Zähler später dennoch exakt dieselbe Zeichenfolge,
        # wird nur diese bereits belegte Nummer übersprungen.
        while self.conn.execute(f"SELECT 1 FROM {table} WHERE number=?",(number,)).fetchone():
            n+=1
            number=f"{p}{year}{n:0{digits}d}"
        self.conn.execute("UPDATE number_ranges SET next_value=? WHERE range_key=?",(n+1,key))
        self.conn.commit()
        return number

    def number_ranges(self):
        return self.conn.execute("""SELECT * FROM number_ranges
          ORDER BY CASE range_key WHEN 'customers' THEN 1 WHEN 'projects' THEN 2
          WHEN 'offers' THEN 3 WHEN 'invoices' THEN 4 WHEN 'reminders' THEN 5 ELSE 99 END""").fetchall()

    def save_number_range(self,key,prefix,next_value,digits,use_year):
        row=self.conn.execute("SELECT * FROM number_ranges WHERE range_key=?",(key,)).fetchone()
        if not row: raise ValueError("Unbekannter Nummernkreis.")
        next_value=max(1,int(next_value));digits=max(1,min(10,int(digits)))
        table=row["table_name"]
        if table:
            where=" WHERE COALESCE(is_historical,0)=0" if table=="invoices" else ""
            used=self.conn.execute(f"SELECT number FROM {table}{where}").fetchall()
            highest=0
            for u in used:
                m=re.search(r"(\d+)$",u["number"] or "")
                if m: highest=max(highest,int(m.group(1)))
            if next_value<=highest:
                raise ValueError(f"Die nächste Nummer muss größer als {highest} sein, da niedrigere Nummern bereits vergeben wurden.")
        self.conn.execute("""UPDATE number_ranges SET prefix=?,next_value=?,digits=?,use_year=?
          WHERE range_key=?""",(prefix.strip(),next_value,digits,1 if use_year else 0,key))
        self.conn.commit()

    def backup(self, reason):
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        BACKUP_DIR.mkdir(parents=True,exist_ok=True)
        dest = BACKUP_DIR / f"aufmasswerk_{stamp}_{reason}.db"
        dc = sqlite3.connect(dest)
        with dc: self.conn.backup(dc)
        dc.close()
        prune_backups()

    def projects(self):
        return self.conn.execute("""SELECT p.*,c.company FROM projects p
            JOIN customers c ON c.id=p.customer_id ORDER BY p.id DESC""").fetchall()

    def services(self):
        return self.conn.execute("SELECT * FROM services WHERE active=1 ORDER BY number").fetchall()

    def service(self, sid):
        return self.conn.execute("SELECT * FROM services WHERE id=?", (sid,)).fetchone()


    def company_settings(self):
        return self.conn.execute("SELECT * FROM company_settings WHERE id=1").fetchone()

    def save_company_settings(self,d):
        self.conn.execute("""UPDATE company_settings SET company_name=?,street=?,zip=?,city=?,phone=?,email=?,website=?,
          tax_no=?,vat_id=?,registry=?,managing_director=?,bank=?,iban=?,bic=?,footer_note=?,logo_path=?,
          invoice_header_color=? WHERE id=1""",d)
        self.conn.commit()

    def customers(self, search=""):
        s=f"%{search}%"
        return self.conn.execute("""SELECT * FROM customers
          WHERE number LIKE ? OR company LIKE ? OR contact LIKE ? OR city LIKE ?
          OR phone LIKE ? OR email LIKE ? ORDER BY company""",(s,s,s,s,s,s)).fetchall()

    def customer(self,cid):
        return self.conn.execute("SELECT * FROM customers WHERE id=?",(cid,)).fetchone()

    def add_customer(self,d):
        cur=self.conn.execute("""INSERT INTO customers
          (number,company,contact,street,zip,city,phone,email,notes)
          VALUES(?,?,?,?,?,?,?,?,?)""",(self.next_number("customers","K"),*d))
        self.conn.commit(); return cur.lastrowid

    def update_customer(self,cid,d):
        self.conn.execute("""UPDATE customers SET company=?,contact=?,street=?,zip=?,city=?,
          phone=?,email=?,notes=? WHERE id=?""",(*d,cid)); self.conn.commit()

    def update_customer_einvoice(self,cid,vat_id,buyer_reference):
        self.conn.execute("UPDATE customers SET vat_id=?,buyer_reference=? WHERE id=?",
                          (vat_id.strip(),buyer_reference.strip(),cid));self.conn.commit()

    def number_new_measurement_positions(self):
        """Positionen ohne Platz ans Ende ihres Projekts stellen. Beim ersten Start nach dem
        Update bleibt so die bisherige Reihenfolge (die des Angebots) erhalten."""
        rows=self.conn.execute("""SELECT mp.id,mp.project_id FROM measurement_positions mp
          JOIN offer_positions op ON op.id=mp.offer_position_id JOIN offers o ON o.id=op.offer_id
          WHERE mp.sort_order IS NULL ORDER BY mp.project_id,o.id,op.sort_order,op.id""").fetchall()
        last={}
        for r in rows:
            pid=r["project_id"]
            if pid not in last:
                last[pid]=float(self.conn.execute("SELECT COALESCE(MAX(sort_order),0) FROM measurement_positions WHERE project_id=?",(pid,)).fetchone()[0] or 0)
            last[pid]+=10;self.conn.execute("UPDATE measurement_positions SET sort_order=? WHERE id=?",(last[pid],r["id"]))
        if rows:self.conn.commit()

    def delete_customer(self,cid):
        n=self.conn.execute("SELECT COUNT(*) FROM projects WHERE customer_id=?",(cid,)).fetchone()[0]
        if n:return False,n
        self.conn.execute("DELETE FROM customers WHERE id=?",(cid,));self.conn.commit();return True,0

    def projects_search(self,search="",status_filter="Aktiv"):
        s=f"%{search}%"
        clauses={
          "Aktiv":"p.status NOT IN ('Abgeschlossen','Archiviert')",
          "Abgeschlossen":"p.status='Abgeschlossen'",
          "Archiv":"p.status='Archiviert'",
          "Alle":"1=1",
        }
        status_clause=clauses.get(status_filter,clauses["Aktiv"])
        return self.conn.execute("""SELECT p.*,c.company FROM projects p JOIN customers c ON c.id=p.customer_id
          WHERE (p.number LIKE ? OR p.name LIKE ? OR p.site LIKE ? OR p.status LIKE ? OR c.company LIKE ?)
            AND """+status_clause+"""
          ORDER BY p.id DESC""",(s,s,s,s,s)).fetchall()

    def archived_project_count(self):
        return self.conn.execute("SELECT COUNT(*) FROM projects WHERE status='Archiviert'").fetchone()[0]

    def project(self,pid):
        return self.conn.execute("""SELECT p.*,c.company FROM projects p JOIN customers c ON c.id=p.customer_id
          WHERE p.id=?""",(pid,)).fetchone()

    def projects_for_customer(self,cid):
        return self.conn.execute("SELECT * FROM projects WHERE customer_id=? ORDER BY id DESC",(cid,)).fetchall()

    def add_project(self,d):
        cur=self.conn.execute("""INSERT INTO projects(number,customer_id,name,site,status,notes)
          VALUES(?,?,?,?,?,?)""",(self.next_number("projects","P"),*d));self.conn.commit();return cur.lastrowid

    def update_project(self,pid,d):
        self.conn.execute("UPDATE projects SET customer_id=?,name=?,site=?,status=?,notes=? WHERE id=?",(*d,pid))
        self.conn.commit()

    def delete_project(self,pid):
        self.conn.execute("DELETE FROM projects WHERE id=?",(pid,));self.conn.commit()

    def project_documents(self,pid):
        return self.conn.execute("""SELECT * FROM project_documents
          WHERE project_id=? ORDER BY created_at DESC,id DESC""",(pid,)).fetchall()

    def add_project_document(self,pid,source_path,description=""):
        project=self.project(pid)
        if not project:raise ValueError("Das Projekt wurde nicht gefunden.")
        source=Path(source_path)
        if not source.is_file():raise ValueError("Die ausgewählte Datei wurde nicht gefunden.")
        folder=PROJECT_DOCUMENT_DIR / str(project["number"])
        folder.mkdir(parents=True,exist_ok=True)
        target=folder / source.name
        stem,suffix=target.stem,target.suffix
        counter=2
        while target.exists():
            target=folder / f"{stem}_{counter}{suffix}"
            counter+=1
        shutil.copy2(source,target)
        relative=target.relative_to(DATA_ROOT).as_posix()
        try:
            cur=self.conn.execute("""INSERT INTO project_documents
              (project_id,filename,filepath,description,created_at) VALUES(?,?,?,?,?)""",
              (pid,target.name,relative,description.strip(),datetime.now().isoformat(timespec="seconds")))
            self.conn.commit();return cur.lastrowid
        except Exception:
            target.unlink(missing_ok=True)
            raise

    def update_project_document_description(self,document_id,description):
        self.conn.execute("UPDATE project_documents SET description=? WHERE id=?",
                          (description.strip(),document_id));self.conn.commit()

    def register_letter(self,customer_id,project_id,letter_date,subject,path):
        """Einen erzeugten Brief beim Kunden und optional beim Projekt vermerken."""
        path=Path(path).resolve();relative=path.relative_to(DATA_ROOT.resolve()).as_posix()
        created=datetime.now().isoformat(timespec="seconds")
        with self.conn:
            cur=self.conn.execute("""INSERT INTO letters
              (customer_id,project_id,letter_date,subject,filename,filepath,created_at)
              VALUES(?,?,?,?,?,?,?)""",
              (customer_id,project_id,letter_date,subject,path.name,relative,created))
            if project_id is not None:
                self.conn.execute("""INSERT INTO project_documents
                  (project_id,filename,filepath,description,created_at) VALUES(?,?,?,?,?)""",
                  (project_id,path.name,relative,f"Geschäftsbrief: {subject}",created))
        return cur.lastrowid

    def project_document_path(self,document_id):
        row=self.conn.execute("SELECT * FROM project_documents WHERE id=?",(document_id,)).fetchone()
        if not row:return None
        path=(DATA_ROOT / row["filepath"]).resolve()
        root=PROJECT_DOCUMENT_DIR.resolve()
        if path!=root and root not in path.parents:
            raise ValueError("Ungültiger Dokumentpfad außerhalb der Projektablage.")
        return path

    def delete_project_document(self,document_id):
        path=self.project_document_path(document_id)
        if path is None:return False
        self.conn.execute("DELETE FROM project_documents WHERE id=?",(document_id,));self.conn.commit()
        path.unlink(missing_ok=True)
        return True

    def complete_project(self,pid):
        self.conn.execute("""UPDATE projects SET status='Abgeschlossen',status_before_archive=NULL
          WHERE id=? AND status<>'Archiviert'""",(pid,));self.conn.commit()

    def archive_project(self,pid):
        self.conn.execute("""UPDATE projects
          SET status_before_archive=CASE WHEN status='Archiviert' THEN status_before_archive ELSE status END,
              status='Archiviert'
          WHERE id=?""",(pid,));self.conn.commit()

    def restore_project(self,pid):
        self.conn.execute("""UPDATE projects
          SET status=CASE WHEN status_before_archive IS NULL OR status_before_archive='Archiviert'
                          THEN 'Offen' ELSE status_before_archive END,
              status_before_archive=NULL
          WHERE id=? AND status='Archiviert'""",(pid,));self.conn.commit()

    def project_lv_positions(self,pid):
        return self.conn.execute("""SELECT lp.*,ls.source_name,ls.imported_at
          FROM project_lv_positions lp JOIN project_lv_sources ls ON ls.id=lp.source_id
          WHERE lp.project_id=? ORDER BY lp.sort_order,lp.id""",(pid,)).fetchall()

    def import_project_lv(self,pid,source_name,positions):
        source_type="PDF" if Path(source_name).suffix.lower()==".pdf" else "ODS"
        cur=self.conn.execute("""INSERT INTO project_lv_sources(project_id,source_name,imported_at,notes)
          VALUES(?,?,?,?)""",(pid,source_name,datetime.now().isoformat(timespec="seconds"),f"{source_type}-Import"))
        sid=cur.lastrowid
        for idx,p in enumerate(positions,1):
            self.conn.execute("""INSERT INTO project_lv_positions
              (source_id,project_id,position_no,short_text,long_text,quantity,unit,source_unit_price,sort_order,
               title_no,title_text,subtitle_no,subtitle_text)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
              (sid,pid,p["position_no"],p["short_text"],p["long_text"],p["quantity"],
               p["unit"],p["unit_price"],idx*10,
               p.get("title_no",""),p.get("title_text",""),p.get("subtitle_no",""),p.get("subtitle_text","")))
        self.conn.commit()
        return sid

    def create_offer_from_project_lv(self,pid,title,lv_ids):
        num=self.next_number("offers","A")
        cur=self.conn.execute("""INSERT INTO offers(number,project_id,title,status,created_at,notes)
          VALUES(?,?,?,?,?,?)""",(num,pid,title or "Angebot aus LV","Entwurf",
          datetime.now().isoformat(timespec="seconds"),"Erstellt aus Projekt-LV"))
        oid=cur.lastrowid
        rows=[]
        if lv_ids:
            marks=",".join("?"*len(lv_ids))
            rows=self.conn.execute(f"""SELECT * FROM project_lv_positions
              WHERE project_id=? AND id IN ({marks}) ORDER BY sort_order,id""",(pid,*lv_ids)).fetchall()
        for idx,p in enumerate(rows,1):
            self.conn.execute("""INSERT INTO offer_positions
              (offer_id,service_id,position_no,short_text,long_text,formula,quantity,unit,unit_price,sort_order,source_type,
               title_no,title_text,subtitle_no,subtitle_text)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
              (oid,None,p["position_no"],p["short_text"],p["long_text"],"",p["quantity"],
               p["unit"],p["source_unit_price"],idx*10,"LV",
               p["title_no"] or "",p["title_text"] or "",p["subtitle_no"] or "",p["subtitle_text"] or ""))
        self.conn.commit()
        return oid

    def project_lv_selected(self,pid):
        return self.conn.execute("""SELECT lp.*,ls.source_name
          FROM project_lv_selection s
          JOIN project_lv_positions lp ON lp.id=s.lv_position_id
          JOIN project_lv_sources ls ON ls.id=lp.source_id
          WHERE s.project_id=? ORDER BY lp.sort_order,lp.id""",(pid,)).fetchall()

    def add_project_lv_selection(self,pid,lv_ids):
        now=datetime.now().isoformat(timespec="seconds")
        for lvid in lv_ids:
            self.conn.execute("""INSERT OR IGNORE INTO project_lv_selection
              (project_id,lv_position_id,created_at) VALUES(?,?,?)""",(pid,lvid,now))
        self.conn.commit()

    def remove_project_lv_selection(self,pid,lv_ids):
        for lvid in lv_ids:
            self.conn.execute("""DELETE FROM project_lv_selection
              WHERE project_id=? AND lv_position_id=?""",(pid,lvid))
        self.conn.commit()

    def clear_project_lv_selection(self,pid):
        self.conn.execute("DELETE FROM project_lv_selection WHERE project_id=?",(pid,))
        self.conn.commit()

    def create_offer_from_selected_project_lv(self,pid,title):
        # Auswahl frisch und direkt aus der Datenbank lesen.
        rows=self.conn.execute("""SELECT lp.*
          FROM project_lv_selection s
          JOIN project_lv_positions lp ON lp.id=s.lv_position_id
          WHERE s.project_id=? AND lp.project_id=?
          ORDER BY lp.sort_order,lp.id""",(pid,pid)).fetchall()

        expected=len(rows)
        if expected==0:
            return None,0,0,"Keine übernommenen LV-Positionen gefunden."

        # Angebotsnummer vorab ermitteln. next_number() speichert den Nummernkreis,
        # deshalb danach den eigentlichen Angebots-/Positionsvorgang sauber prüfen.
        num=self.next_number("offers","A")

        try:
            cur=self.conn.execute("""INSERT INTO offers
              (number,project_id,title,status,created_at,notes)
              VALUES(?,?,?,?,?,?)""",
              (num,pid,title or "Angebot aus LV","Entwurf",
               datetime.now().isoformat(timespec="seconds"),
               "Erstellt aus übernommener LV-Auswahl"))
            oid=cur.lastrowid

            for idx,p in enumerate(rows,1):
                self.conn.execute("""INSERT INTO offer_positions
                  (offer_id,service_id,position_no,short_text,long_text,formula,
                   quantity,unit,unit_price,sort_order,source_type,title_no,title_text,subtitle_no,subtitle_text)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                  (oid,None,p["position_no"],p["short_text"],p["long_text"] or "",
                   "",float(p["quantity"] or 0),p["unit"] or "",
                   float(p["source_unit_price"] or 0),idx*10,"LV",
                   p["title_no"] or "",p["title_text"] or "",p["subtitle_no"] or "",p["subtitle_text"] or ""))

            actual=int(self.conn.execute(
                "SELECT COUNT(*) FROM offer_positions WHERE offer_id=?",(oid,)
            ).fetchone()[0] or 0)

            if actual!=expected:
                self.conn.rollback()
                # Falls SQLite durch einen vorherigen Commit-Zustand doch schon etwas
                # gespeichert haben sollte, den unvollständigen Entwurf gezielt entfernen.
                try:
                    self.conn.execute("DELETE FROM offers WHERE id=?",(oid,))
                    self.conn.commit()
                except Exception:
                    self.conn.rollback()
                return None,actual,expected,(
                    f"Übernahme unvollständig: erwartet {expected}, gespeichert {actual}."
                )

            self.conn.commit()
            return oid,actual,expected,None

        except Exception as e:
            self.conn.rollback()
            return None,0,expected,str(e)

    def services_all(self,search="",category=None,active_only=False):
        s=f"%{search}%"
        where="(number LIKE ? OR short_text LIKE ? OR long_text LIKE ? OR unit LIKE ? OR category LIKE ? OR source LIKE ?)"
        args=[s,s,s,s,s,s]
        if category:
            where+=" AND category=?";args.append(category)
        if active_only:where+=" AND active=1"
        return self.conn.execute(f"SELECT * FROM services WHERE {where} ORDER BY category,number,id",args).fetchall()

    def service_categories(self):
        return [r[0] for r in self.conn.execute(
            "SELECT DISTINCT category FROM services WHERE TRIM(COALESCE(category,''))<>'' ORDER BY category"
        ).fetchall()]

    def add_service(self,d):
        cur=self.conn.execute("""INSERT INTO services
          (number,short_text,long_text,unit,purchase_price,sales_price,wage_share,material_share,active,category,source)
          VALUES(?,?,?,?,?,?,?,?,?,?,?)""",(self.next_number("services","L"),*d));self.conn.commit();return cur.lastrowid

    def update_service(self,sid,d):
        self.conn.execute("""UPDATE services SET short_text=?,long_text=?,unit=?,purchase_price=?,
          sales_price=?,wage_share=?,material_share=?,active=?,category=?,source=? WHERE id=?""",(*d,sid));self.conn.commit()

    def copy_service(self,sid):
        s=self.service(sid)
        if not s:return None
        return self.add_service((s["short_text"]+" (Kopie)",s["long_text"] or "",s["unit"] or "Stk.",
            s["purchase_price"] or 0,s["sales_price"] or 0,s["wage_share"] or 0,s["material_share"] or 0,
            s["active"],s["category"] or "Allgemein",s["source"] or ""))

    def import_services_to_offer(self,oid,service_ids):
        imported=[]
        for sid in service_ids:
            s=self.service(sid)
            if not s or not s["active"]:continue
            # Bewusste Kopie: keine service_id-Verknüpfung im Angebot.
            imported.append(self.add_position(oid,(None,self.next_pos(oid),s["short_text"],s["long_text"] or "",
                "",0,s["unit"] or "Stk.",s["sales_price"] or 0),"Leistung"))
        return imported

    def delete_service(self,sid):
        n=self.conn.execute("SELECT COUNT(*) FROM offer_positions WHERE service_id=?",(sid,)).fetchone()[0]
        if n:return False,n
        self.conn.execute("DELETE FROM services WHERE id=?",(sid,));self.conn.commit();return True,0

    def offers(self):
        return self.conn.execute("""SELECT o.*,p.number AS project_number,p.name AS project_name,c.company
            FROM offers o JOIN projects p ON p.id=o.project_id
            JOIN customers c ON c.id=p.customer_id ORDER BY o.id DESC""").fetchall()

    def offer(self, oid):
        return self.conn.execute("""SELECT o.*,
            p.number AS project_number,p.name AS project_name,p.site,
            c.number AS customer_number,c.company,c.contact AS customer_contact,
            c.street AS customer_street,c.zip AS customer_zip,c.city AS customer_city,
            c.phone AS customer_phone,c.email AS customer_email
            FROM offers o JOIN projects p ON p.id=o.project_id
            JOIN customers c ON c.id=p.customer_id WHERE o.id=?""", (oid,)).fetchone()

    def update_offer(self,oid,project_id,title,status,notes):
        self.conn.execute("""UPDATE offers SET project_id=?,title=?,status=?,notes=? WHERE id=?""",
          (project_id,title,status,notes,oid))
        # Bereits übernommene Aufmaßpositionen beim Projektwechsel sichtbar und
        # konsistent mitführen. Inhalte und Historie bleiben vollständig erhalten.
        self.conn.execute("""UPDATE measurement_positions SET project_id=?
          WHERE offer_position_id IN (SELECT id FROM offer_positions WHERE offer_id=?)""",
          (project_id,oid))
        self.conn.commit()

    def add_offer(self, project_id, title, notes):
        num = self.next_number("offers","A")
        cur = self.conn.execute("""INSERT INTO offers(number,project_id,title,status,created_at,notes)
            VALUES(?,?,?,?,?,?)""", (num, project_id, title, "Entwurf", datetime.now().isoformat(timespec="seconds"), notes))
        self.conn.commit()
        return cur.lastrowid

    def positions(self, oid):
        return self.conn.execute("""SELECT * FROM offer_positions WHERE offer_id=?
            ORDER BY sort_order,id""", (oid,)).fetchall()

    def next_pos(self, oid):
        n = self.conn.execute("SELECT COUNT(*) FROM offer_positions WHERE offer_id=? AND COALESCE(source_type,'')<>'Textblock'", (oid,)).fetchone()[0] + 1
        return f"{n:03d}"

    def add_offer_text(self, oid, heading, text, page_break=False):
        sort=self.conn.execute("SELECT COALESCE(MAX(sort_order),0)+10 FROM offer_positions WHERE offer_id=?",(oid,)).fetchone()[0]
        cur=self.conn.execute("""INSERT INTO offer_positions
          (offer_id,service_id,position_no,short_text,long_text,formula,quantity,unit,unit_price,sort_order,source_type)
          VALUES(?,NULL,'',?,?,?,0,'',0,?,'Textblock')""",
          (oid,heading,text,"Seitenumbruch" if page_break else "",sort))
        self.conn.commit();return cur.lastrowid

    def update_offer_text(self, pid, heading, text, page_break=False):
        self.conn.execute("UPDATE offer_positions SET short_text=?,long_text=?,formula=? WHERE id=?",
          (heading,text,"Seitenumbruch" if page_break else "",pid));self.conn.commit()

    def move_offer_item(self, pid, direction):
        row=self.position(pid)
        if not row:return False
        ordered=[r["id"] for r in self.positions(row["offer_id"])]
        try:index=ordered.index(pid)
        except ValueError:return False
        target=index+(-1 if direction<0 else 1)
        if target<0 or target>=len(ordered):return False
        ordered[index],ordered[target]=ordered[target],ordered[index]
        for order,item_id in enumerate(ordered,1):
            self.conn.execute("UPDATE offer_positions SET sort_order=? WHERE id=?",(order*10,item_id))
        self.conn.commit();return True

    def add_position(self, oid, data, source_type="Manuell"):
        if len(data)>=12:
            sid,pos,short,longtext,formula,qty,unit,price,tno,tt,sno,st=data[:12]
        else:
            sid,pos,short,longtext,formula,qty,unit,price=data[:8]
            tno=tt=sno=st=""
        sort=self.conn.execute("SELECT COALESCE(MAX(sort_order),0)+10 FROM offer_positions WHERE offer_id=?",(oid,)).fetchone()[0]
        cur=self.conn.execute("""INSERT INTO offer_positions
          (offer_id,service_id,position_no,short_text,long_text,formula,quantity,unit,unit_price,sort_order,source_type,
           title_no,title_text,subtitle_no,subtitle_text)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (oid,sid,pos,short,longtext,formula,qty,unit,price,sort,source_type or "Manuell",tno,tt,sno,st))
        self.conn.commit()
        return cur.lastrowid

    def position(self, pid):
        return self.conn.execute("SELECT * FROM offer_positions WHERE id=?", (pid,)).fetchone()

    def update_position(self, pid, data):
        if len(data)>=12:
            sid,pos,short,longtext,formula,qty,unit,price,tno,tt,sno,st=data[:12]
        else:
            sid,pos,short,longtext,formula,qty,unit,price=data[:8]
            row=self.position(pid);tno=row["title_no"] or "";tt=row["title_text"] or ""
            sno=row["subtitle_no"] or "";st=row["subtitle_text"] or ""
        self.conn.execute("""UPDATE offer_positions SET service_id=?,position_no=?,short_text=?,long_text=?,
          formula=?,quantity=?,unit=?,unit_price=?,title_no=?,title_text=?,subtitle_no=?,subtitle_text=? WHERE id=?""",
          (sid,pos,short,longtext,formula,qty,unit,price,tno,tt,sno,st,pid))
        self.conn.commit()

    def position_measurement_count(self, pid):
        return self.conn.execute("SELECT COUNT(*) FROM measurement_positions WHERE offer_position_id=?", (pid,)).fetchone()[0]

    def offer_measurement_count(self, oid):
        return self.conn.execute("""SELECT COUNT(*) FROM measurement_positions mp
          JOIN offer_positions op ON op.id=mp.offer_position_id WHERE op.offer_id=?""",(oid,)).fetchone()[0]

    def delete_offer(self, oid):
        used=self.offer_measurement_count(oid)
        if used:
            return False, used
        self.conn.execute("DELETE FROM offers WHERE id=?", (oid,))
        self.conn.commit()
        return True, 0

    def delete_position(self, pid):
        used=self.position_measurement_count(pid)
        if used:
            return False, used
        self.conn.execute("DELETE FROM offer_positions WHERE id=?", (pid,))
        self.conn.commit()
        return True, 0

    def total(self, oid):
        return self.conn.execute("SELECT COALESCE(SUM(quantity*unit_price),0) FROM offer_positions WHERE offer_id=?", (oid,)).fetchone()[0]



# --- Aufmaß 0.6 -------------------------------------------------------------
def _db_measurement_projects(self):
    return self.conn.execute("""SELECT DISTINCT p.id,p.number,p.name,c.company
      FROM projects p JOIN customers c ON c.id=p.customer_id
      JOIN offers o ON o.project_id=p.id
      ORDER BY p.id DESC""").fetchall()

def _db_project_offers(self, project_id):
    return self.conn.execute("""SELECT id,number,title,status FROM offers
      WHERE project_id=? ORDER BY id DESC""",(project_id,)).fetchall()

def _db_available_offer_positions(self, project_id, offer_id):
    return self.conn.execute("""SELECT op.*,o.number AS offer_number
      FROM offer_positions op JOIN offers o ON o.id=op.offer_id
      LEFT JOIN measurement_positions mp ON mp.offer_position_id=op.id
      WHERE o.project_id=? AND o.id=? AND mp.id IS NULL
      ORDER BY op.sort_order,op.id""",(project_id,offer_id)).fetchall()

def _db_add_measurement_position(self, project_id, offer_position_id):
    cur=self.conn.execute("""INSERT OR IGNORE INTO measurement_positions
      (project_id,offer_position_id,created_at) VALUES(?,?,?)""",
      (project_id,offer_position_id,datetime.now().isoformat(timespec="seconds")))
    self.conn.commit();self.number_new_measurement_positions()
    # Angebotsmenge und Angebotsformel sind Soll-/Referenzwerte. Erst eine
    # ausdrücklich angelegte Aufmaßzeile darf den Ist-Stand erhöhen.

def measurement_title_key(p):
    """Titel einer Aufmaßposition; ohne Titel zählt die Zahl vor dem Punkt der Positionsnummer."""
    tno=(p["title_no"] or "").strip();ttext=(p["title_text"] or "").strip()
    if not tno and "." in (p["position_no"] or ""):
        tno=(p["position_no"] or "").split(".",1)[0].strip();ttext=f"Titel {tno}" if tno else ""
    return (tno,ttext) if tno else ("","")

def _db_measurement_positions(self, project_id):
    """Reihenfolge des Aufmaßes; Positionen desselben Titels bleiben beieinander."""
    groups=[];index={}
    for p in self._measurement_positions_raw(project_id):
        key=(p["offer_number"],measurement_title_key(p))
        if key not in index:index[key]=len(groups);groups.append([])
        groups[index[key]].append(p)
    # Titelblöcke eines Angebots stehen zusammen, in der Reihenfolge ihres ersten Eintrags.
    by_offer={};order=[]
    for g in groups:
        offer=g[0]["offer_number"]
        if offer not in by_offer:by_offer[offer]=[];order.append(offer)
        by_offer[offer].append(g)
    return [p for offer in order for g in by_offer[offer] for p in g]

def _measurement_groups(self, project_id):
    """[(Angebot, Titel), [Positions-IDs]] in Anzeigereihenfolge."""
    groups=[]
    for p in self.measurement_positions(project_id):
        key=(p["offer_number"],measurement_title_key(p))
        if groups and groups[-1][0]==key:groups[-1][1].append(p["measurement_position_id"])
        else:groups.append([key,[p["measurement_position_id"]]])
    return groups

def _db_move_measurement_position(self, mpid, direction):
    """Position um einen Platz verschieben (-1 hoch, +1 runter), innerhalb ihres Titels."""
    row=self.conn.execute("SELECT project_id FROM measurement_positions WHERE id=?",(mpid,)).fetchone()
    if not row:return False
    groups=_measurement_groups(self,row["project_id"])
    gi=next((i for i,g in enumerate(groups) if mpid in g[1]),None)
    if gi is None:return False
    ids=groups[gi][1];i=ids.index(mpid);j=i+direction
    if not 0<=j<len(ids):return False
    ids[i],ids[j]=ids[j],ids[i]
    for number,value in enumerate([x for g in groups for x in g[1]],1):
        self.conn.execute("UPDATE measurement_positions SET sort_order=? WHERE id=?",(number*10,value))
    self.conn.commit();return True

def _db_move_measurement_line(self, line_id, direction):
    row=self.conn.execute("SELECT measurement_position_id FROM measurement_lines WHERE id=?",(line_id,)).fetchone()
    if not row:return False
    ids=[r["id"] for r in self.measurement_lines(row["measurement_position_id"])];i=ids.index(line_id);j=i+direction
    if not 0<=j<len(ids):return False
    ids[i],ids[j]=ids[j],ids[i]
    for number,value in enumerate(ids,1):
        self.conn.execute("UPDATE measurement_lines SET sort_order=? WHERE id=?",(number*10,value))
    self.conn.commit();return True

def _db_measurement_positions_raw(self, project_id):
    return self.conn.execute("""SELECT mp.id AS measurement_position_id,op.id AS offer_position_id,
      op.position_no,op.short_text,op.long_text,op.unit,op.unit_price,op.formula AS offer_formula,
      op.quantity AS offer_quantity,o.number AS offer_number,mp.billed_quantity,
      op.title_no,op.title_text,op.subtitle_no,op.subtitle_text,
      COALESCE((SELECT SUM(ml.quantity) FROM measurement_lines ml
                WHERE ml.measurement_position_id=mp.id),0) AS current_quantity,
      COALESCE((SELECT GROUP_CONCAT(ml.formula,' + ') FROM measurement_lines ml
                WHERE ml.measurement_position_id=mp.id
                  AND TRIM(COALESCE(ml.formula,''))<>''),'') AS measurement_formula
      ,COALESCE(NULLIF(TRIM(mp.location),''),(SELECT GROUP_CONCAT(DISTINCT
                COALESCE(NULLIF(TRIM(ml.room),''),ml.description)) FROM measurement_lines ml
                WHERE ml.measurement_position_id=mp.id
                  AND TRIM(COALESCE(NULLIF(TRIM(ml.room),''),ml.description,''))<>''
                  AND ml.description<>'Aus Angebotsformel übernommen'),'') AS measurement_location
      FROM measurement_positions mp
      JOIN offer_positions op ON op.id=mp.offer_position_id
      JOIN offers o ON o.id=op.offer_id
      WHERE o.project_id=? ORDER BY o.id,COALESCE(mp.sort_order,1e12),op.sort_order,op.id""",(project_id,)).fetchall()

def _db_measurement_position(self, mpid):
    return self.conn.execute("""SELECT mp.*,op.service_id,op.position_no,op.short_text,op.long_text,op.unit,
      op.unit_price,op.formula,op.formula AS offer_formula,op.quantity,op.quantity AS offer_quantity,
      op.source_type,op.title_no,op.title_text,op.subtitle_no,op.subtitle_text,
      COALESCE(NULLIF(TRIM(mp.location),''),(SELECT GROUP_CONCAT(DISTINCT
        COALESCE(NULLIF(TRIM(ml.room),''),ml.description))
        FROM measurement_lines ml WHERE ml.measurement_position_id=mp.id
        AND TRIM(COALESCE(NULLIF(TRIM(ml.room),''),ml.description,''))<>''
        AND ml.description<>'Aus Angebotsformel übernommen'),'') AS measurement_location,
      o.id AS offer_id,o.number AS offer_number
      FROM measurement_positions mp JOIN offer_positions op ON op.id=mp.offer_position_id
      JOIN offers o ON o.id=op.offer_id WHERE mp.id=?""",(mpid,)).fetchone()

def _db_update_measurement_position(self,mpid,data):
    """Bearbeitet die dem Aufmaß zugrunde liegende Angebotsposition vollständig.
    Festgeschriebene Rechnungen bleiben historische Momentaufnahmen."""
    row=self._measurement_position(mpid)
    if not row:return False,"Aufmaßposition wurde nicht gefunden."
    if len(data)<12:return False,"Unvollständige Positionsdaten."
    sid,pos,short,longtext,formula,qty,unit,price,tno,tt,sno,st=data[:12]
    location=(data[12] if len(data)>=13 else row["location"] or "").strip()
    self.conn.execute("""UPDATE offer_positions SET
      service_id=?,position_no=?,short_text=?,long_text=?,formula=?,quantity=?,unit=?,unit_price=?,
      title_no=?,title_text=?,subtitle_no=?,subtitle_text=?
      WHERE id=?""",
      (sid,pos,short,longtext,formula,qty,unit,price,tno,tt,sno,st,row["offer_position_id"]))
    self.conn.execute("UPDATE measurement_positions SET location=? WHERE id=?",(location,mpid))
    self.conn.commit()

    # Die automatisch aus der Angebotsformel erzeugte Aufmaßzeile unmittelbar
    # mitsynchronisieren. Manuell erfasste Aufmaßzeilen werden nie verändert.
    auto=self.conn.execute("""SELECT * FROM measurement_lines
      WHERE measurement_position_id=? AND description=? ORDER BY id LIMIT 1""",
      (mpid,"Aus Angebotsformel übernommen")).fetchone()
    line_count=self.conn.execute(
      "SELECT COUNT(*) FROM measurement_lines WHERE measurement_position_id=?",(mpid,)
    ).fetchone()[0]
    clean_formula=(formula or "").strip()
    if not clean_formula and auto:
        self.delete_measurement_line(auto["id"])
    elif clean_formula:
        try:
            measured_quantity=eval_formula(clean_formula)
        except Exception:
            measured_quantity=None
        if measured_quantity is not None:
            if auto:
                self.update_measurement_line(
                    auto["id"],"Aus Angebotsformel übernommen",clean_formula,measured_quantity
                )
            elif line_count==0:
                self.add_measurement_line(
                    mpid,"Aus Angebotsformel übernommen",clean_formula,measured_quantity
                )
    return True,None

def _db_copy_offer_position(self,offer_position_id,target_offer_id):
    p=self.position(offer_position_id)
    if not p:return None,"Position wurde nicht gefunden."
    sort=self.conn.execute("SELECT COALESCE(MAX(sort_order),0)+10 FROM offer_positions WHERE offer_id=?",
                           (target_offer_id,)).fetchone()[0]
    cur=self.conn.execute("""INSERT INTO offer_positions
      (offer_id,service_id,position_no,short_text,long_text,formula,quantity,unit,unit_price,
       sort_order,source_type,title_no,title_text,subtitle_no,subtitle_text)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
      (target_offer_id,p["service_id"],p["position_no"],p["short_text"],p["long_text"],
       p["formula"],p["quantity"],p["unit"],p["unit_price"],sort,"Kopie",
       p["title_no"] or "",p["title_text"] or "",p["subtitle_no"] or "",p["subtitle_text"] or ""))
    self.conn.commit()
    return cur.lastrowid,None

def _db_create_offer_from_offer_positions(self,source_offer_id,position_ids,title,notes=""):
    source=self.offer(source_offer_id)
    if not source:return None,0,"Quellangebot wurde nicht gefunden."
    if not position_ids:return None,0,"Keine Positionen ausgewählt."

    marks=",".join("?"*len(position_ids))
    rows=self.conn.execute(f"""SELECT * FROM offer_positions
      WHERE offer_id=? AND id IN ({marks}) ORDER BY sort_order,id""",
      (source_offer_id,*position_ids)).fetchall()
    if not rows:return None,0,"Die ausgewählten Positionen wurden im Angebot nicht gefunden."

    num=self.next_number("offers","A")
    try:
        cur=self.conn.execute("""INSERT INTO offers(number,project_id,title,status,created_at,notes)
          VALUES(?,?,?,?,?,?)""",
          (num,source["project_id"],title or "Nachtrag / Teilangebot","Entwurf",
           datetime.now().isoformat(timespec="seconds"),
           notes or f"Erstellt aus Positionen von Angebot {source['number']}"))
        oid=cur.lastrowid

        for idx,p in enumerate(rows,1):
            self.conn.execute("""INSERT INTO offer_positions
              (offer_id,service_id,position_no,short_text,long_text,formula,quantity,unit,unit_price,
               sort_order,source_type,title_no,title_text,subtitle_no,subtitle_text)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
              (oid,p["service_id"],p["position_no"],p["short_text"],p["long_text"],p["formula"],
               p["quantity"],p["unit"],p["unit_price"],idx*10,"Kopie",
               p["title_no"] or "",p["title_text"] or "",p["subtitle_no"] or "",p["subtitle_text"] or ""))
        self.conn.commit()
        return oid,len(rows),None
    except Exception as e:
        self.conn.rollback()
        try:
            self.conn.execute("DELETE FROM offers WHERE id=?",(oid,))
            self.conn.commit()
        except Exception:
            self.conn.rollback()
        return None,0,str(e)

def _db_measurement_lines(self, mpid):
    return self.conn.execute("""SELECT * FROM measurement_lines
      WHERE measurement_position_id=? ORDER BY COALESCE(sort_order,id*10),id""",(mpid,)).fetchall()

def _db_place_measurement_line_after(self,line_id,anchor_id):
    """Aufmaßzeile direkt hinter `anchor_id` einreihen (sonst ans Ende)."""
    row=self.conn.execute("SELECT measurement_position_id FROM measurement_lines WHERE id=?",(line_id,)).fetchone()
    if not row:return
    ids=[r["id"] for r in self.measurement_lines(row["measurement_position_id"]) if r["id"]!=line_id]
    ids.insert(ids.index(anchor_id)+1 if anchor_id in ids else len(ids),line_id)
    for index,value in enumerate(ids,1):
        self.conn.execute("UPDATE measurement_lines SET sort_order=? WHERE id=?",(index*10,value))
    self.conn.commit()

DB.place_measurement_line_after=_db_place_measurement_line_after

def _db_add_measurement_line(self, mpid, description, formula, quantity, sheet="", room=""):
    now=datetime.now().isoformat(timespec="seconds")
    cur=self.conn.execute("""INSERT INTO measurement_lines
      (measurement_position_id,description,sheet,room,formula,quantity,created_at,updated_at)
      VALUES(?,?,?,?,?,?,?,?)""",(mpid,description,sheet,room,formula,quantity,now,now))
    mp=self._measurement_position(mpid)
    self.conn.execute("""INSERT INTO measure_history(project_id,offer_position_id,formula,quantity,created_at,note)
      VALUES(?,?,?,?,?,?)""",(mp["project_id"],mp["offer_position_id"],formula,quantity,now,description))
    self.conn.commit()
    self.add_snapshot(mpid,"Aufmaßzeile hinzugefügt")
    return cur.lastrowid

def _db_update_measurement_line(self, line_id, description, formula, quantity, sheet="", room=""):
    old=self.conn.execute("SELECT * FROM measurement_lines WHERE id=?",(line_id,)).fetchone()
    mpid=old["measurement_position_id"]

    # Entscheidend für die kumulative Historie:
    # VOR der Änderung den bisherigen Gesamtstand sichern.
    snapshots=self.snapshots(mpid)
    old_total=self.measurement_total(mpid)
    if not snapshots or abs(float(snapshots[0]["total_quantity"] or 0)-old_total) > 0.0000001:
        self.add_snapshot(mpid,"Stand vor Änderung")

    now=datetime.now().isoformat(timespec="seconds")
    self.conn.execute("""UPDATE measurement_lines SET description=?,sheet=?,room=?,formula=?,quantity=?,updated_at=?
      WHERE id=?""",(description,sheet,room,formula,quantity,now,line_id))
    mp=self._measurement_position(mpid)
    self.conn.execute("""INSERT INTO measure_history(project_id,offer_position_id,formula,quantity,created_at,note)
      VALUES(?,?,?,?,?,?)""",(mp["project_id"],mp["offer_position_id"],formula,quantity,now,
      (description or "")+" [geändert]"))
    self.conn.commit()

    # Danach den neuen kumulierten Stand sichern.
    self.add_snapshot(mpid,"Stand nach Änderung")

def _db_delete_measurement_line(self,line_id):
    row=self.conn.execute("SELECT measurement_position_id FROM measurement_lines WHERE id=?",(line_id,)).fetchone()
    mpid=row["measurement_position_id"] if row else None
    if mpid:
        old_total=self.measurement_total(mpid)
        snapshots=self.snapshots(mpid)
        if not snapshots or abs(float(snapshots[0]["total_quantity"] or 0)-old_total) > 0.0000001:
            self.add_snapshot(mpid,"Stand vor Löschen")
    self.conn.execute("DELETE FROM measurement_lines WHERE id=?",(line_id,));self.conn.commit()
    if mpid:self.add_snapshot(mpid,"Stand nach Löschen")

def _db_remove_measurement_position(self,mpid):
    self.conn.execute("DELETE FROM measurement_positions WHERE id=?",(mpid,));self.conn.commit()


def _db_measurement_total(self,mpid):
    return float(self.conn.execute("SELECT COALESCE(SUM(quantity),0) FROM measurement_lines WHERE measurement_position_id=?",(mpid,)).fetchone()[0] or 0)

def _db_add_snapshot(self,mpid,note):
    total=self.measurement_total(mpid)
    self.conn.execute("""INSERT INTO measurement_snapshots(measurement_position_id,total_quantity,created_at,note)
      VALUES(?,?,?,?)""",(mpid,total,datetime.now().isoformat(timespec="seconds"),note))
    self.conn.commit()

def _db_snapshots(self,mpid):
    return self.conn.execute("""SELECT * FROM measurement_snapshots
      WHERE measurement_position_id=? ORDER BY id DESC""",(mpid,)).fetchall()


def _db_invoice_projects(self):
    return self.conn.execute("""SELECT DISTINCT p.id,p.number,p.name,c.company
      FROM projects p JOIN customers c ON c.id=p.customer_id
      JOIN measurement_positions mp ON mp.project_id=p.id
      ORDER BY p.id DESC""").fetchall()

def _db_all_invoice_projects(self):
    return self.conn.execute("""SELECT p.id,p.number,p.name,c.company
      FROM projects p JOIN customers c ON c.id=p.customer_id
      ORDER BY p.id DESC""").fetchall()

def _db_next_invoice_number(self):
    return self.next_number("invoices","R")

def _db_create_partial_invoice(self,project_id,title,due_date,vat_rate,tax_mode,performance_from,performance_to,
                               skonto_percent,skonto_due_date,security_enabled,security_percent,
                               construction_enabled,construction_percent,construction_label,notes):
    # 0.7.3.2: Eine Teilrechnung ist vollständig kumulativ.
    # Deshalb werden ALLE aktuell aufgemessenen Positionen des Projekts
    # in die Rechnung übernommen – auch Positionen, die bereits zu 100 %
    # abgerechnet wurden. Nur die Differenz zum bisherigen Abrechnungsstand
    # erhöht den neuen Rechnungsbetrag.
    rows=self.measurement_positions(project_id)
    current_rows=[r for r in rows if float(r["current_quantity"] or 0) > 0.0000001]
    if not current_rows:
        return None,"Für dieses Projekt gibt es derzeit keine aufgemessenen Leistungen."

    # Es muss mindestens irgendwo einen noch nicht abgerechneten Zuwachs geben.
    billable=[r for r in current_rows
              if float(r["current_quantity"] or 0)-float(r["billed_quantity"] or 0) > 0.0000001]
    if not billable:
        return None,"Der aktuelle kumulative Aufmaßstand ist bereits vollständig abgerechnet."

    number=self.next_invoice_number()
    now=datetime.now().isoformat(timespec="seconds")
    if tax_mode.startswith("Steuerschuldnerschaft"):
        vat_rate=0.0

    cur=self.conn.execute("""INSERT INTO invoices
      (number,project_id,invoice_type,title,status,created_at,due_date,vat_rate,tax_mode,
       performance_from,performance_to,skonto_percent,skonto_due_date,
       security_enabled,security_percent,construction_enabled,construction_percent,construction_label,
       notes,net_total,gross_total,payable_total)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
      (number,project_id,"Teilrechnung",title,"Entwurf",now,due_date,vat_rate,tax_mode,
       performance_from,performance_to,skonto_percent,skonto_due_date,
       1 if security_enabled else 0,security_percent,1 if construction_enabled else 0,
       construction_percent,construction_label or "Bauwesen",notes,0.0,0.0,0.0))
    iid=cur.lastrowid

    net_due=0.0
    for r in current_rows:
        cumulative=float(r["current_quantity"] or 0)
        previous=float(r["billed_quantity"] or 0)
        new_qty=max(0.0,cumulative-previous)
        unit_price=float(r["unit_price"] or 0)
        due_line=new_qty*unit_price
        net_due+=due_line
        self.conn.execute("""INSERT INTO invoice_positions
          (invoice_id,measurement_position_id,offer_position_id,position_no,short_text,unit,unit_price,
           cumulative_quantity,previously_billed_quantity,new_quantity,line_total)
          VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
          (iid,r["measurement_position_id"],r["offer_position_id"],r["position_no"],r["short_text"],r["unit"],
           unit_price,cumulative,previous,new_qty,due_line))

    gross=net_due*(1+vat_rate/100.0)
    security_amount=net_due*float(security_percent or 0)/100.0 if security_enabled else 0.0
    construction_amount=net_due*float(construction_percent or 0)/100.0 if construction_enabled else 0.0
    payable=max(0.0,gross-security_amount-construction_amount)
    self.conn.execute("""UPDATE invoices SET net_total=?,gross_total=?,payable_total=? WHERE id=?""",
                      (net_due,gross,payable,iid))
    self.conn.commit()
    return iid,None

def _db_create_invoice(self,project_id,invoice_type,source_mode,installment_no,deduct_previous,title,due_date,vat_rate,tax_mode,
                       performance_from,performance_to,skonto_percent,skonto_due_date,
                       security_enabled,security_percent,construction_enabled,
                       construction_percent,construction_label,notes):
    """Legt immer zuerst einen projektbezogenen, editierbaren Entwurf an."""
    if not self.project(project_id):
        return None,"Das ausgewählte Projekt wurde nicht gefunden."
    if invoice_type not in ("Rechnung","Teilrechnung","Abschlagsrechnung","Schlussrechnung"):
        return None,"Bitte eine gültige Rechnungsart auswählen."
    if invoice_type=="Teilrechnung":
        duplicate=self.conn.execute("""SELECT number FROM invoices WHERE project_id=?
          AND invoice_type='Teilrechnung' AND installment_no=?""",
          (project_id,max(1,int(installment_no or 1)))).fetchone()
        if duplicate:return None,f'Diese laufende Teilrechnungsnummer wird bereits von {duplicate["number"]} verwendet.'
    if source_mode == "Aufmaß":
        rows=[r for r in self.measurement_positions(project_id)
              if float(r["current_quantity"] or 0)>0.0000001]
        if not rows:
            return None,"Für dieses Projekt gibt es derzeit keine aufgemessenen Leistungen."
    else:
        rows=[]
    number=self.next_invoice_number();now=datetime.now().isoformat(timespec="seconds")
    if (tax_mode or "").startswith("Steuerschuldnerschaft"):vat_rate=0.0
    cur=self.conn.execute("""INSERT INTO invoices
      (number,project_id,invoice_type,installment_no,deduct_previous,title,status,created_at,due_date,vat_rate,tax_mode,
       performance_from,performance_to,skonto_percent,skonto_due_date,security_enabled,
       security_percent,construction_enabled,construction_percent,construction_label,notes)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
      (number,project_id,invoice_type,max(1,int(installment_no or 1)),1 if deduct_previous else 0,
       title or invoice_type,"Entwurf",now,due_date,vat_rate,tax_mode,
       performance_from,performance_to,skonto_percent,skonto_due_date,1 if security_enabled else 0,
       security_percent,1 if construction_enabled else 0,construction_percent,
       construction_label or "Bauwesen",notes))
    iid=cur.lastrowid
    for r in rows:
        cumulative=float(r["current_quantity"] or 0);previous=float(r["billed_quantity"] or 0)
        qty=max(0.0,cumulative-previous);price=float(r["unit_price"] or 0)
        self.conn.execute("""INSERT INTO invoice_positions
          (invoice_id,measurement_position_id,offer_position_id,position_no,short_text,unit,unit_price,
           cumulative_quantity,previously_billed_quantity,new_quantity,line_total)
          VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
          (iid,r["measurement_position_id"],r["offer_position_id"],r["position_no"],r["short_text"],
           r["unit"],price,cumulative,previous,qty,qty*price))
    self.conn.commit();self.recalc_invoice_totals(iid)
    return iid,None

def _db_import_historical_invoice(self,project_id,invoice_type,number,invoice_date,
                                  installment_no,net_total,gross_total,vat_rate,
                                  paid_amount,discount_amount,payment_date,source_pdf="",notes=""):
    """Übernimmt einen bereits ausgestellten Beleg ohne Nummernkreisvergabe."""
    if invoice_type not in ("Teilrechnung","Abschlagsrechnung"):
        return None,"Nur vorhandene Teil- oder Abschlagsrechnungen können übernommen werden."
    if not self.project(project_id):
        return None,"Das ausgewählte Projekt wurde nicht gefunden."
    number=(number or "").strip()
    if not number:
        return None,"Bitte die originale Rechnungsnummer eingeben."
    if self.conn.execute("SELECT 1 FROM invoices WHERE number=?",(number,)).fetchone():
        return None,f'Die Rechnungsnummer {number} ist in Aufmaßwerk bereits vorhanden.'
    installment_no=max(1,int(installment_no or 1))
    if invoice_type=="Teilrechnung":
        duplicate=self.conn.execute("""SELECT number FROM invoices WHERE project_id=?
          AND invoice_type='Teilrechnung' AND installment_no=?""",
          (project_id,installment_no)).fetchone()
        if duplicate:
            return None,f'Die {installment_no}. Teilrechnung ist bereits als {duplicate["number"]} vorhanden.'
    net_total=max(0.0,float(net_total or 0));gross_total=max(0.0,float(gross_total or 0))
    paid_amount=max(0.0,float(paid_amount or 0))
    discount_amount=max(0.0,float(discount_amount or 0));vat_rate=max(0.0,float(vat_rate or 0))
    if gross_total<=0.005:
        return None,"Der Bruttobetrag muss größer als 0,00 € sein."
    if net_total>gross_total+0.01:
        return None,"Der Nettobetrag darf nicht größer als der Bruttobetrag sein."
    if paid_amount+discount_amount>gross_total+0.01:
        return None,"Tatsächliche Zahlung und Skonto dürfen zusammen den Bruttobetrag nicht überschreiten."
    now=datetime.now().isoformat(timespec="seconds")
    settled=paid_amount+discount_amount
    status=("Ausgeglichen" if discount_amount>0.005 else "Bezahlt") if abs(settled-gross_total)<=0.01 else ("Teilbezahlt" if settled>0.005 else "Offen")
    try:
        self.conn.execute("BEGIN")
        cur=self.conn.execute("""INSERT INTO invoices
          (number,project_id,invoice_type,installment_no,deduct_previous,title,status,
           created_at,due_date,vat_rate,tax_mode,net_total,gross_total,payable_total,
           notes,is_historical,source_pdf,imported_at)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
          (number,project_id,invoice_type,installment_no,0,
           f'Historisch übernommene {invoice_type}',status,invoice_date,invoice_date,
           vat_rate,"Normale Umsatzsteuer",net_total,gross_total,gross_total,
           notes or "Außerhalb von Aufmaßwerk ausgestellter Originalbeleg.",1,
           source_pdf or None,now))
        iid=cur.lastrowid
        self.conn.execute("""INSERT INTO invoice_positions
          (invoice_id,position_no,short_text,unit,unit_price,cumulative_quantity,
           previously_billed_quantity,new_quantity,line_total)
          VALUES(?,?,?,?,?,?,?,?,?)""",
          (iid,"1",f'Historisch übernommene {invoice_type} {number}',"pauschal",
           net_total,1,0,1,net_total))
        if settled>0.005:
            self.conn.execute("""INSERT INTO payments
              (invoice_id,payment_date,paid_amount,discount_amount,adjustment_amount,
               adjustment_type,adjustment_reason,created_at)
              VALUES(?,?,?,?,?,?,?,?)""",
              (iid,payment_date,paid_amount,discount_amount,0,"",
               "Bei Übernahme vorhandener Rechnung erfasst",now))
        self.conn.commit()
        return iid,None
    except Exception as exc:
        self.conn.rollback()
        return None,f"Der vorhandene Beleg konnte nicht übernommen werden: {exc}"

def _db_add_manual_invoice_position(self,iid,position_no="",short_text="Neue Position",quantity=1.0,unit="Stk",unit_price=0.0):
    inv=self.invoice(iid)
    if not inv or inv["status"]!="Entwurf":
        return None,"Manuelle Positionen können nur in einem Rechnungsentwurf angelegt werden."
    if not position_no:
        position_no=str(self.conn.execute("SELECT COUNT(*)+1 FROM invoice_positions WHERE invoice_id=?",(iid,)).fetchone()[0])
    cur=self.conn.execute("""INSERT INTO invoice_positions
      (invoice_id,position_no,short_text,unit,unit_price,cumulative_quantity,
       previously_billed_quantity,new_quantity,line_total)
      VALUES(?,?,?,?,?,?,?,?,?)""",(iid,position_no,short_text,unit,unit_price,quantity,0,quantity,quantity*unit_price))
    self.conn.commit();self.recalc_invoice_totals(iid)
    return cur.lastrowid,None

def _db_update_invoice_position(self,ipid,position_no,short_text,quantity,unit,unit_price,line_total=None):
    row=self.conn.execute("""SELECT ip.*,i.status FROM invoice_positions ip
      JOIN invoices i ON i.id=ip.invoice_id WHERE ip.id=?""",(ipid,)).fetchone()
    if not row:return False,"Rechnungsposition wurde nicht gefunden."
    if row["status"]!="Entwurf":return False,"Freigegebene Rechnungspositionen sind geschützt."
    quantity=max(0.0,float(quantity or 0));unit_price=float(unit_price or 0)
    total=quantity*unit_price if line_total is None else float(line_total or 0)
    previous=float(row["previously_billed_quantity"] or 0)
    self.conn.execute("""UPDATE invoice_positions SET position_no=?,short_text=?,new_quantity=?,unit=?,
      unit_price=?,line_total=?,cumulative_quantity=? WHERE id=?""",
      (position_no or "",short_text or "",quantity,unit or "",unit_price,total,previous+quantity,ipid))
    self.conn.commit();self.recalc_invoice_totals(row["invoice_id"])
    return True,None

def _db_invoices(self,search=""):
    s=f"%{search}%"
    return self.conn.execute("""SELECT i.*,p.number AS project_number,p.name AS project_name,c.company
      FROM invoices i JOIN projects p ON p.id=i.project_id JOIN customers c ON c.id=p.customer_id
      WHERE i.number LIKE ? OR p.number LIKE ? OR p.name LIKE ? OR c.company LIKE ? OR i.status LIKE ?
      ORDER BY i.id DESC""",(s,s,s,s,s)).fetchall()

def _db_invoice(self,iid):
    return self.conn.execute("""SELECT i.*,p.number AS project_number,p.name AS project_name,p.site,
      c.company,c.number AS customer_number,c.contact AS customer_contact,c.street AS customer_street,
      c.zip AS customer_zip,c.city AS customer_city,c.phone AS customer_phone,c.email AS customer_email
      FROM invoices i JOIN projects p ON p.id=i.project_id JOIN customers c ON c.id=p.customer_id
      WHERE i.id=?""",(iid,)).fetchone()

def _db_invoice_positions(self,iid):
    return self.conn.execute("""SELECT ip.*,op.long_text,op.title_no,op.title_text FROM invoice_positions ip
      LEFT JOIN offer_positions op ON op.id=ip.offer_position_id WHERE ip.invoice_id=? ORDER BY ip.id""",(iid,)).fetchall()

def _db_finalize_invoice(self,iid):
    inv=self.invoice(iid)
    if not inv or inv["status"]!="Entwurf":
        return False,"Nur eine Rechnung im Status Entwurf kann freigegeben werden."
    rows=self.invoice_positions(iid)
    if not rows:
        return False,"Der Rechnungsentwurf enthält keine Positionen."
    for r in rows:
        if r["measurement_position_id"] is not None:
            current=self.conn.execute("SELECT billed_quantity FROM measurement_positions WHERE id=?",
                                      (r["measurement_position_id"],)).fetchone()
            billed=float(current["billed_quantity"] or 0) if current else 0
            target=float(r["cumulative_quantity"] or 0)
            if target < billed-0.0000001:
                return False,"Der aktuelle Abrechnungsstand ist kleiner als ein bereits festgeschriebener Stand."
    for r in rows:
        if r["measurement_position_id"] is not None:
            self.conn.execute("UPDATE measurement_positions SET billed_quantity=? WHERE id=?",
                              (r["cumulative_quantity"],r["measurement_position_id"]))
    self.conn.execute("UPDATE invoices SET status='Offen' WHERE id=?",(iid,))
    self.conn.commit()
    return True,None

def _db_delete_invoice(self,iid):
    inv=self.invoice(iid)
    if not inv:return False,"Rechnung wurde nicht gefunden."
    if inv["status"]!="Entwurf":
        return False,"Festgeschriebene Rechnungen können nicht gelöscht werden."
    self.conn.execute("DELETE FROM invoices WHERE id=?",(iid,));self.conn.commit()
    return True,None

def _db_payments(self,iid):
    return self.conn.execute("""SELECT * FROM payments WHERE invoice_id=? ORDER BY payment_date,id""",(iid,)).fetchall()

def _db_payment_totals(self,iid):
    row=self.conn.execute("""SELECT COALESCE(SUM(paid_amount),0) paid,
      COALESCE(SUM(discount_amount),0) discount,
      COALESCE(SUM(adjustment_amount),0) adjustment
      FROM payments WHERE invoice_id=?""",(iid,)).fetchone()
    return float(row["paid"] or 0),float(row["discount"] or 0),float(row["adjustment"] or 0)

def _db_invoice_open_amount(self,iid):
    inv=self.invoice(iid)
    paid,discount,adjustment=self.payment_totals(iid)
    basis=float(inv["payable_total"] if inv["payable_total"] is not None else inv["gross_total"] or 0)
    return max(0.0,basis-paid-discount-adjustment)

def _db_validate_discount(self,iid,payment_date,discount):
    """Skonto nur innerhalb der auf der Rechnung ausgewiesenen Frist anerkennen."""
    if float(discount or 0)<=0.005:
        return True,None
    inv=self.invoice(iid)
    if not inv:
        return False,"Rechnung wurde nicht gefunden."
    # Bei einem historischen Beleg wird eine bereits erfolgte Zahlung lediglich
    # dokumentiert. Seine damaligen Skontobedingungen müssen deshalb nicht in
    # Aufmaßwerk nachgebildet sein.
    if bool(inv["is_historical"]):
        return True,None
    if float(inv["skonto_percent"] or 0)<=0:
        return False,"Für diese Rechnung wurde kein Skonto vereinbart."
    try:
        paid_on=datetime.strptime(str(payment_date),"%Y-%m-%d").date()
        due_on=datetime.strptime(str(inv["skonto_due_date"] or ""),"%Y-%m-%d").date()
    except (TypeError,ValueError):
        return False,"Die Skontofrist oder das Zahlungsdatum ist ungültig. Bitte prüfen Sie die Datumsangaben."
    if paid_on>due_on:
        return False,(
            f"Die Skontofrist endete am {due_on.strftime('%d.%m.%Y')}. "
            f"Für die Zahlung vom {paid_on.strftime('%d.%m.%Y')} darf kein Skonto gebucht werden. "
            "Bitte erfassen Sie nur den tatsächlich gezahlten Betrag; ein verbleibender Rest bleibt offen."
        )
    return True,None

def _db_add_payment(self,iid,payment_date,paid,discount,adjustment,adjustment_type,reason):
    valid,error=self.validate_discount(iid,payment_date,discount)
    if not valid:
        raise ValueError(error)
    paid=max(0.0,float(paid or 0));discount=max(0.0,float(discount or 0))
    adjustment=max(0.0,float(adjustment or 0))
    open_before=self.invoice_open_amount(iid)
    if paid+discount+adjustment>open_before+0.01:
        raise ValueError(
            f"Die Buchung übersteigt den offenen Betrag von {money(open_before)}. "
            "Bitte nur den tatsächlich noch offenen Betrag erfassen."
        )
    now=datetime.now().isoformat(timespec="seconds")
    self.conn.execute("""INSERT INTO payments
      (invoice_id,payment_date,paid_amount,discount_amount,adjustment_amount,adjustment_type,adjustment_reason,created_at)
      VALUES(?,?,?,?,?,?,?,?)""",(iid,payment_date,paid,discount,adjustment,adjustment_type,reason,now))
    open_amount=self.invoice_open_amount(iid)
    paid_t,disc_t,adj_t=self.payment_totals(iid)
    if open_amount <= 0.005:
        status="Bezahlt" if adj_t<=0.005 and disc_t<=0.005 else "Ausgeglichen"
    elif paid_t+disc_t+adj_t > 0.005:
        status="Teilbezahlt"
    else:
        status="Offen"
    self.conn.execute("UPDATE invoices SET status=? WHERE id=?",(status,iid))
    self.conn.commit()

def _db_previous_invoice_net(self,project_id,iid):
    row=self.conn.execute("""SELECT COALESCE(SUM(net_total),0) AS n FROM invoices
      WHERE project_id=? AND id<? AND status<>'Entwurf'""",(project_id,iid)).fetchone()
    return float(row["n"] or 0)

DB.measurement_projects=_db_measurement_projects
DB.project_offers=_db_project_offers
DB.available_offer_positions=_db_available_offer_positions
DB.add_measurement_position=_db_add_measurement_position
DB.measurement_positions=_db_measurement_positions
DB._measurement_positions_raw=_db_measurement_positions_raw
DB.move_measurement_position=_db_move_measurement_position
DB.move_measurement_line=_db_move_measurement_line
DB._measurement_position=_db_measurement_position
DB.measurement_lines=_db_measurement_lines
DB.add_measurement_line=_db_add_measurement_line
DB.update_measurement_line=_db_update_measurement_line
DB.delete_measurement_line=_db_delete_measurement_line
DB.remove_measurement_position=_db_remove_measurement_position
DB.measurement_total=_db_measurement_total
DB.update_measurement_position=_db_update_measurement_position
DB.copy_offer_position=_db_copy_offer_position
DB.create_offer_from_offer_positions=_db_create_offer_from_offer_positions
DB.add_snapshot=_db_add_snapshot
DB.snapshots=_db_snapshots
DB.invoice_projects=_db_invoice_projects
DB.all_invoice_projects=_db_all_invoice_projects
DB.next_invoice_number=_db_next_invoice_number
DB.create_partial_invoice=_db_create_partial_invoice
DB.create_invoice=_db_create_invoice
DB.import_historical_invoice=_db_import_historical_invoice
DB.add_manual_invoice_position=_db_add_manual_invoice_position
DB.update_invoice_position=_db_update_invoice_position
DB.invoices=_db_invoices
DB.invoice=_db_invoice
DB.invoice_positions=_db_invoice_positions
DB.finalize_invoice=_db_finalize_invoice
DB.delete_invoice=_db_delete_invoice
DB.payments=_db_payments
DB.payment_totals=_db_payment_totals
DB.invoice_open_amount=_db_invoice_open_amount
DB.validate_discount=_db_validate_discount
DB.add_payment=_db_add_payment
DB.previous_invoice_net=_db_previous_invoice_net

def _db_cumulative_invoice_settlement(self,iid):
    """Zentrale Fortschreibung fuer kumulative Teil-/Schlussrechnungen.

    Fruehere Rechnungs- oder Leistungsbetraege gelten nicht automatisch als
    erledigt. Wirtschaftlich erledigt sind ausschliesslich echte Zahlungen und
    anerkannte (in der Zahlungsbuchung erfasste) Skontobetraege. Ein sonstiger
    Ausgleich gehoert in die Forderungs-/Mahnlogik und bleibt hier unberuecksichtigt.
    """
    inv=self.invoice(iid)
    if not inv:
        return {"cumulative_net":0.0,"vat":0.0,"settled":0.0,
                "security":0.0,"construction":0.0,"payable":0.0}

    cumulative=bool(inv["deduct_previous"]) and inv["invoice_type"] in ("Teilrechnung","Schlussrechnung")
    cumulative_net=self.invoice_cumulative_net(iid) if cumulative else float(
        self.conn.execute("SELECT COALESCE(SUM(line_total),0) FROM invoice_positions WHERE invoice_id=?",
                          (iid,)).fetchone()[0] or 0)
    vat_rate=0.0 if (inv["tax_mode"] or "").startswith("Steuerschuldnerschaft") else float(inv["vat_rate"] or 0)
    vat=cumulative_net*vat_rate/100.0
    settled=0.0
    if cumulative:
        # Folge-Teilrechnungen ziehen Zahlungen früherer Teilrechnungen ab.
        # Die Schlussrechnung berücksichtigt zusätzlich erhaltene Abschläge.
        eligible_types=("Teilrechnung","Abschlagsrechnung") if inv["invoice_type"]=="Schlussrechnung" else ("Teilrechnung",)
        placeholders=",".join("?" for _ in eligible_types)
        row=self.conn.execute("""SELECT COALESCE(SUM(MIN(
          (SELECT COALESCE(SUM(p.paid_amount+p.discount_amount),0)
             FROM payments p WHERE p.invoice_id=i.id),
          CASE WHEN COALESCE(i.payable_total,0)>0 THEN i.payable_total ELSE COALESCE(i.gross_total,0) END
          )),0) AS settled
          FROM invoices i
          WHERE i.project_id=? AND i.id<>? AND i.invoice_type IN ("""+placeholders+""")
            AND i.status<>'Entwurf'
            AND (datetime(i.created_at)<datetime(?) OR
                 (datetime(i.created_at)=datetime(?) AND i.id<?))""",
          (inv["project_id"],iid,*eligible_types,inv["created_at"],inv["created_at"],iid)).fetchone()
        settled=float(row["settled"] or 0)
    security=cumulative_net*float(inv["security_percent"] or 0)/100.0 if inv["security_enabled"] else 0.0
    construction=cumulative_net*float(inv["construction_percent"] or 0)/100.0 if inv["construction_enabled"] else 0.0
    payable=max(0.0,cumulative_net+vat-settled-security-construction)
    return {"cumulative_net":cumulative_net,"vat":vat,"settled":settled,
            "security":security,"construction":construction,"payable":payable}

DB.cumulative_invoice_settlement=_db_cumulative_invoice_settlement

# --- Eingangsrechnungen: Kostenüberblick je Projekt, bewusst keine Buchhaltung ---------------
INCOMING_CATEGORIES=("Material","Nachunternehmer","Geräte / Miete","Sonstiges")

def incoming_status(row):
    if row["paid_date"]:return "Bezahlt"
    if row["due_date"] and str(row["due_date"])[:10]<date.today().isoformat():return "Überfällig"
    return "Offen"

def _db_incoming_invoices(self,project_id=None,search=""):
    sql="""SELECT e.*,p.number AS project_number,p.name AS project_name FROM incoming_invoices e
      JOIN projects p ON p.id=e.project_id""";where=[];args=[]
    if project_id:where.append("e.project_id=?");args.append(project_id)
    if search:
        where.append("(e.supplier LIKE ? OR e.invoice_no LIKE ? OR e.note LIKE ? OR e.category LIKE ? OR p.number LIKE ? OR p.name LIKE ?)")
        args+=[f"%{search}%"]*6
    if where:sql+=" WHERE "+" AND ".join(where)
    return self.conn.execute(sql+" ORDER BY e.invoice_date DESC,e.id DESC",args).fetchall()

def _db_incoming_invoice(self,eid):
    return self.conn.execute("SELECT * FROM incoming_invoices WHERE id=?",(eid,)).fetchone()

def _db_save_incoming_invoice(self,eid,d):
    values=(d["project_id"],d["supplier"],d["invoice_no"],d["invoice_date"],d["category"],d["net_amount"],
            d["vat_rate"],d["gross_amount"],d["due_date"],d["paid_date"],d["note"],d["document_id"])
    if eid:
        self.conn.execute("""UPDATE incoming_invoices SET project_id=?,supplier=?,invoice_no=?,invoice_date=?,category=?,
          net_amount=?,vat_rate=?,gross_amount=?,due_date=?,paid_date=?,note=?,document_id=? WHERE id=?""",(*values,eid))
    else:
        eid=self.conn.execute("""INSERT INTO incoming_invoices(project_id,supplier,invoice_no,invoice_date,category,
          net_amount,vat_rate,gross_amount,due_date,paid_date,note,document_id,created_at)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",(*values,datetime.now().isoformat(timespec="seconds"))).lastrowid
    self.conn.commit();return eid

def _db_delete_incoming_invoice(self,eid):
    self.conn.execute("DELETE FROM incoming_invoices WHERE id=?",(eid,));self.conn.commit()

def _db_incoming_suppliers(self):
    return [r[0] for r in self.conn.execute(
        "SELECT DISTINCT supplier FROM incoming_invoices ORDER BY supplier COLLATE NOCASE").fetchall()]

def _db_incoming_open_summary(self):
    rows=self.conn.execute("SELECT * FROM incoming_invoices WHERE paid_date IS NULL OR paid_date=''").fetchall()
    return {"count":len(rows),"total":sum(float(r["gross_amount"] or 0) for r in rows),
            "overdue":sum(1 for r in rows if incoming_status(r)=="Überfällig")}

def _db_project_economics(self,pid):
    """Wo steht das Projekt? Erlöse und Kosten netto, Geldfluss brutto."""
    offers=self.project_offers(pid);ordered=[o for o in offers if o["status"]=="Beauftragt"]
    order_net=sum(float(self.total(o["id"]) or 0) for o in ordered)
    offer_net=sum(float(self.total(o["id"]) or 0) for o in offers)
    performed=sum(float(p["current_quantity"] or 0)*float(p["unit_price"] or 0) for p in self.measurement_positions(pid))
    released=self.conn.execute("""SELECT * FROM invoices WHERE project_id=?
      AND status NOT IN ('Entwurf','Storniert') ORDER BY datetime(created_at),id""",(pid,)).fetchall()
    # Kumulative Teil-/Schlussrechnungen enthalten jeweils den gesamten Leistungsstand:
    # Es zählt nur der Stand der letzten, nicht die Summe aller.
    cumulative=[i for i in released if i["deduct_previous"] and i["invoice_type"] in ("Teilrechnung","Schlussrechnung")]
    invoiced=self.invoice_cumulative_net(cumulative[-1]["id"]) if cumulative else 0.0
    # Abschläge sind Vorauszahlungen; mit Schlussrechnung stecken sie bereits in deren Leistung.
    has_final=any(i["invoice_type"]=="Schlussrechnung" for i in released)
    for i in released:
        if i in cumulative or (has_final and i["invoice_type"]=="Abschlagsrechnung"):continue
        invoiced+=float(i["net_total"] or 0)
    received=float(self.conn.execute("""SELECT COALESCE(SUM(pa.paid_amount),0) FROM payments pa
      JOIN invoices i ON i.id=pa.invoice_id WHERE i.project_id=?""",(pid,)).fetchone()[0] or 0)
    incoming=self.incoming_invoices(pid);categories={}
    for e in incoming:categories[e["category"]]=categories.get(e["category"],0.0)+float(e["net_amount"] or 0)
    costs=sum(categories.values())
    paid_out=sum(float(e["gross_amount"] or 0) for e in incoming if e["paid_date"])
    open_out=sum(float(e["gross_amount"] or 0) for e in incoming if not e["paid_date"])
    base=order_net or offer_net
    return {"order_net":order_net,"offer_net":offer_net,"has_order":bool(ordered),"base":base,"performed":performed,
            "invoiced":invoiced,"received":received,"costs":costs,"categories":categories,"incoming_count":len(incoming),
            "paid_out":paid_out,"open_out":open_out,
            "overdue_out":sum(1 for e in incoming if incoming_status(e)=="Überfällig"),
            "result_now":invoiced-costs,"result_expected":base-costs,
            "cost_share":(costs/base*100.0) if base>0 else None}

DB.incoming_invoices=_db_incoming_invoices
DB.incoming_invoice=_db_incoming_invoice
DB.save_incoming_invoice=_db_save_incoming_invoice
DB.delete_incoming_invoice=_db_delete_incoming_invoice
DB.incoming_suppliers=_db_incoming_suppliers
DB.incoming_open_summary=_db_incoming_open_summary
DB.project_economics=_db_project_economics

def project_economics_html(e):
    """Kompakter Block für die Projektvorschau."""
    def row(label,value,bold=False,color=None,indent=False):
        style=("font-weight:600;" if bold else "")+(f"color:{color};" if color else "")
        pad="padding-left:22px;" if indent else ""
        return (f'<tr><td style="padding:3px 28px 3px 0;{pad}{style}">{label}</td>'
                f'<td align="right" style="padding:3px 0;{style}">{value}</td></tr>')
    def signed(v):
        return ("+ " if v>0 else "− " if v<0 else "")+money(abs(v))
    def tone(v):
        return "#1f7a43" if v>0 else "#b3261e" if v<0 else None
    html='<table cellspacing="0" cellpadding="0">'
    html+=row("Auftragssumme (beauftragte Angebote)" if e["has_order"] else "Angebotssumme (noch nicht beauftragt)",money(e["base"]))
    html+=row("Leistung laut Aufmaß",money(e["performed"]))
    html+=row("Abgerechnet (Ausgangsrechnungen)",money(e["invoiced"]))
    html+=row(f'Kosten (Eingangsrechnungen, {e["incoming_count"]})',money(e["costs"]),bold=True)
    for name,value in sorted(e["categories"].items(),key=lambda x:-x[1]):
        html+=row("davon "+name,money(value),indent=True)
    html+='<tr><td colspan="2"><hr></td></tr>'
    html+=row("Ergebnis bisher (abgerechnet − Kosten)",signed(e["result_now"]),bold=True,color=tone(e["result_now"]))
    html+=row("Erwartetes Ergebnis (Auftragssumme − Kosten)",signed(e["result_expected"]),bold=True,color=tone(e["result_expected"]))
    if e["cost_share"] is not None:
        share=e["cost_share"];color="#b3261e" if share>=100 else "#9a6700" if share>=80 else None
        html+=row("Kostenanteil an der Auftragssumme",de_num(share,1)+" %",color=color)
    html+='<tr><td colspan="2"><hr></td></tr>'
    html+=row("Geld erhalten (brutto)",money(e["received"]))
    html+=row("An Lieferanten bezahlt (brutto)",money(e["paid_out"]))
    overdue=f', davon {e["overdue_out"]} überfällig' if e["overdue_out"] else ""
    html+=row(f"Eingangsrechnungen noch offen (brutto{overdue})",money(e["open_out"]),color="#b3261e" if e["overdue_out"] else None)
    html+="</table>"
    html+='<p style="color:#6b7780">Alle Erlöse und Kosten netto. Löhne und eigene Stunden sind nicht enthalten.</p>'
    return html

def _db_recalc_invoice_totals(self,iid):
    inv=self.invoice(iid)
    net=float(self.conn.execute("""SELECT COALESCE(SUM(line_total),0) FROM invoice_positions
      WHERE invoice_id=?""",(iid,)).fetchone()[0] or 0)
    vat_rate=0.0 if (inv["tax_mode"] or "").startswith("Steuerschuldnerschaft") else float(inv["vat_rate"] or 0)
    gross=net*(1+vat_rate/100.0)
    settlement=self.cumulative_invoice_settlement(iid)
    payable=settlement["payable"]
    self.conn.execute("""UPDATE invoices SET net_total=?,gross_total=?,payable_total=?,vat_rate=? WHERE id=?""",
                      (net,gross,payable,vat_rate,iid))
    self.conn.commit()

def _db_update_invoice_draft(self,iid,title,due_date,vat_rate,tax_mode,performance_from,
                             performance_to,skonto_percent,skonto_due_date,
                             security_enabled,security_percent,construction_enabled,
                             construction_percent,construction_label,notes,
                             installment_no=1,deduct_previous=True):
    inv=self.invoice(iid)
    if not inv or inv["status"]!="Entwurf":
        return False,"Nur Rechnungen im Status Entwurf können bearbeitet werden."
    if inv["invoice_type"]=="Teilrechnung":
        duplicate=self.conn.execute("""SELECT number FROM invoices WHERE project_id=?
          AND invoice_type='Teilrechnung' AND installment_no=? AND id<>?""",
          (inv["project_id"],max(1,int(installment_no or 1)),iid)).fetchone()
        if duplicate:return False,f'Diese laufende Teilrechnungsnummer wird bereits von {duplicate["number"]} verwendet.'
    if (tax_mode or "").startswith("Steuerschuldnerschaft"):
        vat_rate=0.0
    self.conn.execute("""UPDATE invoices SET title=?,due_date=?,vat_rate=?,tax_mode=?,
      performance_from=?,performance_to=?,skonto_percent=?,skonto_due_date=?,
      security_enabled=?,security_percent=?,construction_enabled=?,construction_percent=?,
      construction_label=?,notes=?,installment_no=?,deduct_previous=? WHERE id=?""",
      (title,due_date,vat_rate,tax_mode,performance_from,performance_to,
       skonto_percent,skonto_due_date,1 if security_enabled else 0,security_percent,
       1 if construction_enabled else 0,construction_percent,construction_label or "Bauwesen",
       notes,max(1,int(installment_no or 1)),1 if deduct_previous else 0,iid))
    self.conn.commit()
    self.recalc_invoice_totals(iid)
    return True,None

def _db_available_positions_for_invoice(self,iid):
    inv=self.invoice(iid)
    if not inv:return []
    return self.conn.execute("""SELECT mp.id AS measurement_position_id,
      op.id AS offer_position_id,op.position_no,op.short_text,op.unit,op.unit_price,
      COALESCE((SELECT SUM(ml.quantity) FROM measurement_lines ml
                WHERE ml.measurement_position_id=mp.id),0) AS current_quantity,
      mp.billed_quantity
      FROM measurement_positions mp
      JOIN offer_positions op ON op.id=mp.offer_position_id
      LEFT JOIN invoice_positions ip ON ip.invoice_id=? AND ip.measurement_position_id=mp.id
      WHERE mp.project_id=? AND ip.id IS NULL
        AND (
          EXISTS(SELECT 1 FROM invoice_position_exclusions e
                 WHERE e.invoice_id=? AND e.measurement_position_id=mp.id)
          OR (COALESCE((SELECT SUM(ml.quantity) FROM measurement_lines ml
                        WHERE ml.measurement_position_id=mp.id),0)-mp.billed_quantity) > 0.0000001
        )
      ORDER BY op.sort_order,op.id""",(iid,inv["project_id"],iid)).fetchall()

def _db_add_invoice_position(self,iid,mpid):
    inv=self.invoice(iid)
    if not inv or inv["status"]!="Entwurf":
        return False,"Positionen können nur einem Rechnungsentwurf hinzugefügt werden."
    row=self.conn.execute("""SELECT mp.id AS measurement_position_id,mp.offer_position_id,
      mp.billed_quantity,op.position_no,op.short_text,op.unit,op.unit_price,
      COALESCE((SELECT SUM(ml.quantity) FROM measurement_lines ml
                WHERE ml.measurement_position_id=mp.id),0) AS current_quantity
      FROM measurement_positions mp JOIN offer_positions op ON op.id=mp.offer_position_id
      WHERE mp.id=? AND mp.project_id=?""",(mpid,inv["project_id"])).fetchone()
    if not row:return False,"Die Aufmaßposition wurde nicht gefunden."
    exists=self.conn.execute("""SELECT COUNT(*) FROM invoice_positions
      WHERE invoice_id=? AND measurement_position_id=?""",(iid,mpid)).fetchone()[0]
    if exists:return False,"Diese Position ist bereits in der Rechnung enthalten."
    cumulative=float(row["current_quantity"] or 0)
    previous=float(row["billed_quantity"] or 0)
    new_qty=max(0.0,cumulative-previous)
    unit_price=float(row["unit_price"] or 0)
    total=new_qty*unit_price
    self.conn.execute("""INSERT INTO invoice_positions
      (invoice_id,measurement_position_id,offer_position_id,position_no,short_text,unit,unit_price,
       cumulative_quantity,previously_billed_quantity,new_quantity,line_total)
      VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
      (iid,mpid,row["offer_position_id"],row["position_no"],row["short_text"],row["unit"],
       unit_price,cumulative,previous,new_qty,total))
    self.conn.execute("""DELETE FROM invoice_position_exclusions
      WHERE invoice_id=? AND measurement_position_id=?""",(iid,mpid))
    self.conn.commit()
    self.recalc_invoice_totals(iid)
    return True,None

def _db_remove_invoice_position(self,invoice_position_id):
    row=self.conn.execute("""SELECT ip.id,ip.invoice_id,ip.measurement_position_id,i.status
      FROM invoice_positions ip JOIN invoices i ON i.id=ip.invoice_id WHERE ip.id=?""",
      (invoice_position_id,)).fetchone()
    if not row:return False,"Rechnungsposition wurde nicht gefunden."
    if row["status"]!="Entwurf":
        return False,"Positionen einer festgeschriebenen Rechnung sind geschützt."

    # Die Position wird nur aus DIESEM Rechnungsentwurf ausgeschlossen.
    # Aufmaß und Angebot bleiben unverändert.
    if row["measurement_position_id"] is not None:
        self.conn.execute("""INSERT OR REPLACE INTO invoice_position_exclusions
          (invoice_id,measurement_position_id,created_at) VALUES(?,?,?)""",
          (row["invoice_id"],row["measurement_position_id"],datetime.now().isoformat(timespec="seconds")))
    self.conn.execute("DELETE FROM invoice_positions WHERE id=?",(invoice_position_id,))
    self.conn.commit()
    self.recalc_invoice_totals(row["invoice_id"])
    return True,None

def _db_rebuild_project_billed_quantities(self,project_id):
    # Abrechnungsstand vollständig aus den noch vorhandenen festgeschriebenen
    # Rechnungen neu aufbauen.
    self.conn.execute("UPDATE measurement_positions SET billed_quantity=0 WHERE project_id=?",(project_id,))
    rows=self.conn.execute("""SELECT ip.measurement_position_id,MAX(ip.cumulative_quantity) AS q
      FROM invoice_positions ip JOIN invoices i ON i.id=ip.invoice_id
      WHERE i.project_id=? AND i.status<>'Entwurf' AND ip.measurement_position_id IS NOT NULL
      GROUP BY ip.measurement_position_id""",(project_id,)).fetchall()
    for r in rows:
        self.conn.execute("UPDATE measurement_positions SET billed_quantity=? WHERE id=?",
                          (float(r["q"] or 0),r["measurement_position_id"]))
    self.conn.commit()

def _db_reset_project_invoices(self,project_id):
    ids=[r[0] for r in self.conn.execute(
        "SELECT id FROM invoices WHERE project_id=?",(project_id,)).fetchall()]
    stats={"invoices":len(ids),"payments":0,"reminders":0,"positions":0}
    try:
        with self.conn:
            if ids:
                marks=",".join("?" for _ in ids)
                stats["payments"]=self.conn.execute(
                    f"SELECT COUNT(*) FROM payments WHERE invoice_id IN ({marks})",ids).fetchone()[0]
                stats["reminders"]=self.conn.execute(
                    f"SELECT COUNT(*) FROM reminders WHERE invoice_id IN ({marks})",ids).fetchone()[0]
                stats["positions"]=self.conn.execute(
                    f"SELECT COUNT(*) FROM invoice_positions WHERE invoice_id IN ({marks})",ids).fetchone()[0]
                # Abhängige Datensätze ausdrücklich entfernen. Damit funktioniert
                # die Test-Nullstellung auch bei älteren Datenbanken, in denen die
                # Fremdschlüssel-Kaskade noch nicht aktiv gewesen sein sollte.
                self.conn.execute(f"DELETE FROM reminders WHERE invoice_id IN ({marks})",ids)
                self.conn.execute(f"DELETE FROM payments WHERE invoice_id IN ({marks})",ids)
                self.conn.execute(f"DELETE FROM invoice_position_exclusions WHERE invoice_id IN ({marks})",ids)
                self.conn.execute(f"DELETE FROM invoice_positions WHERE invoice_id IN ({marks})",ids)
                self.conn.execute(f"DELETE FROM invoices WHERE id IN ({marks})",ids)
            self.conn.execute("UPDATE measurement_positions SET billed_quantity=0 WHERE project_id=?",(project_id,))
            remaining=self.conn.execute(
                "SELECT COUNT(*) FROM invoices WHERE project_id=?",(project_id,)).fetchone()[0]
            if remaining:
                raise RuntimeError(f"{remaining} Rechnung(en) konnten nicht entfernt werden.")
        return True,stats,None
    except Exception as exc:
        self.conn.rollback()
        return False,stats,str(exc)

DB.recalc_invoice_totals=_db_recalc_invoice_totals
DB.update_invoice_draft=_db_update_invoice_draft
DB.available_positions_for_invoice=_db_available_positions_for_invoice
DB.add_invoice_position=_db_add_invoice_position
DB.remove_invoice_position=_db_remove_invoice_position

def _db_restore_invoice_position(self,iid,mpid):
    inv=self.invoice(iid)
    if not inv or inv["status"]!="Entwurf":
        return False,"Nur ein Rechnungsentwurf kann geändert werden."
    self.conn.execute("""DELETE FROM invoice_position_exclusions
      WHERE invoice_id=? AND measurement_position_id=?""",(iid,mpid))
    self.conn.commit()
    return self.sync_invoice_with_measurement(iid)

DB.restore_invoice_position=_db_restore_invoice_position
DB.rebuild_project_billed_quantities=_db_rebuild_project_billed_quantities
DB.reset_project_invoices=_db_reset_project_invoices

def _db_sync_invoice_with_measurement(self,iid):
    inv=self.invoice(iid)
    if not inv or inv["status"]!="Entwurf":
        return False,"Nur ein Rechnungsentwurf kann mit dem Aufmaß aktualisiert werden."

    rows=self.measurement_positions(inv["project_id"])
    current_rows=[r for r in rows if float(r["current_quantity"] or 0) > 0.0000001]
    keep_mpids=set()

    excluded={x["measurement_position_id"] for x in self.conn.execute(
        "SELECT measurement_position_id FROM invoice_position_exclusions WHERE invoice_id=?",(iid,)).fetchall()}

    for r in current_rows:
        mpid=r["measurement_position_id"]
        if mpid in excluded:
            continue
        keep_mpids.add(mpid)
        cumulative=float(r["current_quantity"] or 0)
        previous=float(r["billed_quantity"] or 0)
        new_qty=max(0.0,cumulative-previous)
        unit_price=float(r["unit_price"] or 0)
        due_line=new_qty*unit_price

        existing=self.conn.execute("""SELECT id FROM invoice_positions
          WHERE invoice_id=? AND measurement_position_id=?""",(iid,mpid)).fetchone()
        if existing:
            self.conn.execute("""UPDATE invoice_positions SET
              offer_position_id=?,position_no=?,short_text=?,unit=?,unit_price=?,
              cumulative_quantity=?,previously_billed_quantity=?,new_quantity=?,line_total=?
              WHERE id=?""",
              (r["offer_position_id"],r["position_no"],r["short_text"],r["unit"],unit_price,
               cumulative,previous,new_qty,due_line,existing["id"]))
        else:
            self.conn.execute("""INSERT INTO invoice_positions
              (invoice_id,measurement_position_id,offer_position_id,position_no,short_text,unit,unit_price,
               cumulative_quantity,previously_billed_quantity,new_quantity,line_total)
              VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
              (iid,mpid,r["offer_position_id"],r["position_no"],r["short_text"],r["unit"],
               unit_price,cumulative,previous,new_qty,due_line))

    # Positionen, die im aktuellen Aufmaß nicht mehr existieren bzw. Menge 0 haben,
    # werden aus dem ENTWURF entfernt. Festgeschriebene Rechnungen bleiben unverändert.
    existing_rows=self.conn.execute("""SELECT id,measurement_position_id FROM invoice_positions
      WHERE invoice_id=?""",(iid,)).fetchall()
    for x in existing_rows:
        if x["measurement_position_id"] is not None and x["measurement_position_id"] not in keep_mpids:
            self.conn.execute("DELETE FROM invoice_positions WHERE id=?",(x["id"],))

    self.conn.commit()
    self.recalc_invoice_totals(iid)
    return True,None

def _db_invoice_cumulative_net(self,iid):
    row=self.conn.execute("""SELECT COALESCE(SUM(cumulative_quantity*unit_price),0) AS n
      FROM invoice_positions WHERE invoice_id=?""",(iid,)).fetchone()
    return float(row["n"] or 0)

DB.sync_invoice_with_measurement=_db_sync_invoice_with_measurement
DB.invoice_cumulative_net=_db_invoice_cumulative_net

def _db_payment_overview(self,search=""):
    s=f"%{search}%"
    return self.conn.execute("""SELECT i.id,i.number,i.invoice_type,i.project_id,i.created_at,i.due_date,
      i.gross_total,i.payable_total,i.status,p.number AS project_number,p.name AS project_name,c.company,
      COALESCE((SELECT SUM(pa.paid_amount) FROM payments pa WHERE pa.invoice_id=i.id),0) AS paid_total,
      COALESCE((SELECT SUM(pa.discount_amount) FROM payments pa WHERE pa.invoice_id=i.id),0) AS discount_total,
      COALESCE((SELECT SUM(pa.adjustment_amount) FROM payments pa WHERE pa.invoice_id=i.id),0) AS adjustment_total
      FROM invoices i
      JOIN projects p ON p.id=i.project_id
      JOIN customers c ON c.id=p.customer_id
      WHERE i.status<>'Entwurf'
        AND (i.number LIKE ? OR p.number LIKE ? OR p.name LIKE ? OR c.company LIKE ? OR i.status LIKE ?)
      ORDER BY i.id DESC""",(s,s,s,s,s)).fetchall()

def _db_payment_detail(self,iid):
    return self.invoice(iid)

def _db_delete_payment(self,payment_id):
    row=self.conn.execute("SELECT invoice_id FROM payments WHERE id=?",(payment_id,)).fetchone()
    if not row:return False,"Zahlung wurde nicht gefunden."
    iid=row["invoice_id"]
    self.conn.execute("DELETE FROM payments WHERE id=?",(payment_id,))
    self.conn.commit()
    # Status aus verbleibenden Buchungen neu bestimmen
    inv=self.invoice(iid)
    paid,discount,adjustment=self.payment_totals(iid)
    basis=float(inv["payable_total"] if inv["payable_total"] is not None else inv["gross_total"] or 0)
    open_amount=max(0.0,basis-paid-discount-adjustment)
    if open_amount<=0.005:
        status="Bezahlt" if discount<=0.005 and adjustment<=0.005 else "Ausgeglichen"
    elif paid+discount+adjustment>0.005:
        status="Teilbezahlt"
    else:
        status="Offen"
    self.conn.execute("UPDATE invoices SET status=? WHERE id=?",(status,iid))
    self.conn.commit()
    return True,None

DB.payment_overview=_db_payment_overview
DB.payment_detail=_db_payment_detail
DB.delete_payment=_db_delete_payment

def _parse_iso_date(value):
    try:
        return datetime.strptime(value,"%Y-%m-%d").date()
    except Exception:
        return None

def _db_days_overdue(self,iid):
    inv=self.invoice(iid)
    if not inv:return 0
    due=_parse_iso_date(inv["due_date"] or "")
    if not due:return 0
    open_amount=self.invoice_open_amount(iid)
    if open_amount<=0.005:return 0
    return max(0,(date.today()-due).days)

def _db_overdue_invoices(self):
    rows=self.payment_overview("")
    result=[]
    for x in rows:
        iid=x["id"]
        basis=float(x["payable_total"] if x["payable_total"] is not None else x["gross_total"] or 0)
        open_amount=max(0.0,basis-float(x["paid_total"] or 0)
                        -float(x["discount_total"] or 0)-float(x["adjustment_total"] or 0))
        days=self.days_overdue(iid)
        if open_amount>0.005 and days>0:
            result.append((x,open_amount,days))
    return result

def _db_reminders(self,iid):
    return self.conn.execute("""SELECT * FROM reminders WHERE invoice_id=?
      ORDER BY reminder_level,id""",(iid,)).fetchall()

def _db_next_reminder_level(self,iid):
    row=self.conn.execute("""SELECT COALESCE(MAX(reminder_level),0) AS m
      FROM reminders WHERE invoice_id=?""",(iid,)).fetchone()
    return int(row["m"] or 0)+1

def _db_add_reminder(self,iid,level,reminder_date,new_due_date,amount_due,note):
    inv=self.invoice(iid)
    if not inv:return False,"Rechnung wurde nicht gefunden."
    open_amount=self.invoice_open_amount(iid)
    if open_amount<=0.005:return False,"Diese Rechnung hat keinen mahnbaren offenen Betrag."
    level=max(0,min(3,int(level)))
    days=self.days_overdue(iid)
    if level>0 and days<=0:return False,"Eine Mahnung ist erst nach Fälligkeit möglich. Bitte Zahlungserinnerung wählen."
    self.conn.execute("""INSERT INTO reminders
      (invoice_id,reminder_level,reminder_date,new_due_date,amount_due,status,note,created_at)
      VALUES(?,?,?,?,?,?,?,?)""",
      (iid,level,reminder_date,new_due_date,amount_due,"Offen",note,
       datetime.now().isoformat(timespec="seconds")))
    self.conn.commit()
    return True,None

def _db_last_reminder_label(self,iid):
    row=self.conn.execute("""SELECT reminder_level,reminder_date FROM reminders
      WHERE invoice_id=? ORDER BY id DESC LIMIT 1""",(iid,)).fetchone()
    if not row:return ""
    label="Zahlungserinnerung" if int(row["reminder_level"] or 0)==0 else f'{row["reminder_level"]}. Mahnung'
    return f'{label} · {row["reminder_date"]}'

DB.days_overdue=_db_days_overdue
DB.overdue_invoices=_db_overdue_invoices
DB.reminders=_db_reminders
DB.next_reminder_level=_db_next_reminder_level
DB.add_reminder=_db_add_reminder
DB.last_reminder_label=_db_last_reminder_label

def _reminder_label(level):
    return "Zahlungserinnerung" if int(level or 0)==0 else f"{int(level)}. Mahnung"

def _db_reminders_due(self):
    """Überfällige Rechnungen, bei denen jetzt eine (weitere) Mahnung fällig ist.

    Liefert (fällig, wartend): wartend sind Rechnungen, deren Frist aus der
    letzten Mahnung noch läuft ({invoice_id: (Stufe, Frist)})."""
    due=[];waiting={};today=date.today()
    for x,open_amount,days in self.overdue_invoices():
        last=self.conn.execute("""SELECT * FROM reminders WHERE invoice_id=?
          ORDER BY id DESC LIMIT 1""",(x["id"],)).fetchone()
        previous="–"
        if last:
            label=_reminder_label(last["reminder_level"])
            deadline=_parse_iso_date(last["new_due_date"] or "")
            if deadline and today<=deadline:
                waiting[x["id"]]=(label,last["new_due_date"]);continue
            previous=f'{label} vom {de_date(last["reminder_date"])}'
        level=self.next_reminder_level(x["id"])
        due.append({"invoice_id":x["id"],"project_id":x["project_id"],"number":x["number"],
            "customer":x["company"],"project":f'{x["project_number"]} – {x["project_name"]}',
            "open_amount":open_amount,"days":days,"previous":previous,
            "next":_reminder_label(level) if level<=3 else "Stufen ausgeschöpft – weitere Schritte prüfen"})
    due.sort(key=lambda r:-r["days"])
    return due,waiting

DB.reminders_due=_db_reminders_due

def _db_dashboard_summary(self):
    invoice_rows=self.payment_overview("")
    invoice_total=0.0
    open_total=0.0
    overdue_count=0
    open_count=0
    for x in invoice_rows:
        gross=float(x["gross_total"] or 0)
        payable=float(x["payable_total"] if x["payable_total"] is not None else gross)
        paid=float(x["paid_total"] or 0)
        discount=float(x["discount_total"] or 0)
        adjustment=float(x["adjustment_total"] or 0)
        open_amount=max(0.0,payable-paid-discount-adjustment)
        invoice_total+=gross
        open_total+=open_amount
        if open_amount>0.005:
            open_count+=1
            if self.days_overdue(x["id"])>0:
                overdue_count+=1

    active_projects=self.conn.execute("""SELECT COUNT(*) FROM projects
      WHERE status NOT IN ('Abgeschlossen','Storniert','Archiviert')""").fetchone()[0]

    draft_count=self.conn.execute("""SELECT COUNT(*) FROM invoices
      WHERE status='Entwurf'""").fetchone()[0]

    unbilled_row=self.conn.execute("""SELECT COALESCE(SUM(
      CASE
        WHEN (COALESCE((SELECT SUM(ml.quantity) FROM measurement_lines ml
                       WHERE ml.measurement_position_id=mp.id),0)-mp.billed_quantity)>0
        THEN (COALESCE((SELECT SUM(ml.quantity) FROM measurement_lines ml
                       WHERE ml.measurement_position_id=mp.id),0)-mp.billed_quantity)*op.unit_price
        ELSE 0
      END),0) AS value
      FROM measurement_positions mp
      JOIN offer_positions op ON op.id=mp.offer_position_id""").fetchone()
    unbilled_value=float(unbilled_row["value"] or 0)

    return {
        "invoice_total":invoice_total,
        "open_total":open_total,
        "open_count":open_count,
        "overdue_count":overdue_count,
        "active_projects":int(active_projects or 0),
        "draft_count":int(draft_count or 0),
        "unbilled_value":unbilled_value,
    }

def _db_dashboard_actions(self):
    items=[]

    # Überfällige Forderungen: höchste Priorität.
    for x,open_amount,days in self.overdue_invoices():
        items.append({
            "priority":0,"priority_text":"🔴 Hoch","type":"Überfällige Rechnung",
            "invoice_id":x["id"],"project_id":x["project_id"],
            "project":f'{x["project_number"]} – {x["project_name"]}',
            "customer":x["company"],
            "hint":f'{x["number"]} · {days} Tage überfällig',
            "amount":open_amount,"target":7
        })

    # Offene Rechnungen, die noch nicht überfällig sind.
    for x in self.payment_overview(""):
        gross=float(x["gross_total"] or 0)
        payable=float(x["payable_total"] if x["payable_total"] is not None else gross)
        paid=float(x["paid_total"] or 0)
        discount=float(x["discount_total"] or 0)
        adjustment=float(x["adjustment_total"] or 0)
        open_amount=max(0.0,payable-paid-discount-adjustment)
        if open_amount>0.005 and self.days_overdue(x["id"])<=0:
            items.append({
                "priority":1,"priority_text":"🟡 Offen","type":"Offene Rechnung",
                "invoice_id":x["id"],"project_id":x["project_id"],
                "project":f'{x["project_number"]} – {x["project_name"]}',
                "customer":x["company"],
                "hint":f'{x["number"]} · fällig {x["due_date"] or "ohne Datum"}',
                "amount":open_amount,"target":7
            })

    # Rechnungsentwürfe.
    drafts=self.conn.execute("""SELECT i.id AS invoice_id,p.id AS project_id,i.number,p.number AS project_number,p.name AS project_name,c.company
      FROM invoices i JOIN projects p ON p.id=i.project_id
      JOIN customers c ON c.id=p.customer_id
      WHERE i.status='Entwurf' ORDER BY i.id DESC""").fetchall()
    for x in drafts:
        items.append({
            "priority":1,"priority_text":"🟡 Prüfen","type":"Rechnungsentwurf",
            "invoice_id":x["invoice_id"],"project_id":x["project_id"],
            "project":f'{x["project_number"]} – {x["project_name"]}',
            "customer":x["company"],"hint":f'{x["number"]} noch nicht festgeschrieben',
            "amount":0.0,"target":6
        })

    # Noch nicht abgerechnete Aufmaßleistung pro Projekt.
    rows=self.conn.execute("""SELECT p.id,p.number,p.name,c.company,
      COALESCE(SUM(
        CASE
          WHEN (COALESCE((SELECT SUM(ml.quantity) FROM measurement_lines ml
                         WHERE ml.measurement_position_id=mp.id),0)-mp.billed_quantity)>0
          THEN (COALESCE((SELECT SUM(ml.quantity) FROM measurement_lines ml
                         WHERE ml.measurement_position_id=mp.id),0)-mp.billed_quantity)*op.unit_price
          ELSE 0
        END),0) AS unbilled
      FROM projects p JOIN customers c ON c.id=p.customer_id
      JOIN measurement_positions mp ON mp.project_id=p.id
      JOIN offer_positions op ON op.id=mp.offer_position_id
      GROUP BY p.id,p.number,p.name,c.company
      HAVING unbilled>0.005
      ORDER BY unbilled DESC""").fetchall()
    for x in rows:
        items.append({
            "priority":2,"priority_text":"🔵 Aufmaß","type":"Noch nicht abgerechnet",
            "invoice_id":None,"project_id":x["id"],
            "project":f'{x["number"]} – {x["name"]}',"customer":x["company"],
            "hint":"Aufmaß enthält noch abrechenbare Leistung",
            "amount":float(x["unbilled"] or 0),"target":5
        })

    items.sort(key=lambda x:(x["priority"],-x["amount"],x["project"]))
    return items

def _db_dashboard_projects(self):
    return self.conn.execute("""SELECT p.id,p.number,p.name,p.status,c.company,
      COALESCE(SUM(
        COALESCE((SELECT SUM(ml.quantity) FROM measurement_lines ml
                  WHERE ml.measurement_position_id=mp.id),0)*op.unit_price
      ),0) AS measured_value,
      COALESCE(SUM(
        CASE
          WHEN (COALESCE((SELECT SUM(ml.quantity) FROM measurement_lines ml
                         WHERE ml.measurement_position_id=mp.id),0)-mp.billed_quantity)>0
          THEN (COALESCE((SELECT SUM(ml.quantity) FROM measurement_lines ml
                         WHERE ml.measurement_position_id=mp.id),0)-mp.billed_quantity)*op.unit_price
          ELSE 0
        END
      ),0) AS unbilled_value
      FROM projects p JOIN customers c ON c.id=p.customer_id
      LEFT JOIN measurement_positions mp ON mp.project_id=p.id
      LEFT JOIN offer_positions op ON op.id=mp.offer_position_id
      WHERE p.status NOT IN ('Abgeschlossen','Storniert','Archiviert')
      GROUP BY p.id,p.number,p.name,p.status,c.company
      ORDER BY p.id DESC""").fetchall()

DB.dashboard_summary=_db_dashboard_summary
DB.dashboard_actions=_db_dashboard_actions
DB.dashboard_projects=_db_dashboard_projects

def _db_project_cumulative_net(self,project_id):
    row=self.conn.execute("""SELECT COALESCE(SUM(
      (SELECT COALESCE(SUM(ml.quantity),0) FROM measurement_lines ml
       WHERE ml.measurement_position_id=mp.id) * op.unit_price
      ),0) AS n
      FROM measurement_positions mp
      JOIN offer_positions op ON op.id=mp.offer_position_id
      WHERE mp.project_id=?""",(project_id,)).fetchone()
    return float(row["n"] or 0)

def _db_project_billed_net_before_invoice(self,project_id,iid):
    row=self.conn.execute("""SELECT COALESCE(SUM(ip.line_total),0) AS n
      FROM invoice_positions ip JOIN invoices i ON i.id=ip.invoice_id
      WHERE i.project_id=? AND i.id<? AND i.status<>'Entwurf'""",(project_id,iid)).fetchone()
    return float(row["n"] or 0)

def _db_previous_final_invoices(self,project_id,iid):
    return self.conn.execute("""SELECT id,number,invoice_type,installment_no,created_at,
      net_total,gross_total,payable_total,status,
      COALESCE((SELECT SUM(paid_amount) FROM payments WHERE invoice_id=invoices.id),0) AS paid_total,
      COALESCE((SELECT SUM(discount_amount) FROM payments WHERE invoice_id=invoices.id),0) AS discount_total,
      COALESCE((SELECT SUM(adjustment_amount) FROM payments WHERE invoice_id=invoices.id),0) AS adjustment_total
      FROM invoices WHERE project_id=? AND id<>? AND status<>'Entwurf'
        AND (datetime(created_at)<datetime((SELECT created_at FROM invoices WHERE id=?)) OR
             (datetime(created_at)=datetime((SELECT created_at FROM invoices WHERE id=?)) AND id<?))
      ORDER BY datetime(created_at),id""",(project_id,iid,iid,iid,iid)).fetchall()

def _db_next_installment_no(self,project_id):
    row=self.conn.execute("""SELECT COALESCE(MAX(installment_no),0)+1 FROM invoices
      WHERE project_id=? AND invoice_type='Teilrechnung'""",(project_id,)).fetchone()
    return max(1,int(row[0] or 1))

DB.project_cumulative_net=_db_project_cumulative_net
DB.project_billed_net_before_invoice=_db_project_billed_net_before_invoice
DB.previous_final_invoices=_db_previous_final_invoices
DB.next_installment_no=_db_next_installment_no

class MeasurementLineDialog(QDialog):
    def __init__(self,parent=None,row=None):
        super().__init__(parent);self.setMinimumWidth(560)
        self.setWindowTitle("Aufmaßzeile bearbeiten" if row else "Neue Aufmaßzeile")
        f=QFormLayout(self);self.sheet=QLineEdit();self.room=QLineEdit();self.desc=QLineEdit();self.formula=QLineEdit()
        self.sheet.setPlaceholderText("z. B. 2.OG oder Blatt 3")
        self.room.setPlaceholderText("z. B. Raum 2.15 oder Treppenhaus")
        self.desc.setPlaceholderText("optionale Erläuterung zur Aufmaßzeile")
        self.formula.setPlaceholderText("z. B. 111*10*0,5")
        self.qty=QDoubleSpinBox();self.qty.setDecimals(3);self.qty.setMaximum(999999999)
        self.result=QLabel("Formelergebnis: —")
        f.addRow("Blatt",self.sheet);f.addRow("Raum / Ort",self.room);f.addRow("Beschreibung",self.desc)
        f.addRow("Aufmaß / Formel *",self.formula);f.addRow("",self.result);f.addRow("Ergebnis",self.qty)
        self.formula.textChanged.connect(self.calc)
        if row:
            self.sheet.setText(row["sheet"] or "");self.room.setText(row["room"] or "")
            self.desc.setText(row["description"] or "");self.formula.setText(row["formula"] or "")
            self.qty.setValue(row["quantity"] or 0)
        bb=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        bb.accepted.connect(self.validate);bb.rejected.connect(self.reject);f.addRow(bb)
    def calc(self):
        try:
            q=eval_formula(self.formula.text());self.qty.setValue(q);self.result.setText("Formelergebnis: "+de_num(q,3))
        except:
            self.result.setText("Formelergebnis: Formel prüfen")
    def validate(self):
        try:q=eval_formula(self.formula.text())
        except Exception as e:QMessageBox.warning(self,"Formel",str(e));return
        self.qty.setValue(q);self.accept()
    def data(self):
        return (self.desc.text().strip(),self.formula.text().strip(),self.qty.value(),
                self.sheet.text().strip(),self.room.text().strip())

class ImportPositionDialog(QDialog):
    def __init__(self,db,project_id,parent=None):
        super().__init__(parent);self.db=db;self.project_id=project_id;self.setMinimumSize(760,500)
        self.setWindowTitle("Position aus Angebot übernehmen")
        l=QVBoxLayout(self);f=QHBoxLayout();f.addWidget(QLabel("Angebot:"));self.offer=QComboBox()
        for o in db.project_offers(project_id):self.offer.addItem(f'{o["number"]} – {o["title"] or "Angebot"}',o["id"])
        self.offer.currentIndexChanged.connect(self.refresh);f.addWidget(self.offer);f.addStretch();l.addLayout(f)
        self.table=QTableWidget(0,5);self.table.setHorizontalHeaderLabels(["Pos.","Kurztext","Formel","Menge","Einheit"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows);self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers);l.addWidget(self.table)
        hint=QLabel(
            "Angebot auswählen und die gewünschten Positionen mit Strg/Shift markieren. "
            "Neu erzeugte Teil-/Nachtragsangebote erscheinen hier automatisch. "
            "Bereits ins Aufmaß übernommene Positionen werden nicht erneut angeboten."
        )
        hint.setWordWrap(True);l.addWidget(hint)
        bb=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);bb.accepted.connect(self.accept);bb.rejected.connect(self.reject);l.addWidget(bb)
        self.refresh()
    def refresh(self):
        oid=self.offer.currentData()
        rows=self.db.available_offer_positions(self.project_id,oid) if oid else []
        self.table.setRowCount(len(rows))
        for r,p in enumerate(rows):
            vals=[p["position_no"],p["short_text"],p["formula"] or "",de_num(p["quantity"],3),p["unit"]]
            for c,v in enumerate(vals):
                it=QTableWidgetItem(v);it.setData(Qt.UserRole,p["id"]) if c==0 else None;self.table.setItem(r,c,it)
    def selected_ids(self):
        return sorted({self.table.item(i.row(),0).data(Qt.UserRole) for i in self.table.selectionModel().selectedRows()})


class OfferSubsetDialog(QDialog):
    def __init__(self,source_offer,count,parent=None):
        super().__init__(parent)
        self.setWindowTitle("Neues Angebot aus Auswahl")
        self.setMinimumWidth(620)
        f=QFormLayout(self)
        self.title=QLineEdit("Nachtrag / Teilangebot")
        self.notes=QTextEdit()
        self.notes.setPlainText(
            f"Aus {count} ausgewählten Position(en) von Angebot {source_offer['number']} erstellt."
        )
        info=QLabel(
            f"<b>{count} Position(en)</b> werden kopiert.<br>"
            "Das ursprüngliche Angebot bleibt vollständig erhalten. "
            "Das neue Angebot gehört automatisch zum gleichen Projekt."
        )
        info.setWordWrap(True)
        f.addRow("",info)
        f.addRow("Bezeichnung *",self.title)
        f.addRow("Notizen",self.notes)
        bb=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText("Neues Angebot erstellen")
        bb.accepted.connect(self.validate);bb.rejected.connect(self.reject);f.addRow(bb)

    def validate(self):
        if not self.title.text().strip():
            QMessageBox.warning(self,"Neues Angebot","Bitte eine Bezeichnung eintragen.");return
        self.accept()

    def data(self):
        return self.title.text().strip(),self.notes.toPlainText().strip()

class PositionCopyDialog(QDialog):
    def __init__(self,db,project_id,parent=None):
        super().__init__(parent);self.db=db;self.project_id=project_id
        self.setWindowTitle("Position kopieren")
        self.setMinimumWidth(620)
        f=QFormLayout(self)

        self.target=QComboBox()
        self.target.addItem("Neues Angebot für dieses Projekt",None)
        for o in db.project_offers(project_id):
            self.target.addItem(f'{o["number"]} – {o["title"] or "Angebot"}',o["id"])
        self.target.currentIndexChanged.connect(self.target_changed)

        self.title=QLineEdit("Nachtrag / Zusatzangebot")
        self.title.setPlaceholderText("Bezeichnung des neuen Angebots")
        self.info=QLabel(
            "Die Position wird kopiert. Das Original bleibt vollständig erhalten. "
            "Die Kopie kann anschließend unabhängig bearbeitet werden."
        )
        self.info.setWordWrap(True)

        f.addRow("Ziel",self.target)
        f.addRow("Neues Angebot",self.title)
        f.addRow("",self.info)

        bb=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText("Position kopieren")
        bb.accepted.connect(self.validate);bb.rejected.connect(self.reject);f.addRow(bb)
        self.target_changed()

    def target_changed(self,*_):
        self.title.setEnabled(self.target.currentData() is None)

    def validate(self):
        if self.target.currentData() is None and not self.title.text().strip():
            QMessageBox.warning(self,"Position kopieren","Bitte eine Bezeichnung für das neue Angebot eintragen.");return
        self.accept()

    def data(self):
        return self.target.currentData(),self.title.text().strip()

class MeasurementHistoryDialog(QDialog):
    def __init__(self,db,mpid,parent=None):
        super().__init__(parent);self.setWindowTitle("Aufmaß-Historie");self.setMinimumSize(760,500)
        l=QVBoxLayout(self);p=db._measurement_position(mpid)
        title=QLabel(f'{p["offer_number"]} · Pos. {p["position_no"]} – {p["short_text"]}')
        title.setObjectName("subTitle");l.addWidget(title)
        table=QTableWidget(0,5)
        table.setHorizontalHeaderLabels(["Zeitpunkt","Stand kumuliert","Vorheriger Stand","Zuwachs","Hinweis"])
        table.setEditTriggers(QAbstractItemView.NoEditTriggers);l.addWidget(table)
        rows=list(reversed(db.snapshots(mpid)))
        table.setRowCount(len(rows));prev=0.0
        for r,s in enumerate(rows):
            total=float(s["total_quantity"] or 0);delta=total-prev
            vals=[s["created_at"].replace("T"," "),de_num(total,3),de_num(prev,3),de_num(delta,3),s["note"] or ""]
            for c,v in enumerate(vals):table.setItem(r,c,QTableWidgetItem(v))
            prev=total
        bb=QDialogButtonBox(QDialogButtonBox.Close);bb.rejected.connect(self.reject);bb.accepted.connect(self.accept);l.addWidget(bb)

class MeasurementPreviewDialog(QDialog):
    def __init__(self,db,project_id,parent=None):
        super().__init__(parent);self.db=db;self.project_id=project_id
        self.setWindowTitle("Aufmaß anzeigen")
        self.setMinimumSize(1180,720)
        self.header=self.db.conn.execute("""SELECT p.*,c.number AS customer_number,
          c.company,c.contact,c.street AS customer_street,c.zip AS customer_zip,c.city AS customer_city,
          c.email AS customer_email
          FROM projects p JOIN customers c ON c.id=p.customer_id WHERE p.id=?""",
          (project_id,)).fetchone()
        l=QVBoxLayout(self)
        title=QLabel("Aufmaßnachweis");title.setObjectName("pageTitle");l.addWidget(title)
        meta=QLabel(
            f'<b>Kunde:</b> {self.header["company"]} &nbsp;&nbsp; '
            f'<b>Projekt:</b> {self.header["number"]} – {one_line(self.header["name"])}<br>'
            f'<b>Baustelle:</b> {one_line(self.header["site"] or "—")} &nbsp;&nbsp; '
            f'<b>Stand:</b> {date.today().strftime("%d.%m.%Y")}'
        );meta.setWordWrap(True);l.addWidget(meta)

        self.rows=self._report_rows()
        self.table=QTableWidget(0,7)
        self.table.setHorizontalHeaderLabels([
            "Pos.","Leistung","Blatt","Raum","Beschreibung","Aufmaß","Ergebnis"
        ])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        widths=[85,300,105,145,210,175,115]
        for c,w in enumerate(widths):self.table.setColumnWidth(c,w)
        self._fill_table();l.addWidget(self.table)

        buttons=QHBoxLayout()
        preview=icon_button("preview","Aufmaß als PDF-Vorschau öffnen",self.open_pdf_preview)
        save=icon_button("pdf","Aufmaß als PDF speichern",self.save_pdf)
        email=icon_button("email","Aufmaß per E-Mail senden",self.send_email)
        close=icon_button("cancel","Aufmaßansicht schließen",self.accept)
        buttons.addStretch();buttons.addWidget(preview);buttons.addWidget(save);buttons.addWidget(email);buttons.addWidget(close)
        l.addLayout(buttons)

    def _report_rows(self):
        positions=self.db.measurement_positions(self.project_id)
        result=[];last_offer=None;last_title=None;last_sub=None
        for p in positions:
            offer=p["offer_number"] or ""
            tno=(p["title_no"] or "").strip();tt=(p["title_text"] or "").strip()
            sno=(p["subtitle_no"] or "").strip();st=(p["subtitle_text"] or "").strip()
            if offer!=last_offer:
                last_offer=offer;last_title=None;last_sub=None
            if tno and (offer,tno,tt)!=last_title:
                children=[q for q in positions if (q["offer_number"] or "")==offer
                          and (q["title_no"] or "").strip()==tno]
                subtotal=sum(float(q["current_quantity"] or 0)*float(q["unit_price"] or 0)
                             for q in children)
                result.append(("title",offer,tno,tt,subtotal));last_title=(offer,tno,tt);last_sub=None
            if sno and (offer,sno,st)!=last_sub:
                result.append(("subtitle",offer,sno,st));last_sub=(offer,sno,st)
            result.append(("position",p))
            lines=self.db.measurement_lines(p["measurement_position_id"])
            for line in lines:
                room=(line["room"] or "").strip()
                if not room:room=(line["description"] or "").strip()
                if room=="Aus Angebotsformel übernommen":
                    room=(p["measurement_location"] or "").strip()
                result.append(("room",p,line,room))
            result.append(("position_total",p))
        return result

    def _fill_table(self):
        self.table.setRowCount(len(self.rows))
        for r,row in enumerate(self.rows):
            if row[0] in ("title","subtitle"):
                if row[0]=="title":
                    _,offer,num,text,subtotal=row
                    vals=[f"{offer} · TITEL {num}",text]+[""]*5
                else:
                    _,offer,num,text=row
                    vals=[f"Untertitel {num}",text]+[""]*5
                for c,v in enumerate(vals):
                    it=QTableWidgetItem(str(v or ""));font=it.font();font.setBold(True);it.setFont(font)
                    it.setFlags(Qt.ItemIsEnabled);self.table.setItem(r,c,it)
                continue
            if row[0]=="position":
                p=row[1]
                vals=[p["position_no"],p["short_text"]]+[""]*5
                for c,v in enumerate(vals):
                    it=QTableWidgetItem(str(v or ""))
                    it.setFlags(Qt.ItemIsEnabled);self.table.setItem(r,c,it)
                continue
            if row[0]=="room":
                p,line,room=row[1],row[2],row[3]
                description="" if (line["description"] or "")=="Aus Angebotsformel übernommen" else line["description"] or ""
                vals=["","",line["sheet"] or "",room,description,
                      line["formula"] or "",f'{de_num(line["quantity"],3)} {p["unit"]}']
                for c,v in enumerate(vals):self.table.setItem(r,c,QTableWidgetItem(str(v or "")))
                continue
            p=row[1];current=float(p["current_quantity"] or 0)
            vals=["","","","",f'Summe Pos. {p["position_no"]}',"",f'{de_num(current,3)} {p["unit"]}']
            for c,v in enumerate(vals):
                it=QTableWidgetItem(str(v or ""));font=it.font();font.setBold(True);it.setFont(font)
                it.setFlags(Qt.ItemIsEnabled);self.table.setItem(r,c,it)

    def write_pdf(self,path):
        writer=QPdfWriter(str(path));writer.setPageSize(QPageSize(QPageSize.A4))
        writer.setResolution(96)  # Hochformat (wie Angebot und Rechnung)
        writer.setTitle(f'Aufmaß {self.header["number"]}');writer.setCreator(f"Aufmaßwerk {APP_VERSION}")
        painter=QPainter(writer)
        if not painter.isActive():return False,"Die PDF-Datei konnte nicht erstellt werden."
        page=writer.pageLayout().paintRectPixels(writer.resolution())
        left=42;right=42;top=30;bottom=38;width=page.width()-left-right;y=top;page_no=1
        letterhead=Letterhead("measurement",writer);letterhead.draw(painter,True);y=letterhead.content_top(y)
        company=self.db.company_settings()
        def cval(key):return (company[key] if company and key in company.keys() else "") or ""
        def font(size=8,bold=False):
            f=QFont("DejaVu Sans",size);f.setBold(bold);return f
        def txt(x,y0,w,h,text,size=8,bold=False,align=Qt.AlignLeft|Qt.AlignVCenter):
            painter.setFont(font(size,bold));painter.drawText(QRectF(x,y0,w,h),align|Qt.TextWordWrap,str(text or ""))
        def text_height(text,w,size=8,bold=False,min_h=0,pad=6):
            painter.setFont(font(size,bold))
            rect=painter.boundingRect(QRectF(0,0,max(1,w),2000),Qt.AlignLeft|Qt.AlignTop|Qt.TextWordWrap,str(text or ""))
            return max(min_h,int(rect.height())+pad)
        def footer():
            if letterhead.active:
                txt(left,letterhead.page_number_y(),width*.8,14,f'Aufmaßnachweis · {self.header["number"]} · Stand {date.today().strftime("%d.%m.%Y")}',6)
                txt(left+width*.82,letterhead.page_number_y(),width*.18,14,f"Seite {page_no}",7,False,Qt.AlignRight|Qt.AlignVCenter);return
            txt(left,page.height()-28,width*.8,13,
                f'Aufmaßnachweis · {self.header["number"]} · Stand {date.today().strftime("%d.%m.%Y")}',6)
            txt(left+width*.82,page.height()-28,width*.18,13,f"Seite {page_no}",7,False,Qt.AlignRight|Qt.AlignVCenter)
        def header(repeat=False):
            nonlocal y
            brand_h=40 if not repeat else 27
            if not letterhead.active:draw_pdf_brand(painter,cval("logo_path"),cval("company_name"),left,y,width*.35,brand_h,15 if not repeat else 10,width*.58)
            txt(left+width*.62,y,width*.38,brand_h,"Aufmaßnachweis",17 if not repeat else 11,True,Qt.AlignRight|Qt.AlignVCenter)
            y+=brand_h+3
            contact=" · ".join(x for x in [cval("street"),(cval("zip")+" "+cval("city")).strip(),cval("phone"),cval("email")] if x)
            if contact and not repeat and not letterhead.active:
                contact_h=text_height(contact,width,7,False,13,3);txt(left,y,width,contact_h,contact,7);y+=contact_h
            if not repeat:
                y+=4
                meta_left=f'Kunde: {one_line(self.header["company"])}';meta_right=f'Stand / Datum: {date.today().strftime("%d.%m.%Y")}'
                mh=max(text_height(meta_left,width*.65,9,True,19),text_height(meta_right,width*.32,9,True,19))
                txt(left,y,width*.65,mh,meta_left,9,True,Qt.AlignLeft|Qt.AlignTop)
                txt(left+width*.68,y,width*.32,mh,meta_right,9,True,Qt.AlignRight|Qt.AlignTop);y+=mh
                project=f'Projekt-Nr.: {self.header["number"]}    Projektbezeichnung: {one_line(self.header["name"])}'
                ph=text_height(project,width,9,True,20);txt(left,y,width,ph,project,9,True,Qt.AlignLeft|Qt.AlignTop);y+=ph
                if self.header["site"]:
                    site=f'Baustelle: {one_line(self.header["site"])}';sh=text_height(site,width,8,False,18)
                    txt(left,y,width,sh,site,8,False,Qt.AlignLeft|Qt.AlignTop);y+=sh
            y+=5
        col=[0,.075,.31,.40,.51,.68,.88,1.0]
        labels=["Pos.","Leistung","Blatt","Raum","Beschreibung","Aufmaß","Ergebnis"]
        def table_header():
            nonlocal y
            painter.fillRect(QRectF(left,y,width,25),Qt.lightGray)
            for i,label in enumerate(labels):txt(left+width*col[i]+3,y,width*(col[i+1]-col[i])-6,25,label,7,True)
            y+=27
        def new_page():
            nonlocal y,page_no
            footer();writer.newPage();page_no+=1;y=top;letterhead.draw(painter,False);y=letterhead.content_top(y);header(True);table_header()
        header();table_header()
        for row_index,row in enumerate(self.rows):
            if row[0]=="title":
                _,offer,num,text,subtotal=row;value=f'{offer} · TITEL {num} - {text}'
                h=text_height(value,width-6,9,True,26,8)
                if y+h>letterhead.limit(page.height()-bottom-28):new_page()
                painter.fillRect(QRectF(left,y,width,h),Qt.lightGray)
                txt(left+3,y,width-6,h,value,9,True);y+=h+3
                continue
            if row[0]=="subtitle":
                _,offer,num,text=row;value=f'Untertitel {num} - {text}';h=text_height(value,width*.80,8,True,22,7)
                if y+h>letterhead.limit(page.height()-bottom-28):new_page()
                txt(left+8,y,width*.80,h,value,8,True);y+=h+2;continue
            if row[0]=="position":
                p=row[1];h=max(text_height(p["position_no"],width*.075-6,8,False,25),text_height(p["short_text"],width*.605-6,8,False,25,8))
                first_room_h=0
                if row_index+1<len(self.rows) and self.rows[row_index+1][0]=="room":
                    rr=self.rows[row_index+1];rp,rline,rroom=rr[1],rr[2],rr[3]
                    rdesc="" if (rline["description"] or "")=="Aus Angebotsformel übernommen" else rline["description"] or ""
                    room_vals=[rline["sheet"] or "",rroom or "",rdesc,rline["formula"] or "",f'{de_num(rline["quantity"],3)} {rp["unit"]}']
                    room_widths=[width*(col[3]-col[2])-6,width*(col[4]-col[3])-6,width*(col[5]-col[4])-6,width*(col[6]-col[5])-6,width*(col[7]-col[6])-6]
                    first_room_h=max([27]+[text_height(v,w,7,False,27,8) for v,w in zip(room_vals,room_widths)])
                if y+h+first_room_h>letterhead.limit(page.height()-bottom-28):new_page()
                painter.fillRect(QRectF(left,y,width,h),QColor(235,238,241))
                txt(left+3,y,width*.075-6,h,p["position_no"],8,False)
                txt(left+width*.075+3,y,width*.605-6,h,p["short_text"],8,False,Qt.AlignLeft|Qt.AlignVCenter)
                y+=h+2;continue
            if row[0]=="room":
                p,line,room=row[1],row[2],row[3]
                description="" if (line["description"] or "")=="Aus Angebotsformel übernommen" else line["description"] or ""
                vals=["","",line["sheet"] or "",room or "",description,line["formula"] or "",
                      f'{de_num(line["quantity"],3)} {p["unit"]}']
                h=max([27]+[text_height(value,width*(col[i+1]-col[i])-6,7,False,27,8) for i,value in enumerate(vals) if value])
                if y+h>letterhead.limit(page.height()-bottom-28):new_page()
                for i,value in enumerate(vals):
                    align=(Qt.AlignRight|Qt.AlignVCenter) if i==6 else (Qt.AlignLeft|Qt.AlignTop)
                    txt(left+width*col[i]+3,y+2,width*(col[i+1]-col[i])-6,h-4,value,7,False,align)
                y+=h;continue
            p=row[1];current=float(p["current_quantity"] or 0)
            h=27
            if y+h>letterhead.limit(page.height()-bottom-28):new_page()
            painter.fillRect(QRectF(left,y,width,h),QColor(242,242,242))
            vals=["","","","",f'Summe Pos. {p["position_no"]}',"",f'{de_num(current,3)} {p["unit"]}']
            for i,value in enumerate(vals):
                align=(Qt.AlignRight|Qt.AlignVCenter) if i==6 else (Qt.AlignLeft|Qt.AlignTop)
                txt(left+width*col[i]+3,y+2,width*(col[i+1]-col[i])-6,h-4,value,7,True,align)
            painter.drawLine(left,y+h,left+width,y+h);y+=h+3
        footer();painter.end();return True,None

    def open_pdf_preview(self):
        path=PREVIEW_DIR/f'Aufmass_{self.header["number"]}_Vorschau.pdf'
        ok,err=self.write_pdf(path)
        if not ok:QMessageBox.warning(self,"Aufmaßvorschau",err);return
        open_desktop_file(path,self,"Aufmaßvorschau")

    def send_email(self):
        path=PREVIEW_DIR/f'Aufmass_{self.header["number"]}_Vorschau.pdf'
        ok,err=self.write_pdf(path)
        if not ok:
            QMessageBox.warning(self,"Aufmaß per E-Mail",err);return False
        result=compose_email_with_pdf(self,path,self.header["customer_email"],
            f'Aufmaßnachweis Projekt {self.header["number"]}',
            "Guten Tag,\n\nanbei erhalten Sie den aktuellen Aufmaßnachweis als PDF.\n\nMit freundlichen Grüßen")
        file_generated_document(self.db,self.project_id,path,f'Aufmass_{self.header["number"]}_versendet_{date.today().isoformat()}.pdf',
            f'Aufmaß – per E-Mail versendet am {today_de()}')
        return result

    def save_pdf(self):
        path,_=QFileDialog.getSaveFileName(self,"Aufmaß als PDF speichern",
            str(MEASUREMENT_DOCUMENT_DIR/f'Aufmass_{self.header["number"]}.pdf'),"PDF-Dateien (*.pdf)")
        if not path:return
        if not path.lower().endswith(".pdf"):path += ".pdf"
        ok,err=self.write_pdf(path)
        if not ok:QMessageBox.warning(self,"Aufmaß PDF",err);return
        file_generated_document(self.db,self.project_id,path,f'Aufmass_{self.header["number"]}_{date.today().isoformat()}.pdf',
            f'Aufmaß – erstellt am {today_de()}')
        QMessageBox.information(self,"Aufmaß PDF",f"PDF wurde erstellt:\n{path}")
        open_desktop_file(path,self,"Aufmaß PDF")

class MeasurementsPage(QWidget):
    def __init__(self,db):
        super().__init__();self.db=db;self.project_id=None;self.mpid=None;self._loading_positions=False
        self.offer_filter=None;self.on_changed=None
        self._formula_editor_row=None;self._formula_editor_mpid=None;self._formula_editor_line_id=None
        self._formula_editor_room=None;self._formula_editor_input=None
        self._formula_editor_result=None;self._formula_editor_save=None
        o=QVBoxLayout(self);top=QHBoxLayout();t=QLabel("Kumulatives Aufmaß");t.setObjectName("pageTitle")
        self.header_title=t;self.header_project_label=QLabel("Projekt:")
        top.addWidget(t);top.addStretch();top.addWidget(self.header_project_label);self.project=QComboBox()
        for p in db.measurement_projects():
            self.project.addItem(
                f'{p["number"]} – {one_line(p["name"])} – {one_line(p["company"])}',p["id"]
            )
        self.project.setMinimumWidth(560)
        self.project.currentIndexChanged.connect(self.load_project);top.addWidget(self.project);o.addLayout(top)
        bar=QHBoxLayout()
        editpos=icon_button("edit","Aufmaßposition bearbeiten",self.edit_measurement_position)
        copypos=QPushButton("Position in Angebot kopieren");copypos.clicked.connect(self.copy_measurement_position)
        rem=QPushButton("🗑  Zeile löschen");rem.clicked.connect(self.remove_pos);self.remove_button=rem
        rem.setToolTip("Markierte Aufmaßzeile löschen (auch mit Entf oder Rechtsklick)")
        hist=QPushButton("Aufmaß-Historie");hist.clicked.connect(self.show_history)
        addroom=QPushButton("+ Aufmaßzeile hinzufügen");addroom.setToolTip("Weitere Aufmaßzeile hinzufügen");addroom.clicked.connect(self.add_line)
        show=icon_button("preview","Aufmaß anzeigen",self.show_measurement)
        email=icon_button("email","Aufmaß per E-Mail senden",self.send_measurement_email)
        invoice=QPushButton("Rechnung aus Aufmaß erstellen");invoice.clicked.connect(self.create_invoice_from_measurement)
        # Bearbeiten erledigt das Feld unter der Zeile, E-Mail der Button oben rechts.
        show.setText("Aufmaß als PDF");rem.setToolTip("Markierte Aufmaßzeile oder Position löschen");self.show_pdf_button=show
        hist.setText("Historie");hist.setObjectName("subtleButton")
        self.move_up_button=QPushButton("↑  Hoch");self.move_down_button=QPushButton("↓  Runter")
        self.move_up_button.setToolTip("Markierte Aufmaßposition oder Aufmaßzeile einen Platz nach oben schieben")
        self.move_down_button.setToolTip("Markierte Aufmaßposition oder Aufmaßzeile einen Platz nach unten schieben")
        self.move_up_button.clicked.connect(lambda:self.move_selected(-1));self.move_down_button.clicked.connect(lambda:self.move_selected(1))
        self.move_up_button.setEnabled(False);self.move_down_button.setEnabled(False)
        bar.addWidget(addroom);bar.addWidget(rem);bar.addWidget(self.move_up_button);bar.addWidget(self.move_down_button)
        bar.addWidget(show);bar.addWidget(invoice);bar.addStretch();bar.addWidget(hist);o.addLayout(bar)
        self.offer_toggle=QPushButton("Positionen aus Angebot übernehmen ▾")
        self.offer_toggle.setToolTip("Positionen aus dem Angebot einblenden, markieren und zum Aufmaß hinzufügen")
        self.offer_toggle.setMinimumHeight(36);self.offer_toggle.clicked.connect(self.toggle_offer_positions)
        o.addWidget(self.offer_toggle)
        self.offer_panel=QFrame();self.offer_panel.setObjectName("measurementOfferPanel")
        offer_layout=QVBoxLayout(self.offer_panel);offer_layout.setContentsMargins(8,8,8,8)
        offer_head=QHBoxLayout();offer_head.addWidget(QLabel("Angebot:"));self.available_offer=QComboBox()
        self.available_offer.currentIndexChanged.connect(self.refresh_available_positions)
        offer_head.addWidget(self.available_offer,1)
        take=QPushButton("+ Markierte Positionen zum Aufmaß hinzufügen");take.clicked.connect(self.import_selected_positions)
        take_all=QPushButton("Alle übernehmen");take_all.clicked.connect(self.import_all_positions)
        offer_head.addWidget(take);offer_head.addWidget(take_all);offer_layout.addLayout(offer_head)
        self.available_positions=QTableWidget(0,6)
        self.available_positions.setHorizontalHeaderLabels(["Auswahl","Pos.","Kurztext","Formel","Menge","Einheit"])
        self.available_positions.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.available_positions.setSelectionMode(QAbstractItemView.NoSelection)
        self.available_positions.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.available_positions.cellClicked.connect(self.toggle_available_position_check)
        self.available_positions.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.available_positions.setColumnWidth(0,72);self.available_positions.setColumnWidth(1,90)
        self.available_positions.setColumnWidth(2,420);self.available_positions.setColumnWidth(3,260)
        self.available_positions.setColumnWidth(4,100)
        self.available_positions.setFixedHeight(145)
        self.available_positions.horizontalHeader().setStretchLastSection(True)
        offer_layout.addWidget(self.available_positions)
        self.offer_panel.setMaximumHeight(215)
        self.offer_panel.setVisible(False);o.addWidget(self.offer_panel)
        self.positions=QTableWidget(0,13);self.positions.setHorizontalHeaderLabels(
            ["Angebot","Pos.","Kurztext","Raum / Ort","Formel / Aufmaß","Angebotsmenge","Aufmaß aktuell",
             "Zuwachs","Bereits abgerechnet","Noch offen","Einheit","EP","Wert aktuell"])
        self.positions.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.positions.setSelectionMode(QAbstractItemView.SingleSelection)
        self.positions.setEditTriggers(QAbstractItemView.DoubleClicked|QAbstractItemView.EditKeyPressed|QAbstractItemView.SelectedClicked)
        self.positions.itemSelectionChanged.connect(self.select_position)
        self.positions.itemSelectionChanged.connect(self._update_remove_button)
        self.positions.setContextMenuPolicy(Qt.CustomContextMenu);self.positions.customContextMenuRequested.connect(self._measure_menu)
        self.positions.installEventFilter(self)
        self.positions.itemChanged.connect(self.inline_position_changed)
        self.positions.setEditTriggers(QAbstractItemView.SelectedClicked|QAbstractItemView.DoubleClicked|QAbstractItemView.EditKeyPressed|QAbstractItemView.AnyKeyPressed)
        self.positions_tab_delegate=TabAwareDelegate(self._prepare_measure_tab,self.positions)
        self.positions.setItemDelegateForColumn(3,self.positions_tab_delegate);self.positions.setItemDelegateForColumn(4,self.positions_tab_delegate)
        # Der vollständige Positionsdialog wird bewusst nur über den Button
        # "Aufmaßposition bearbeiten" geöffnet. So kann ein schneller Doppel-
        # klick in der Tabelle niemals den Formeleditor überlagern.
        self.positions.installEventFilter(self)
        self.positions.setColumnWidth(0,90);self.positions.setColumnWidth(1,90)
        self.positions.setColumnWidth(2,280);self.positions.setColumnWidth(3,160)
        self.positions.setColumnWidth(4,230);self.positions.setColumnWidth(5,115)
        self.positions.setColumnWidth(6,115);self.positions.setColumnWidth(7,100)
        self.positions.setColumnWidth(8,125);self.positions.setColumnWidth(9,100)
        self.positions.setColumnWidth(10,75);self.positions.setColumnWidth(11,95)
        self.positions.setColumnWidth(12,120)
        o.addWidget(self.positions,1)
        self.details_toggle=QPushButton("Details zur ausgewählten Position anzeigen ▾")
        self.details_toggle.clicked.connect(self.toggle_position_details)
        o.addWidget(self.details_toggle)
        self.details_panel=QWidget();ll=QVBoxLayout(self.details_panel);ll.setContentsMargins(0,0,0,0)
        self.info=compact_hint("Bitte eine Aufmaßposition auswählen.");ll.addWidget(self.info)
        self.lines=QTableWidget(0,6);self.lines.setHorizontalHeaderLabels(
            ["Blatt","Raum / Ort","Beschreibung","Aufmaß / Formel","Ergebnis","Letzte Änderung"])
        self.lines.setSelectionBehavior(QAbstractItemView.SelectRows);self.lines.setEditTriggers(QAbstractItemView.NoEditTriggers);self.lines.doubleClicked.connect(self.edit_line)
        ll.addWidget(self.lines);lr=QHBoxLayout()
        add=icon_button("new","Weitere Aufmaßzeile hinzufügen",self.add_line);edit=icon_button("edit","Aufmaßzeile bearbeiten",self.edit_line)
        delete=icon_button("delete","Aufmaßzeile löschen",self.delete_line);lr.addWidget(add);lr.addWidget(edit);lr.addWidget(delete);lr.addStretch();ll.addLayout(lr)
        self.details_panel.setVisible(False);o.addWidget(self.details_panel)
        # Die Aufmaßzeilen stehen bereits in der Tabelle; der Detailbereich entfällt.
        self.details_toggle.setVisible(False)
        if self.project.count():self.load_project()

    def set_embedded(self):
        """Als Reiter im Modul Angebot & Aufmaß: Projekt kommt vom Angebot."""
        for widget in (self.header_title,self.header_project_label,self.project,self.offer_toggle,self.show_pdf_button):widget.setVisible(False)

    def show_offer(self,project_id,offer_id):
        """Aufmaß des Projekts zeigen, gefiltert auf die Positionen dieses Angebots."""
        self.offer_filter=offer_id
        index=self.project.findData(project_id)
        if index<0:
            project=self.db.project(project_id)
            if project:
                self.project.addItem(f'{project["number"]} – {one_line(project["name"])} – {one_line(project["company"])}',project_id)
                index=self.project.findData(project_id)
        self.project.blockSignals(True);self.project.setCurrentIndex(max(0,index));self.project.blockSignals(False)
        self.load_project()

    def import_all_positions(self):
        for row in range(self.available_positions.rowCount()):
            item=self.available_positions.item(row,0)
            if item:item.setCheckState(Qt.Checked)
        self.import_selected_positions()

    def toggle_position_details(self):
        visible=not self.details_panel.isVisible()
        self.details_panel.setVisible(visible)
        self.details_toggle.setText(
            "Details zur ausgewählten Position ausblenden ▴" if visible
            else "Details zur ausgewählten Position anzeigen ▾"
        )
        translate_widget_tree(self.details_toggle)

    def toggle_offer_positions(self):
        visible=not self.offer_panel.isVisible()
        self.set_offer_panel_visible(visible)

    def set_offer_panel_visible(self,visible):
        self.offer_panel.setVisible(visible)
        self.offer_toggle.setText(
            "Positionen aus Angebot ausblenden ▴" if visible
            else "Positionen aus Angebot übernehmen ▾"
        )
        if visible:self.refresh_available_offers()
        translate_widget_tree(self.offer_toggle)

    def refresh_available_offers(self):
        selected=self.available_offer.currentData()
        self.available_offer.blockSignals(True);self.available_offer.clear()
        for offer in self.db.project_offers(self.project_id) if self.project_id else []:
            if self.offer_filter and offer["id"]!=self.offer_filter:continue
            self.available_offer.addItem(f'{offer["number"]} – {offer["title"] or "Angebot"}',offer["id"])
        if selected is not None:
            index=self.available_offer.findData(selected)
            if index>=0:self.available_offer.setCurrentIndex(index)
        self.available_offer.blockSignals(False)
        self.refresh_available_positions()

    def refresh_available_positions(self):
        offer_id=self.available_offer.currentData()
        rows=self.db.available_offer_positions(self.project_id,offer_id) if self.project_id and offer_id else []
        self.available_positions.setRowCount(len(rows))
        for row,position in enumerate(rows):
            check=QTableWidgetItem("");check.setFlags(Qt.ItemIsEnabled|Qt.ItemIsUserCheckable)
            check.setCheckState(Qt.Unchecked);check.setData(Qt.UserRole,position["id"])
            self.available_positions.setItem(row,0,check)
            values=[position["position_no"],position["short_text"],position["formula"] or "",
                    de_num(position["quantity"],3),position["unit"]]
            for column,value in enumerate(values):
                item=QTableWidgetItem(str(value or ""))
                self.available_positions.setItem(row,column+1,item)

    def toggle_available_position_check(self,row,column):
        item=self.available_positions.item(row,0)
        if item is None:return
        # Ein Klick auf die ganze Zeile darf das kleine Kästchen bequem umschalten.
        if column!=0:item.setCheckState(Qt.Unchecked if item.checkState()==Qt.Checked else Qt.Checked)

    def import_selected_positions(self):
        ids=[self.available_positions.item(row,0).data(Qt.UserRole)
             for row in range(self.available_positions.rowCount())
             if self.available_positions.item(row,0).checkState()==Qt.Checked]
        if not ids:
            QMessageBox.information(self,"Übernahme","Bitte mindestens eine Position markieren.");return
        self.db.backup("vor_aufmass_uebernahme")
        for position_id in ids:self.db.add_measurement_position(self.project_id,position_id)
        self.set_offer_panel_visible(False)
        self.load_project()
    def refresh(self):
        """Liest Angebotssollwerte beim Öffnen des Aufmaßmoduls erneut ein."""
        selected_project=self.project.currentData()
        selected_mpid=self.selected_mpid()

        projects=self.db.measurement_projects()
        self.project.blockSignals(True)
        self.project.clear()
        selected_index=-1
        for index,p in enumerate(projects):
            self.project.addItem(
                f'{p["number"]} – {one_line(p["name"])} – {one_line(p["company"])}',p["id"]
            )
            if p["id"]==selected_project:selected_index=index
        if selected_index>=0:self.project.setCurrentIndex(selected_index)
        self.project.blockSignals(False)

        self.load_project()
        if selected_mpid is not None:
            for row in range(self.positions.rowCount()):
                item=self.positions.item(row,0)
                if item and item.data(Qt.UserRole)==selected_mpid and item.data(Qt.UserRole+1) is None:
                    self.positions.selectRow(row)
                    self.select_position()
                    break
    def load_project(self):
        self._clear_formula_editor_state()
        self._loading_positions=True
        # Keine unsichtbaren Zell-Zusammenfassungen eines früheren Editors
        # in den neu aufgebauten Tabelleninhalt übernehmen.
        self.positions.clearSpans()
        self.project_id=self.project.currentData()
        self.mpid=None
        self.lines.setRowCount(0)

        rows=self.db.measurement_positions(self.project_id) if self.project_id else []
        if self.offer_filter:
            offer=self.db.offer(self.offer_filter)
            rows=[p for p in rows if offer and p["offer_number"]==offer["number"]]
        display=[]
        last_offer=None
        last_title=None
        last_subtitle=None

        for p in rows:
            offer_no=p["offer_number"] or ""
            tno=(p["title_no"] or "").strip()
            ttext=(p["title_text"] or "").strip()
            sno=(p["subtitle_no"] or "").strip()
            stext=(p["subtitle_text"] or "").strip()

            if not tno and "." in (p["position_no"] or ""):
                tno=(p["position_no"] or "").split(".",1)[0].strip()
                if tno:
                    ttext=f"Titel {tno}"

            if offer_no!=last_offer:
                last_offer=offer_no
                last_title=None
                last_subtitle=None

            if tno and (tno,ttext)!=last_title:
                title_rows=[]
                for q in rows:
                    if (q["offer_number"] or "")!=offer_no:
                        continue
                    qtno=(q["title_no"] or "").strip()
                    if not qtno and "." in (q["position_no"] or ""):
                        qtno=(q["position_no"] or "").split(".",1)[0].strip()
                    if qtno==tno:
                        title_rows.append(q)
                current_value=sum(float(q["current_quantity"] or 0)*float(q["unit_price"] or 0)
                                  for q in title_rows)
                display.append(("title",offer_no,tno,ttext,current_value))
                last_title=(tno,ttext)
                last_subtitle=None

            if sno and (sno,stext)!=last_subtitle:
                display.append(("subtitle",offer_no,sno,stext))
                last_subtitle=(sno,stext)

            display.append(("position",p))
            for line in self.db.measurement_lines(p["measurement_position_id"]):
                room=(line["room"] or "").strip()
                description=(line["description"] or "").strip()
                if not room:
                    room=description
                if room=="Aus Angebotsformel übernommen":
                    room=(p["measurement_location"] or "").strip()
                if description=="Aus Angebotsformel übernommen":
                    description=""
                display.append(("room",p,line,room,description))
            display.append(("position_total",p))

        self.positions.setRowCount(len(display))

        for r,item in enumerate(display):
            kind=item[0]

            if kind=="title":
                _,offer_no,tno,ttext,current_value=item
                vals=[offer_no,f"TITEL {tno}",ttext or f"Titel {tno}"]+[""]*9+[money(current_value)]
                for c,v in enumerate(vals):
                    it=QTableWidgetItem(str(v or ""))
                    f=it.font();f.setBold(True);it.setFont(f)
                    it.setFlags(Qt.ItemIsEnabled)
                    if c==2:
                        it.setToolTip("Titel = Gliederung. Abgerechnet werden ausschließlich die Positionen darunter.")
                    if c==12:
                        it.setToolTip("Interne Orientierung: aktueller kumulierter Wert aller Positionen dieses Titels.")
                    self.positions.setItem(r,c,it)
                continue

            if kind=="subtitle":
                _,offer_no,sno,stext=item
                vals=[offer_no,f"Untertitel {sno}",stext or f"Untertitel {sno}"]+[""]*10
                for c,v in enumerate(vals):
                    it=QTableWidgetItem(str(v or ""))
                    f=it.font();f.setBold(True);it.setFont(f)
                    it.setFlags(Qt.ItemIsEnabled)
                    self.positions.setItem(r,c,it)
                continue

            p=item[1]
            current=float(p["current_quantity"] or 0)
            billed=float(p["billed_quantity"] or 0)
            hist=self.db.snapshots(p["measurement_position_id"])
            prev=float(hist[1]["total_quantity"] if len(hist)>1 else 0)
            increase=current-prev
            offer_quantity=float(p["offer_quantity"] or 0)
            unit_price=float(p["unit_price"] or 0)
            open_qty=offer_quantity-current
            if kind=="position":
                vals=[p["offer_number"],p["position_no"],p["short_text"],"","",
                      de_num(offer_quantity,3),de_num(current,3),de_num(increase,3),de_num(billed,3),
                      de_num(open_qty,3),p["unit"],money(unit_price),money(current*unit_price)]
            elif kind=="room":
                _,p,line,room,description=item
                details=[]
                if (line["sheet"] or "").strip():details.append((line["sheet"] or "").strip())
                if description:details.append(description)
                vals=["",""," · ".join(details),room,line["formula"] or "","",
                      de_num(line["quantity"],3),"","","",p["unit"],money(unit_price),
                      money(float(line["quantity"] or 0)*unit_price)]
            else:
                vals=["",f'Summe Pos. {p["position_no"]}',"","","",de_num(offer_quantity,3),
                      de_num(current,3),de_num(increase,3),de_num(billed,3),
                      de_num(open_qty,3),p["unit"],money(unit_price),money(current*unit_price)]
            for c,v in enumerate(vals):
                it=QTableWidgetItem(str(v or ""))
                if c==0:
                    it.setData(Qt.UserRole,p["measurement_position_id"])
                    if kind=="room":it.setData(Qt.UserRole+1,line["id"])
                if kind=="room" and c not in (3,4):
                    it.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable)
                elif kind=="room" and c in (3,4):
                    # Raum und Formel direkt in der Zelle bearbeiten.
                    it.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable|Qt.ItemIsEditable)
                elif kind=="position":
                    # In der Positionszeile erzeugt eine Eingabe die erste Aufmaßzeile.
                    it.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable|(Qt.ItemIsEditable if c in (3,4) else Qt.NoItemFlags))
                if kind=="position_total":
                    f=it.font();f.setBold(True);it.setFont(f)
                if kind=="position_total":
                    it.setFlags(Qt.ItemIsEnabled)
                if c==2 and kind=="position":
                    it.setToolTip(p["long_text"] or p["short_text"] or "")
                if c==3 and kind=="room":it.setToolTip("Raum / Ort dieser einzelnen Aufmaßzeile.")
                if c==4 and kind=="room":it.setToolTip("Formel / Mengenermittlung dieser einzelnen Aufmaßzeile.")
                if c==3 and kind=="position":it.setToolTip("Eingabe erzeugt automatisch die erste Aufmaßzeile.")
                if c==4 and kind=="position":it.setToolTip("Formel eingeben; die erste Aufmaßzeile wird automatisch angelegt.")
                self.positions.setItem(r,c,it)

        self.info.setText(
            "Titel und Untertitel dienen ausschließlich der Gliederung. "
            "Abgerechnet werden die Positionen. Formel und kumulativer Stand bleiben sichtbar."
        )
        self._loading_positions=False
        if self.offer_panel.isVisible():self.refresh_available_offers()
        if self.on_changed:self.on_changed()

    def eventFilter(self,obj,event):
        if obj is self.positions and event.type()==QEvent.KeyPress and event.key()==Qt.Key_Delete \
                and self.positions.state()!=QAbstractItemView.EditingState:
            self.remove_pos();return True
        if obj is self._formula_editor_input and event.type()==QEvent.KeyPress and event.key()==Qt.Key_Tab:
            self._last_saved_line=None;self.save_formula_editor()
            if self._last_saved_line:self._insert_line_below(*self._last_saved_line)
            return True
        if obj is self._formula_editor_room and event.type()==QEvent.KeyPress:
            if event.key() in (Qt.Key_Return,Qt.Key_Enter):
                if self._formula_editor_input:
                    self._formula_editor_input.setFocus();self._formula_editor_input.selectAll()
                return True
            if event.key()==Qt.Key_Escape:
                self.cancel_formula_editor();return True
        if obj is self._formula_editor_input and event.type()==QEvent.KeyPress:
            if event.key() in (Qt.Key_Return,Qt.Key_Enter):
                self.save_formula_editor();return True
            if event.key()==Qt.Key_Escape:
                self.cancel_formula_editor();return True
        if obj is self.positions and event.type()==QEvent.KeyPress and event.key()==Qt.Key_Tab:
            r=self.positions.currentRow();c=self.positions.currentColumn()
            key=self.positions.item(r,0) if r>=0 else None
            mpid=key.data(Qt.UserRole) if key else None
            line_id=key.data(Qt.UserRole+1) if key else None
            if c==self.positions.columnCount()-1 and mpid and line_id:
                self.db.backup("vor_aufmass_tabzeile")
                new_line_id=self.db.add_measurement_line(mpid,"","0",0,"","")
                self.db.place_measurement_line_after(new_line_id,line_id);self._pending_new_line=new_line_id
                self.reload_position(mpid,new_line_id)
                for row in range(self.positions.rowCount()):
                    it=self.positions.item(row,0)
                    if it and it.data(Qt.UserRole+1)==new_line_id:
                        self.positions.setCurrentCell(row,3)
                        self.open_formula_editor(row,3)
                        break
                return True
        return super().eventFilter(obj,event)

    def _clear_formula_editor_state(self):
        self._formula_editor_row=None;self._formula_editor_mpid=None;self._formula_editor_line_id=None
        self._formula_editor_room=None;self._formula_editor_input=None
        self._formula_editor_result=None;self._formula_editor_save=None

    def open_formula_editor(self,row,column):
        """Klappt direkt unter der gewählten Aufmaßzeile einen großen Formeleditor auf."""
        if self._loading_positions or column not in (3,4):return
        key=self.positions.item(row,0)
        mpid=key.data(Qt.UserRole) if key else None
        line_id=key.data(Qt.UserRole+1) if key else None
        if not mpid:return

        if self._formula_editor_row is not None:
            if self._formula_editor_row==row+1 and self._formula_editor_mpid==mpid and self._formula_editor_line_id==line_id:
                target=self._formula_editor_room if column==3 else self._formula_editor_input
                if target:target.setFocus();target.selectAll()
                return
            self.cancel_formula_editor()
            # Die Zeilennummer kann sich nach Entfernen des alten Editors verschoben haben.
            for candidate in range(self.positions.rowCount()):
                item=self.positions.item(candidate,0)
                if item and item.data(Qt.UserRole)==mpid and item.data(Qt.UserRole+1)==line_id:
                    row=candidate;break

        db_line=self.db.conn.execute("SELECT * FROM measurement_lines WHERE id=?",(line_id,)).fetchone() if line_id else None
        room=(db_line["room"] or "").strip() if db_line else ""
        formula=(db_line["formula"] or "").strip() if db_line else ""
        self._loading_positions=True
        editor_row=row+1
        self.positions.insertRow(editor_row)
        self.positions.setSpan(editor_row,0,1,self.positions.columnCount())
        self.positions.setRowHeight(editor_row,142)

        panel=QFrame();panel.setObjectName("formulaInlineEditor")
        layout=QGridLayout(panel);layout.setContentsMargins(12,8,12,8)
        layout.addWidget(QLabel("Raum / Ort:"),0,0)
        room_edit=QLineEdit(room);room_edit.setPlaceholderText("z. B. Raum 2.15 oder Treppenhaus")
        room_edit.setMinimumWidth(430);layout.addWidget(room_edit,0,1,1,4)
        layout.addWidget(QLabel("Aufmaß / Formel:"),1,0)
        edit=QLineEdit(formula);edit.setPlaceholderText("z. B. 5+3+7+2*1,25")
        edit.setMinimumWidth(430);layout.addWidget(edit,1,1,1,4)
        layout.addWidget(QLabel("Ergebnis:"),2,0)
        result=QLabel("—");result.setObjectName("formulaResult");layout.addWidget(result,2,1)
        save=icon_button("save","Aufmaßformel speichern");cancel=icon_button("cancel","Bearbeitung abbrechen")
        layout.addWidget(save,2,3);layout.addWidget(cancel,2,4);layout.setColumnStretch(2,1)
        self.positions.setCellWidget(editor_row,0,panel)
        self._formula_editor_row=editor_row;self._formula_editor_mpid=mpid;self._formula_editor_line_id=line_id
        self._formula_editor_room=room_edit;self._formula_editor_input=edit
        self._formula_editor_result=result;self._formula_editor_save=save
        edit.textChanged.connect(self.update_formula_preview)
        room_edit.installEventFilter(self);edit.installEventFilter(self)
        save.clicked.connect(self.save_formula_editor);cancel.clicked.connect(self.cancel_formula_editor)
        self._loading_positions=False
        self.update_formula_preview(formula)
        target=room_edit if column==3 else edit;target.setFocus();target.selectAll()

    def update_formula_preview(self,formula):
        if not self._formula_editor_result:return
        try:
            quantity=eval_formula(formula)
            self._formula_editor_result.setText(de_num(quantity,3))
            self._formula_editor_result.setStyleSheet(f"color:{current_theme_color('accent')};")
            self._formula_editor_result.setToolTip("")
            if self._formula_editor_save:self._formula_editor_save.setEnabled(True)
        except Exception as e:
            self._formula_editor_result.setText("Formel prüfen")
            self._formula_editor_result.setStyleSheet(f"color:{current_theme_color('delete')};")
            self._formula_editor_result.setToolTip(str(e))
            if self._formula_editor_save:self._formula_editor_save.setEnabled(False)

    def _prepare_measure_tab(self,row,column,backward=False):
        """Tab in der Formel einer Aufmaßzeile: nach dem Speichern neue Zeile direkt darunter."""
        if column!=4 or backward:return None
        key=self.positions.item(row,0)
        mpid=key.data(Qt.UserRole) if key else None;line_id=key.data(Qt.UserRole+1) if key else None
        if not mpid or not line_id:return None
        return lambda:self._insert_line_below(mpid,line_id)

    def _insert_line_below(self,mpid,anchor_line_id):
        new_line_id=self.db.add_measurement_line(mpid,"","0",0,"","")
        self.db.place_measurement_line_after(new_line_id,anchor_line_id);self._pending_new_line=new_line_id
        self.reload_position(mpid,new_line_id)
        for row in range(self.positions.rowCount()):
            item=self.positions.item(row,0)
            if item and item.data(Qt.UserRole+1)==new_line_id:
                self.positions.setCurrentCell(row,3);self.positions.editItem(self.positions.item(row,3));break

    def cancel_formula_editor(self):
        row=self._formula_editor_row
        pending=getattr(self,"_pending_new_line",None);self._pending_new_line=None
        if row is None:return
        self._loading_positions=True
        self.positions.clearSpans()
        if row<self.positions.rowCount():
            self.positions.removeRow(row)
        self._clear_formula_editor_state()
        self._loading_positions=False
        # Eine gerade erst angelegte, leere Zeile beim Abbrechen wieder entfernen.
        if pending:
            line=self.db.conn.execute("SELECT * FROM measurement_lines WHERE id=?",(pending,)).fetchone()
            if line and (line["formula"] or "").strip() in ("","0") and not (line["room"] or "").strip():
                mpid=line["measurement_position_id"];self.db.delete_measurement_line(pending);self.reload_position(mpid)

    def save_formula_editor(self):
        if not self._formula_editor_input or not self._formula_editor_room:return
        room=self._formula_editor_room.text().strip()
        formula=self._formula_editor_input.text().strip()
        try:quantity=eval_formula(formula)
        except Exception as e:
            QMessageBox.warning(self,"Aufmaß / Formel",str(e));return
        mpid=self._formula_editor_mpid;line_id=self._formula_editor_line_id
        self._pending_new_line=None;self._last_saved_line=(mpid,line_id)
        if line_id:
            row=self.db.conn.execute("SELECT * FROM measurement_lines WHERE id=?",(line_id,)).fetchone()
            if not row:return
            if formula==(row["formula"] or "").strip() and room==(row["room"] or "").strip():
                self.cancel_formula_editor();return
            self.db.backup("vor_inline_aufmass_aenderung")
            self.db.update_measurement_line(line_id,row["description"] or "",formula,quantity,
                                            row["sheet"] or "",room)
        else:
            self.db.backup("vor_erster_aufmasszeile_inline")
            line_id=self.db.add_measurement_line(mpid,"",formula,quantity,"",room);self._last_saved_line=(mpid,line_id)
        # Die eingefügte Editorzeile vor dem Neuaufbau der Tabelle wirklich
        # entfernen. Ein bloßes Zurücksetzen der Referenzen lässt die Zeile
        # sonst an ihrer bisherigen Position sichtbar stehen.
        self.cancel_formula_editor()
        self.reload_position(mpid,line_id)

    def inline_position_changed(self,item):
        if self._loading_positions or item.column() not in (3,4):return
        key=self.positions.item(item.row(),0)
        mpid=key.data(Qt.UserRole) if key else None
        line_id=key.data(Qt.UserRole+1) if key else None
        if not mpid:return
        if not line_id:
            edited_column=item.column()
            room_item=self.positions.item(item.row(),3)
            formula_item=self.positions.item(item.row(),4)
            room=(room_item.text() if room_item else "").strip()
            entered_formula=(formula_item.text() if formula_item else "").strip()
            if not room and not entered_formula:return
            formula=entered_formula or "0"
            try:quantity=eval_formula(formula)
            except Exception as e:
                QMessageBox.warning(self,"Aufmaß / Formel",str(e))
                self.reload_position(mpid);return
            self.db.backup("vor_erster_aufmasszeile")
            new_line_id=self.db.add_measurement_line(mpid,"",formula,quantity,"",room)
            self.reload_position(mpid,new_line_id)
            if edited_column==3 and not entered_formula:
                for r in range(self.positions.rowCount()):
                    row_key=self.positions.item(r,0)
                    if row_key and row_key.data(Qt.UserRole+1)==new_line_id:
                        self.positions.setCurrentCell(r,4)
                        self.positions.editItem(self.positions.item(r,4));break
            return
        row=self.db.conn.execute("SELECT * FROM measurement_lines WHERE id=?",(line_id,)).fetchone()
        if not row:return
        room=item.text().strip() if item.column()==3 else (row["room"] or "")
        formula=item.text().strip() if item.column()==4 else (row["formula"] or "")
        if not formula:formula="0"
        try:quantity=eval_formula(formula)
        except Exception as e:
            QMessageBox.warning(self,"Aufmaß / Formel",str(e))
            self.reload_position(row["measurement_position_id"],line_id);return
        if room==(row["room"] or "") and formula==(row["formula"] or ""):return
        self.db.update_measurement_line(line_id,row["description"] or "",formula,quantity,row["sheet"] or "",room)
        if item.column()==4:self.reload_position(row["measurement_position_id"],line_id)

    def selected_mpid(self):
        r=self.positions.currentRow();return self.positions.item(r,0).data(Qt.UserRole) if r>=0 and self.positions.item(r,0) else None
    def selected_line(self):
        r=self.lines.currentRow();return self.lines.item(r,0).data(Qt.UserRole) if r>=0 and self.lines.item(r,0) else None
    def reload_position(self,mpid,line_id=None):
        self.load_project()
        fallback=None
        for r in range(self.positions.rowCount()):
            it=self.positions.item(r,0)
            if it and it.data(Qt.UserRole)==mpid:
                if fallback is None:fallback=r
                if line_id is not None and it.data(Qt.UserRole+1)==line_id:
                    fallback=r;break
        if fallback is not None:
            self.positions.selectRow(fallback)
            self.select_position()
    def import_pos(self):
        if not self.project_id:return
        d=ImportPositionDialog(self.db,self.project_id,self)
        if d.exec():
            ids=d.selected_ids()
            if not ids:QMessageBox.information(self,"Übernahme","Bitte mindestens eine Position markieren.");return
            self.db.backup("vor_aufmass_uebernahme")
            for pid in ids:self.db.add_measurement_position(self.project_id,pid)
            self.load_project()
    def show_measurement(self):
        if not self.project_id:
            QMessageBox.information(self,"Aufmaß anzeigen","Bitte zuerst ein Projekt auswählen.");return
        if not self.db.measurement_positions(self.project_id):
            QMessageBox.information(self,"Aufmaß anzeigen","Dieses Projekt enthält noch keine Aufmaßpositionen.");return
        MeasurementPreviewDialog(self.db,self.project_id,self).exec()
    def send_measurement_email(self):
        if not self.project_id:
            QMessageBox.information(self,"Aufmaß per E-Mail","Bitte zuerst ein Projekt auswählen.");return
        if not self.db.measurement_positions(self.project_id):
            QMessageBox.information(self,"Aufmaß per E-Mail","Dieses Projekt enthält noch keine Aufmaßpositionen.");return
        MeasurementPreviewDialog(self.db,self.project_id,self).send_email()
    def create_invoice_from_measurement(self):
        if not self.project_id:
            QMessageBox.information(self,"Rechnung aus Aufmaß","Bitte zuerst ein Projekt auswählen.");return
        d=PartialInvoiceDialog(self.db,self,project_id=self.project_id,source_mode="Aufmaß")
        if not d.exec():return
        self.db.backup("vor_rechnung_aus_aufmass")
        iid,err=self.db.create_invoice(*d.new_invoice_data())
        if err:
            QMessageBox.information(self,"Rechnung aus Aufmaß",err);return
        w=self.window();pages=getattr(w,"pages",{});stack=getattr(w,"stack",None)
        page=pages.get("Rechnungen") if isinstance(pages,dict) else None
        if page is not None and stack is not None:
            w.navigate(list(pages).index("Rechnungen"))
            if hasattr(page,"refresh_keep_invoice"):page.refresh_keep_invoice(iid)
        QMessageBox.information(self,"Rechnungsentwurf erstellt",
            "Alle aktuell aufgemessenen Positionen wurden in den Rechnungsentwurf übernommen.\n\n"
            "Positionen können dort entfernt oder wieder hinzugefügt werden, ohne das Aufmaß zu verändern.")
    def select_position(self):
        top_row=self.positions.currentRow()
        top_line_id=None
        if top_row>=0 and self.positions.item(top_row,0):
            top_line_id=self.positions.item(top_row,0).data(Qt.UserRole+1)
        self.mpid=self.selected_mpid()
        if not self.mpid:
            self.lines.setRowCount(0)
            r=self.positions.currentRow()
            if r>=0 and self.positions.item(r,1):
                label=self.positions.item(r,1).text()
                text=self.positions.item(r,2).text() if self.positions.item(r,2) else ""
                if label.startswith("TITEL") or label.startswith("Untertitel"):
                    self.info.setText(
                        f"<b>{label} – {text}</b><br>"
                        "Dieser Eintrag dient nur der Gliederung. "
                        "Bitte eine Position darunter auswählen, um Aufmaßzeilen/Formeln zu bearbeiten."
                    )
            return
        p=self.db._measurement_position(self.mpid);rows=self.db.measurement_lines(self.mpid);self.lines.setRowCount(len(rows)+1)
        total=sum((x["quantity"] or 0) for x in rows);billed=float(p["billed_quantity"] or 0)
        hist=self.db.snapshots(self.mpid);prev=float(hist[1]["total_quantity"] if len(hist)>1 else 0)
        increase=total-prev;open_qty=float(p["offer_quantity"] or 0)-total
        self.info.setText(f'<b>{p["offer_number"]} · Pos. {p["position_no"]} – {p["short_text"]}</b><br>'
                          f'Angebot: {de_num(p["offer_quantity"],3)} {p["unit"]} · '
                          f'Aktueller kumulierter Aufmaßstand: {de_num(total,3)} {p["unit"]} · '
                          f'Zuwachs: {de_num(increase,3)} {p["unit"]}<br>'
                          f'Bereits abgerechnet: {de_num(billed,3)} {p["unit"]} · '
                          f'Noch offen: {de_num(open_qty,3)} {p["unit"]}')
        for r,x in enumerate(rows):
            vals=[x["sheet"] or "",x["room"] or "",x["description"] or "",x["formula"],
                  de_num(x["quantity"],3),x["updated_at"].replace("T"," ")]
            for c,v in enumerate(vals):
                it=QTableWidgetItem(v);it.setData(Qt.UserRole,x["id"]) if c==0 else None;self.lines.setItem(r,c,it)
        sum_row=len(rows)
        vals=["","",f'Summe Pos. {p["position_no"]}',"",de_num(total,3),""]
        for c,v in enumerate(vals):
            it=QTableWidgetItem(v);font=it.font();font.setBold(True);it.setFont(font)
            it.setFlags(Qt.ItemIsEnabled);self.lines.setItem(sum_row,c,it)
        if top_line_id is not None:
            for r in range(len(rows)):
                it=self.lines.item(r,0)
                if it and it.data(Qt.UserRole)==top_line_id:
                    self.lines.selectRow(r);break
    def edit_measurement_position(self):
        mpid=self.selected_mpid()
        if not mpid:
            QMessageBox.information(self,"Aufmaßposition bearbeiten","Bitte zuerst eine Aufmaßposition auswählen.");return
        p=self.db._measurement_position(mpid)
        d=PositionDialog(self.db,p["offer_id"],self,p,measurement_location=p["measurement_location"] or "")
        d.setWindowTitle("Aufmaßposition vollständig bearbeiten")
        if d.exec():
            self.db.backup("vor_aufmassposition_bearbeiten")
            ok,err=self.db.update_measurement_position(mpid,d.data())
            if not ok:
                QMessageBox.warning(self,"Aufmaßposition bearbeiten",err);return
            # Offene Rechnungsentwürfe können beim nächsten Öffnen mit dem aktuellen
            # Aufmaß synchronisiert werden; festgeschriebene Rechnungen bleiben unverändert.
            self.load_project()
            for r in range(self.positions.rowCount()):
                it=self.positions.item(r,0)
                if it and it.data(Qt.UserRole)==mpid:
                    self.positions.selectRow(r);self.select_position();break

    def copy_measurement_position(self):
        mpid=self.selected_mpid()
        if not mpid:
            QMessageBox.information(self,"Position kopieren","Bitte zuerst eine Aufmaßposition auswählen.");return
        p=self.db._measurement_position(mpid)
        d=PositionCopyDialog(self.db,self.project_id,self)
        if not d.exec():return
        target_oid,title=d.data()

        self.db.backup("vor_position_kopieren")
        created_offer=False
        if target_oid is None:
            target_oid=self.db.add_offer(self.project_id,title or "Nachtrag / Zusatzangebot","Position aus Aufmaß kopiert")
            created_offer=True

        new_pid,err=self.db.copy_offer_position(p["offer_position_id"],target_oid)
        if err:
            QMessageBox.warning(self,"Position kopieren",err);return

        target=self.db.offer(target_oid)
        QMessageBox.information(self,"Position kopiert",
            f'Pos. {p["position_no"]} wurde in Angebot {target["number"]} kopiert.\n\n'
            f'{"Das neue Angebot wurde dabei angelegt. " if created_offer else ""}'
            "Originalposition und Aufmaß bleiben unverändert.\n"
            "Die kopierte Position kann im Angebotsmodul unabhängig bearbeitet werden.")
        if created_offer:
            offers_page=getattr(self.window(),"pages",{}).get("Angebote")
            if offers_page is not None:offers_page.refresh()

    def show_history(self):
        mpid=self.selected_mpid()
        if not mpid:
            QMessageBox.information(self,"Aufmaß-Historie","Bitte zuerst eine Aufmaßposition auswählen.");return
        if not self.db.snapshots(mpid):
            self.db.add_snapshot(mpid,"Ausgangsstand aus 0.6.1 übernommen")
        MeasurementHistoryDialog(self.db,mpid,self).exec()

    def add_line(self):
        if not self.mpid:QMessageBox.information(self,"Aufmaß","Bitte zuerst eine Aufmaßposition auswählen.");return
        mpid=self.mpid
        row=self.positions.currentRow();key=self.positions.item(row,0) if row>=0 else None
        anchor=key.data(Qt.UserRole+1) if key and key.data(Qt.UserRole)==mpid else None
        d=MeasurementLineDialog(self)
        if d.exec():
            line_id=self.db.add_measurement_line(mpid,*d.data())
            if anchor:self.db.place_measurement_line_after(line_id,anchor)
            self.reload_position(mpid,line_id)
    def edit_line(self,*args):
        lid=self.selected_line()
        if not lid:return
        row=self.db.conn.execute("SELECT * FROM measurement_lines WHERE id=?",(lid,)).fetchone();d=MeasurementLineDialog(self,row)
        if d.exec():
            mpid=row["measurement_position_id"]
            self.db.backup("vor_aufmass_aenderung");self.db.update_measurement_line(lid,*d.data());self.reload_position(mpid,lid)
    def delete_line(self):
        lid=self.selected_line()
        if lid and QMessageBox.question(self,"Aufmaßzeile löschen","Zeile wirklich löschen?",QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            row=self.db.conn.execute("SELECT measurement_position_id FROM measurement_lines WHERE id=?",(lid,)).fetchone()
            mpid=row["measurement_position_id"] if row else self.mpid
            self.db.backup("vor_aufmass_loeschen");self.db.delete_measurement_line(lid);self.reload_position(mpid)
    def _row_kind(self,row):
        key=self.positions.item(row,0) if row>=0 else None
        if key and key.data(Qt.UserRole+1):return "line"
        if key and isinstance(key.data(Qt.UserRole),int):return "position"
        return None

    def _update_remove_button(self):
        kind=self._row_kind(self.positions.currentRow())
        if kind=="position":
            self.remove_button.setText("🗑  Position entfernen")
            self.remove_button.setToolTip("Position mit allen Aufmaßzeilen aus dem Aufmaß entfernen (bleibt im Angebot)")
        else:
            self.remove_button.setText("🗑  Zeile löschen")
            self.remove_button.setToolTip("Markierte Aufmaßzeile löschen (auch mit Entf oder Rechtsklick)")
        self.remove_button.setEnabled(kind is not None)
        self.move_up_button.setEnabled(kind is not None);self.move_down_button.setEnabled(kind is not None)

    def _measure_menu(self,point):
        item=self.positions.itemAt(point)
        if item is None:return
        row=item.row();self.positions.setCurrentCell(row,item.column())
        kind=self._row_kind(row)
        if kind is None:return
        key=self.positions.item(row,0);menu=QMenu(self)
        if kind=="line":
            below=menu.addAction("＋  Neue Zeile darunter")
            menu.addSeparator();delete=menu.addAction("🗑  Zeile löschen")
        else:
            below=menu.addAction("＋  Aufmaßzeile hinzufügen")
            menu.addSeparator();delete=menu.addAction("🗑  Position aus Aufmaß entfernen")
        chosen=menu.exec(self.positions.viewport().mapToGlobal(point))
        if chosen is delete:self.remove_pos()
        elif chosen is below:
            if kind=="line":self._insert_line_below(key.data(Qt.UserRole),key.data(Qt.UserRole+1))
            else:self.add_line()

    def move_selected(self,direction):
        """Markierte Aufmaßzeile bzw. Aufmaßposition hoch oder runter schieben."""
        row=self.positions.currentRow();kind=self._row_kind(row)
        if kind is None:return
        key=self.positions.item(row,0);mpid=key.data(Qt.UserRole);line_id=key.data(Qt.UserRole+1)
        if self.positions.state()==QAbstractItemView.EditingState:
            self.positions.closePersistentEditor(self.positions.currentItem());self.positions.setFocus()
        moved=self.db.move_measurement_line(line_id,direction) if kind=="line" else self.db.move_measurement_position(mpid,direction)
        if not moved:
            where="am Anfang" if direction<0 else "am Ende"
            what="der Position" if kind=="line" else "des Titels"
            self.window().statusBar().showMessage(f"Steht bereits {where} {what}.",3000);return
        self.reload_position(mpid,line_id if kind=="line" else None)

    def remove_pos(self):
        row=self.positions.currentRow();key=self.positions.item(row,0) if row>=0 else None
        line_id=key.data(Qt.UserRole+1) if key else None
        if line_id:
            # Markierte Aufmaßzeile löschen (früher im Detailbereich).
            if QMessageBox.question(self,"Aufmaßzeile löschen","Diese Aufmaßzeile wirklich löschen?",
                                    QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:return
            mpid=key.data(Qt.UserRole);self.db.backup("vor_aufmass_loeschen")
            neighbours=[self.positions.item(r,0).data(Qt.UserRole+1) for r in (row+1,row-1)
                        if 0<=r<self.positions.rowCount() and self.positions.item(r,0) and self.positions.item(r,0).data(Qt.UserRole)==mpid]
            neighbours=[n for n in neighbours if n]
            self.db.delete_measurement_line(line_id);self.reload_position(mpid,neighbours[0] if neighbours else None);return
        mpid=self.selected_mpid()
        if mpid and QMessageBox.question(self,"Aufmaßposition entfernen","Position und ihre Aufmaßzeilen wirklich aus dem Aufmaß entfernen?",QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            self.db.backup("vor_aufmassposition_loeschen");self.db.remove_measurement_position(mpid)
            self.set_offer_panel_visible(False);self.load_project()

class LanguageSelectionDialog(QDialog):
    """Einmalige, sprachneutral erkennbare Auswahl beim ersten Start."""
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sprache / اللغة")
        self.setMinimumWidth(520)
        layout=QVBoxLayout(self)
        title=QLabel("<b>Sprache der Bedienoberfläche / لغة واجهة المستخدم</b>")
        title.setObjectName("pageTitle");layout.addWidget(title)
        explanation=QLabel(
            "Bitte die gewünschte Sprache für die Bedienung auswählen.<br>"
            "يرجى اختيار اللغة المطلوبة لاستخدام البرنامج.<br><br>"
            "<b>Hinweis / ملاحظة:</b> Geschäftsdokumente bleiben auf Deutsch.<br>"
            "تبقى المستندات التجارية باللغة الألمانية."
        )
        explanation.setWordWrap(True);layout.addWidget(explanation)
        self.language=QComboBox()
        self.language.addItem("Deutsch", "de")
        self.language.addItem("العربية", "ar")
        layout.addWidget(self.language)
        buttons=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Weiter / متابعة")
        buttons.button(QDialogButtonBox.Cancel).setText("Deutsch verwenden")
        buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_language(self):
        return self.language.currentData() or "de"

class CustomerDialog(QDialog):
    def __init__(self,parent=None,row=None):
        super().__init__(parent);self.setMinimumWidth(500)
        self.setWindowTitle(ui("customer_edit_title") if row else ui("customer_new_title"))
        f=QFormLayout(self)
        self.company=QLineEdit();self.contact=QLineEdit();self.street=QLineEdit();self.zip=QLineEdit()
        self.city=QLineEdit();self.phone=QLineEdit();self.email=QLineEdit();self.notes=QTextEdit()
        for a,b in zip(ui("customer_fields"),[self.company,self.contact,self.street,self.zip,self.city,self.phone,self.email,self.notes]):
            f.addRow(a,b)
        self.vat_id=QLineEdit();self.vat_id.setPlaceholderText("z. B. DE123456789 – Pflicht für E-Rechnungen nach § 13b")
        self.buyer_reference=QLineEdit();self.buyer_reference.setPlaceholderText("nur bei öffentlichen Auftraggebern")
        f.addRow("USt-IdNr. des Kunden",self.vat_id);f.addRow("Leitweg-ID",self.buyer_reference)
        if row:
            for k,w in zip(["company","contact","street","zip","city","phone","email"],
                           [self.company,self.contact,self.street,self.zip,self.city,self.phone,self.email]):
                w.setText(row[k] or "")
            self.notes.setPlainText(row["notes"] or "")
            keys=row.keys()
            self.vat_id.setText((row["vat_id"] if "vat_id" in keys else "") or "")
            self.buyer_reference.setText((row["buyer_reference"] if "buyer_reference" in keys else "") or "")
        bb=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Save).setText(ui("save"));bb.button(QDialogButtonBox.Cancel).setText(ui("cancel"))
        bb.accepted.connect(self.validate);bb.rejected.connect(self.reject);f.addRow(bb)
    def validate(self):
        if not self.company.text().strip():
            QMessageBox.warning(self,ui("required_title"),ui("required_customer"));return
        self.accept()
    def data(self):
        return [self.company.text().strip(),self.contact.text().strip(),self.street.text().strip(),
                self.zip.text().strip(),self.city.text().strip(),self.phone.text().strip(),
                self.email.text().strip(),self.notes.toPlainText().strip()]

class ProjectDialog(QDialog):
    def __init__(self,db,parent=None,row=None):
        super().__init__(parent);self.setMinimumWidth(520);self.setWindowTitle("Projekt bearbeiten" if row else "Neues Projekt")
        f=QFormLayout(self);self.customer=QComboBox()
        for c in db.customers():self.customer.addItem(f'{c["number"]} – {c["company"]}',c["id"])
        self.name=QLineEdit();self.site=QLineEdit();self.status=QComboBox()
        self.status.addItems(["Offen","In Arbeit","Wartet","Abgeschlossen","Storniert"]);self.notes=QTextEdit()
        for a,b in [("Kunde *",self.customer),("Projektname *",self.name),("Baustelle",self.site),
                    ("Status",self.status),("Notizen",self.notes)]:f.addRow(a,b)
        if row:
            self.customer.setCurrentIndex(max(self.customer.findData(row["customer_id"]),0))
            self.name.setText(row["name"] or "");self.site.setText(row["site"] or "")
            self.status.setCurrentIndex(max(self.status.findText(row["status"] or "Offen"),0))
            self.notes.setPlainText(row["notes"] or "")
        bb=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        bb.accepted.connect(self.validate);bb.rejected.connect(self.reject);f.addRow(bb)
    def validate(self):
        if self.customer.currentIndex()<0:
            QMessageBox.warning(self,"Pflichtfeld","Bitte zuerst einen Kunden anlegen.");return
        if not self.name.text().strip():
            QMessageBox.warning(self,"Pflichtfeld","Bitte Projektnamen eintragen.");return
        self.accept()
    def data(self):
        return [self.customer.currentData(),self.name.text().strip(),self.site.text().strip(),
                self.status.currentText(),self.notes.toPlainText().strip()]

class ProjectDocumentsDialog(QDialog):
    def __init__(self,db,project_id,parent=None):
        super().__init__(parent);self.db=db;self.project_id=project_id
        project=db.project(project_id)
        self.setWindowTitle(f'Dokumente – {project["number"]} – {project["name"]}')
        self.setMinimumSize(1180,680)
        o=QVBoxLayout(self)
        title=QLabel(f'<b>Projekt {project["number"]}</b> – {project["name"]}')
        title.setWordWrap(True);o.addWidget(title)
        hint=QLabel("Die Dateien werden ausschließlich diesem Projekt zugeordnet und in der Projektablage der Anwendung gespeichert.")
        hint.setWordWrap(True);o.addWidget(hint)
        content=QSplitter(Qt.Horizontal)
        self.table=QTableWidget(0,4)
        self.table.setHorizontalHeaderLabels(["Dateiname","Beschreibung","Hinzugefügt am","Ablage"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.show_description)
        self.table.doubleClicked.connect(self.open_document)
        self.table.setColumnWidth(0,230);self.table.setColumnWidth(1,250)
        self.table.setColumnWidth(2,115);self.table.setColumnWidth(3,220)
        content.addWidget(self.table)

        preview_box=QGroupBox("Dokumentenvorschau")
        preview_layout=QVBoxLayout(preview_box)
        self.preview_title=QLabel("Kein Dokument ausgewählt")
        self.preview_title.setWordWrap(True)
        self.preview_title.setStyleSheet("font-weight:600;padding:4px")
        preview_layout.addWidget(self.preview_title)
        self.preview_stack=QStackedWidget()
        self.preview_empty=compact_hint("Bitte links ein Dokument auswählen.")
        self.preview_empty.setAlignment(Qt.AlignCenter);self.preview_empty.setWordWrap(True)
        self.image_preview=QLabel()
        self.image_preview.setAlignment(Qt.AlignCenter)
        self.pdf_document=QPdfDocument(self)
        self.pdf_preview=QPdfView();self.pdf_preview.setDocument(self.pdf_document)
        self.pdf_preview.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        self.pdf_preview.setPageMode(QPdfView.PageMode.MultiPage)
        for widget in (self.preview_empty,self.image_preview,self.pdf_preview):self.preview_stack.addWidget(widget)
        preview_layout.addWidget(self.preview_stack,1)
        self.preview_info=QLabel("");self.preview_info.setWordWrap(True)
        preview_layout.addWidget(self.preview_info)
        content.addWidget(preview_box);content.setSizes([650,500])
        o.addWidget(content,1)
        form=QFormLayout();self.description=QTextEdit();self.description.setMaximumHeight(90)
        self.description.setPlaceholderText("Optionale Beschreibung zum markierten Dokument")
        form.addRow("Beschreibung",self.description);o.addLayout(form)
        actions=QHBoxLayout()
        add=icon_button("new","Dokument hinzufügen",self.add_document)
        open_button=icon_button("open","Dokument öffnen",self.open_document)
        save=icon_button("save","Dokumentbeschreibung speichern",self.save_description)
        delete=icon_button("delete","Dokument löschen",self.delete_document)
        close=icon_button("cancel","Dokumentenfenster schließen",self.accept)
        for button in (add,open_button,save,delete):actions.addWidget(button)
        actions.addStretch();actions.addWidget(close);o.addLayout(actions)
        self.refresh()

    def document_id(self):
        row=self.table.currentRow()
        item=self.table.item(row,0) if row>=0 else None
        return item.data(Qt.UserRole) if item else None

    def refresh(self,select_id=None):
        rows=self.db.project_documents(self.project_id);self.table.setRowCount(len(rows))
        selected=-1
        for r,doc in enumerate(rows):
            created=de_date(doc["created_at"])
            values=[doc["filename"],doc["description"] or "",created,doc["filepath"]]
            for c,value in enumerate(values):
                item=QTableWidgetItem(value)
                if c==0:item.setData(Qt.UserRole,doc["id"])
                self.table.setItem(r,c,item)
            if doc["id"]==select_id:selected=r
        if selected>=0:self.table.selectRow(selected)
        elif rows:self.table.selectRow(0)
        else:
            self.description.clear();self.clear_preview()

    def show_description(self):
        row=self.table.currentRow()
        self.description.setPlainText(self.table.item(row,1).text() if row>=0 and self.table.item(row,1) else "")
        self.update_preview()

    def clear_preview(self,message="Bitte links ein Dokument auswählen."):
        self.pdf_document.close();self.image_preview.clear()
        self.preview_empty.setText(message);self.preview_stack.setCurrentWidget(self.preview_empty)
        self.preview_title.setText("Kein Dokument ausgewählt");self.preview_info.clear()

    def update_preview(self):
        document_id=self.document_id()
        if not document_id:
            self.clear_preview();return
        row=self.table.currentRow();filename=self.table.item(row,0).text()
        try:path=self.db.project_document_path(document_id)
        except Exception as exc:
            self.clear_preview(str(exc));return
        self.preview_title.setText(filename)
        if not path or not path.is_file():
            self.clear_preview("Die gespeicherte Datei wurde nicht gefunden.");return
        size=path.stat().st_size
        self.preview_info.setText(f"{path.suffix.upper().lstrip('.') or 'Datei'} · {de_num(size/1024,1)} KB")
        suffix=path.suffix.lower()
        if suffix in {".png",".jpg",".jpeg",".bmp",".gif",".webp",".tif",".tiff"}:
            pixmap=QPixmap(str(path))
            if pixmap.isNull():
                self.clear_preview("Für dieses Bild konnte keine Vorschau erzeugt werden.");return
            available=self.image_preview.size()
            width=max(available.width()-20,500);height=max(available.height()-20,450)
            self.image_preview.setPixmap(pixmap.scaled(width,height,Qt.KeepAspectRatio,Qt.SmoothTransformation))
            self.preview_stack.setCurrentWidget(self.image_preview);return
        if suffix==".pdf":
            self.pdf_document.close()
            self.pdf_document.load(str(path))
            if self.pdf_document.pageCount()>0:
                self.preview_stack.setCurrentWidget(self.pdf_preview);return
            self.clear_preview("Die PDF-Datei konnte nicht dargestellt werden.");return
        self.preview_empty.setText(
            "Für diesen Dateityp ist keine direkte Vorschau verfügbar.\n\n"
            "Mit „Öffnen“ wird das Dokument in der passenden Anwendung gestartet."
        )
        self.preview_stack.setCurrentWidget(self.preview_empty)

    def add_document(self):
        paths,_=QFileDialog.getOpenFileNames(self,"Dokumente für dieses Projekt auswählen (mehrere möglich)","",
            "Alle Dateien (*);;Bilder (*.png *.jpg *.jpeg *.bmp *.gif *.webp *.tif *.tiff *.heic);;PDF (*.pdf)")
        if not paths:return
        document_id=None;failed=[]
        for path in paths:
            try:document_id=self.db.add_project_document(self.project_id,path,self.description.toPlainText())
            except Exception as exc:failed.append(f"{Path(path).name}: {exc}")
        self.refresh(document_id)
        if failed:
            QMessageBox.warning(self,"Dokument hinzufügen","Folgende Dateien konnten nicht importiert werden:\n\n"+"\n".join(failed))

    def open_document(self,*_):
        document_id=self.document_id()
        if not document_id:
            QMessageBox.information(self,"Dokument öffnen","Bitte zuerst ein Dokument auswählen.");return
        try:path=self.db.project_document_path(document_id)
        except Exception as exc:
            QMessageBox.warning(self,"Dokument öffnen",str(exc));return
        if not path or not path.is_file():
            QMessageBox.warning(self,"Dokument öffnen","Die gespeicherte Datei wurde nicht gefunden.");return
        open_desktop_file(path,self,"Dokument öffnen")

    def save_description(self):
        document_id=self.document_id()
        if not document_id:
            QMessageBox.information(self,"Beschreibung","Bitte zuerst ein Dokument auswählen.");return
        self.db.update_project_document_description(document_id,self.description.toPlainText())
        self.refresh(document_id)

    def delete_document(self):
        document_id=self.document_id()
        if not document_id:return
        filename=self.table.item(self.table.currentRow(),0).text()
        if QMessageBox.question(self,"Dokument löschen",
            f'„{filename}“ aus Projekt und Projektablage löschen?',
            QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:return
        try:
            self.db.backup("vor_projektdokument_loeschen")
            self.db.delete_project_document(document_id);self.refresh()
        except Exception as exc:
            QMessageBox.warning(self,"Dokument löschen",f"Das Dokument konnte nicht gelöscht werden.\n\n{exc}")

class ServiceDialog(QDialog):
    UNITS=["Stk.","m","m²","m³","lfm","Std.","Tag","kg","t","pauschal"]
    def __init__(self,parent=None,row=None):
        super().__init__(parent);self.setMinimumWidth(540);self.setWindowTitle("Leistung bearbeiten" if row else "Neue Leistung")
        f=QFormLayout(self);self.category=QLineEdit();self.category.setPlaceholderText("z. B. Trockenbau")
        self.short=QLineEdit();self.long=PlainTextPasteEdit();self.unit=QComboBox();self.unit.setEditable(True);self.unit.addItems(self.UNITS)
        self.source=QLineEdit();self.source.setPlaceholderText("optional")
        self.ek=QDoubleSpinBox();self.vk=QDoubleSpinBox();self.lohn=QDoubleSpinBox();self.mat=QDoubleSpinBox()
        for x in [self.ek,self.vk]:x.setMaximum(9999999);x.setDecimals(2);x.setSuffix(" €")
        for x in [self.lohn,self.mat]:x.setMaximum(100);x.setDecimals(1);x.setSuffix(" %")
        self.active=QCheckBox("Leistung ist aktiv");self.active.setChecked(True)
        for a,b in [("Leistungsgruppe / Kategorie *",self.category),("Kurztext *",self.short),("Langtext",self.long),("Einheit",self.unit),("Quelle",self.source),("Einkaufspreis",self.ek),
                    ("Verkaufspreis",self.vk),("Lohnanteil",self.lohn),("Materialanteil",self.mat),("",self.active)]:f.addRow(a,b)
        if row:
            self.category.setText(row["category"] or "Allgemein");self.source.setText(row["source"] or "")
            self.short.setText(row["short_text"] or "");self.long.setPlainText(row["long_text"] or "")
            self.unit.setCurrentIndex(max(self.unit.findText(row["unit"] or "Stk."),0))
            self.ek.setValue(row["purchase_price"] or 0);self.vk.setValue(row["sales_price"] or 0)
            self.lohn.setValue(row["wage_share"] or 0);self.mat.setValue(row["material_share"] or 0);self.active.setChecked(bool(row["active"]))
        bb=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        bb.accepted.connect(self.validate);bb.rejected.connect(self.reject);f.addRow(bb)
    def validate(self):
        if not self.category.text().strip() or not self.short.text().strip():
            QMessageBox.warning(self,"Pflichtfeld","Bitte Kategorie und Kurztext eintragen.");return
        self.accept()
    def data(self):
        return [self.short.text().strip(),self.long.toPlainText().strip(),self.unit.currentText().strip(),
                self.ek.value(),self.vk.value(),self.lohn.value(),self.mat.value(),1 if self.active.isChecked() else 0,
                self.category.text().strip(),self.source.text().strip()]

class EconomicsChart(QWidget):
    """Ring: Anteil der Kosten an der Auftragssumme, nach Kostenart; darunter der Abrechnungsstand."""
    SERIES_LIGHT=("#2a78d6","#eb6834","#1baf7a","#eda100","#e87ba4")
    SERIES_DARK=("#3987e5","#d95926","#199e70","#c98500","#d55181")
    def __init__(self,parent=None):
        super().__init__(parent);self.e=None;self.setFixedSize(480,330)

    def set_data(self,economics):
        self.e=economics;self.update()

    def _segments(self):
        """[(Name, Betrag, Farbindex)] – feste Farbe je Kostenart, freie Arten zusammen als „Weitere“."""
        categories=dict(self.e["categories"]);segments=[]
        for index,name in enumerate(INCOMING_CATEGORIES):
            value=categories.pop(name,0.0)
            if value>0:segments.append((name,value,index))
        other=sum(v for v in categories.values() if v>0)
        if other>0:segments.append(("Weitere",other,4))
        return segments

    def paintEvent(self,_event):
        from PySide6.QtGui import QPen
        if not self.e:return
        e=self.e;painter=QPainter(self);painter.setRenderHint(QPainter.Antialiasing)
        ink=self.palette().color(QPalette.ColorRole.WindowText);dark=self.palette().color(QPalette.ColorRole.Window).lightness()<128
        muted=QColor(ink);muted.setAlpha(150);track=QColor(ink);track.setAlpha(34)
        series=self.SERIES_DARK if dark else self.SERIES_LIGHT;critical=QColor("#d03b3b")
        segments=self._segments();costs=e["costs"];base=e["base"];over=base>0 and costs>base
        whole=costs if (over or base<=0) else base
        size=168;ring=24;rect=QRectF(ring/2+2,ring/2+6,size-ring,size-ring)
        painter.setPen(QPen(track,ring,Qt.SolidLine,Qt.FlatCap));painter.drawArc(rect,0,360*16)
        gap=1.6 if len(segments)>1 or (segments and not over and base>0 and costs<base) else 0.0
        # Auch kleine Beträge bleiben als schmaler Farbstreifen sichtbar.
        spans=[max(5.0,360.0*value/whole) if whole>0 and value>0 else 0.0 for _name,value,_color in segments]
        if sum(spans)>360.0:spans=[x*360.0/sum(spans) for x in spans]
        angle=90.0
        for (name,value,color_index),span in zip(segments,spans):
            if span<=0:continue
            painter.setPen(QPen(QColor(series[color_index]),ring,Qt.SolidLine,Qt.FlatCap))
            painter.drawArc(rect,int((angle-gap/2)*16),-int(max(0.4,span-gap)*16));angle-=span
        # Mitte: Kostenanteil als Zahl
        base_px=max(12,self.fontInfo().pixelSize());normal=QFont(self.font());normal.setPixelSize(base_px)
        center=QRectF(rect);big=QFont(self.font());big.setPixelSize(base_px*2);big.setBold(True)
        painter.setFont(big);painter.setPen(critical if over else ink)
        def percent(v):
            return de_num(v,1 if 0<abs(v)<10 or 90<abs(v)<100 else 0)+" %"
        text=percent(e["cost_share"]) if e["cost_share"] is not None else "–"
        painter.drawText(center.adjusted(0,-10,0,-10),Qt.AlignCenter,text)
        small=QFont(self.font());small.setPixelSize(max(11,base_px-1));painter.setFont(small);painter.setPen(muted)
        painter.drawText(center.adjusted(0,24,0,24),Qt.AlignCenter,"Kosten" if base>0 else "ohne Auftrag")
        # Legende rechts: Farbe + Name, Betrag und Anteil in normaler Schrift
        x=size+26;y=10;painter.setFont(normal)
        def legend(color,name,value,share):
            nonlocal y
            painter.setPen(Qt.NoPen);painter.setBrush(color);painter.drawRoundedRect(QRectF(x,y+3,12,12),3,3)
            painter.setPen(ink);painter.setFont(normal);painter.drawText(QRectF(x+20,y,260,18),Qt.AlignLeft|Qt.AlignVCenter,name)
            painter.setPen(muted);painter.setFont(small)
            detail=money(value)+(f" · {percent(share)}" if share is not None else "")
            painter.drawText(QRectF(x+20,y+18,260,18),Qt.AlignLeft|Qt.AlignVCenter,detail);y+=44
        for name,value,color_index in segments:
            legend(QColor(series[color_index]),name,value,value/base*100.0 if base>0 else None)
        if base>0 and not over:
            legend(track,"Noch nicht verbraucht",base-costs,(base-costs)/base*100.0)
        if over:
            painter.setPen(critical);painter.setFont(normal)
            painter.drawText(QRectF(x,y,280,40),Qt.AlignLeft|Qt.TextWordWrap,"⚠ Kosten liegen über der Auftragssumme");y+=44
        if not segments:
            painter.setPen(muted);painter.setFont(normal)
            painter.drawText(QRectF(x,y,280,36),Qt.AlignLeft|Qt.TextWordWrap,"Noch keine Eingangsrechnungen");y+=40
        # Abrechnungsstand als Balken
        top=max(size+30,y+14);width=self.width()-12;painter.setFont(normal);painter.setPen(ink)
        share=min(1.0,e["invoiced"]/base) if base>0 else 0.0
        label=f'Abgerechnet: {de_num(e["invoiced"]/base*100.0,0)} % der Auftragssumme' if base>0 else "Abgerechnet: noch keine Auftragssumme"
        painter.drawText(QRectF(4,top,width,20),Qt.AlignLeft|Qt.AlignVCenter,label)
        painter.setPen(Qt.NoPen);painter.setBrush(track);painter.drawRoundedRect(QRectF(4,top+24,width,10),4,4)
        if share>0:
            fill=QColor(ink);fill.setAlpha(170);painter.setBrush(fill);painter.drawRoundedRect(QRectF(4,top+24,max(8.0,width*share),10),4,4)
        painter.end()


class CustomersPage(QWidget):
    def __init__(self,db):
        super().__init__();self.db=db;self.module_navigator=None;self.context_listener=None;self.project_id=None
        o=QVBoxLayout(self);top=QHBoxLayout()
        t=QLabel(ui("customers_title"));t.setObjectName("pageTitle")
        self.search=QLineEdit();self.search.setVisible(False)
        self.customer_selector=QComboBox();self.customer_selector.setEditable(True);self.customer_selector.setMinimumWidth(420)
        self.customer_selector.lineEdit().setPlaceholderText("Kunde auswählen …")
        self.customer_selector.currentIndexChanged.connect(self.choose_customer)
        b=icon_button("new",ui("customer_new"),self.add)
        top.addWidget(t);top.addStretch();top.addWidget(QLabel("Kunde:"));top.addWidget(self.customer_selector);top.addWidget(b);o.addLayout(top)
        sp=QSplitter(Qt.Horizontal);self.table=QTableWidget(0,2);self.table.setHorizontalHeaderLabels(ui("customer_headers")[:2])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows);self.table.setEditTriggers(QAbstractItemView.NoEditTriggers);self.table.itemSelectionChanged.connect(self.show)
        self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeToContents);self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.Stretch)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left=QWidget();ll=QVBoxLayout(left);ll.addWidget(self.table);ar=QHBoxLayout()
        e=icon_button("edit",ui("customer_edit"),self.edit);d=icon_button("delete",ui("customer_delete"),self.delete);ar.addWidget(e);ar.addWidget(d);ar.addStretch();ll.addLayout(ar)
        right=QWidget();rl=QVBoxLayout(right)
        detail_top=QHBoxLayout()
        self.detail=QLabel(ui("customer_select"));self.detail.setWordWrap(True)
        edit_detail=icon_button("edit",ui("customer_edit"),self.edit)
        detail_top.addWidget(self.detail,1);detail_top.addWidget(edit_detail,0,Qt.AlignTop)
        rl.addLayout(detail_top)
        project_choice=QHBoxLayout();project_choice.addWidget(QLabel("Projekt:"))
        self.project_selector=QComboBox();self.project_selector.setEditable(True);self.project_selector.setMinimumWidth(520)
        self.project_selector.lineEdit().setPlaceholderText("Projekt auswählen …");self.project_selector.currentIndexChanged.connect(self.choose_project)
        project_choice.addWidget(self.project_selector,1)
        self.new_project_button=icon_button("new","Neues Projekt",self.add_project)
        self.new_project_button.setToolTip("Neues Projekt für den gewählten Kunden anlegen")
        self.edit_project_button=icon_button("edit","Projekt bearbeiten",self.edit_project)
        self.edit_project_button.setToolTip("Name, Baustelle, Status (auch Archiviert) und Notizen ändern oder das Projekt löschen")
        self.documents_button=QPushButton("📄  Dokumente");self.documents_button.clicked.connect(self.open_documents)
        self.documents_button.setToolTip("Bilder, Baupläne, PDFs und andere Dateien zu diesem Projekt hinzufügen und ansehen")
        self.archive_button=QPushButton("📦  Archivieren");self.archive_button.clicked.connect(self.toggle_archive)
        self.archive_button.setToolTip("Abgeschlossenes Projekt ausblenden – alle Daten bleiben erhalten")
        self.show_archived=QCheckBox("Archivierte anzeigen");self.show_archived.toggled.connect(self._archived_filter_changed)
        project_choice.addWidget(self.show_archived)
        project_choice.addWidget(self.new_project_button);project_choice.addWidget(self.edit_project_button);project_choice.addWidget(self.archive_button)
        project_choice.addWidget(self.documents_button);rl.addLayout(project_choice)
        content=QSplitter(Qt.Horizontal);content.setObjectName("customerProjectContent")
        project_side=QWidget();project_layout=QVBoxLayout(project_side);project_layout.setContentsMargins(0,0,8,0)
        projects_title=QLabel("Projekte dieses Kunden");projects_title.setObjectName("sectionTitle");project_layout.addWidget(projects_title)
        self.pt=QTableWidget(0,4);self.pt.setHorizontalHeaderLabels(ui("project_headers"));self.pt.setMaximumHeight(230)
        self.pt.setSelectionBehavior(QAbstractItemView.SelectRows);self.pt.setSelectionMode(QAbstractItemView.SingleSelection);self.pt.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.pt.setMaximumHeight(16777215);self.pt.itemSelectionChanged.connect(self.show_project);project_layout.addWidget(self.pt,1)
        overview=QWidget();overview_layout=QVBoxLayout(overview);overview_layout.setContentsMargins(12,0,0,0)
        self.project_heading=QLabel("Projekt auswählen");self.project_heading.setObjectName("projectOverviewTitle");overview_layout.addWidget(self.project_heading)
        self.project_hint=QLabel("Danach wird hier sichtbar, was bereits zu diesem Projekt gehört.");self.project_hint.setWordWrap(True);overview_layout.addWidget(self.project_hint)
        # Links der Projektinhalt, rechts die Vorschau des angeklickten Eintrags.
        # Geöffnet wird per Doppelklick oder über den einen Button in der Vorschau.
        self.preview_frame=QSplitter(Qt.Horizontal);self.preview_frame.setObjectName("projectPreview");self.preview_frame.setChildrenCollapsible(False)
        self.project_tree=QTreeWidget();self.project_tree.setObjectName("projectContentTree");self.project_tree.setHeaderHidden(True)
        self.project_tree.setMinimumWidth(240);self.project_tree.setIndentation(18)
        self.project_tree.currentItemChanged.connect(lambda *_:self.update_preview())
        self.project_tree.itemDoubleClicked.connect(lambda *_:self.open_preview_item())
        preview_side=QWidget();preview_layout=QVBoxLayout(preview_side);preview_layout.setContentsMargins(10,0,0,0)
        preview_head=QHBoxLayout();self.preview_title=QLabel("Vorschau");self.preview_title.setObjectName("sectionTitle")
        self.preview_open=QPushButton("Öffnen");self.preview_open.setEnabled(False);self.preview_open.clicked.connect(self.open_preview_item)
        preview_head.addWidget(self.preview_title,1);preview_head.addWidget(self.preview_open);preview_layout.addLayout(preview_head)
        self.preview_info=QLabel("");self.preview_info.setWordWrap(True);self.preview_info.setTextFormat(Qt.RichText)
        self.preview_info.setTextInteractionFlags(Qt.TextSelectableByMouse);self.preview_info.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Maximum)
        info_row=QHBoxLayout();info_row.addWidget(self.preview_info,0,Qt.AlignTop)
        self.economics_chart=EconomicsChart();self.economics_chart.setVisible(False)
        info_row.addSpacing(36);info_row.addWidget(self.economics_chart,0,Qt.AlignTop);info_row.addStretch(1)
        preview_layout.addLayout(info_row)
        # Bewusst die einfache Qt-Tabelle: Spalten wechseln je nach Eintrag und
        # sollen nicht in den gespeicherten Spaltenlayouts landen.
        self.preview_table=_QtTableWidget(0,0);self.preview_table.setObjectName("projectPreviewTable")
        self.preview_table.setSelectionBehavior(QAbstractItemView.SelectRows);self.preview_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.preview_table.setEditTriggers(QAbstractItemView.NoEditTriggers);self.preview_table.setAlternatingRowColors(True)
        self.preview_table.verticalHeader().setVisible(False);self.preview_table.setWordWrap(False)
        self.preview_table.doubleClicked.connect(lambda *_:self.open_preview_item())
        self.preview_table.itemSelectionChanged.connect(self.update_preview_open_button)
        preview_layout.addWidget(self.preview_table,1);preview_layout.addStretch(0)
        self.preview_frame.addWidget(self.project_tree);self.preview_frame.addWidget(preview_side)
        self.preview_frame.setStretchFactor(0,0);self.preview_frame.setStretchFactor(1,1);self.preview_frame.setSizes([320,900])
        self.preview_frame.setVisible(False);overview_layout.addWidget(self.preview_frame,1)
        content.addWidget(project_side);project_side.setVisible(False);content.addWidget(overview);content.setSizes([0,1]);content.setStretchFactor(1,1);rl.addWidget(content,1)
        self.customer_splitter=sp;self.customer_left=left
        sp.addWidget(left);sp.addWidget(right);sp.setStretchFactor(0,0);sp.setStretchFactor(1,1);sp.setSizes([350,1000]);o.addWidget(sp);self.refresh()
    def set_navigator(self,navigator,context_listener=None):
        self.module_navigator=navigator;self.context_listener=context_listener
    def choose_customer(self):
        customer_id=self.customer_selector.currentData()
        if customer_id is not None:self.select_customer(customer_id)
    def choose_project(self):
        project_id=self.project_selector.currentData()
        if project_id is None:self.clear_project();return
        for row in range(self.pt.rowCount()):
            item=self.pt.item(row,0)
            if item and item.data(Qt.UserRole)==project_id:
                self.pt.blockSignals(True);self.pt.selectRow(row);self.pt.blockSignals(False);break
        self.show_project()
    def set_compact_mode(self):
        self.customer_left.setVisible(False);self.customer_splitter.setSizes([0,1])
    def select_customer(self,customer_id,project_id=None):
        if project_id is not None and not self.show_archived.isChecked():
            target=self.db.project(project_id)
            if target and target["status"]=="Archiviert":
                self.show_archived.blockSignals(True);self.show_archived.setChecked(True);self.show_archived.blockSignals(False)
        for row in range(self.table.rowCount()):
            item=self.table.item(row,0)
            if item and item.data(Qt.UserRole)==customer_id:
                self.table.blockSignals(True);self.table.selectRow(row);self.table.blockSignals(False);self.show();break
        if project_id is not None:
            index=self.project_selector.findData(project_id)
            if index>=0:self.project_selector.setCurrentIndex(index);self.choose_project()
    def sid(self):
        r=self.table.currentRow();return self.table.item(r,0).data(Qt.UserRole) if r>=0 and self.table.item(r,0) else None
    def refresh(self):
        selected=self.sid() or self.customer_selector.currentData();rows=self.db.customers(self.search.text());self.table.setRowCount(len(rows))
        for r,x in enumerate(rows):
            for c,v in enumerate([x["number"],x["company"]]):
                it=QTableWidgetItem(v or "");it.setData(Qt.UserRole,x["id"]) if c==0 else None;self.table.setItem(r,c,it)
        self.customer_selector.blockSignals(True);self.customer_selector.clear();self.customer_selector.addItem("",None)
        for customer in rows:self.customer_selector.addItem(f'{customer["number"]} · {customer["company"]}',customer["id"])
        index=self.customer_selector.findData(selected);self.customer_selector.setCurrentIndex(max(0,index));self.customer_selector.blockSignals(False)
        self.detail.setText(ui("customer_select"));self.pt.setRowCount(0);self.clear_project()
    def show(self):
        cid=self.sid()
        if not cid:return
        if self.context_listener:self.context_listener(cid,None)
        x=self.db.customer(cid)
        contact=" · ".join(value for value in [x["contact"],x["street"],f'{x["zip"] or ""} {x["city"] or ""}'.strip(),x["phone"],x["email"]] if value)
        self.detail.setText(f'<b>{x["company"]}</b> · {x["number"]}<br>{contact or "Keine Kontaktdaten hinterlegt"}')
        ps=sorted(self.db.projects_for_customer(cid),key=lambda p:p["status"]=="Archiviert")
        archived_count=sum(1 for p in ps if p["status"]=="Archiviert")
        if not self.show_archived.isChecked():ps=[p for p in ps if p["status"]!="Archiviert"]
        self.show_archived.setText(f"Archivierte anzeigen ({archived_count})" if archived_count else "Archivierte anzeigen")
        self.pt.setRowCount(len(ps))
        self.project_selector.blockSignals(True);self.project_selector.clear();self.project_selector.addItem("",None)
        for r,p in enumerate(ps):
            for c,v in enumerate([p["number"],p["name"],p["site"],ui_status(p["status"])]):
                item=QTableWidgetItem(v or "");item.setData(Qt.UserRole,p["id"]) if c==0 else None;self.pt.setItem(r,c,item)
            archived=" (Archiviert)" if p["status"]=="Archiviert" else ""
            self.project_selector.addItem(f'{p["number"]} · {one_line(p["name"])} · {p["site"] or "ohne Baustelle"}{archived}',p["id"])
        self.project_selector.blockSignals(False);self.clear_project()
        self.new_project_button.setEnabled(True)
    def show_project(self):
        self.project_id=self.project_selector.currentData()
        project=self.db.project(self.project_id) if self.project_id else None
        if not project:self.clear_project();return
        self.project_heading.setText(f'{project["number"]} · {project["name"]}')
        self.project_hint.setText(f'{project["site"] or "Keine Baustelle angegeben"} · Status: {ui_status(project["status"])}')
        if self.context_listener:self.context_listener(self.sid(),self.project_id)
        self._build_project_tree();self.preview_frame.setVisible(True);self.edit_project_button.setEnabled(True)
        self.archive_button.setEnabled(True)
        self.archive_button.setText("♻  Wiederherstellen" if project["status"]=="Archiviert" else "📦  Archivieren")
        self.archive_button.setToolTip("Archiviertes Projekt wieder in die normale Liste holen" if project["status"]=="Archiviert"
                                       else "Abgeschlossenes Projekt ausblenden – alle Daten bleiben erhalten")
        self.documents_button.setEnabled(True)
        self.documents_button.setText(f"📄  Dokumente ({len(self.db.project_documents(self.project_id))})")
        self.show_preview("Übersicht")
    def clear_project(self):
        self.project_id=None;self.project_heading.setText("Projekt auswählen");self.project_hint.setText("Danach wird hier auf einen Blick sichtbar, was bereits zu diesem Projekt gehört.")
        self.hide_preview();self.edit_project_button.setEnabled(False);self.archive_button.setEnabled(False)
        self.documents_button.setEnabled(False);self.documents_button.setText("📄  Dokumente")
        self.project_selector.blockSignals(True);self.project_selector.setCurrentIndex(0);self.project_selector.blockSignals(False)
    def _project_invoices(self):
        return [x for x in self.db.invoices() if x["project_id"]==self.project_id]
    def _project_payments(self):
        return self.db.conn.execute("""SELECT pa.*,i.number AS invoice_number FROM payments pa
          JOIN invoices i ON i.id=pa.invoice_id WHERE i.project_id=? ORDER BY pa.payment_date,pa.id""",(self.project_id,)).fetchall()
    def _invoice_amounts(self,invoice):
        paid,discount,adjustment=self.db.payment_totals(invoice["id"]);gross=float(invoice["gross_total"] or 0)
        basis=float(invoice["payable_total"] if invoice["payable_total"] is not None else gross)
        return gross,paid,max(0.0,basis-paid-discount-adjustment)
    def _build_project_tree(self):
        tree=self.project_tree;tree.blockSignals(True);tree.clear()
        def group(module,icon,label,count):
            item=QTreeWidgetItem([f"{icon}  {module} ({label})" if count else f"{icon}  {module} (keine)"])
            item.setData(0,Qt.UserRole,module);item.setData(0,Qt.UserRole+1,None)
            font=item.font(0);font.setBold(True);item.setFont(0,font);tree.addTopLevelItem(item);return item
        def child(parent,module,record_id,text):
            item=QTreeWidgetItem([text]);item.setData(0,Qt.UserRole,module);item.setData(0,Qt.UserRole+1,record_id);parent.addChild(item)
        overview_item=QTreeWidgetItem(["📊  Wirtschaftlicher Stand"])
        overview_item.setData(0,Qt.UserRole,"Übersicht");overview_item.setData(0,Qt.UserRole+1,None)
        font=overview_item.font(0);font.setBold(True);overview_item.setFont(0,font);tree.addTopLevelItem(overview_item)
        offers=self.db.project_offers(self.project_id)
        g=group("Angebote","📋",str(len(offers)),len(offers))
        for x in offers:child(g,"Angebote",x["id"],f'{x["number"]} · {one_line(x["title"]) or "Angebot"}')
        count=len(self.db.measurement_positions(self.project_id))
        group("Aufmaß","📐",f"{count} Positionen",count)
        invoices=self._project_invoices()
        g=group("Rechnungen","🧾",str(len(invoices)),len(invoices))
        for x in invoices:child(g,"Rechnungen",x["id"],f'{x["number"]} · {x["invoice_type"]} · {x["status"]}')
        count=len(self._project_payments())
        group("Zahlungen","💰",f"{count} Buchungen",count)
        count=len(self.db.incoming_invoices(self.project_id))
        group("Eingangsrechnungen","📥",str(count),count)
        count=len(self.db.project_documents(self.project_id))
        group("Dokumente","📄",str(count),count)
        tree.expandAll();tree.blockSignals(False)
    def _fill_preview_table(self,headers,rows,numeric=()):
        """rows: Liste aus (record_id, [Zellen]); Zahlenspalten rechtsbündig."""
        table=self.preview_table;table.clearContents();table.setColumnCount(len(headers));table.setRowCount(len(rows))
        table.setHorizontalHeaderLabels(headers)
        for r,(record_id,cells) in enumerate(rows):
            for c,value in enumerate(cells):
                item=QTableWidgetItem(str(value if value is not None else ""))
                if c in numeric:item.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
                if c==0:item.setData(Qt.UserRole,record_id)
                table.setItem(r,c,item)
        header=table.horizontalHeader();header.setSectionResizeMode(QHeaderView.ResizeToContents)
        if headers:header.setSectionResizeMode(min(1,len(headers)-1),QHeaderView.Stretch)
        table.setVisible(bool(headers))
    def show_preview(self,module):
        """Gruppe im Projektinhalt auswählen (auch für „Zurück“ aus der Hauptleiste)."""
        if not self.project_id:return
        tree=self.project_tree
        for i in range(tree.topLevelItemCount()):
            item=tree.topLevelItem(i)
            if item.data(0,Qt.UserRole)==module or module=="Übersicht" and i==0:
                tree.setCurrentItem(item);self.update_preview();return
    def update_preview(self):
        item=self.project_tree.currentItem()
        if not item or not self.project_id:return
        module=item.data(0,Qt.UserRole);record_id=item.data(0,Qt.UserRole+1);self._preview_module=module
        info="";headers=[];rows=[];numeric=()
        if module=="Übersicht":
            title="Wirtschaftlicher Stand";economics=self.db.project_economics(self.project_id)
            info=project_economics_html(economics);self.economics_chart.set_data(economics)
        elif module=="Eingangsrechnungen":
            title="Eingangsrechnungen";incoming=self.db.incoming_invoices(self.project_id)
            if incoming:
                info=(f'{len(incoming)} Rechnung(en) · <b>Kosten netto: {money(sum(float(x["net_amount"] or 0) for x in incoming))}</b>'
                      f' · noch zu bezahlen (brutto): {money(sum(float(x["gross_amount"] or 0) for x in incoming if not x["paid_date"]))}')
            headers=["Datum","Lieferant","Rechnungs-Nr.","Art","Netto","Brutto","Status"];numeric=(4,5)
            rows=[(x["id"],[de_date(x["invoice_date"]),x["supplier"],x["invoice_no"] or "",x["category"],money(x["net_amount"]),
                            money(x["gross_amount"]),incoming_status(x)]) for x in incoming]
            if not incoming:
                info="Noch keine Eingangsrechnungen. Über „Eingangsrechnungen öffnen“ lassen sich Lieferantenrechnungen zu diesem Projekt erfassen."
        elif module=="Angebote" and record_id is None:
            offers=self.db.project_offers(self.project_id);title="Angebote"
            headers=["Nr.","Bezeichnung","Status","Summe netto"];numeric=(3,)
            rows=[(x["id"],[x["number"],one_line(x["title"]),x["status"],money(self.db.total(x["id"]))]) for x in offers]
        elif module=="Angebote":
            offer=self.db.offer(record_id);title=f'Angebot {offer["number"]}'
            info=f'{one_line(offer["title"]) or "Angebot"} · Status: {offer["status"]} · <b>Summe netto: {money(self.db.total(record_id))}</b>'
            headers=["Pos.","Kurztext","Menge","Einheit","EP","Gesamt"];numeric=(2,4,5)
            for p in self.db.positions(record_id):
                if p["source_type"]=="Textblock":rows.append((None,["",f'[Text] {one_line(p["short_text"])}',"","","",""]))
                else:
                    q=float(p["quantity"] or 0);ep=float(p["unit_price"] or 0)
                    rows.append((None,[p["position_no"],one_line(p["short_text"]),de_num(q),p["unit"],money(ep),money(q*ep)]))
        elif module=="Aufmaß":
            positions=self.db.measurement_positions(self.project_id);title="Aufmaß"
            value=sum(float(p["current_quantity"] or 0)*float(p["unit_price"] or 0) for p in positions)
            info=f'{len(positions)} Positionen · <b>Wert aktuell: {money(value)}</b>' if positions else ""
            headers=["Pos.","Kurztext","Angebotsmenge","Aufmaß aktuell","Abgerechnet","Noch offen","Einheit"];numeric=(2,3,4,5)
            for p in positions:
                current=float(p["current_quantity"] or 0);billed=float(p["billed_quantity"] or 0)
                rows.append((None,[p["position_no"],one_line(p["short_text"]),de_num(p["offer_quantity"] or 0),de_num(current),de_num(billed),de_num(max(0.0,current-billed)),p["unit"]]))
        elif module=="Rechnungen" and record_id is None:
            title="Rechnungen";headers=["Nr.","Typ","Status","Brutto","Bezahlt","Offen","Fällig"];numeric=(3,4,5)
            for x in self._project_invoices():
                gross,paid,open_amount=self._invoice_amounts(x)
                rows.append((x["id"],[x["number"],x["invoice_type"],x["status"],money(gross),money(paid),money(open_amount),de_date(x["due_date"])]))
        elif module=="Rechnungen":
            invoice=self.db.invoice(record_id);title=f'Rechnung {invoice["number"]}'
            gross,paid,open_amount=self._invoice_amounts(invoice)
            payable=float(invoice["payable_total"] if invoice["payable_total"] is not None else gross)
            info=f'{invoice["invoice_type"]} · Status: {invoice["status"]} · erstellt {de_date(invoice["created_at"])} · fällig {de_date(invoice["due_date"]) or "–"}<br>'
            if invoice["deduct_previous"] and invoice["invoice_type"] in ("Teilrechnung","Schlussrechnung"):
                s=self.db.cumulative_invoice_settlement(record_id)
                info+=f'Leistung kumuliert netto {money(s["cumulative_net"])} · '
            else:info+=f'Netto {money(invoice["net_total"] or 0)} · Brutto {money(gross)} · '
            info+=f'Zahlbetrag {money(payable)} · bezahlt {money(paid)} · <b>offen {money(open_amount)}</b>'
            headers=["Pos.","Kurztext","Kumuliert","Zuwachs","Einheit","EP","Gesamt"];numeric=(2,3,5,6)
            rows=[(None,[p["position_no"],one_line(p["short_text"]),de_num(p["cumulative_quantity"] or 0),de_num(p["new_quantity"] or 0),p["unit"],money(p["unit_price"] or 0),money(p["line_total"] or 0)]) for p in self.db.invoice_positions(record_id)]
        elif module=="Zahlungen":
            title="Zahlungen";headers=["Datum","Rechnung","Bezahlt","Skonto","Ausgleich","Begründung"];numeric=(2,3,4)
            rows=[(x["invoice_id"],[de_date(x["payment_date"]),x["invoice_number"],money(x["paid_amount"] or 0),money(x["discount_amount"] or 0),money(x["adjustment_amount"] or 0),one_line(x["adjustment_reason"])]) for x in self._project_payments()]
        else:
            title="Dokumente";headers=["Dokument","Beschreibung","Hinzugefügt"]
            rows=[(x["id"],[x["filename"],one_line(x["description"]),de_date(x["created_at"])]) for x in self.db.project_documents(self.project_id)]
        if not rows and record_id is None and module not in ("Übersicht","Eingangsrechnungen"):info="Für dieses Projekt ist hier noch nichts vorhanden.";headers=[]
        if not rows:headers=[]
        self.economics_chart.setVisible(module=="Übersicht")
        self.preview_title.setText(title);self.preview_info.setText(info);self.preview_info.setVisible(bool(info))
        self._fill_preview_table(headers,rows,numeric);self.update_preview_open_button()
    def hide_preview(self):
        if hasattr(self,"preview_frame"):self.preview_frame.setVisible(False)
    def _open_target(self):
        """(Modul, Datensatz) für „Öffnen“: markierte Vorschauzeile vor Baumeintrag."""
        item=self.project_tree.currentItem() if hasattr(self,"project_tree") else None
        if not item or not self.project_id:return None
        module=item.data(0,Qt.UserRole);record_id=item.data(0,Qt.UserRole+1)
        if module=="Übersicht":return None
        if record_id is None:
            row=self.preview_table.currentRow();cell=self.preview_table.item(row,0) if row>=0 else None
            if cell is not None and cell.data(Qt.UserRole) is not None and self.preview_table.selectionModel().hasSelection():record_id=cell.data(Qt.UserRole)
        if module=="Aufmaß":record_id=self.project_id
        return module,record_id
    def open_preview_item(self):
        target=self._open_target()
        if target and self.module_navigator:self.module_navigator(target[0],self.project_id,target[1])
    def update_preview_open_button(self):
        target=self._open_target() if hasattr(self,"preview_table") else None
        self.preview_open.setEnabled(bool(target))
        if not target:self.preview_open.setText("Öffnen");return
        module,record_id=target;item=self.project_tree.currentItem()
        if module in ("Angebote","Rechnungen") and record_id is not None:
            number=next((self.preview_table.item(r,0).text() for r in range(self.preview_table.rowCount())
                         if self.preview_table.item(r,0) and self.preview_table.item(r,0).data(Qt.UserRole)==record_id),None)
            if item.data(0,Qt.UserRole+1) is not None:number=self.preview_title.text().split(" ",1)[-1]
            self.preview_open.setText(f'{"Angebot" if module=="Angebote" else "Rechnung"} {number} öffnen')
        else:self.preview_open.setText(f"{module} öffnen")
    def add_project(self):
        cid=self.sid()
        if not cid:
            QMessageBox.information(self,"Neues Projekt","Bitte zuerst oben einen Kunden auswählen.");return
        d=ProjectDialog(self.db,self);d.customer.setCurrentIndex(max(0,d.customer.findData(cid)))
        if not d.exec():return
        pid=self.db.add_project(d.data());self._reselect(d.data()[0],pid)
    def edit_project(self):
        pid=self.project_id
        if not pid:
            QMessageBox.information(self,"Projekt bearbeiten","Bitte zuerst ein Projekt auswählen.");return
        project=self.db.project(pid);d=ProjectDialog(self.db,self,project)
        if d.status.findText("Archiviert")<0:d.status.addItem("Archiviert")
        d.status.setCurrentText(project["status"] or "Offen")
        d.delete_requested=False
        def request_delete():
            d.delete_requested=True;d.reject()
        remove=QPushButton("Projekt löschen …");remove.clicked.connect(request_delete)
        d.findChild(QDialogButtonBox).addButton(remove,QDialogButtonBox.DestructiveRole)
        accepted=d.exec()
        if d.delete_requested:
            if QMessageBox.question(self,"Projekt löschen",
                "Projekt wirklich löschen? Diese Funktion ist nur für Fehlanlagen vorgesehen.\n\n"
                "Anders als beim Archivieren werden zugehörige Projektdaten dabei dauerhaft gelöscht.\n"
                "Für echte Projekte bitte stattdessen den Status ‚Archiviert‘ verwenden.",
                QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:return
            self.db.backup("vor_projekt_loeschen");self.db.delete_project(pid);self._reselect(self.sid());return
        if accepted and save_project_data(self,self.db,pid,d.data()):
            self._reselect(d.data()[0],pid)
    def open_documents(self):
        if not self.project_id:return
        pid=self.project_id;module=getattr(self,"_preview_module",None)
        ProjectDocumentsDialog(self.db,pid,self).exec()
        self.show_project()
        if module:self.show_preview(module)

    def _archived_filter_changed(self,*_):
        cid=self.sid()
        if cid:self._reselect(cid,self.project_id)

    def toggle_archive(self):
        pid=self.project_id;project=self.db.project(pid) if pid else None
        if not project:return
        data=(project["customer_id"],project["name"],project["site"] or "",None,project["notes"] or "")
        if project["status"]=="Archiviert":
            restored=project["status_before_archive"] or "Abgeschlossen"
            if save_project_data(self,self.db,pid,data[:3]+(restored,)+data[4:]):
                self._reselect(project["customer_id"],pid)
                self.window().statusBar().showMessage(f'Projekt {project["number"]} ist wiederhergestellt (Status: {restored}).',6000)
            return
        if save_project_data(self,self.db,pid,data[:3]+("Archiviert",)+data[4:]):
            self._reselect(project["customer_id"],pid if self.show_archived.isChecked() else None)
            self.window().statusBar().showMessage(
                f'Projekt {project["number"]} ist archiviert. Über „Archivierte anzeigen“ holst du es wieder hervor.',8000)

    def _reselect(self,customer_id,project_id=None):
        self.customer_selector.blockSignals(True)
        self.customer_selector.setCurrentIndex(max(0,self.customer_selector.findData(customer_id)))
        self.customer_selector.blockSignals(False);self.select_customer(customer_id,project_id)
    def add(self):
        d=CustomerDialog(self)
        if d.exec():
            cid=self.db.add_customer(d.data());self.db.update_customer_einvoice(cid,d.vat_id.text(),d.buyer_reference.text());self.refresh()
    def edit(self):
        cid=self.sid()
        if not cid:
            QMessageBox.information(self,ui("customer_edit"),ui("select_customer_edit"));return
        d=CustomerDialog(self,self.db.customer(cid))
        if d.exec():
            self.db.backup("vor_kunde_bearbeiten")
            self.db.update_customer(cid,d.data());self.db.update_customer_einvoice(cid,d.vat_id.text(),d.buyer_reference.text())
            self.refresh()
            # Den bearbeiteten Kunden wieder auswählen und Details sofort aktualisieren.
            for r in range(self.table.rowCount()):
                it=self.table.item(r,0)
                if it and it.data(Qt.UserRole)==cid:
                    self.table.selectRow(r)
                    self.show()
                    break
    def delete(self):
        cid=self.sid()
        if not cid:return
        ok,n=self.db.delete_customer(cid)
        if not ok:QMessageBox.warning(self,ui("not_possible"),ui("customer_has_projects").format(count=n))
        self.refresh()

def save_project_data(parent,db,pid,data):
    """Projektdaten speichern; Status „Archiviert“ merkt sich den vorherigen
    Status, jeder andere Status holt ein archiviertes Projekt zurück."""
    customer_id,name,site,new,notes=data
    old=db.project(pid)["status"]
    if new=="Archiviert" and old!="Archiviert" and QMessageBox.question(parent,"Projekt archivieren",
        "Das Projekt wird archiviert.\n\n"
        "Alle Angebote, Aufmaße, Rechnungen, Zahlungen und Dokumente bleiben vollständig erhalten.\n\n"
        "Projekt jetzt archivieren?",QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:return False
    db.backup("vor_projekt_bearbeiten")
    db.update_project(pid,(customer_id,name,site,new,notes))
    before=(old if old!="Archiviert" else db.project(pid)["status_before_archive"]) if new=="Archiviert" else None
    db.conn.execute("UPDATE projects SET status_before_archive=? WHERE id=?",(before,pid));db.conn.commit()
    return True

class ProjectsPage(QWidget):
    """Projekt auswählen und seine Stammdaten direkt bearbeiten. LV-Import und
    Angebote aus dem LV gibt es im Modul Angebote."""
    STATUSES=["Offen","In Arbeit","Wartet","Abgeschlossen","Storniert","Archiviert"]
    def __init__(self,db):
        super().__init__();self.db=db;self.selected_project_id=None
        o=QVBoxLayout(self);top=QHBoxLayout()
        t=QLabel("Projektverwaltung");t.setObjectName("pageTitle")
        self.filter=QComboBox();self.filter.addItems(["Aktiv","Abgeschlossen","Archiv","Alle"])
        self.filter.currentTextChanged.connect(self.refresh)
        b=icon_button("new","Neues Projekt hinzufügen",self.add)
        top.addWidget(t);top.addStretch();top.addWidget(QLabel("Ansicht:"));top.addWidget(self.filter);top.addWidget(b);o.addLayout(top)

        choice=QHBoxLayout()
        self.customer_selector=QComboBox();self.customer_selector.setMinimumWidth(320)
        self.customer_selector.currentIndexChanged.connect(self._customer_changed)
        self.project_selector=QComboBox();self.project_selector.setMinimumWidth(420)
        self.project_selector.currentIndexChanged.connect(self._project_changed)
        choice.addWidget(QLabel("Kunde:"));choice.addWidget(self.customer_selector)
        choice.addSpacing(12);choice.addWidget(QLabel("Projekt:"));choice.addWidget(self.project_selector,1);o.addLayout(choice)

        self.form_box=QGroupBox("Projektdaten");form=QFormLayout(self.form_box)
        self.number=QLabel("—");self.customer=QComboBox()
        self.name=QLineEdit();self.site=QLineEdit()
        self.status=QComboBox();self.status.addItems(self.STATUSES)
        self.notes=PlainTextPasteEdit();self.notes.setMinimumHeight(110)
        for label,widget in [("Nr.",self.number),("Kunde *",self.customer),("Projektname *",self.name),
                             ("Baustelle",self.site),("Status",self.status),("Notizen",self.notes)]:form.addRow(label,widget)
        actions=QHBoxLayout()
        self.save_button=icon_button("save","Projektdaten speichern",self.save)
        self.documents_button=QPushButton("📄 Dokumente");self.documents_button.clicked.connect(self.open_documents)
        self.documents_button.setToolTip("Dokumente zu diesem Projekt anzeigen, hinzufügen oder löschen")
        delete=icon_button("delete","Projekt löschen",self.delete)
        actions.addWidget(self.save_button);actions.addWidget(self.documents_button);actions.addStretch();actions.addWidget(delete)
        form.addRow(actions)
        o.addWidget(self.form_box)
        self.empty_hint=QLabel("Bitte oben ein Projekt auswählen oder ein neues Projekt anlegen.");o.addWidget(self.empty_hint)
        o.addStretch()
        self.refresh()

    def sid(self):
        return self.project_selector.currentData()

    def select_project(self,project_id):
        """Von außen (Projektkontext) ein Projekt vorwählen; die Ansicht passt sich an."""
        project=self.db.project(project_id) if project_id else None
        if not project:return
        self.selected_project_id=project_id
        view="Archiv" if project["status"]=="Archiviert" else ("Abgeschlossen" if project["status"]=="Abgeschlossen" else "Aktiv")
        if self.filter.currentText()!="Alle" and self.filter.currentText()!=view:
            self.filter.blockSignals(True);self.filter.setCurrentText(view);self.filter.blockSignals(False)
        self.refresh()

    def refresh(self):
        project_id=self.sid() or self.selected_project_id
        project=self.db.project(project_id) if project_id else None
        customer_id=project["customer_id"] if project else self.customer_selector.currentData()
        customers=self.db.customers()
        self.customer_selector.blockSignals(True);self.customer_selector.clear();self.customer_selector.addItem("Alle Kunden",None)
        for c in customers:self.customer_selector.addItem(f'{c["number"]} · {c["company"]}',c["id"])
        self.customer_selector.setCurrentIndex(max(0,self.customer_selector.findData(customer_id)));self.customer_selector.blockSignals(False)
        self.customer.clear()
        for c in customers:self.customer.addItem(f'{c["number"]} – {c["company"]}',c["id"])
        self._load_projects(project_id)

    def _load_projects(self,project_id=None):
        customer_id=self.customer_selector.currentData()
        rows=[p for p in self.db.projects_search("",self.filter.currentText()) if customer_id is None or p["customer_id"]==customer_id]
        self.project_selector.blockSignals(True);self.project_selector.clear()
        self.project_selector.addItem("Projekt auswählen …" if rows else "Keine Projekte in dieser Ansicht",None)
        for p in rows:
            text=f'{p["number"]} · {one_line(p["name"])}'+("" if customer_id else f' · {one_line(p["company"])}')+f' ({p["status"]})'
            self.project_selector.addItem(text,p["id"])
        index=self.project_selector.findData(project_id) if project_id else -1
        if index<0 and len(rows)==1:index=1
        self.project_selector.setCurrentIndex(max(0,index));self.project_selector.blockSignals(False)
        self._show_project()

    def _customer_changed(self):
        self.selected_project_id=None;self._load_projects()

    def _project_changed(self):
        self.selected_project_id=self.sid();self._show_project()
        project=self.db.project(self.sid()) if self.sid() else None
        window=self.window()
        if project and hasattr(window,"update_context"):window.update_context(project["customer_id"],project["id"])

    def _show_project(self):
        project=self.db.project(self.sid()) if self.sid() else None
        self.form_box.setVisible(project is not None);self.empty_hint.setVisible(project is None)
        if not project:return
        self.number.setText(f'<b>{project["number"]}</b>')
        self.customer.setCurrentIndex(max(0,self.customer.findData(project["customer_id"])))
        self.name.setText(project["name"] or "");self.site.setText(project["site"] or "")
        self.status.setCurrentText(project["status"] or "Offen");self.notes.setPlainText(project["notes"] or "")
        count=len(self.db.project_documents(project["id"]))
        self.documents_button.setText(f"📄 Dokumente ({count})")

    def save(self):
        pid=self.sid()
        if not pid:return
        if not self.name.text().strip():
            QMessageBox.warning(self,"Projekt speichern","Bitte einen Projektnamen eingeben.");return
        old=self.db.project(pid)["status"];new=self.status.currentText()
        if new=="Archiviert" and old!="Archiviert" and QMessageBox.question(self,"Projekt archivieren",
            "Das Projekt wird archiviert und aus der aktiven Projektliste entfernt.\n\n"
            "Alle Angebote, Aufmaße, Rechnungen, Zahlungen und Dokumente bleiben vollständig erhalten.\n\n"
            "Projekt jetzt archivieren?",QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:return
        self.db.backup("vor_projekt_bearbeiten")
        self.db.update_project(pid,(self.customer.currentData(),self.name.text().strip(),self.site.text().strip(),new,
                                    self.notes.toPlainText().strip()))
        # Beim Archivieren den vorherigen Status merken, sonst zurücksetzen.
        before=(old if old!="Archiviert" else self.db.project(pid)["status_before_archive"]) if new=="Archiviert" else None
        self.db.conn.execute("UPDATE projects SET status_before_archive=? WHERE id=?",(before,pid));self.db.conn.commit()
        self.selected_project_id=pid;self.select_project(pid)
        self.window().statusBar().showMessage("Projektdaten gespeichert.",4000)

    def open_documents(self):
        pid=self.sid()
        if not pid:return
        ProjectDocumentsDialog(self.db,pid,self).exec();self._show_project()

    def add(self):
        if not self.db.customers():
            QMessageBox.information(self,"Projekt","Bitte zuerst einen Kunden anlegen.");return
        d=ProjectDialog(self.db,self)
        if self.customer_selector.currentData() is not None:
            d.customer.setCurrentIndex(max(0,d.customer.findData(self.customer_selector.currentData())))
        if d.exec():
            pid=self.db.add_project(d.data());self.select_project(pid);self._project_changed()

    def delete(self):
        pid=self.sid()
        if not pid:return
        if QMessageBox.question(self,"Projekt löschen",
            "Projekt wirklich löschen? Diese Funktion ist nur für Fehlanlagen vorgesehen.\n\n"
            "Anders als beim Archivieren werden zugehörige Projektdaten dabei dauerhaft gelöscht.\n"
            "Für echte Projekte bitte stattdessen den Status ‚Archiviert‘ verwenden.",
            QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            self.db.backup("vor_projekt_loeschen")
            self.db.delete_project(pid);self.selected_project_id=None
            self.project_selector.blockSignals(True);self.project_selector.setCurrentIndex(0);self.project_selector.blockSignals(False)
            self.refresh()

class ServicesCrudPage(QWidget):
    def __init__(self,db):
        super().__init__();self.db=db;self._loading=False
        self._service_editor_row=None;self._service_editor_sid=None
        self._service_category=None;self._service_short=None;self._service_unit=None
        self._service_price=None;self._service_source=None
        o=QVBoxLayout(self);top=QHBoxLayout()
        t=QLabel("Leistungsbibliothek");t.setObjectName("pageTitle")
        self.category=QComboBox();self.category.addItem("Alle Kategorien",None);self.category.currentIndexChanged.connect(self.refresh)
        self.search=QLineEdit();self.search.setPlaceholderText("Leistung, Text oder Quelle suchen …")
        self.search.textChanged.connect(self.refresh)
        top.addWidget(t);top.addStretch();top.addWidget(QLabel("Kategorie:"));top.addWidget(self.category);top.addWidget(self.search);o.addLayout(top)
        actions = QHBoxLayout()
        add = QPushButton("+ Neue Leistung"); add.clicked.connect(self.add)
        edit = QPushButton("Bearbeiten"); edit.clicked.connect(self.edit)
        copy = QPushButton("Kopieren"); copy.clicked.connect(self.copy)

        # Komplett als Text für 100% einheitliche Höhe
        delete = QPushButton("Löschen"); delete.clicked.connect(self.delete)

        self.take_button=QPushButton("➜ Ins Angebot übernehmen");self.take_button.setObjectName("ctaButton")
        self.take_button.clicked.connect(self.take_into_offer);self.take_button.setEnabled(False)
        actions.addWidget(add); actions.addWidget(edit); actions.addWidget(copy); actions.addWidget(delete); actions.addStretch()
        actions.addWidget(self.take_button)
        o.addLayout(actions)
        self.table=QTableWidget(0,7);self.table.setHorizontalHeaderLabels(["Nr.","Kategorie","Kurztext","Einheit","Standard-EP","Quelle","Aktiv"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows);self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # Nur auswählen; gepflegt wird über „Bearbeiten“ (oder Doppelklick).
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers);self.table.doubleClicked.connect(lambda *_:self.edit())
        self.table.itemSelectionChanged.connect(self._update_take_button)
        self.table.setColumnWidth(0,90);self.table.setColumnWidth(1,180);self.table.setColumnWidth(2,520)
        self.table.setColumnWidth(3,90);self.table.setColumnWidth(4,120);self.table.setColumnWidth(5,210);o.addWidget(self.table)
        hint=QLabel("Mehrere Leistungen mit Strg oder Shift markieren und mit „➜ Ins Angebot übernehmen“ in das geöffnete Angebot einfügen. Doppelklick bearbeitet eine Leistung.")
        hint.setWordWrap(True);o.addWidget(hint);self.refresh_categories();self.refresh()
    def sid(self):
        r=self.table.currentRow();return self.table.item(r,0).data(Qt.UserRole) if r>=0 and self.table.item(r,0) else None
    def refresh(self):
        if self._service_editor_row is not None:self.cancel_service_editor()
        if collect_offer_positions(self.db) and hasattr(self,"category"):self.refresh_categories()
        self.table.clearSpans()
        selected=self.sid();self._loading=True
        rows=self.db.services_all(self.search.text(),self.category.currentData());self.table.setRowCount(len(rows))
        for r,x in enumerate(rows):
            vals=[x["number"],x["category"] or "Allgemein",x["short_text"],x["unit"],money(x["sales_price"]),x["source"] or "","Ja" if x["active"] else "Nein"]
            for c,v in enumerate(vals):
                it=QTableWidgetItem(v);it.setData(Qt.UserRole,x["id"]) if c==0 else None
                if c!=6:it.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable)
                self.table.setItem(r,c,it)
            if x["id"]==selected:self.table.selectRow(r)
        self._loading=False
    def selected_service_ids(self):
        rows=sorted({index.row() for index in self.table.selectionModel().selectedRows()})
        return [self.table.item(r,0).data(Qt.UserRole) for r in rows if self.table.item(r,0)]

    def _update_take_button(self):
        count=len(self.selected_service_ids())
        self.take_button.setEnabled(count>0)
        self.take_button.setText(f"➜ Ins Angebot übernehmen ({count})" if count else "➜ Ins Angebot übernehmen")

    def take_into_offer(self):
        ids=self.selected_service_ids();window=self.window();pages=getattr(window,"pages",{})
        offers_page=pages.get("Angebote")
        if not ids or offers_page is None:return
        if not offers_page.current_offer:
            offers=self.db.offers()
            if not offers:
                QMessageBox.information(self,"Ins Angebot übernehmen","Bitte zuerst ein Angebot anlegen.");return
            labels=[f'{o["number"]} · {one_line(o["title"]) or "Angebot"} · {one_line(o["company"])}' for o in offers]
            label,ok=QInputDialog.getItem(self,"Ins Angebot übernehmen","In welches Angebot?",labels,0,False)
            if not ok:return
            offers_page.select_offer_by_id(offers[labels.index(label)]["id"])
        window.navigate(list(pages).index("Angebote"));offers_page.show_view(0)
        count=offers_page.insert_services(ids)
        window.statusBar().showMessage(f"{count} Leistung(en) in Angebot {offers_page.db.offer(offers_page.current_offer)['number']} übernommen.",6000)

    def refresh_categories(self):
        current=self.category.currentData();self.category.blockSignals(True);self.category.clear();self.category.addItem("Alle Kategorien",None)
        for value in self.db.service_categories():self.category.addItem(value,value)
        i=self.category.findData(current);self.category.setCurrentIndex(max(i,0));self.category.blockSignals(False)
    def add(self):
        d=ServiceDialog(self)
        if d.exec():self.db.add_service(d.data());self.refresh_categories();self.refresh()
    def edit(self,*args):
        sid=self.sid()
        if not sid:
            QMessageBox.information(self,"Leistung bearbeiten","Bitte zuerst eine Leistung auswählen.");return
        d=ServiceDialog(self,self.db.service(sid))
        if d.exec():
            self.db.backup("vor_leistung_bearbeiten")
            self.db.update_service(sid,d.data());self.refresh_categories();self.refresh()
    def copy(self):
        sid=self.sid()
        if not sid:
            QMessageBox.information(self,"Leistung kopieren","Bitte zuerst eine Leistung auswählen.");return
        self.db.backup("vor_leistung_kopieren")
        new_sid=self.db.copy_service(sid)
        self.refresh_categories();self.refresh()
        for r in range(self.table.rowCount()):
            it=self.table.item(r,0)
            if it and it.data(Qt.UserRole)==new_sid:
                self.table.selectRow(r);self.table.scrollToItem(it);break
    def inline_changed(self,item):
        if self._loading or item.column()!=6:return
        sid=self.table.item(item.row(),0).data(Qt.UserRole);s=self.db.service(sid)
        if not s:return
        def number(value):return parse_de_number(value)
        try:price=number(self.table.item(item.row(),4).text())
        except ValueError:QMessageBox.warning(self,"Leistung","Standard-EP bitte als Zahl eingeben.");self.refresh();return
        active=self.table.item(item.row(),6).text().strip().lower() in ("ja","1","true","aktiv","x")
        data=(self.table.item(item.row(),2).text().strip(),s["long_text"] or "",self.table.item(item.row(),3).text().strip() or "Stk.",
              s["purchase_price"] or 0,price,s["wage_share"] or 0,s["material_share"] or 0,1 if active else 0,
              self.table.item(item.row(),1).text().strip() or "Allgemein",self.table.item(item.row(),5).text().strip())
        if not data[0]:return
        self.db.update_service(sid,data);self.refresh_categories();self.refresh()
    def _clear_service_editor_state(self):
        self._service_editor_row=None;self._service_editor_sid=None
        self._service_category=None;self._service_short=None;self._service_unit=None
        self._service_price=None;self._service_source=None
    def open_service_editor(self,row,column):
        if self._loading or column not in (1,2,3,4,5):return
        key=self.table.item(row,0);sid=key.data(Qt.UserRole) if key else None
        if not isinstance(sid,int):return
        if self._service_editor_row is not None:
            if self._service_editor_sid==sid:
                if self._service_short:self._service_short.setFocus()
                return
            self.cancel_service_editor()
            for candidate in range(self.table.rowCount()):
                item=self.table.item(candidate,0)
                if item and item.data(Qt.UserRole)==sid:row=candidate;break
        service=self.db.service(sid)
        if not service:return
        self._loading=True
        editor_row=row+1;self.table.insertRow(editor_row)
        self.table.setSpan(editor_row,0,1,self.table.columnCount());self.table.setRowHeight(editor_row,104)
        panel=QFrame();panel.setObjectName("serviceInlineEditor")
        layout=QGridLayout(panel);layout.setContentsMargins(12,8,12,8)
        layout.addWidget(QLabel("Kategorie:"),0,0)
        category=QLineEdit(service["category"] or "Allgemein");category.setMinimumWidth(170);layout.addWidget(category,0,1)
        layout.addWidget(QLabel("Kurztext:"),0,2)
        short=QLineEdit(service["short_text"] or "");short.setMinimumWidth(520);layout.addWidget(short,0,3,1,5)
        layout.addWidget(QLabel("Einheit:"),1,0)
        unit=QComboBox();unit.setEditable(True);unit.addItems(PositionDialog.UNITS)
        unit.setCurrentText((service["unit"] or "Stk.").strip());unit.setMinimumWidth(95);layout.addWidget(unit,1,1)
        layout.addWidget(QLabel("Standard-EP:"),1,2)
        price=QLineEdit(money(service["sales_price"]));price.setAlignment(Qt.AlignRight);price.setMinimumWidth(120);layout.addWidget(price,1,3)
        layout.addWidget(QLabel("Quelle:"),1,4)
        source=QLineEdit(service["source"] or "");source.setMinimumWidth(180);layout.addWidget(source,1,5)
        save=icon_button("save","Leistungsformel speichern");cancel=icon_button("cancel","Bearbeitung abbrechen")
        layout.addWidget(save,1,6);layout.addWidget(cancel,1,7);layout.setColumnStretch(3,1)
        self.table.setCellWidget(editor_row,0,panel)
        self._service_editor_row=editor_row;self._service_editor_sid=sid
        self._service_category=category;self._service_short=short;self._service_unit=unit
        self._service_price=price;self._service_source=source
        for editor in (category,short,price,source,unit.lineEdit()):editor.installEventFilter(self)
        save.clicked.connect(self.save_service_editor);cancel.clicked.connect(self.cancel_service_editor)
        self._loading=False;short.setFocus();short.selectAll()
    def cancel_service_editor(self):
        row=self._service_editor_row
        if row is None:return
        self._loading=True;self.table.clearSpans()
        if row<self.table.rowCount():self.table.removeRow(row)
        self._clear_service_editor_state();self._loading=False
    def save_service_editor(self):
        if not all((self._service_category,self._service_short,self._service_unit,
                    self._service_price,self._service_source)):return
        sid=self._service_editor_sid;service=self.db.service(sid)
        if not service:return
        short=self._service_short.text().strip()
        if not short:
            QMessageBox.warning(self,"Leistung","Bitte einen Kurztext eingeben.")
            self._service_short.setFocus();return
        try:price=parse_de_number(self._service_price.text())
        except ValueError:
            QMessageBox.warning(self,"Leistung","Standard-EP bitte als Zahl eingeben.")
            self._service_price.setFocus();self._service_price.selectAll();return
        data=(short,service["long_text"] or "",self._service_unit.currentText().strip() or "Stk.",
              service["purchase_price"] or 0,price,service["wage_share"] or 0,service["material_share"] or 0,
              service["active"],self._service_category.text().strip() or "Allgemein",self._service_source.text().strip())
        current=(service["short_text"] or "",service["long_text"] or "",service["unit"] or "Stk.",
                 service["purchase_price"] or 0,float(service["sales_price"] or 0),service["wage_share"] or 0,
                 service["material_share"] or 0,service["active"],service["category"] or "Allgemein",service["source"] or "")
        if data==current:self.cancel_service_editor();return
        self.db.backup("vor_inline_leistung_aenderung")
        self.db.update_service(sid,data)
        self.cancel_service_editor();self.refresh_categories();self.refresh()
        for row in range(self.table.rowCount()):
            item=self.table.item(row,0)
            if item and item.data(Qt.UserRole)==sid:self.table.selectRow(row);break
    def eventFilter(self,obj,event):
        editors=(self._service_category,self._service_short,self._service_price,self._service_source)
        unit_editor=self._service_unit.lineEdit() if self._service_unit else None
        if obj in (*editors,unit_editor) and event.type()==QEvent.KeyPress:
            if event.key() in (Qt.Key_Return,Qt.Key_Enter):self.save_service_editor();return True
            if event.key()==Qt.Key_Escape:self.cancel_service_editor();return True
        if obj is self.table and event.type()==QEvent.KeyPress and event.key()==Qt.Key_Tab:
            if self.table.currentColumn()==self.table.columnCount()-1:
                sid=self.db.add_service(("Neue Leistung","","Stk.",0,0,0,0,1,
                    self.category.currentData() or "Allgemein",""));self.refresh_categories();self.refresh()
                for r in range(self.table.rowCount()):
                    if self.table.item(r,0).data(Qt.UserRole)==sid:self.table.setCurrentCell(r,2);self.table.editItem(self.table.item(r,2));break
                return True
        return super().eventFilter(obj,event)
    def delete(self):
        sid=self.sid()
        if not sid:
            QMessageBox.information(self,"Leistung löschen","Bitte zuerst eine Leistung auswählen.");return
        service=self.db.service(sid)
        if QMessageBox.question(self,"Leistung löschen",
            f'Die Leistung „{service["number"]} – {service["short_text"]}“ wirklich löschen?\n\n'
            "Bereits als unabhängige Kopien übernommene Angebotspositionen bleiben erhalten.",
            QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:return
        self.db.backup("vor_leistung_loeschen")
        ok,n=self.db.delete_service(sid)
        if not ok:QMessageBox.warning(self,"Nicht möglich",f"Diese Leistung wird bereits in {n} Angebotsposition(en) verwendet.")
        self.refresh_categories();self.refresh()

class ServiceLibraryDialog(QDialog):
    def __init__(self,db,parent=None):
        super().__init__(parent);self.db=db;self.setWindowTitle("Position aus Leistung übernehmen");self.setMinimumSize(950,620)
        collect_offer_positions(db)
        o=QVBoxLayout(self);filters=QHBoxLayout();self.search=QLineEdit();self.search.setPlaceholderText("Leistung suchen …")
        self.category=QComboBox();self.category.addItem("Alle Kategorien",None)
        for value in db.service_categories():self.category.addItem(value,value)
        self.search.textChanged.connect(self.refresh);self.category.currentIndexChanged.connect(self.refresh)
        self.search.setPlaceholderText("Kurztext, Langtext oder Nummer suchen – eigene Leistungen und alle bisherigen Angebotspositionen")
        filters.addWidget(QLabel("Suche:"));filters.addWidget(self.search);filters.addWidget(QLabel("Kategorie:"));filters.addWidget(self.category);o.addLayout(filters)
        self.table=QTableWidget(0,6);self.table.setHorizontalHeaderLabels(["Auswahl","Nr.","Kategorie","Kurztext","Einheit","Standard-EP"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows);self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setColumnWidth(0,80);self.table.setColumnWidth(1,90);self.table.setColumnWidth(2,180);self.table.setColumnWidth(3,430)
        self.table.cellDoubleClicked.connect(self.toggle);o.addWidget(self.table)
        info=QLabel("Mehrfachauswahl möglich. Die Positionen werden als unabhängige Kopien übernommen; spätere Änderungen an der Bibliothek verändern das Angebot nicht.")
        info.setWordWrap(True);o.addWidget(info)
        bb=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel);bb.button(QDialogButtonBox.Ok).setText("Ausgewählte Positionen übernehmen")
        bb.accepted.connect(self.validate);bb.rejected.connect(self.reject);o.addWidget(bb);self.refresh()
    def refresh(self):
        checked=set(self.selected_ids());rows=self.db.services_all(self.search.text(),self.category.currentData(),True);self.table.setRowCount(len(rows))
        for r,x in enumerate(rows):
            check=QTableWidgetItem();check.setFlags(Qt.ItemIsEnabled|Qt.ItemIsUserCheckable|Qt.ItemIsSelectable);check.setCheckState(Qt.Checked if x["id"] in checked else Qt.Unchecked);check.setData(Qt.UserRole,x["id"]);self.table.setItem(r,0,check)
            for c,v in enumerate([x["number"],x["category"] or "Allgemein",x["short_text"],x["unit"],money(x["sales_price"])] ,1):self.table.setItem(r,c,QTableWidgetItem(str(v or "")))
    def toggle(self,row,column):
        it=self.table.item(row,0);it.setCheckState(Qt.Unchecked if it.checkState()==Qt.Checked else Qt.Checked)
    def selected_ids(self):
        return [self.table.item(r,0).data(Qt.UserRole) for r in range(self.table.rowCount()) if self.table.item(r,0) and self.table.item(r,0).checkState()==Qt.Checked]
    def validate(self):
        if not self.selected_ids():QMessageBox.information(self,"Leistungsbibliothek","Bitte mindestens eine Leistung auswählen.");return
        self.accept()


def ods_number(value):
    s=str(value or "").strip().replace("€","").replace("\xa0","").replace(" ","")
    if not s:return None
    if "," in s:
        s=s.replace(".","").replace(",",".")
    try:return float(s)
    except:return None

PDF_POSITION_RE=re.compile(r"^(\d+)\.\.\s*(\d+)\s+([\d.]+,\d{3})\s+(\S+)\s+(.+)$")
PDF_PRICE_RE=re.compile(r"^(\d{1,3}(?:\.\d{3})*,\d{2})\s+(\d{1,3}(?:\.\d{3})*,\d{2})$")
PDF_PAGE_HEADER_RE=re.compile(r"^Akkordauftrag:.*(?:Seite:\s*\d+)?.*Datum:")

def read_pdf_offer_positions(path):
    """Liest textbasierte LVs im wiederkehrenden Spaltenformat der Referenz-PDF."""
    document=QPdfDocument()
    error=document.load(str(path))
    if error!=QPdfDocument.Error.None_:
        raise ValueError("Die PDF-Datei konnte nicht geöffnet werden.")
    try:
        pages=[document.getAllText(page).text() for page in range(document.pageCount())]
    finally:
        document.close()
    plain="".join(pages).strip()
    if len(plain)<100:
        raise ValueError(
            "Die PDF enthält keinen ausreichend auslesbaren Text. "
            "Vermutlich handelt es sich um einen Scan; dafür wäre OCR-Texterkennung erforderlich."
        )

    positions=[];headings=[];current=None
    current_title_no="";current_title_text=""
    ignored_prefixes=("Position Menge EH Montagetext", "Summe:", "Summe (Netto)")
    unit_map={"m2":"m²","m3":"m³","St":"Stk.","Stk":"Stk."}

    def finish_position(unit_price,total):
        nonlocal current
        current["unit_price"]=unit_price;current["source_total"]=total
        current["long_text"]="\n".join(current.pop("description_lines")).strip()
        current["short_text"]=current["short_text"].strip()
        calculated=round(current["quantity"]*unit_price+1e-9,2)
        current["total_matches"]=abs(calculated-total)<=0.02
        positions.append(current);current=None

    for page_text in pages:
        for raw_line in page_text.replace("\r","\n").splitlines():
            line=" ".join(raw_line.replace("\xa0"," ").split()).strip()
            if not line:continue
            if PDF_PAGE_HEADER_RE.match(line) or line.startswith(ignored_prefixes):continue

            match=PDF_POSITION_RE.match(line)
            if match:
                if current is not None:
                    raise ValueError(
                        f"Bei Position {current['position_no']} wurden Einzel- und Gesamtpreis nicht erkannt."
                    )
                section,item,qty_text,unit,short=match.groups()
                if not current_title_no or current_title_no!=section:
                    current_title_no=section
                current={
                    "position_no":f"{section}.{int(item)}",
                    "quantity":ods_number(qty_text),
                    "unit":unit_map.get(unit,unit),
                    "short_text":short,
                    "description_lines":[short],
                    "title_no":current_title_no,"title_text":current_title_text,
                    "subtitle_no":"","subtitle_text":"",
                }
                continue

            price_match=PDF_PRICE_RE.match(line)
            if current is not None and price_match:
                unit_price=ods_number(price_match.group(1));total=ods_number(price_match.group(2))
                finish_position(unit_price,total);continue

            section_match=re.match(r"^(\d+)\s+([^\d].+)$",line)
            if current is None and section_match:
                number,text=section_match.groups()
                if not any(h["number"]==number for h in headings):
                    current_title_no=number;current_title_text=text
                    headings.append({"number":number,"text":text,"level":"Titel",
                        "title_no":number,"title_text":text,"subtitle_no":"","subtitle_text":""})
                continue

            if current is not None:current["description_lines"].append(line)

    if current is not None:
        raise ValueError(f"Bei Position {current['position_no']} fehlt der abschließende Preis.")
    if not positions:
        raise ValueError(
            "Es wurden keine Positionen im erwarteten PDF-LV-Format erkannt. "
            "Benötigt werden Position, Menge, Einheit, Beschreibung, Einzelpreis und Gesamtpreis."
        )
    return positions,headings

def _xlsx_rows(path):
    """Alle Zeilen aller Tabellenblätter einer .xlsx-Datei als Textlisten."""
    main="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    tag=lambda name:"{%s}%s"%(main,name)
    with zipfile.ZipFile(path,"r") as z:
        names=z.namelist();shared=[]
        if "xl/sharedStrings.xml" in names:
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(tag("si")):
                shared.append("".join(t.text or "" for t in si.iter(tag("t"))))
        sheets=sorted((n for n in names if re.fullmatch(r"xl/worksheets/sheet\d+\.xml",n)),
                      key=lambda n:int(re.search(r"(\d+)\.xml$",n).group(1)))
        rows=[]
        for name in sheets:
            for row in ET.fromstring(z.read(name)).iter(tag("row")):
                vals={};next_col=0
                for cell in row.findall(tag("c")):
                    letters=re.match(r"[A-Z]+",cell.attrib.get("r",""))
                    col=next_col
                    if letters:
                        col=0
                        for ch in letters.group(0):col=col*26+ord(ch)-64
                        col-=1
                    next_col=col+1
                    kind=cell.attrib.get("t","");v=cell.find(tag("v"))
                    if kind=="s" and v is not None:text=shared[int(v.text)]
                    elif kind=="inlineStr":text="".join(t.text or "" for t in cell.iter(tag("t")))
                    else:text=v.text if v is not None and v.text else ""
                    vals[col]=" ".join(str(text).split())
                if vals:rows.append([vals.get(i,"") for i in range(max(vals)+1)])
    return rows

def _lv_positions_from_rows(rows):
    """Gleiche Spaltenlogik wie beim ODS-LV: Pos., Menge, Einheit, Beschreibung, EP."""
    positions=[];headings=[]
    current_title_no="";current_title_text="";current_subtitle_no="";current_subtitle_text=""
    for vals in rows:
        vals=list(vals)+[""]*(7-len(vals))
        pos,qty_txt,unit,desc,price_txt=[str(v) for v in vals[0:5]]
        pos=pos.strip();unit=unit.strip();desc=desc.strip()
        qty=ods_number(qty_txt);price=ods_number(price_txt)
        if pos and qty is not None and unit and desc and price is not None:
            short=desc if len(desc)<=90 else desc[:87].rstrip()+"..."
            positions.append({"position_no":pos,"quantity":qty,"unit":unit,"short_text":short,"long_text":desc,
                "unit_price":price,"title_no":current_title_no,"title_text":current_title_text,
                "subtitle_no":current_subtitle_no,"subtitle_text":current_subtitle_text})
        elif pos and desc and qty is None and price is None:
            if pos.count(".")==0:
                current_title_no=pos;current_title_text=desc;current_subtitle_no="";current_subtitle_text="";level="Titel"
            else:
                current_subtitle_no=pos;current_subtitle_text=desc;level="Untertitel"
            headings.append({"number":pos,"text":desc,"level":level,"title_no":current_title_no,"title_text":current_title_text,
                "subtitle_no":current_subtitle_no,"subtitle_text":current_subtitle_text})
    return positions,headings

def read_lv_offer_positions(path):
    suffix=Path(path).suffix.lower()
    if suffix==".pdf":
        positions,headings=read_pdf_offer_positions(path);return positions,headings,"PDF"
    if suffix==".ods":
        positions,headings=read_ods_offer_positions(path);return positions,headings,"ODS"
    if suffix==".xlsx":
        positions,headings=_lv_positions_from_rows(_xlsx_rows(path));return positions,headings,"Excel"
    if suffix==".xls":
        raise ValueError("Das alte Excel-Format .xls wird nicht unterstützt. Bitte die Datei in Excel oder LibreOffice als .xlsx oder .ods speichern.")
    raise ValueError("Unterstützt werden ODS-, Excel- (.xlsx) und textbasierte PDF-Dateien.")

def read_ods_offer_positions(path):
    """Liest ODS-LVs und erhält Titel / Untertitel als Gliederung."""
    ns={
      "office":"urn:oasis:names:tc:opendocument:xmlns:office:1.0",
      "table":"urn:oasis:names:tc:opendocument:xmlns:table:1.0",
      "text":"urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    }
    with zipfile.ZipFile(path,"r") as z:
        root=ET.fromstring(z.read("content.xml"))

    positions=[];headings=[]
    current_title_no="";current_title_text=""
    current_subtitle_no="";current_subtitle_text=""

    for sheet in root.findall(".//table:table",ns):
        for row in sheet.findall("table:table-row",ns):
            vals=[]
            for cell in row.findall("table:table-cell",ns):
                rep=int(cell.attrib.get("{%s}number-columns-repeated"%ns["table"],"1"))
                txt=" ".join("".join(cell.itertext()).split())
                vals.extend([txt]*min(rep,20))
            vals += [""]*(7-len(vals))
            pos,qty_txt,unit,desc,price_txt=vals[0:5]
            pos=pos.strip();unit=unit.strip();desc=desc.strip()
            qty=ods_number(qty_txt);price=ods_number(price_txt)

            if pos and qty is not None and unit and desc and price is not None:
                short=desc if len(desc)<=90 else desc[:87].rstrip()+"..."
                positions.append({
                    "position_no":pos,"quantity":qty,"unit":unit,
                    "short_text":short,"long_text":desc,"unit_price":price,
                    "title_no":current_title_no,"title_text":current_title_text,
                    "subtitle_no":current_subtitle_no,"subtitle_text":current_subtitle_text
                })
            elif pos and desc and qty is None and price is None:
                # Überschriften ohne Menge/EP: 01 = Titel, 01.01 = Untertitel.
                dot_count=pos.count(".")
                if dot_count==0:
                    current_title_no=pos;current_title_text=desc
                    current_subtitle_no="";current_subtitle_text=""
                    level="Titel"
                else:
                    current_subtitle_no=pos;current_subtitle_text=desc
                    level="Untertitel"
                headings.append({
                    "number":pos,"text":desc,"level":level,
                    "title_no":current_title_no,"title_text":current_title_text,
                    "subtitle_no":current_subtitle_no,"subtitle_text":current_subtitle_text
                })
    return positions,headings

class ODSImportDialog(QDialog):
    def __init__(self, positions, parent=None, used=None):
        super().__init__(parent)
        self.positions=positions
        self.setWindowTitle("LV-Positionen prüfen")
        self.resize(1050,620)
        l=QVBoxLayout(self)
        info=QLabel(
            "Erkannte Positionen aus der LV-Datei. Haken entfernen, wenn eine Position "
            "nicht übernommen werden soll. Der vollständige Beschreibungstext wird als Langtext gespeichert."
        )
        info.setWordWrap(True);l.addWidget(info)
        self.table=QTableWidget(len(positions),8)
        self.table.setHorizontalHeaderLabels(["Übernehmen","Titel","Pos.","Menge","Einheit","Beschreibung","EP","Gesamt"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        for r,p in enumerate(positions):
            chk=QTableWidgetItem("")
            chk.setFlags(Qt.ItemIsEnabled|Qt.ItemIsUserCheckable)
            # Schon in einem Angebot dieses Projekts verwendete Positionen starten
            # beim Nachtrag abgewählt.
            chk.setCheckState(Qt.Unchecked if used and used[r] else Qt.Checked)
            self.table.setItem(r,0,chk)
            group=" / ".join(x for x in [p.get("title_no",""),p.get("subtitle_no","")] if x)
            for c,v in enumerate([
                group,p["position_no"],de_num(p["quantity"],3),p["unit"],
                p["long_text"],money(p["unit_price"]),money(p.get("source_total",p["quantity"]*p["unit_price"]))
            ],1):
                it=QTableWidgetItem(str(v))
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r,c,it)
        self.table.setColumnWidth(0,90);self.table.setColumnWidth(1,120);self.table.setColumnWidth(2,90)
        self.table.setColumnWidth(3,100);self.table.setColumnWidth(4,80)
        self.table.setColumnWidth(5,430);self.table.setColumnWidth(6,105);self.table.setColumnWidth(7,115)
        if used is not None:
            # Direkt neben dem Haken, weil sie beim Anhaken gebraucht wird.
            self.table.insertColumn(1);self.table.setHorizontalHeaderItem(1,QTableWidgetItem("Bereits in Angebot"))
            for r,text in enumerate(used):
                it=QTableWidgetItem(text or "");it.setFlags(it.flags() & ~Qt.ItemIsEditable);self.table.setItem(r,1,it)
            self.table.setColumnWidth(1,140)
            info.setText(info.text()+" Positionen, die schon in einem Angebot dieses Projekts stehen, sind zunächst nicht angehakt.")
        l.addWidget(self.table)
        self.summary=QLabel();l.addWidget(self.summary)
        allrow=QHBoxLayout()
        a=QPushButton("Alle auswählen");a.clicked.connect(lambda:self.set_all(True))
        n=QPushButton("Keine auswählen");n.clicked.connect(lambda:self.set_all(False))
        allrow.addWidget(a);allrow.addWidget(n);allrow.addStretch();l.addLayout(allrow)
        bb=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText("Ausgewählte übernehmen")
        bb.accepted.connect(self.accept);bb.rejected.connect(self.reject);l.addWidget(bb)
        self.update_summary()
        self.table.itemChanged.connect(self.update_summary)

    def set_all(self, checked):
        self.table.blockSignals(True)
        for r in range(self.table.rowCount()):
            self.table.item(r,0).setCheckState(Qt.Checked if checked else Qt.Unchecked)
        self.table.blockSignals(False);self.update_summary()

    def update_summary(self,*_):
        selected=sum(1 for r in range(self.table.rowCount())
                     if self.table.item(r,0).checkState()==Qt.Checked)
        total=sum(self.positions[r]["quantity"]*self.positions[r]["unit_price"]
                  for r in range(len(self.positions))
                  if self.table.item(r,0).checkState()==Qt.Checked)
        self.summary.setText(f"<b>Ausgewählt: {selected} Position(en) · Netto: {money(total)}</b>")

    def selected_positions(self):
        return [p for r,p in enumerate(self.positions)
                if self.table.item(r,0).checkState()==Qt.Checked]

def _lv_used_in_offers(db,project_id,positions):
    """Pro LV-Position: Angebotsnummern dieses Projekts, in denen sie schon steht
    (Abgleich über Positionsnummer und Kurztext)."""
    used={}
    for row in db.conn.execute("""SELECT o.number,op.position_no,op.short_text FROM offer_positions op
      JOIN offers o ON o.id=op.offer_id WHERE o.project_id=?""",(project_id,)).fetchall():
        key=(str(row["position_no"] or "").strip(),one_line(row["short_text"]))
        used.setdefault(key,[])
        if row["number"] not in used[key]:used[key].append(row["number"])
    return [", ".join(used.get((str(p["position_no"] or "").strip(),one_line(p["short_text"])),[])) for p in positions]

def _stored_lv_positions(db,project_id):
    return [{"position_no":p["position_no"],"short_text":p["short_text"],"long_text":p["long_text"] or "",
             "quantity":float(p["quantity"] or 0),"unit":p["unit"] or "","unit_price":float(p["source_unit_price"] or 0),
             "title_no":p["title_no"] or "","title_text":p["title_text"] or "",
             "subtitle_no":p["subtitle_no"] or "","subtitle_text":p["subtitle_text"] or ""}
            for p in db.project_lv_positions(project_id)]

def pick_lv_positions(parent,db,project_id):
    """LV-Positionen für ein Angebot auswählen: aus dem im Projekt gespeicherten
    LV oder aus einer neuen LV-Datei (die dann im Projekt gespeichert wird).
    Liefert (Positionen, Quelle) oder (None, None)."""
    stored=_stored_lv_positions(db,project_id)
    use_file=True
    if stored:
        sources=", ".join(dict.fromkeys(p["source_name"] for p in db.project_lv_positions(project_id)))
        box=QMessageBox(parent);box.setWindowTitle("LV-Quelle wählen")
        box.setText(f"Für dieses Projekt ist bereits ein LV gespeichert ({len(stored)} Positionen).\n\nDatei: {sources}")
        saved_btn=box.addButton("Gespeichertes LV verwenden",QMessageBox.AcceptRole)
        file_btn=box.addButton("Neue LV-Datei …",QMessageBox.ActionRole)
        box.addButton("Abbrechen",QMessageBox.RejectRole);box.exec()
        if box.clickedButton()==saved_btn:use_file=False
        elif box.clickedButton()!=file_btn:return None,None
    if use_file:
        path,_=QFileDialog.getOpenFileName(parent,"LV-Datei auswählen","",
            "LV-Dateien (*.ods *.xlsx *.pdf);;ODS-Dateien (*.ods);;Excel-Dateien (*.xlsx);;PDF-Dateien (*.pdf)")
        if not path:return None,None
        try:
            positions,headings,source_type=read_lv_offer_positions(path)
        except Exception as e:
            QMessageBox.warning(parent,"LV-Import",f"Die LV-Datei konnte nicht gelesen werden.\n\n{e}");return None,None
        if not positions:
            QMessageBox.information(parent,"LV-Import",
                "Es wurden keine importierbaren Positionen erkannt.\n\n"
                "Erwartet werden Position, Menge, Einheit, Beschreibung und Einzelpreis.");return None,None
        # Das komplette LV im Projekt speichern (für Nachträge); dieselbe Datei
        # ersetzt eine frühere Fassung statt sie zu verdoppeln.
        db.backup("vor_projekt_lv_import")
        db.conn.execute("DELETE FROM project_lv_sources WHERE project_id=? AND source_name=?",(project_id,Path(path).name))
        db.import_project_lv(project_id,Path(path).name,positions)
    else:
        positions,source_type=stored,"LV"
    dlg=ODSImportDialog(positions,parent,used=_lv_used_in_offers(db,project_id,positions))
    if not dlg.exec():return None,None
    selected=dlg.selected_positions()
    return (selected,source_type) if selected else (None,None)

class OfferDialog(QDialog):
    def __init__(self, db, parent=None, row=None):
        super().__init__(parent)
        self.row=row
        self.setWindowTitle("Angebot bearbeiten" if row else "Neues Angebot")
        self.setMinimumSize(720,430)
        f=QFormLayout(self)
        f.setHorizontalSpacing(18);f.setVerticalSpacing(12)
        self.project=QComboBox()
        for p in db.projects():
            label=f'{one_line(p["number"])} – {one_line(p["name"])}'
            self.project.addItem(label,p["id"])
            self.project.setItemData(self.project.count()-1,
                f'Kunde: {one_line(p["company"])}' + (f'\nBaustelle: {one_line(p["site"])}' if p["site"] else ""),Qt.ToolTipRole)
        self.project.setMinimumWidth(500)
        self.project_info=QLabel();self.project_info.setWordWrap(True)
        self.title=QLineEdit()
        self.title.setPlaceholderText("z. B. Trockenbauarbeiten Erdgeschoss")
        self.status=QComboBox();self.status.addItems(["Entwurf","Versendet","Beauftragt","Abgelehnt","Storniert"])
        self.notes=QTextEdit();self.notes.setPlaceholderText("Optionale interne Hinweise zum Angebot …")
        self.notes.setMinimumHeight(120)

        f.addRow("Projekt *",self.project)
        f.addRow("",self.project_info)
        f.addRow("Bezeichnung",self.title)
        f.addRow("Status",self.status)
        f.addRow("Notizen",self.notes)

        if row:
            self.project.setCurrentIndex(max(self.project.findData(row["project_id"]),0))
            self.title.setText(row["title"] or "")
            self.status.setCurrentIndex(max(self.status.findText(row["status"] or "Entwurf"),0))
            self.notes.setPlainText(row["notes"] or "")

        self.project.currentIndexChanged.connect(lambda *_:self.update_project_info(db))
        self.update_project_info(db)

        bb=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept);bb.rejected.connect(self.reject);f.addRow(bb)

    def update_project_info(self,db):
        p=db.project(self.project.currentData()) if self.project.currentData() else None
        if not p:self.project_info.setText("Kein Projekt ausgewählt.");return
        details=[f'<b>Kunde:</b> {p["company"]}']
        if p["site"]:details.append(f'<b>Baustelle:</b> {p["site"]}')
        self.project_info.setText(" &nbsp;&nbsp; · &nbsp;&nbsp; ".join(details))

class PositionDialog(QDialog):
    UNITS = ["Stk.","m","m²","m³","lfm","Std.","Tag","kg","t","pauschal"]
    def __init__(self, db, oid, parent=None, row=None, measurement_location=None):
        super().__init__(parent)
        self.db=db
        self.setWindowTitle("Position bearbeiten" if row else "Neue Angebotsposition")
        self.setMinimumWidth(620)
        f=QFormLayout(self)
        self.service=QComboBox(); self.service.addItem("— Leistung auswählen —", None)
        for s in db.services():
            self.service.addItem(f'{s["number"]} – {s["short_text"]}', s["id"])
        self.pos=QLineEdit(row["position_no"] if row else db.next_pos(oid))
        self.title_no=QLineEdit();self.title_no.setPlaceholderText("z. B. 01")
        self.title_text=QLineEdit();self.title_text.setPlaceholderText("z. B. Wände")
        self.subtitle_no=QLineEdit();self.subtitle_no.setPlaceholderText("z. B. 01.01")
        self.subtitle_text=QLineEdit();self.subtitle_text.setPlaceholderText("z. B. Metallständerwände")
        self.short=QLineEdit()
        self.location=QLineEdit() if measurement_location is not None else None
        if self.location is not None:
            self.location.setPlaceholderText("z. B. Raum 201, Erdgeschoss oder Treppenhaus")
            self.location.setText(measurement_location or "")
        self.long=PlainTextPasteEdit()
        self.formula=QLineEdit(); self.formula.setPlaceholderText("z. B. 111*10*0,5")
        self.qty=QDoubleSpinBox(); self.qty.setDecimals(3); self.qty.setMaximum(999999999)
        self.unit=QComboBox(); self.unit.setEditable(True);self.unit.addItems(self.UNITS)
        self.price=QDoubleSpinBox(); self.price.setDecimals(2); self.price.setMaximum(99999999); self.price.setSuffix(" €")
        self.result=QLabel("Formelergebnis: —")

        self.service.currentIndexChanged.connect(self.load_service)
        self.formula.textChanged.connect(self.calc)

        fields=[("Leistung",self.service),("Titel-Nr.",self.title_no),("Titel",self.title_text),
                    ("Untertitel-Nr.",self.subtitle_no),("Untertitel",self.subtitle_text),
                    ("Positionsnummer",self.pos),("Kurztext *",self.short)]
        if self.location is not None:fields.append(("Raum / Ort",self.location))
        fields += [
                    ("Langtext",self.long),("Formel / Mengenermittlung",self.formula),("",self.result),
                    ("Menge",self.qty),("Einheit",self.unit),("Einheitspreis",self.price)]
        for a,b in fields:
            f.addRow(a,b)

        if row:
            i=self.service.findData(row["service_id"]); self.service.setCurrentIndex(max(i,0))
            self.title_no.setText(row["title_no"] or "")
            self.title_text.setText(row["title_text"] or "")
            self.subtitle_no.setText(row["subtitle_no"] or "")
            self.subtitle_text.setText(row["subtitle_text"] or "")
            self.short.setText(row["short_text"] or "")
            self.long.setPlainText(row["long_text"] or "")
            self.formula.setText(row["formula"] or "")
            self.qty.setValue(row["quantity"] or 0)
            i=self.unit.findText(row["unit"] or "Stk."); self.unit.setCurrentIndex(max(i,0))
            self.price.setValue(row["unit_price"] or 0)

        bb=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        bb.accepted.connect(self.validate); bb.rejected.connect(self.reject)
        f.addRow(bb)

    def load_service(self):
        sid=self.service.currentData()
        if not sid:return
        s=self.db.service(sid)
        self.short.setText(s["short_text"] or "")
        self.long.setPlainText(s["long_text"] or "")
        i=self.unit.findText(s["unit"] or "Stk."); self.unit.setCurrentIndex(max(i,0))
        self.price.setValue(s["sales_price"] or 0)

    def calc(self):
        if not self.formula.text().strip():
            self.result.setText("Formelergebnis: —"); return
        try:
            q=eval_formula(self.formula.text())
            self.qty.setValue(q)
            self.result.setText(f"Formelergebnis: {de_num(q,3)}")
        except:
            self.result.setText("Formelergebnis: Formel prüfen")

    def validate(self):
        if not self.short.text().strip():
            QMessageBox.warning(self,"Pflichtfeld","Bitte Kurztext eintragen."); return
        if self.formula.text().strip():
            try:self.qty.setValue(eval_formula(self.formula.text()))
            except Exception as e:
                QMessageBox.warning(self,"Formel",str(e)); return
        self.accept()

    def data(self):
        data=(
            self.service.currentData(),self.pos.text().strip(),self.short.text().strip(),
            self.long.toPlainText().strip(),self.formula.text().strip(),self.qty.value(),
            self.unit.currentText(),self.price.value(),
            self.title_no.text().strip(),self.title_text.text().strip(),
            self.subtitle_no.text().strip(),self.subtitle_text.text().strip()
        )
        return data+((self.location.text().strip(),) if self.location is not None else ())


class OfferTextDialog(QDialog):
    def __init__(self,parent=None,row=None):
        super().__init__(parent);self.setWindowTitle("Textblock bearbeiten" if row else "Textblock hinzufügen")
        self.setMinimumSize(650,430);f=QFormLayout(self)
        self.heading=QLineEdit(row["short_text"] if row else "");self.heading.setPlaceholderText("Optional, z. B. Vorbemerkung")
        self.text=PlainTextPasteEdit(row["long_text"] if row else "");self.text.setPlaceholderText("Freien Angebotstext eingeben …")
        self.page_break=QCheckBox("Nach diesem Textblock eine neue Seite beginnen")
        self.page_break.setChecked(bool(row and (row["formula"] or "")=="Seitenumbruch"))
        f.addRow("Überschrift",self.heading);f.addRow("Text *",self.text);f.addRow("",self.page_break)
        info=QLabel("Der Textblock verändert die Angebotssumme nicht.");info.setWordWrap(True);f.addRow("",info)
        bb=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        bb.accepted.connect(self.validate);bb.rejected.connect(self.reject);f.addRow(bb)
    def validate(self):
        if not self.text.toPlainText().strip():QMessageBox.warning(self,"Textblock","Bitte einen Text eingeben.");return
        self.accept()
    def data(self):return self.heading.text().strip(),self.text.toPlainText().strip(),self.page_break.isChecked()


class ExternalODSOfferDialog(QDialog):
    def __init__(self,db,source_path,position_count,parent=None):
        super().__init__(parent);self.db=db
        self.setWindowTitle("Externes LV-Angebot zuordnen")
        self.setMinimumWidth(650)
        f=QFormLayout(self)

        source=QLabel(Path(source_path).name)
        source.setWordWrap(True)
        count=QLabel(f"<b>{position_count} erkannte Position(en)</b>")

        self.project=QComboBox()
        for p in db.projects_search(""):
            self.project.addItem(f'{p["number"]} – {p["name"]} – {p["company"]}',p["id"])

        self.title=QLineEdit(Path(source_path).stem)
        self.notes=QTextEdit()
        self.notes.setPlaceholderText("Optionaler Hinweis zum importierten Angebot …")

        f.addRow("Datei",source)
        f.addRow("Erkannt",count)
        f.addRow("Kunde / Projekt *",self.project)
        f.addRow("Bezeichnung",self.title)
        f.addRow("Notizen",self.notes)

        info=QLabel(
            "Das externe Dokument wird einem vorhandenen Aufmaßwerk-Projekt zugeordnet. "
            "Die Aufmaßwerk-Angebotsnummer wird automatisch aus dem Nummernkreis vergeben."
        )
        info.setWordWrap(True);f.addRow("",info)

        bb=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText("Angebot anlegen")
        bb.accepted.connect(self.validate);bb.rejected.connect(self.reject);f.addRow(bb)

    def validate(self):
        if self.project.currentIndex()<0:
            QMessageBox.warning(self,"Projekt fehlt",
                "Bitte zuerst einen Kunden und ein Projekt in Aufmaßwerk anlegen.")
            return
        self.accept()

    def data(self):
        return self.project.currentData(),self.title.text().strip(),self.notes.toPlainText().strip()

class TabAwareDelegate(QStyledItemDelegate):
    """Zellbearbeitung wie gewohnt; Tab ruft zusätzlich `prepare(row, column)` auf
    (vor dem Speichern) und führt die zurückgegebene Aktion danach aus."""
    def __init__(self,prepare,parent=None):
        super().__init__(parent);self.prepare=prepare;self._cell=None
    def createEditor(self,parent,option,index):
        self._cell=(index.row(),index.column());editor=super().createEditor(parent,option,index)
        if editor is not None:editor.setObjectName("cellEditor")
        return editor
    def updateEditorGeometry(self,editor,option,index):
        editor.setGeometry(option.rect)
    def eventFilter(self,editor,event):
        if event.type()==QEvent.KeyPress and event.key() in (Qt.Key_Tab,Qt.Key_Backtab) and self._cell:
            action=self.prepare(*self._cell,event.key()==Qt.Key_Backtab)
            # Kurz warten, bis Qt den eigenen Feldwechsel abgeschlossen hat.
            if action:QTimer.singleShot(40,action)
        return super().eventFilter(editor,event)

class UnitItemDelegate(QStyledItemDelegate):
    def __init__(self,units,parent=None):
        super().__init__(parent);self.units=list(units)
    def createEditor(self,parent,option,index):
        editor=QComboBox(parent);editor.setObjectName("cellEditor");editor.setEditable(True);editor.addItems(self.units)
        def chosen(*_):
            self.commitData.emit(editor)
            self.closeEditor.emit(editor,QAbstractItemDelegate.NoHint)
        editor.activated.connect(chosen)
        editor.lineEdit().editingFinished.connect(lambda:self.commitData.emit(editor))
        editor.installEventFilter(self);editor.lineEdit().installEventFilter(self)
        return editor
    def updateEditorGeometry(self,editor,option,index):
        editor.setGeometry(option.rect)
    def eventFilter(self,obj,event):
        if event.type()==QEvent.KeyPress and event.key() in (Qt.Key_Tab,Qt.Key_Backtab):
            editor=obj if isinstance(obj,QComboBox) else obj.parent()
            if isinstance(editor,QComboBox):
                self.commitData.emit(editor)
                self.closeEditor.emit(editor,QAbstractItemDelegate.EditPreviousItem if event.key()==Qt.Key_Backtab
                                      else QAbstractItemDelegate.EditNextItem)
                return True
        # Nur die Klappliste selbst ist der registrierte Editor; ihr inneres
        # Textfeld darf keine Fokus-Ereignisse an die Standardbehandlung geben.
        if not isinstance(obj,QComboBox):return False
        return super().eventFilter(obj,event)
    def setEditorData(self,editor,index):
        value=str(index.data(Qt.EditRole) or "")
        editor.setCurrentText(value)
    def setModelData(self,editor,model,index):
        model.setData(index,editor.currentText().strip(),Qt.EditRole)

class OffersPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db=db;self.current_offer=None;self._loading_offer_positions=False
        self._offer_formula_editor_row=None;self._offer_formula_editor_pid=None
        self._offer_formula_input=None;self._offer_formula_result=None;self._offer_formula_save=None
        self._offer_formula_unit=None;self._offer_formula_price=None
        self._offer_editor_fields={};self._offer_editor_new=False;self._inline_backup_offer=None

        o=QVBoxLayout(self)
        top=QHBoxLayout()
        t=QLabel("Angebot & Aufmaß");t.setObjectName("pageTitle")
        new=QPushButton("+ Neues Angebot");new.clicked.connect(self.new_offer)
        new.setToolTip("Neues Angebot für ein vorhandenes Projekt anlegen")
        new = QPushButton("+ Neues Angebot")
        new_menu=QMenu(new);new_menu.addAction("Leeres Angebot …",self.new_offer)
        new_menu.addAction("Aus LV (gespeichert oder neue Datei) …",self.new_offer_from_lv);new.setMenu(new_menu)
        new.setToolTip("Neues Angebot anlegen: leer oder aus dem LV des Projekts")
        new.setObjectName("ctaButton")  # <--- Diese Zeile kommt genau hier neu dazu!
        # Der Knopf steht bewusst direkt bei der Überschrift. Bei schmaleren
        # Fenstern darf er nicht mehr hinter dem breiten Positionsbereich nach
        # rechts aus dem sichtbaren Ausschnitt rutschen.
        top.addWidget(t);top.addWidget(new);top.addStretch();o.addLayout(top)

        # Kompakte Angebotsauswahl: Die grosse Tabelle wird nur bei Bedarf gezeigt.
        sp=QSplitter(Qt.Vertical)
        self.offer_splitter=sp

        upper=QWidget()
        ul=QVBoxLayout(upper)
        ul.setContentsMargins(0,0,0,0)

        summary_row=QHBoxLayout()
        self.offer_summary=compact_hint("Bitte ein Angebot auswählen.")
        self.offer_summary.setObjectName("offerSummary");self.offer_summary.setWordWrap(False)
        self.offer_summary.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.toggle_offers_btn=QPushButton("Angebotsauswahl anzeigen ▾")
        self.toggle_offers_btn.setObjectName("subtleButton")
        self.toggle_offers_btn.clicked.connect(self.toggle_offer_list)
        # Angebotsauswahl als Klappliste; die (unsichtbare) Tabelle bleibt Datenquelle.
        self.offer_summary.setVisible(False);self.toggle_offers_btn.setVisible(False)
        self.offer_selector=QComboBox();self.offer_selector.setMinimumWidth(520)
        self.offer_selector.currentIndexChanged.connect(self._offer_selector_changed)
        summary_row.addWidget(QLabel("Angebot:"));summary_row.addWidget(self.offer_selector,1)
        ul.addLayout(summary_row)

        self.offers=QTableWidget(0,5)
        self.offers.setHorizontalHeaderLabels(["Nr.","Projekt","Kunde","Bezeichnung","Status"])
        self.offers.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.offers.setSelectionMode(QAbstractItemView.SingleSelection)
        self.offers.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.offers.itemSelectionChanged.connect(self.select_offer)
        self.offers.doubleClicked.connect(self.edit_offer)
        self.offers.setColumnWidth(0,90)
        self.offers.setColumnWidth(1,250)
        self.offers.setColumnWidth(2,270)
        self.offers.setColumnWidth(3,310)
        self.offers.setColumnWidth(4,100)
        ul.addWidget(self.offers)
        self.offers.setVisible(False)

        offer_buttons = QHBoxLayout()

        edit_offer_btn = QPushButton("Bearbeiten"); edit_offer_btn.clicked.connect(self.edit_offer)
        delete_offer_btn = QPushButton("Löschen"); delete_offer_btn.clicked.connect(self.delete_offer)
        preview_offer_btn = QPushButton("Vorschau"); preview_offer_btn.clicked.connect(self.preview_offer_pdf)
        output_top = QPushButton("Ausgeben"); output_top.clicked.connect(self.output_offer)
        email_top = QPushButton("E-Mail"); email_top.clicked.connect(self.send_offer_email)

        offer_buttons.addWidget(edit_offer_btn); offer_buttons.addWidget(delete_offer_btn)
        offer_buttons.addWidget(preview_offer_btn); offer_buttons.addWidget(output_top)
        # Steuerausweis vor dem Versand wählen; gilt für Anzeige, PDF und ODT.
        self.tax_selector=QComboBox()
        self.tax_selector.addItem("mit MwSt.","Normale Umsatzsteuer")
        self.tax_selector.addItem("§ 13b – nur netto (Steuerschuldnerschaft)","Steuerschuldnerschaft §13b")
        self.tax_selector.setToolTip("Wie die Angebotssumme ausgewiesen wird")
        self.vat_rate=QDoubleSpinBox();self.vat_rate.setRange(0,100);self.vat_rate.setDecimals(1)
        self.vat_rate.setSuffix(" %");self.vat_rate.setValue(19);self.vat_rate.setMinimumWidth(90)
        self.vat_rate.setToolTip("MwSt.-Satz; bei 0 % steht im Angebot nur die Nettosumme")
        self.tax_selector.currentIndexChanged.connect(self._tax_changed);self.vat_rate.valueChanged.connect(self._tax_changed)
        tax_label=QLabel("Steuer:");vat_label=QLabel("MwSt.:")
        offer_buttons.addSpacing(16);offer_buttons.addWidget(tax_label);offer_buttons.addWidget(self.tax_selector)
        offer_buttons.addWidget(vat_label);offer_buttons.addWidget(self.vat_rate)
        # Im Aufmaß-Reiter gelten Vorschau/Ausgeben fürs Aufmaß; der Rest nur fürs Angebot.
        self.preview_button=preview_offer_btn;self.output_button=output_top
        self.offer_only_widgets=[edit_offer_btn,delete_offer_btn,tax_label,self.tax_selector,vat_label,self.vat_rate]
        offer_buttons.addStretch()

        ul.addLayout(offer_buttons)
        views=QHBoxLayout();views.setSpacing(0)
        self.view_offer_btn=QPushButton("📋  Angebotspositionen");self.view_measure_btn=QPushButton("📐  Aufmaßpositionen")
        for index,button in enumerate((self.view_offer_btn,self.view_measure_btn)):
            button.setCheckable(True);button.setMinimumHeight(34);button.setMinimumWidth(210)
            button.setStyleSheet("QPushButton:checked{font-weight:bold;border-bottom:3px solid palette(highlight);}")
            button.clicked.connect(lambda _checked=False,i=index:self.show_view(i));views.addWidget(button)
        self.add_measure_combo=QComboBox();self.add_measure_combo.setMinimumWidth(460)
        self.add_measure_combo.setToolTip("Angebotsposition ins Aufmaß holen; danach gleich die erste Aufmaßzeile erfassen")
        self.add_measure_combo.activated.connect(self._add_to_measurement);self.add_measure_combo.setVisible(False)
        views.addSpacing(16);views.addWidget(self.add_measure_combo)
        self.view_offer_btn.setChecked(True);views.addStretch();ul.addLayout(views)

        lower=QGroupBox("Angebotspositionen")
        ll=QVBoxLayout(lower)
        ll.setSpacing(3)

        self.meta=compact_hint("Bitte ein Angebot auswählen.")
        ll.addWidget(self.meta)

        self.pos=QTableWidget(0,8)
        self.pos.setHorizontalHeaderLabels(
            ["Pos.","Kurztext","Formel / Mengenermittlung","Menge","Einheit","EP","Gesamt","Quelle"])
        self.pos.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.pos.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.pos.setEditTriggers(QAbstractItemView.SelectedClicked|QAbstractItemView.DoubleClicked|QAbstractItemView.EditKeyPressed|QAbstractItemView.AnyKeyPressed)
        # Langtext und Titel über „Bearbeiten“ oder Rechtsklick.
        self.pos.setContextMenuPolicy(Qt.CustomContextMenu);self.pos.customContextMenuRequested.connect(self._position_menu)
        self.pos_tab_delegate=TabAwareDelegate(self._prepare_offer_tab,self.pos)
        self.pos.itemSelectionChanged.connect(self.show_position_detail)
        self.pos.itemChanged.connect(self.inline_offer_position_changed)
        for column in (0,1,2,3,5):self.pos.setItemDelegateForColumn(column,self.pos_tab_delegate)
        self.pos.installEventFilter(self)
        self.unit_delegate=UnitItemDelegate(PositionDialog.UNITS,self.pos)
        self.pos.setItemDelegateForColumn(4,self.unit_delegate)
        self.pos.setColumnWidth(0,90)
        self.pos.setColumnWidth(1,390)
        self.pos.setColumnWidth(2,280)
        self.pos.setColumnWidth(3,105)
        self.pos.setColumnWidth(4,80)
        self.pos.setColumnWidth(5,110)
        self.pos.setColumnWidth(6,125)
        self.pos.setColumnWidth(7,90)
        row = QHBoxLayout()

        add = QPushButton("+ Position"); add.clicked.connect(self.add_position)
        add_text = QPushButton("+ Textblock"); add_text.clicked.connect(self.add_text_block)
        service = QPushButton("Aus Leistung"); service.clicked.connect(self.import_services)
        ods = QPushButton("Aus LV (PDF / ODS / Excel)"); ods.clicked.connect(self.import_ods)
        edit = QPushButton("Bearbeiten"); edit.clicked.connect(self.edit_position)
        copy = QPushButton("Kopieren"); copy.clicked.connect(self.copy_offer_position)
        move_up = QPushButton("↑ Hoch"); move_up.clicked.connect(lambda: self.move_position(-1))
        move_down = QPushButton("↓ Runter"); move_down.clicked.connect(lambda: self.move_position(1))
        subset = QPushButton("Als Angebot"); subset.clicked.connect(self.create_offer_from_selected_positions)
        delete = QPushButton("Löschen"); delete.clicked.connect(self.delete_position)

        self.total = QLabel("<b>Angebotssumme netto: 0,00 €</b>")

        row.addWidget(add); row.addWidget(add_text); row.addWidget(service)
        row.addWidget(ods); row.addWidget(edit); row.addWidget(copy)
        row.addWidget(move_up); row.addWidget(move_down); row.addWidget(subset)
        row.addWidget(delete)

        row.addStretch()
        row.addWidget(self.total, 0, Qt.AlignRight | Qt.AlignVCenter)
        table_area=QWidget()
        table_layout=QVBoxLayout(table_area)
        table_layout.setContentsMargins(0,0,0,0)
        table_layout.addWidget(self.pos,1)
        table_layout.addLayout(row)

        # Die Positionsdetails teilen sich den verfügbaren Platz mit der Tabelle.
        # Auf kleinen Displays startet der Bereich bewusst kompakt, kann aber mit
        # dem Trenner vergrößert oder über die Schaltfläche eingeklappt werden.
        self.position_splitter=QSplitter(Qt.Vertical)
        self.position_splitter.setChildrenCollapsible(False)
        # Der Bereich bleibt mit der Maus höhenverstellbar, der Trenner selbst
        # soll in den kompakten Angebotsaktionen jedoch nicht als Linie auffallen.
        self.position_splitter.setStyleSheet("QSplitter::handle { background: transparent; }")
        self.position_splitter.addWidget(table_area)

        self.detail_area=QWidget()
        self.detail_area.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Ignored)
        detail_area_layout=QVBoxLayout(self.detail_area)
        detail_area_layout.setContentsMargins(0,0,0,0)
        detail_header=QHBoxLayout()
        detail_title=QLabel("Ausgewählte Position")
        detail_title.setObjectName("sectionTitle")
        self.toggle_position_detail_btn=QPushButton("Details ausblenden ▴")
        self.toggle_position_detail_btn.setObjectName("subtleButton")
        self.toggle_position_detail_btn.setToolTip(
            "Den Detailbereich der ausgewählten Angebotsposition ein- oder ausblenden")
        self.toggle_position_detail_btn.setAccessibleName("Positionsdetails ein- oder ausblenden")
        self.toggle_position_detail_btn.clicked.connect(self.toggle_position_detail)
        detail_header.addWidget(detail_title)
        detail_header.addStretch()
        detail_header.addWidget(self.toggle_position_detail_btn)
        detail_area_layout.addLayout(detail_header)

        self.detail_box=QGroupBox()
        self.detail_box.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Ignored)
        dl=QVBoxLayout(self.detail_box)
        dl.setContentsMargins(10,6,10,6)
        self.position_detail=QLabel("Position auswählen, um Kurz-/Langtext und Mengenermittlung vollständig zu sehen.")
        self.position_detail.setWordWrap(True)
        self.position_detail.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.position_detail.setAlignment(Qt.AlignTop|Qt.AlignLeft)
        self.position_detail.setMargin(3)
        detail_scroll=QScrollArea()
        detail_scroll.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Ignored)
        detail_scroll.setWidgetResizable(True)
        detail_scroll.setFrameShape(QFrame.NoFrame)
        detail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        detail_scroll.setWidget(self.position_detail)
        dl.addWidget(detail_scroll)
        detail_area_layout.addWidget(self.detail_box,1)

        self.position_help_text=(
            "Ein Klick auf Kurztext, Formel, Menge, Einheit oder EP öffnet die große Bearbeitungsleiste. Die vollständige Bearbeitung "
            "ist über „Position bearbeiten“ erreichbar. Mehrere Positionen können mit Strg/Shift markiert "
            "und mit „Auswahl als neues Angebot“ als Teil-/Nachtragsangebot im gleichen Projekt kopiert werden."
        )
        self.position_help_label=QLabel("Bedienhinweise")
        self.position_help_label.setObjectName("detailHelp")
        self.position_help_label.setToolTip(self.position_help_text)
        self.position_help_label.setAccessibleName("Bedienhinweise zu Angebotspositionen")
        self.position_help_label.setAccessibleDescription(self.position_help_text)
        detail_area_layout.addWidget(self.position_help_label)

        self.position_splitter.addWidget(self.detail_area)
        self.position_splitter.setStretchFactor(0,1)
        self.position_splitter.setStretchFactor(1,0)
        self.position_splitter.setSizes([620,135])
        ll.addWidget(self.position_splitter,1)

        self.detail_settings=QSettings(
            str(DATA_ROOT / "settings" / "window.ini"),QSettings.IniFormat)
        saved_detail_state=self.detail_settings.value("offers/positionDetailSplitter")
        if saved_detail_state:
            QTimer.singleShot(0,lambda:self.position_splitter.restoreState(saved_detail_state))
        else:
            QTimer.singleShot(0,lambda:self.position_splitter.setSizes([620,135]))
        details_visible=self.detail_settings.value(
            "offers/positionDetailsVisible",True,type=bool)
        if not details_visible:
            QTimer.singleShot(0,lambda:self.set_position_detail_visible(False))
        self.position_splitter.splitterMoved.connect(self.save_position_detail_state)
        # Der Detailbereich ist durch das Bearbeitungsfeld unter der Position ersetzt.
        self.detail_area.setVisible(False)

        self.view_stack=QStackedWidget();self.view_stack.addWidget(lower)
        self.measurement=MeasurementsPage(self.db);self.measurement.set_embedded();self.view_stack.addWidget(self.measurement)
        self.measurement.on_changed=self._refresh_measure_combo
        sp.addWidget(upper)
        sp.addWidget(self.view_stack)
        sp.setSizes([130,760])
        o.addWidget(sp)
        self.refresh()

    def _total_text(self,oid):
        offer=self.db.offer(oid) if oid else None
        if not offer:return "<b>Angebotssumme netto: 0,00 €</b>"
        parts=[f"{text}: <b>{amount}</b>" if bold else f"{text}: {amount}"
               for text,amount,bold in offer_tax_lines(offer,self.db.total(oid)) if amount]
        if (offer["tax_mode"] or "").startswith("Steuerschuldnerschaft"):parts.append("(§ 13b)")
        return " · ".join(parts)

    def _sync_tax_selector(self,oid):
        offer=self.db.offer(oid)
        if not offer:return
        reverse=(offer["tax_mode"] or "").startswith("Steuerschuldnerschaft")
        rate=float(offer["vat_rate"] if offer["vat_rate"] is not None else 19)
        self.tax_selector.blockSignals(True);self.tax_selector.setCurrentIndex(1 if reverse else 0);self.tax_selector.blockSignals(False)
        self.vat_rate.blockSignals(True);self.vat_rate.setValue(rate);self.vat_rate.setEnabled(not reverse);self.vat_rate.blockSignals(False)

    def _tax_changed(self):
        if not self.current_offer:return
        mode=self.tax_selector.currentData();rate=self.vat_rate.value()
        self.vat_rate.setEnabled(not mode.startswith("Steuerschuldnerschaft"))
        self.db.conn.execute("UPDATE offers SET tax_mode=?,vat_rate=? WHERE id=?",(mode,rate,self.current_offer))
        self.db.conn.commit();self.total.setText(self._total_text(self.current_offer))

    def show_view(self,index):
        """0 = Angebotspositionen, 1 = Aufmaßpositionen des gewählten Angebots."""
        if index==1:
            if not self.current_offer:
                QMessageBox.information(self,"Aufmaß","Bitte zuerst oben ein Angebot auswählen.")
                index=0
            else:
                self._finish_editor_silently()
                self.measurement.show_offer(self.db.offer(self.current_offer)["project_id"],self.current_offer)
        self.view_stack.setCurrentIndex(index)
        self.view_offer_btn.setChecked(index==0);self.view_measure_btn.setChecked(index==1)
        self.add_measure_combo.setVisible(index==1)
        for widget in self.offer_only_widgets:widget.setVisible(index==0)
        self.preview_button.setText("Aufmaß-Vorschau" if index==1 else "Vorschau")
        self.output_button.setText("Aufmaß ausgeben" if index==1 else "Ausgeben")
        if index==1:self._refresh_measure_combo()

    def _refresh_measure_combo(self):
        combo=getattr(self,"add_measure_combo",None)
        if combo is None:return
        combo.blockSignals(True);combo.clear()
        offer=self.db.offer(self.current_offer) if self.current_offer else None
        rows=self.db.available_offer_positions(offer["project_id"],offer["id"]) if offer else []
        rows=[r for r in rows if (r["source_type"] or "").strip()!="Textblock"]
        combo.addItem("➕  Angebotsposition zum Aufmaß hinzufügen …" if rows else "Alle Angebotspositionen sind im Aufmaß",None)
        model=combo.model();last_title=None
        for r in rows:
            title=((r["title_no"] or "").strip(),(r["title_text"] or "").strip())
            if any(title) and title!=last_title:
                combo.addItem(f"── Titel {title[0]} · {title[1]} ──".replace(" ·  ──"," ──"),None)
                model.item(combo.count()-1).setEnabled(False);last_title=title
            short=one_line(r["short_text"]);short=short if len(short)<=70 else short[:67]+"…"
            combo.addItem(f'   {r["position_no"]} · {short}  ({de_num(r["quantity"],3)} {r["unit"]})',r["id"])
        if len(rows)>1:combo.addItem(f"   Alle übrigen übernehmen ({len(rows)})","all")
        combo.setEnabled(bool(rows));combo.setCurrentIndex(0);combo.blockSignals(False)

    def _add_to_measurement(self,index):
        data=self.add_measure_combo.itemData(index)
        offer=self.db.offer(self.current_offer) if self.current_offer else None
        if data is None or not offer:
            self.add_measure_combo.setCurrentIndex(0);return
        project_id=offer["project_id"];me=self.measurement
        if data=="all":
            rows=[r for r in self.db.available_offer_positions(project_id,offer["id"]) if (r["source_type"] or "").strip()!="Textblock"]
            if QMessageBox.question(self,"Aufmaß",f"Alle {len(rows)} übrigen Positionen dieses Angebots ins Aufmaß übernehmen?",
                                    QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:
                self.add_measure_combo.setCurrentIndex(0);return
            self.db.backup("vor_aufmass_uebernahme")
            for r in rows:self.db.add_measurement_position(project_id,r["id"])
            me.load_project();return
        self.db.backup("vor_aufmass_uebernahme")
        self.db.add_measurement_position(project_id,data)
        mp=self.db.conn.execute("SELECT id FROM measurement_positions WHERE project_id=? AND offer_position_id=?",
                                (project_id,data)).fetchone()
        me.load_project()
        if not mp:return
        # Gleich die erste Aufmaßzeile erfassen (Raum / Ort, Formel).
        for row in range(me.positions.rowCount()):
            item=me.positions.item(row,0)
            if item and item.data(Qt.UserRole)==mp["id"] and item.data(Qt.UserRole+1) is None:
                me.positions.setCurrentCell(row,3);me.positions.scrollToItem(item);me.positions.editItem(me.positions.item(row,3));break

    def open_measurement(self,project_id):
        """Von außen (Kunden, Dashboard) direkt ins Aufmaß eines Projekts springen."""
        row=self.db.conn.execute("""SELECT o.id FROM offers o JOIN offer_positions op ON op.offer_id=o.id
          JOIN measurement_positions mp ON mp.offer_position_id=op.id WHERE o.project_id=?
          ORDER BY o.id LIMIT 1""",(project_id,)).fetchone()
        offers=self.db.project_offers(project_id)
        oid=row["id"] if row else (offers[-1]["id"] if offers else None)
        if oid is None:
            QMessageBox.information(self,"Aufmaß","Für dieses Projekt gibt es noch kein Angebot.");return
        self.select_offer_by_id(oid);self.show_view(1)

    def send_email_for_current_view(self):
        if self.view_stack.currentIndex()==1:self.measurement.send_measurement_email()
        else:self.send_offer_email()

    def _offer_selector_changed(self):
        oid=self.offer_selector.currentData()
        if oid is not None:self.select_offer_by_id(oid)

    def save_position_detail_state(self,*_):
        if self.detail_box.isVisible():
            self.detail_settings.setValue(
                "offers/positionDetailSplitter",self.position_splitter.saveState())
            self.detail_settings.sync()

    def set_position_detail_visible(self,visible):
        self.detail_box.setVisible(visible)
        self.position_help_label.setVisible(visible)
        self.toggle_position_detail_btn.setText(
            "Details ausblenden ▴" if visible else "Details anzeigen ▾")
        self.detail_settings.setValue("offers/positionDetailsVisible",visible)
        if visible:
            state=self.detail_settings.value("offers/positionDetailSplitter")
            if state:self.position_splitter.restoreState(state)
            else:self.position_splitter.setSizes([620,135])
        else:
            self.position_splitter.setSizes([1,36])
        self.detail_settings.sync()

    def toggle_position_detail(self):
        self.set_position_detail_visible(not self.detail_box.isVisible())

    def toggle_offer_list(self):
        expanded=not self.offers.isVisible();self.offers.setVisible(expanded)
        self.toggle_offers_btn.setText(
            "Angebotsauswahl ausblenden ▴" if expanded else "Angebotsauswahl anzeigen ▾")
        self.offer_splitter.setSizes([300,590] if expanded else [130,760])

    def collapse_offer_list(self):
        if self.offers.isVisible():
            self.offers.setVisible(False)
            self.toggle_offers_btn.setText("Angebotsauswahl anzeigen ▾")
            self.offer_splitter.setSizes([130,760])

    def refresh(self, preserve_selection=True):
        self._finish_editor_silently()
        self._clear_offer_formula_editor_state()
        self.pos.clearSpans()
        selected_offer = self.offer_id() if preserve_selection else None
        if selected_offer is None:
            selected_offer = self.current_offer
        rows=self.db.offers()
        context_project_id=getattr(self,"context_project_id",None)
        if context_project_id is not None:
            rows=[row for row in rows if row["project_id"]==context_project_id]
        self.offers.blockSignals(True)
        self.offers.setRowCount(len(rows))
        for r,x in enumerate(rows):
            vals=[x["number"],f'{x["project_number"]} – {x["project_name"]}',x["company"],x["title"] or "",x["status"]]
            for c,v in enumerate(vals):
                it=QTableWidgetItem(v)
                if c==0: it.setData(Qt.UserRole,x["id"])
                if c in (1,2,3):it.setToolTip(v)
                self.offers.setItem(r,c,it)
        self.offers.blockSignals(False)
        self.offer_selector.blockSignals(True);self.offer_selector.clear()
        self.offer_selector.addItem("Angebot auswählen …" if rows else "Keine Angebote vorhanden",None)
        for x in rows:
            self.offer_selector.addItem(f'{x["number"]} · {one_line(x["title"]) or "Angebot"} · '
                f'{x["project_number"]} – {one_line(x["company"])} ({x["status"]})',x["id"])
        self.offer_selector.blockSignals(False)
        self.current_offer=None
        self.pos.setRowCount(0)
        self.meta.setText("Bitte ein Angebot auswählen.")
        self.offer_summary.setText("Bitte ein Angebot auswählen.")
        self.position_detail.setText("Position auswählen, um Kurz-/Langtext und Mengenermittlung vollständig zu sehen.")
        self.total.setText("<b>Angebotssumme netto: 0,00 €</b>")
        if selected_offer is not None:
            self.select_offer_by_id(selected_offer)
        elif self.offers.rowCount()==1:
            # QTableWidget kann nach dem Neuaufbau die erste Zeile optisch als
            # aktuellen Datensatz darstellen, ohne itemSelectionChanged erneut
            # auszulösen. Daher Auswahl und Detailbereich explizit synchronisieren.
            only_id=self.offers.item(0,0).data(Qt.UserRole)
            self.select_offer_by_id(only_id)

    def select_offer_by_id(self,oid):
        for r in range(self.offers.rowCount()):
            it=self.offers.item(r,0)
            if it and it.data(Qt.UserRole)==oid:
                self.offers.selectRow(r)
                self.select_offer()
                return

    def refresh_and_select(self,oid=None):
        self.refresh(preserve_selection=False)
        if oid is None:
            return
        for r in range(self.offers.rowCount()):
            it=self.offers.item(r,0)
            if it and it.data(Qt.UserRole)==oid:
                self.offers.selectRow(r)
                self.select_offer()
                break

    def offer_id(self):
        r=self.offers.currentRow()
        return self.offers.item(r,0).data(Qt.UserRole) if r>=0 and self.offers.item(r,0) else None

    def pos_id(self):
        r=self.pos.currentRow()
        value=self.pos.item(r,0).data(Qt.UserRole) if r>=0 and self.pos.item(r,0) else None
        return value if isinstance(value,int) else None

    def show_position_detail(self):
        pid=self.pos_id()
        if not pid:
            self.position_detail.setText(
                "Position auswählen, um Kurz-/Langtext und Mengenermittlung vollständig zu sehen."
            )
            return
        p=self.db.position(pid)
        if not p:return
        if (p["source_type"] or "").strip()=="Textblock":
            heading=f'<b>{p["short_text"]}</b><br><br>' if (p["short_text"] or "").strip() else ""
            page='<br><br><i>Neue Seite danach</i>' if (p["formula"] or "")=="Seitenumbruch" else ""
            self.position_detail.setText(heading+(p["long_text"] or "").replace("\n","<br>")+page);return
        line_total=float(p["quantity"] or 0)*float(p["unit_price"] or 0)
        parts=[
            f'<b>Pos. {p["position_no"]}</b> · Quelle: {p["source_type"] or "Manuell"}',
            f'<b>{p["short_text"] or ""}</b>'
        ]
        longtext=(p["long_text"] or "").strip()
        if longtext and longtext!=(p["short_text"] or "").strip():
            parts.append(longtext)
        if (p["formula"] or "").strip():
            parts.append(f'<b>Mengenermittlung:</b> {p["formula"]}')
        parts.append(
            f'<b>Menge:</b> {de_num(p["quantity"],3)} {p["unit"]} &nbsp;&nbsp; '
            f'<b>EP:</b> {money(p["unit_price"])} &nbsp;&nbsp; '
            f'<b>Gesamt:</b> {money(line_total)}'
        )
        self.position_detail.setText("<br><br>".join(parts))

    def select_offer(self):
        oid=self.offer_id()
        if not oid:return
        self._finish_editor_silently()
        self.pos.clearSpans()
        self.current_offer=oid
        self.offer_selector.blockSignals(True)
        self.offer_selector.setCurrentIndex(max(0,self.offer_selector.findData(oid)));self.offer_selector.blockSignals(False)
        self._sync_tax_selector(oid)
        x=self.db.offer(oid)
        compact=" · ".join(filter(None,[f'Angebot {x["number"]}',
            f'Projekt {x["project_number"]}',one_line(x["company"]),one_line(x["title"] or "")]))
        self.offer_summary.setText(f"<b>{compact}</b>");self.offer_summary.setToolTip(compact)
        self.collapse_offer_list()
        self.meta.setText(
            f'<b>Angebot {x["number"]}</b> · {x["status"]} &nbsp;&nbsp; '
            f'<b>Projekt:</b> {x["project_number"]} – {x["project_name"]}'
            f'{" · Baustelle: "+x["site"] if x["site"] else ""}<br>'
            f'<b>Kunde:</b> {x["company"]}'
            f'{" &nbsp;&nbsp; <b>Bezeichnung:</b> "+x["title"] if x["title"] else ""}'
        )

        self._loading_offer_positions=True
        rows=self.db.positions(oid)
        display=[];last_title=None;last_sub=None
        for p in rows:
            if (p["source_type"] or "").strip()=="Textblock":
                display.append(("text",p));last_title=None;last_sub=None;continue
            tno,tt,sno,st=lv_group_values(p)
            if tno and (tno,tt)!=last_title:
                title_children=[q["id"] for q in rows if lv_group_values(q)[0]==tno]
                title_sum=sum(float(q["quantity"] or 0)*float(q["unit_price"] or 0)
                              for q in rows if lv_group_values(q)[0]==tno)
                display.append(("title",tno,tt,title_sum,title_children))
                last_title=(tno,tt);last_sub=None
            if sno and (sno,st)!=last_sub:
                sub_children=[q["id"] for q in rows if lv_group_values(q)[2]==sno]
                sub_sum=sum(float(q["quantity"] or 0)*float(q["unit_price"] or 0)
                            for q in rows if lv_group_values(q)[2]==sno)
                display.append(("subtitle",sno,st,sub_sum,sub_children))
                last_sub=(sno,st)
            display.append(("position",p))

        self.pos.setRowCount(len(display))
        for r,item in enumerate(display):
            if item[0]=="text":
                p=item[1];vals=["TEXT",p["short_text"] or "Textblock","Neue Seite danach" if (p["formula"] or "")=="Seitenumbruch" else "","","","","","Textblock"]
                for c,v in enumerate(vals):
                    it=QTableWidgetItem(str(v or ""));it.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable)
                    if c==0:it.setData(Qt.UserRole,p["id"])
                    if c==1:it.setToolTip(p["long_text"] or "")
                    f=it.font();f.setItalic(True);it.setFont(f);self.pos.setItem(r,c,it)
                continue
            if item[0] in ("title","subtitle"):
                kind,num,text,subtotal,child_ids=item
                label=("TITEL " if kind=="title" else "  Untertitel ")+num
                vals=[label,text,"","","","",money(subtotal),""]
                for c,v in enumerate(vals):
                    it=QTableWidgetItem(str(v or ""))
                    f=it.font();f.setBold(True);it.setFont(f)
                    it.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable)
                    if c==0:it.setData(Qt.UserRole,child_ids)
                    if c==1:
                        it.setToolTip(
                            "Diese Gliederungszeile kann markiert werden. "
                            "Bei „Auswahl als neues Angebot“ werden alle zugehörigen Positionen kopiert."
                        )
                    self.pos.setItem(r,c,it)
                continue

            p=item[1]
            line_total=float(p["quantity"] or 0)*float(p["unit_price"] or 0)
            vals=[p["position_no"],p["short_text"],p["formula"] or "",de_num(p["quantity"],3),p["unit"],
                  money(p["unit_price"]),money(line_total),p["source_type"] or "Manuell"]
            for c,v in enumerate(vals):
                it=QTableWidgetItem(str(v or ""))
                if c==0:it.setData(Qt.UserRole,p["id"])
                it.setFlags(Qt.ItemIsEnabled|Qt.ItemIsSelectable|(Qt.ItemIsEditable if c<=5 else Qt.NoItemFlags))
                if c==1:
                    tno,tt,sno,st=lv_group_values(p)
                    it.setToolTip(p["long_text"] or p["short_text"] or "")
                self.pos.setItem(r,c,it)

        self.position_detail.setText(
            "Position auswählen, um Kurz-/Langtext und Mengenermittlung vollständig zu sehen."
        )
        # erste echte Position auswählen
        for r in range(self.pos.rowCount()):
            if self.pos.item(r,0) and isinstance(self.pos.item(r,0).data(Qt.UserRole),int):
                self.pos.selectRow(r);self.show_position_detail();break
        self.total.setText(self._total_text(oid))
        self._loading_offer_positions=False
        if getattr(self,"view_stack",None) is not None and self.view_stack.currentIndex()==1:
            self.measurement.show_offer(x["project_id"],oid)

    def eventFilter(self,obj,event):
        f=self._offer_editor_fields
        if f and event.type()==QEvent.KeyPress and obj in f["inputs"]:
            key=event.key()
            if key==Qt.Key_Escape:
                self.cancel_offer_formula_editor();return True
            if key in (Qt.Key_Return,Qt.Key_Enter) and (obj is not f["long"] or event.modifiers()&Qt.ControlModifier):
                self.save_offer_formula_editor();return True
            if key==Qt.Key_Tab and obj is f["price"]:
                # Letztes Feld: speichern und in die nächste Zeile springen.
                self.save_offer_formula_editor(next_row=True);return True
        return super().eventFilter(obj,event)

    def open_unit_selection(self,row,column):
        if column!=4:return
        key=self.pos.item(row,0);pid=key.data(Qt.UserRole) if key else None
        if not isinstance(pid,int):return
        item=self.pos.item(row,column)
        self.pos.setCurrentCell(row,column)
        self.pos.editItem(item)
        QApplication.processEvents()
        editor=self.pos.indexWidget(self.pos.model().index(row,column))
        if isinstance(editor,QComboBox):editor.showPopup()

    def _clear_offer_formula_editor_state(self):
        self._offer_formula_editor_row=None;self._offer_formula_editor_pid=None
        self._offer_formula_input=None;self._offer_formula_result=None;self._offer_formula_save=None
        self._offer_formula_unit=None;self._offer_formula_price=None
        self._offer_editor_fields={};self._offer_editor_new=False

    def _row_of_position(self,pid):
        for row in range(self.pos.rowCount()):
            item=self.pos.item(row,0)
            if item and item.data(Qt.UserRole)==pid:return row
        return None

    def _offer_titles(self):
        """Titel des aktuellen Angebots in Reihenfolge: [(nr, text), ...]."""
        titles=[]
        for p in self.db.positions(self.current_offer):
            key=((p["title_no"] or "").strip(),(p["title_text"] or "").strip())
            if any(key) and key not in titles:titles.append(key)
        return titles

    @staticmethod
    def _plain_number(value):
        s=("%.3f"%float(value or 0)).rstrip("0").rstrip(".")
        return s.replace(".",",")

    @staticmethod
    def _parse_price(text):
        s=str(text or "").replace("€","").strip().replace(" ","")
        if "," in s:s=s.replace(".","").replace(",",".")
        return float(s or 0)

    def open_offer_formula_editor(self,row,column,focus=None):
        """Bearbeitungsfeld unter der Position (wie im Aufmaß) mit allen Angaben.
        Tab springt von Feld zu Feld, Tab im EP-Feld speichert und öffnet die
        nächste Zeile, Enter speichert, Esc bricht ab."""
        if self._loading_offer_positions:return
        key=self.pos.item(row,0);pid=key.data(Qt.UserRole) if key else None
        if not isinstance(pid,int):return
        selected=self.db.position(pid)
        if not selected or (selected["source_type"] or "").strip()=="Textblock":return
        if self._offer_formula_editor_row is not None:
            if self._offer_formula_editor_pid==pid:return
            # Wechsel in eine andere Zeile: bisherige Eingaben übernehmen.
            if not self.save_offer_formula_editor():return
            row=self._row_of_position(pid)
            if row is None:return
        p=self.db.position(pid)
        self._loading_offer_positions=True
        editor_row=row+1;self.pos.insertRow(editor_row)
        self.pos.setSpan(editor_row,0,1,self.pos.columnCount());self.pos.setRowHeight(editor_row,214)
        panel=QFrame();panel.setObjectName("offerFormulaInlineEditor")
        layout=QGridLayout(panel);layout.setContentsMargins(12,8,12,8)
        title=QComboBox();title.setEditable(True);title.addItem("— kein Titel —")
        for no,text in self._offer_titles():title.addItem(f"{no} · {text}".strip(" ·"))
        current_title=f'{(p["title_no"] or "").strip()} · {(p["title_text"] or "").strip()}'.strip(" ·")
        title.setCurrentText(current_title or "— kein Titel —");title.setMinimumWidth(260)
        title.lineEdit().setPlaceholderText("Titel wählen oder neu eintippen, z. B. Decken")
        pos_edit=QLineEdit(p["position_no"] or "");pos_edit.setMaximumWidth(110)
        short=QLineEdit(p["short_text"] or "");short.setPlaceholderText("Kurztext")
        long=PlainTextPasteEdit();long.setPlainText(p["long_text"] or "");long.setTabChangesFocus(True)
        long.setFixedHeight(62);long.setPlaceholderText("Langtext (optional)")
        formula=(p["formula"] or "").strip()
        edit=QLineEdit(formula or (self._plain_number(p["quantity"]) if float(p["quantity"] or 0) else ""))
        edit.setPlaceholderText("Menge oder Formel, z. B. 12*3,5+4")
        result=QLabel("");result.setObjectName("offerFormulaResult")
        unit=QComboBox();unit.setEditable(True);unit.addItems(PositionDialog.UNITS)
        unit.setCurrentText((p["unit"] or "Stk.").strip());unit.setMinimumWidth(95)
        price=QLineEdit(money(p["unit_price"]));price.setMinimumWidth(115);price.setAlignment(Qt.AlignRight)
        total=QLabel("");total.setObjectName("offerFormulaResult")
        save=icon_button("save","Speichern");cancel=icon_button("cancel","Abbrechen")
        save.setFocusPolicy(Qt.NoFocus);cancel.setFocusPolicy(Qt.NoFocus)
        layout.addWidget(QLabel("Titel:"),0,0);layout.addWidget(title,0,1,1,3)
        layout.addWidget(QLabel("Pos.-Nr.:"),1,0);layout.addWidget(pos_edit,1,1)
        layout.addWidget(QLabel("Kurztext:"),1,2);layout.addWidget(short,1,3,1,6)
        layout.addWidget(QLabel("Langtext:"),2,0);layout.addWidget(long,2,1,1,8)
        layout.addWidget(QLabel("Menge / Formel:"),3,0);layout.addWidget(edit,3,1,1,3);layout.addWidget(result,3,4)
        layout.addWidget(QLabel("Einheit:"),3,5);layout.addWidget(unit,3,6)
        layout.addWidget(QLabel("EP:"),3,7);layout.addWidget(price,3,8)
        layout.addWidget(total,4,1,1,4);layout.addWidget(save,4,7);layout.addWidget(cancel,4,8)
        layout.setColumnStretch(3,1)
        hint=QLabel("Tab: nächstes Feld · Tab im EP: nächste Zeile · Enter: speichern · Esc: abbrechen")
        hint.setObjectName("compactHint");layout.addWidget(hint,4,5,1,2)
        order=[title,pos_edit,short,long,edit,unit,price]
        for a,b in zip(order,order[1:]):QWidget.setTabOrder(a,b)
        self.pos.setCellWidget(editor_row,0,panel)
        inputs=[title.lineEdit(),title,pos_edit,short,long,edit,unit.lineEdit(),unit,price]
        self._offer_editor_fields={"title":title,"pos":pos_edit,"short":short,"long":long,"formula":edit,
            "result":result,"unit":unit,"price":price,"total":total,"save":save,"inputs":inputs}
        self._offer_formula_editor_row=editor_row;self._offer_formula_editor_pid=pid
        self._offer_formula_input=edit;self._offer_formula_result=result;self._offer_formula_save=save
        self._offer_formula_unit=unit;self._offer_formula_price=price
        for widget in inputs:widget.installEventFilter(self)
        edit.textChanged.connect(self.update_offer_formula_preview);price.textChanged.connect(self.update_offer_formula_preview)
        save.clicked.connect(lambda:self.save_offer_formula_editor());cancel.clicked.connect(self.cancel_offer_formula_editor)
        self._loading_offer_positions=False
        self.update_offer_formula_preview()
        self.pos.scrollToItem(self.pos.item(row,0))
        target={"title":title,"short":short,"pos":pos_edit}.get(focus) or {0:pos_edit,1:short,2:edit,3:edit,4:unit,5:price}.get(column,short)
        target.setFocus()
        if isinstance(target,QLineEdit):target.selectAll()

    def update_offer_formula_preview(self,*_):
        f=self._offer_editor_fields
        if not f:return
        ok=True;quantity=0.0;price=0.0
        try:
            quantity=eval_formula(f["formula"].text())
            f["result"].setText(f"= {de_num(quantity,3)}");f["result"].setToolTip("")
            f["result"].setStyleSheet(f"color:{current_theme_color('accent')};")
        except Exception as e:
            ok=False;f["result"].setText("Formel prüfen");f["result"].setToolTip(str(e))
            f["result"].setStyleSheet(f"color:{current_theme_color('delete')};")
        try:price=self._parse_price(f["price"].text())
        except ValueError:ok=False
        f["total"].setText(f"<b>Gesamt: {money(quantity*price)}</b>" if ok else "Gesamt: —")
        f["save"].setEnabled(ok)

    def _close_editor_row(self):
        row=self._offer_formula_editor_row
        if row is None:return
        self._loading_offer_positions=True;self.pos.clearSpans()
        if row<self.pos.rowCount():self.pos.removeRow(row)
        self._clear_offer_formula_editor_state();self._loading_offer_positions=False

    def _write_editor(self,quiet=False):
        """Eingaben speichern. False, wenn etwas ungültig ist (Feld bleibt offen)."""
        f=self._offer_editor_fields
        if not f:return True
        pid=self._offer_formula_editor_pid;is_new=self._offer_editor_new;p=self.db.position(pid)
        if not p:self._close_editor_row();return True
        pos_no=f["pos"].text().strip();short=f["short"].text().strip();longtext=f["long"].toPlainText().strip()
        formula=f["formula"].text().strip();unit=f["unit"].currentText().strip() or "Stk."
        try:quantity=eval_formula(formula)
        except Exception as e:
            if not quiet:QMessageBox.warning(self,"Menge / Formel",str(e));f["formula"].setFocus()
            return False
        try:price=self._parse_price(f["price"].text())
        except ValueError:
            if not quiet:
                QMessageBox.warning(self,"Angebotsposition","Bitte den Einheitspreis als Zahl eingeben.")
                f["price"].setFocus();f["price"].selectAll()
            return False
        if is_new and not short and not longtext and not quantity and not price:
            # Leere neue Zeile wird nicht gespeichert.
            self._close_editor_row();self.db.delete_position(pid);return True
        # Reine Zahlen sind eine Menge, keine Formel.
        stored_formula="" if re.fullmatch(r"[\d\s.,]*",formula) else formula
        title_text=f["title"].currentText().strip()
        tno=(p["title_no"] or "").strip();tt=(p["title_text"] or "").strip()
        sno=p["subtitle_no"] or "";st=p["subtitle_text"] or ""
        if title_text in ("","— kein Titel —"):new_title=("","")
        else:
            known={f"{no} · {text}".strip(" ·"):(no,text) for no,text in self._offer_titles()}
            if title_text in known:new_title=known[title_text]
            else:
                m=re.match(r"^(\d[\d.]*)\s*[·\-]?\s*(.*)$",title_text)
                if m:new_title=(m.group(1),m.group(2).strip())
                else:
                    numbers=[int(no) for no,_ in self._offer_titles() if no.isdigit()]
                    new_title=(f"{(max(numbers) if numbers else 0)+1:02d}",title_text)
        title_changed=new_title!=(tno,tt)
        if title_changed:sno=st=""
        values=(pos_no,short,longtext,stored_formula,unit)
        changed=(title_changed or values!=((p["position_no"] or "").strip(),(p["short_text"] or "").strip(),
                 (p["long_text"] or "").strip(),(p["formula"] or "").strip(),(p["unit"] or "").strip())
                 or abs(quantity-float(p["quantity"] or 0))>1e-9 or abs(price-float(p["unit_price"] or 0))>1e-9)
        self._close_editor_row()
        if not changed:return True
        if self._inline_backup_offer!=self.current_offer:
            self.db.backup("vor_inline_angebotsposition_aenderung");self._inline_backup_offer=self.current_offer
        self.db.update_position(pid,(p["service_id"],pos_no,short,longtext,stored_formula,quantity,unit,price,
                                     new_title[0],new_title[1],sno,st))
        if title_changed:self._move_into_title(pid,new_title[0])
        return True

    def _move_into_title(self,pid,title_no):
        """Position hinter die letzte Position ihres Titels setzen, damit der
        Titel zusammenbleibt; danach die Reihenfolge sauber durchnummerieren."""
        rows=[r for r in self.db.positions(self.current_offer)]
        ids=[r["id"] for r in rows if r["id"]!=pid]
        same=[i for i,r in enumerate(rows) if r["id"]!=pid and (r["title_no"] or "").strip()==title_no and title_no]
        if same:
            anchor=rows[same[-1]]["id"];ids.insert(ids.index(anchor)+1,pid)
        else:ids.append(pid)
        for index,row_id in enumerate(ids,1):
            self.db.conn.execute("UPDATE offer_positions SET sort_order=? WHERE id=?",(index*10,row_id))
        self.db.conn.commit()

    def _finish_editor_silently(self):
        """Beim Angebotswechsel oder Neuladen offene Eingaben übernehmen, sonst verwerfen."""
        if getattr(self,"_offer_formula_editor_row",None) is None:return
        if not self._write_editor(quiet=True):self.cancel_offer_formula_editor(reload=False)

    def save_offer_formula_editor(self,next_row=False):
        pid=self._offer_formula_editor_pid
        if not self._write_editor():return False
        self.select_offer()
        row=self._row_of_position(pid)
        if row is not None:self.pos.selectRow(row);self.pos.scrollToItem(self.pos.item(row,0))
        if next_row:self._open_next_position(pid)
        return True

    def cancel_offer_formula_editor(self,reload=True):
        pid=self._offer_formula_editor_pid;is_new=self._offer_editor_new
        self._close_editor_row()
        if is_new and pid:
            self.db.delete_position(pid)
            if reload:self.select_offer()

    def _open_next_position(self,pid):
        row=self._row_of_position(pid)
        if row is None:
            # Leere neue Zeile wurde verworfen: ans Ende eine neue anlegen.
            self._new_offer_position();return
        for candidate in range(row+1,self.pos.rowCount()):
            item=self.pos.item(candidate,0);next_pid=item.data(Qt.UserRole) if item else None
            if isinstance(next_pid,int):
                p=self.db.position(next_pid)
                if p and (p["source_type"] or "").strip()!="Textblock":
                    self.pos.selectRow(candidate);self.open_offer_formula_editor(candidate,0,focus="pos");return
        self._new_offer_position(after=pid)

    @staticmethod
    def _next_number(previous):
        """Letzte Zahl (bzw. einen Endbuchstaben) weiterzählen, Nullen bleiben."""
        s=str(previous or "").strip()
        m=re.match(r"^(.*?\d)([a-y])$",s)
        if m:return m.group(1)+chr(ord(m.group(2))+1)
        m=re.match(r"^(.*?)(\d+)(\D*)$",s)
        if not m:return ""
        digits=m.group(2);return f"{m.group(1)}{int(digits)+1:0{len(digits)}d}{m.group(3)}"

    def _suggest_position_no(self,ref=None):
        rows=[r for r in self.db.positions(self.current_offer) if (r["source_type"] or "").strip()!="Textblock"]
        base=ref if ref is not None else (rows[-1] if rows else None)
        used={(r["position_no"] or "").strip() for r in rows}
        candidate=self._next_number(base["position_no"]) if base is not None else ""
        for _ in range(50):
            if candidate and candidate not in used:return candidate
            candidate=self._next_number(candidate) if candidate else ""
            if not candidate:break
        return self.db.next_pos(self.current_offer)

    def _new_offer_position(self,after=None):
        """Neue leere Position direkt hinter `after` (gleicher Titel) oder am Ende."""
        if not self.current_offer:return
        tno=tt=sno=st=""
        ref=self.db.position(after) if after else None
        if ref and (ref["source_type"] or "").strip()=="Textblock":ref=None
        if ref:tno,tt,sno,st=(ref["title_no"] or ""),(ref["title_text"] or ""),(ref["subtitle_no"] or ""),(ref["subtitle_text"] or "")
        new_pid=self.db.add_position(self.current_offer,(None,self._suggest_position_no(ref),"","","",0,"Stk.",0,tno,tt,sno,st))
        if ref:
            ids=[r["id"] for r in self.db.positions(self.current_offer) if r["id"]!=new_pid]
            ids.insert(ids.index(ref["id"])+1,new_pid)
            for index,row_id in enumerate(ids,1):
                self.db.conn.execute("UPDATE offer_positions SET sort_order=? WHERE id=?",(index*10,row_id))
            self.db.conn.commit()
        self.select_offer();row=self._row_of_position(new_pid)
        if row is None:return
        self.pos.setCurrentCell(row,1);self.pos.editItem(self.pos.item(row,1))

    def inline_offer_position_changed(self,item):
        return self._offer_cell_changed(item)

    def _offer_cell_changed(self,item):
        if self._loading_offer_positions or item.column()>5:return
        key=self.pos.item(item.row(),0);pid=key.data(Qt.UserRole) if key else None
        if not isinstance(pid,int):return
        p=self.db.position(pid)
        if not p or (p["source_type"] or "").strip()=="Textblock":return
        cell=lambda c:(self.pos.item(item.row(),c).text() if self.pos.item(item.row(),c) else "").strip()
        formula=(p["formula"] or "").strip();quantity=float(p["quantity"] or 0)
        try:
            if item.column()==2:
                formula=cell(2);quantity=eval_formula(formula) if formula else 0.0
                if re.fullmatch(r"[\d\s.,]*",formula):formula=""
            elif item.column()==3:
                quantity=parse_de_number(cell(3));formula=""
            price=self._parse_price(cell(5))
        except Exception as e:
            QMessageBox.warning(self,"Angebotsposition",f"Bitte eine gültige Zahl bzw. Formel eingeben.\n\n{e}")
            self._loading_offer_positions=True;self.select_offer();return
        values=(cell(0),cell(1),formula,quantity,cell(4) or "Stk.",price)
        before=((p["position_no"] or "").strip(),(p["short_text"] or "").strip(),(p["formula"] or "").strip(),
                float(p["quantity"] or 0),(p["unit"] or "").strip(),float(p["unit_price"] or 0))
        if values==before:return
        if self._inline_backup_offer!=self.current_offer:
            self.db.backup("vor_inline_angebotsposition_aenderung");self._inline_backup_offer=self.current_offer
        self.db.update_position(pid,(p["service_id"],values[0],values[1],p["long_text"] or "",formula,quantity,values[4],price,
                                     p["title_no"] or "",p["title_text"] or "",p["subtitle_no"] or "",p["subtitle_text"] or ""))
        self._loading_offer_positions=True
        for column,text in ((2,formula),(3,de_num(quantity,3)),(5,money(price)),(6,money(quantity*price))):
            if self.pos.item(item.row(),column):self.pos.item(item.row(),column).setText(text)
        # Titel-Zwischensummen und Angebotssumme sofort nachziehen.
        for row in range(self.pos.rowCount()):
            head=self.pos.item(row,0);children=head.data(Qt.UserRole) if head else None
            if isinstance(children,list) and self.pos.item(row,6):
                total=sum(float(q["quantity"] or 0)*float(q["unit_price"] or 0) for q in self.db.positions(self.current_offer) if q["id"] in children)
                self.pos.item(row,6).setText(money(total))
        self.total.setText(self._total_text(self.current_offer))
        self._loading_offer_positions=False

    def _prepare_offer_tab(self,row,column,backward=False):
        """Tab im EP: nächste Position (Kurztext) bzw. am Ende eine neue Zeile.
        In die Einheiten-Klappliste (aus Menge vor bzw. aus EP zurück) wird sie
        gezielt geöffnet, weil Qt sie beim automatischen Springen sofort schließt."""
        key=self.pos.item(row,0);pid=key.data(Qt.UserRole) if key else None
        if not isinstance(pid,int):return None
        if (column==3 and not backward) or (column==5 and backward):
            def unit():
                target=self._row_of_position(pid)
                if target is None:return
                if self.pos.state()==QAbstractItemView.EditingState and self.pos.currentColumn()==4:return
                self.pos.setCurrentCell(target,4);self.pos.editItem(self.pos.item(target,4))
            return unit
        if column!=5 or backward:return None
        def go():
            start=self._row_of_position(pid)
            for candidate in range((start if start is not None else row)+1,self.pos.rowCount()):
                item=self.pos.item(candidate,0);next_pid=item.data(Qt.UserRole) if item else None
                if isinstance(next_pid,int):
                    q=self.db.position(next_pid)
                    if q and (q["source_type"] or "").strip()!="Textblock":
                        self.pos.setCurrentCell(candidate,1);self.pos.editItem(self.pos.item(candidate,1));return
            self._new_offer_position(after=pid)
        return go

    def _position_menu(self,point):
        index=self.pos.indexAt(point)
        if not index.isValid():return
        self.pos.setCurrentCell(index.row(),0)
        menu=QMenu(self.pos);menu.addAction("Langtext / Titel bearbeiten …",self.edit_position)
        menu.addAction("Position kopieren",self.copy_offer_position);menu.addAction("Position löschen",self.delete_position)
        menu.exec(self.pos.viewport().mapToGlobal(point))

    def _place_position_after(self,pid,after):
        ids=[r["id"] for r in self.db.positions(self.current_offer) if r["id"]!=pid]
        ids.insert(ids.index(after)+1 if after in ids else len(ids),pid)
        for index,value in enumerate(ids,1):
            self.db.conn.execute("UPDATE offer_positions SET sort_order=? WHERE id=?",(index*10,value))
        self.db.conn.commit()

    @staticmethod
    def _is_free_position(p):
        return (p is not None and (p["source_type"] or "").strip()!="Textblock" and not (p["short_text"] or "").strip()
                and not float(p["quantity"] or 0) and not float(p["unit_price"] or 0))

    def insert_services(self,service_ids):
        """Leistungen einfügen: erste in die freie Zeile, weitere direkt darunter
        (gleicher Titel); ohne freie Zeile hinter der markierten Position."""
        oid=self.current_offer
        if not oid or not service_ids:return 0
        self._finish_editor_silently()
        anchor=self.db.position(self.pos_id()) if self.pos_id() else None
        if anchor and (anchor["source_type"] or "").strip()=="Textblock":anchor=None
        free=anchor if self._is_free_position(anchor) else next((r for r in self.db.positions(oid) if self._is_free_position(r)),None)
        if free:anchor=free
        title=((anchor["title_no"] or ""),(anchor["title_text"] or ""),(anchor["subtitle_no"] or ""),(anchor["subtitle_text"] or "")) if anchor else ("","","","")
        self.db.backup("vor_leistungsuebernahme");after=anchor["id"] if anchor else None;inserted=[]
        for sid in service_ids:
            s=self.db.service(sid)
            if not s:continue
            data=(s["short_text"],s["long_text"] or "","",0,s["unit"] or "Stk.",float(s["sales_price"] or 0))+title
            if free is not None and not inserted:
                pid=free["id"];self.db.update_position(pid,(None,free["position_no"] or self._suggest_position_no(None))+data)
            else:
                base=self.db.position(after) if after else None
                pid=self.db.add_position(oid,(None,self._suggest_position_no(base))+data,"Leistung")
                if after:self._place_position_after(pid,after)
            after=pid;inserted.append(pid)
        self.select_offer()
        row=self._row_of_position(inserted[-1]) if inserted else None
        if row is not None:self.pos.selectRow(row);self.pos.scrollToItem(self.pos.item(row,0))
        return len(inserted)

    def _old_inline_offer_position_changed(self,item):
        if self._loading_offer_positions or item.column() not in (0,1,3,4,5):return
        key=self.pos.item(item.row(),0);pid=key.data(Qt.UserRole) if key else None
        if not isinstance(pid,int):return
        p=self.db.position(pid)
        if not p:return
        pos_no=self.pos.item(item.row(),0).text().strip()
        short=self.pos.item(item.row(),1).text().strip()
        unit=self.pos.item(item.row(),4).text().strip() or "Stk."
        def number(text):
            s=str(text or "").replace("€","").strip().replace(" ","")
            if "," in s:s=s.replace(".","").replace(",",".")
            return float(s or 0)
        try:
            qty=number(self.pos.item(item.row(),3).text())
            price=number(self.pos.item(item.row(),5).text())
        except ValueError:
            QMessageBox.warning(self,"Angebotsposition","Bitte Menge und Einheitspreis als Zahl eingeben.")
            self.select_offer();return
        formula="" if item.column()==3 else (p["formula"] or "")
        self.db.update_position(pid,(
            p["service_id"],pos_no,short,p["long_text"] or "",formula,qty,unit,price,
            p["title_no"] or "",p["title_text"] or "",p["subtitle_no"] or "",p["subtitle_text"] or ""
        ))
        self._loading_offer_positions=True
        self.pos.item(item.row(),3).setText(de_num(qty,3))
        self.pos.item(item.row(),5).setText(money(price))
        self.pos.item(item.row(),6).setText(money(qty*price))
        self.total.setText(self._total_text(self.current_offer))
        self._loading_offer_positions=False
        self.show_position_detail()

    def import_external_ods(self):
        path,_=QFileDialog.getOpenFileName(
            self,"Externes Angebot / Leistungsverzeichnis auswählen","",
            "LV-Dateien (*.ods *.xlsx *.pdf);;ODS-Dateien (*.ods);;Excel-Dateien (*.xlsx);;PDF-Dateien (*.pdf)")
        if not path:return

        try:
            positions,headings,source_type=read_lv_offer_positions(path)
        except Exception as e:
            QMessageBox.warning(self,"Externer LV-Import",
                f"Die LV-Datei konnte nicht gelesen werden.\n\n{e}")
            return

        if not positions:
            QMessageBox.information(self,"Externer LV-Import",
                "Es wurden keine importierbaren Positionen erkannt.\n\n"
                "Erwartet werden Positionszeilen mit Positionsnummer, Menge, Einheit, "
                "Beschreibung und Einheitspreis.")
            return

        preview=ODSImportDialog(positions,self)
        preview.setWindowTitle(f"Externes {source_type}-Angebot – Positionen prüfen")
        if not preview.exec():return
        selected=preview.selected_positions()
        if not selected:return

        if not self.db.projects_search(""):
            QMessageBox.information(self,"Externer LV-Import",
                "Für den Import wird ein Zielprojekt benötigt.\n\n"
                "Bitte zuerst unter Kunden/Projekte den gewünschten Kunden und das Projekt anlegen.")
            return

        target=ExternalODSOfferDialog(self.db,path,len(selected),self)
        if not target.exec():return
        project_id,title,notes=target.data()

        self.db.backup(f"vor_externem_{source_type.lower()}_angebotsimport")
        oid=self.db.add_offer(project_id,title or "Importiertes Angebot",notes)
        try:
            for p in selected:
                self.db.add_position(oid,(
                    None,p["position_no"],p["short_text"],p["long_text"],"",
                    p["quantity"],p["unit"],p["unit_price"],
                    p.get("title_no",""),p.get("title_text",""),
                    p.get("subtitle_no",""),p.get("subtitle_text","")
                ),source_type)
        except Exception as e:
            try:self.db.delete_offer(oid)
            except:pass
            QMessageBox.warning(self,"Externer LV-Import",
                f"Der Import konnte nicht vollständig abgeschlossen werden.\n\n{e}")
            return

        self.refresh()
        self.select_offer_by_id(oid)
        extra=(f"\n\n{len(headings)} Gliederungs-/Überschriftszeile(n) wurden erkannt "
               "und in dieser Version bewusst nicht als abrechenbare Position importiert.") if headings else ""
        QMessageBox.information(self,"Externer LV-Import",
            f"Das externe Angebot wurde als neuer Aufmaßwerk-Angebotsentwurf angelegt.\n\n"
            f"Übernommen: {len(selected)} Position(en)\n"
            f"Netto: {money(sum(p['quantity']*p['unit_price'] for p in selected))}{extra}")

    def new_offer(self):
        if not self.db.projects():
            QMessageBox.information(self,"Angebot","Bitte zuerst einen Kunden und ein Projekt anlegen."); return
        d=OfferDialog(self.db,self)
        if d.exec():
            project_id=d.project.currentData()
            oid=self.db.add_offer(project_id,d.title.text().strip(),d.notes.toPlainText().strip())
            self.db.update_offer(oid,project_id,d.title.text().strip(),d.status.currentText(),d.notes.toPlainText().strip())
            # Das neue, leere Angebot aktivieren. Die bisherige Auswahl darf hier
            # nicht erhalten bleiben, sonst erscheinen optisch die alten Positionen.
            self.refresh_and_select(oid)


    def _measurement_document(self):
        offer=self.db.offer(self.current_offer) if self.current_offer else None
        if not offer:
            QMessageBox.information(self,"Aufmaß","Bitte zuerst oben ein Angebot auswählen.");return None
        if not self.db.measurement_positions(offer["project_id"]):
            QMessageBox.information(self,"Aufmaß","Dieses Projekt enthält noch keine Aufmaßpositionen.");return None
        return MeasurementPreviewDialog(self.db,offer["project_id"],self)

    def output_offer(self):
        if getattr(self,"view_stack",None) is not None and self.view_stack.currentIndex()==1:
            document=self._measurement_document()
            if document:document.save_pdf()
            return
        oid=self.offer_id()
        if not oid:
            QMessageBox.information(self,"Angebot ausgeben","Bitte zuerst ein Angebot auswählen.");return
        box=QMessageBox(self);box.setWindowTitle("Angebot ausgeben");box.setText("Ausgabeformat wählen:")
        pdf_btn=box.addButton("PDF erstellen",QMessageBox.AcceptRole)
        odt_btn=box.addButton("ODT erstellen",QMessageBox.ActionRole)
        box.addButton("Abbrechen",QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton()==pdf_btn:self.create_offer_pdf(oid)
        elif box.clickedButton()==odt_btn:self.create_offer_odt(oid)

    def preview_offer_pdf(self):
        if getattr(self,"view_stack",None) is not None and self.view_stack.currentIndex()==1:
            document=self._measurement_document()
            if document:document.open_pdf_preview()
            return
        oid=self.offer_id()
        if not oid:
            QMessageBox.information(self,"Angebotsvorschau","Bitte zuerst ein Angebot auswählen.");return
        self.create_offer_pdf(oid,preview=True)

    def send_offer_email(self):
        oid=self.offer_id()
        if not oid:
            QMessageBox.information(self,"E-Mail senden","Bitte zuerst ein Angebot auswählen.");return
        offer=self.db.offer(oid);path=self.create_offer_pdf(oid,preview=True,open_after=False)
        if not path:return
        compose_email_with_pdf(self,path,offer["customer_email"],f'Angebot {offer["number"]}',
            "Guten Tag,\n\nanbei erhalten Sie unser Angebot als PDF.\n\nMit freundlichen Grüßen")
        file_generated_document(self.db,offer["project_id"],path,f'Angebot_{offer["number"]}_versendet_{date.today().isoformat()}.pdf',
            f'Angebot {offer["number"]} – per E-Mail versendet am {today_de()}')

    def create_offer_pdf(self,oid,preview=False,open_after=True):
        offer=self.db.offer(oid);positions=self.db.positions(oid);company=self.db.company_settings()
        if preview:
            # Die Vorschau bleibt bewusst außerhalb der finalen Angebotsablage.
            # Sie durchläuft anschließend exakt denselben PDF-Renderer.
            safe_number=re.sub(r'[^A-Za-z0-9_.-]+','_',str(offer["number"] or "Angebot"))
            path=str(PREVIEW_DIR/f'VORSCHAU_{safe_number}_Angebot.pdf')
        else:
            path,_=QFileDialog.getSaveFileName(
                self,"Angebot als PDF speichern",
                str(OFFER_DOCUMENT_DIR/f'{offer["number"]}_Angebot.pdf'),
                "PDF-Dateien (*.pdf)")
            if not path:return
            if not path.lower().endswith(".pdf"):path += ".pdf"

        writer=QPdfWriter(path);writer.setPageSize(QPageSize(QPageSize.A4));writer.setResolution(96)
        writer.setTitle(f'Angebot {offer["number"]}');writer.setCreator(f"{APP_NAME} {APP_VERSION}")
        painter=QPainter(writer)
        if not painter.isActive():
            QMessageBox.critical(self,"Angebot PDF","Die PDF-Datei konnte nicht erstellt werden.");return None

        page=writer.pageLayout().paintRectPixels(writer.resolution())
        left=48;right=48;top=42;bottom=46;width=page.width()-left-right;y=top;page_no=1
        letterhead=Letterhead("offer",writer);letterhead.draw(painter,True)
        def val(k):
            try:return (company[k] if company else "") or ""
            except:return ""
        def font(size=9,bold=False):
            f=QFont("DejaVu Sans",size);f.setBold(bold);return f
        def txt(x,y0,w,h,text,size=9,bold=False,align=Qt.AlignLeft|Qt.AlignVCenter):
            painter.setFont(font(size,bold))
            painter.drawText(QRectF(x,y0,w,h),align|Qt.TextWordWrap,str(text or ""))
        def line(y0):painter.drawLine(left,y0,left+width,y0)
        def footer():
            if letterhead.active:
                txt(left+width*.84,letterhead.page_number_y(),width*.16,14,f"Seite {page_no}",7,False,Qt.AlignRight|Qt.AlignVCenter);return
            fy=page.height()-47
            contact=" | ".join(x for x in [val("company_name"),val("phone"),val("email")] if x)
            bank=("IBAN: "+val("iban")) if val("iban") else ""
            txt(left,fy,width*.82,15,contact,6,False,Qt.AlignLeft|Qt.AlignTop)
            txt(left,fy+15,width*.82,15,bank,6,False,Qt.AlignLeft|Qt.AlignTop)
            txt(left+width*.84,fy,width*.16,30,f"Seite {page_no}",7,False,Qt.AlignRight|Qt.AlignVCenter)
        def new_page():
            nonlocal y,page_no
            footer();writer.newPage();page_no+=1;y=top
            letterhead.draw(painter,False);y=letterhead.content_top(y)
            if not letterhead.active:draw_pdf_brand(painter,val("logo_path"),val("company_name"),left,y,width*.18,22,11,width*.62)
            txt(left+width*.64,y,width*.36,22,f'Angebot {offer["number"]}',10,True,Qt.AlignRight|Qt.AlignVCenter)
            y+=28;line(y);y+=12
        def ensure(h):
            nonlocal y
            if y+h>letterhead.limit(page.height()-bottom-28):new_page()
        def text_h(text,w,size,bold=False,min_h=18):
            painter.setFont(font(size,bold))
            r=painter.boundingRect(QRectF(0,0,w,1200),Qt.AlignLeft|Qt.AlignTop|Qt.TextWordWrap,str(text or ""))
            return max(min_h,int(r.height())+4)

        if letterhead.active:
            y=letterhead.content_top(y)
            txt(left+width*.62,y,width*.38,28,"Angebot",17,True,Qt.AlignRight|Qt.AlignVCenter);y+=36
        else:
            draw_pdf_brand(painter,val("logo_path"),val("company_name"),left,y,width*.20,28,18,width*.60)
            txt(left+width*.62,y,width*.38,28,"Angebot",17,True,Qt.AlignRight|Qt.AlignVCenter);y+=31
            contact=" · ".join(x for x in [val("street"),(val("zip")+" "+val("city")).strip(),val("phone"),val("email")] if x)
            txt(left,y,width,15,contact,7);y+=19;line(y);y+=14

        sender=" · ".join(x for x in [val("company_name"),val("street"),(val("zip")+" "+val("city")).strip()] if x)
        sender_h=text_h(sender,width*.55,6,False,16)
        txt(left,y,width*.55,sender_h,sender,6,False,Qt.AlignLeft|Qt.AlignTop);y+=sender_h+3
        ry=y
        for item in [offer["company"],offer["customer_contact"],offer["customer_street"],
                     f'{offer["customer_zip"] or ""} {offer["customer_city"] or ""}'.strip()]:
            if item:
                txt(left,ry,width*.53,17,item,9,item==offer["company"]);ry+=17

        mx=left+width*.60;mw=width*.40;my=y
        for k,v in [("Kunden-Nr.",offer["customer_number"]),("Projekt-Nr.",offer["project_number"]),
                    ("Angebots-Nr.",offer["number"]),("Datum",de_date(offer["created_at"]))]:
            txt(mx,my,mw*.44,16,k,8,True);txt(mx+mw*.45,my,mw*.55,16,v,8);my+=16
        y=max(ry,my)+12
        project_text=f'Projekt: {one_line(offer["project_name"])}'
        project_h=text_h(project_text,width,10,True,20)
        txt(left,y,width,project_h,project_text,10,True,Qt.AlignLeft|Qt.AlignTop);y+=project_h
        if offer["site"]:txt(left,y,width,18,f'Baustelle: {offer["site"]}',9);y+=18
        if offer["title"]:txt(left,y,width,18,f'Bezeichnung: {offer["title"]}',9);y+=18
        y+=8

        def columns_header():
            nonlocal y
            ensure(29);painter.fillRect(QRectF(left,y,width,25),Qt.lightGray)
            txt(left+3,y,width*.08,25,"Pos.",8,True)
            txt(left+width*.08+3,y,width*.50,25,"Menge / Bezeichnung",8,True)
            txt(left+width*.59,y,width*.10,25,"Einheit",8,True)
            txt(left+width*.69,y,width*.14,25,"EP",8,True,Qt.AlignRight|Qt.AlignVCenter)
            txt(left+width*.83,y,width*.17-3,25,"Gesamt",8,True,Qt.AlignRight|Qt.AlignVCenter);y+=27

        last_title=None;last_sub=None;header_drawn=False
        for p in positions:
            if (p["source_type"] or "").strip()=="Textblock":
                heading=(p["short_text"] or "").strip();body=(p["long_text"] or "").strip()
                if header_drawn:y+=12
                if heading:
                    hh=text_h(heading,width,12,True,22);ensure(hh+5)
                    txt(left,y,width,hh,heading,12,True,Qt.AlignLeft|Qt.AlignTop);y+=hh+5
                for paragraph in body.split("\n"):
                    ph=text_h(paragraph or " ",width,10,False,18);ensure(ph)
                    txt(left,y,width,ph,paragraph,10,False,Qt.AlignLeft|Qt.AlignTop);y+=ph
                y+=10;header_drawn=False;last_title=None;last_sub=None
                if (p["formula"] or "")=="Seitenumbruch":new_page()
                continue
            if not header_drawn:columns_header();header_drawn=True
            tno,tt,sno,st=lv_group_values(p)
            if tno and (tno,tt)!=last_title:
                title_sum=sum(float(q["quantity"] or 0)*float(q["unit_price"] or 0)
                              for q in positions if lv_group_values(q)[0]==tno)
                ensure(34)
                painter.fillRect(QRectF(left,y,width,28),Qt.lightGray)
                txt(left+4,y,width*.72,28,f"TITEL {tno} – {tt}",10,True)
                txt(left+width*.74,y,width*.26-3,28,money(title_sum),9,True,Qt.AlignRight|Qt.AlignVCenter)
                y+=32;last_title=(tno,tt);last_sub=None
            # Imported source title rows remain stored and auditable, but the
            # group heading above is their visual representation in the PDF.
            if (p["source_type"] or "").strip()=="Titel":
                continue
            if sno and (sno,st)!=last_sub:
                sub_sum=sum(float(q["quantity"] or 0)*float(q["unit_price"] or 0)
                            for q in positions if lv_group_values(q)[2]==sno)
                ensure(28)
                txt(left+10,y,width*.70,24,f"Untertitel {sno} – {st}",9,True)
                txt(left+width*.74,y,width*.26-3,24,money(sub_sum),8,True,Qt.AlignRight|Qt.AlignVCenter)
                y+=27;last_sub=(sno,st)
            longtext=(p["long_text"] or "").strip()
            sh=text_h(p["short_text"],width*.36,8,True,22)
            lh=text_h(longtext,width*.36,7,False,0) if longtext else 0
            row_h=max(32,sh+lh+10);ensure(row_h+5);rt=y
            txt(left+3,rt,width*.08-4,28,p["position_no"],8)
            txt(left+width*.08+3,rt,width*.14,28,de_num(p["quantity"],3),8)
            txt(left+width*.22,rt,width*.36,sh,p["short_text"],8,True,Qt.AlignLeft|Qt.AlignTop)
            txt(left+width*.59,rt,width*.10,28,p["unit"],8)
            txt(left+width*.69,rt,width*.14,28,money(p["unit_price"]),8,False,Qt.AlignRight|Qt.AlignVCenter)
            line_total=float(p["quantity"] or 0)*float(p["unit_price"] or 0)
            txt(left+width*.83,rt,width*.17-3,28,money(line_total),8,False,Qt.AlignRight|Qt.AlignVCenter)
            if longtext:
                txt(left+width*.22,rt+sh+1,width*.36,lh,longtext,7,False,Qt.AlignLeft|Qt.AlignTop)
            y=rt+row_h;line(y);y+=5

        total=sum(float(p["quantity"] or 0)*float(p["unit_price"] or 0) for p in positions)
        y+=12;ensure(110)
        for text,amount,bold in offer_tax_lines(offer,total):
            if amount:
                size=11 if bold else 9;h=24 if bold else 20
                txt(left,y,width*.70,h,text,size,bold)
                txt(left+width*.72,y,width*.28,h,amount,size,bold,Qt.AlignRight|Qt.AlignVCenter);y+=h+4
            else:
                txt(left,y,width,30,text,8,False,Qt.AlignLeft|Qt.AlignTop);y+=32
        y+=6
        if offer["notes"]:
            txt(left,y,width,18,"Hinweise:",9,True);y+=18
            nh=text_h(offer["notes"],width,8,False,30);ensure(nh)
            txt(left,y,width,nh,offer["notes"],8,False,Qt.AlignLeft|Qt.AlignTop)
        footer();painter.end()
        if preview:
            if open_after:
                open_desktop_file(path,self,"Angebotsvorschau")
        else:
            QMessageBox.information(self,"Angebot PDF",f"PDF wurde erstellt:\n{path}")
            if open_after:open_desktop_file(path,self,"Angebot PDF")
            file_generated_document(self.db,offer["project_id"],path,f'Angebot_{offer["number"]}.pdf',
                f'Angebot {offer["number"]} – erstellt am {today_de()}')
        return str(Path(path).resolve())

    def create_offer_odt(self,oid):
        offer=self.db.offer(oid);positions=self.db.positions(oid);company=self.db.company_settings()
        path,_=QFileDialog.getSaveFileName(
            self,"Angebot als ODT speichern",
            str(OFFER_DOCUMENT_DIR/f'{offer["number"]}_Angebot.odt'),
            "ODT-Dateien (*.odt)")
        if not path:return
        if not path.lower().endswith(".odt"):path += ".odt"
        try:create_simple_offer_odt(path,offer,positions,company)
        except Exception as e:
            QMessageBox.warning(self,"Angebot ODT",f"ODT konnte nicht erstellt werden.\n\n{e}");return
        file_generated_document(self.db,offer["project_id"],path,f'Angebot_{offer["number"]}.odt',
            f'Angebot {offer["number"]} (ODT) – erstellt am {today_de()}')
        QMessageBox.information(self,"Angebot ODT",f"ODT wurde erstellt:\n{path}")
        open_desktop_file(path,self,"Angebot ODT")

    def edit_offer(self,*args):
        oid=self.offer_id()
        if not oid:
            QMessageBox.information(self,"Angebot bearbeiten","Bitte zuerst ein Angebot auswählen.");return
        row=self.db.offer(oid)
        d=OfferDialog(self.db,self,row)
        if d.exec():
            self.db.backup("vor_angebot_bearbeiten")
            self.db.update_offer(
                oid,d.project.currentData(),d.title.text().strip(),
                d.status.currentText(),d.notes.toPlainText().strip()
            )
            self.refresh_and_select(oid)

    def add_position(self):
        if not self.current_offer:
            QMessageBox.information(self,"Position","Bitte zuerst ein Angebot auswählen."); return
        if self._offer_formula_editor_row is not None and not self.save_offer_formula_editor():return
        # Hinter der markierten Position (gleicher Titel), sonst am Ende.
        self._new_offer_position(after=self.pos_id())

    def add_text_block(self):
        if not self.current_offer:
            QMessageBox.information(self,"Textblock","Bitte zuerst ein Angebot auswählen.");return
        d=OfferTextDialog(self)
        if d.exec():
            self.db.backup("vor_angebotstext_hinzufuegen")
            self.db.add_offer_text(self.current_offer,*d.data());self.select_offer()

    def move_position(self,direction):
        pid=self.pos_id()
        if not pid:
            QMessageBox.information(self,"Reihenfolge","Bitte zuerst einen Textblock oder eine Position auswählen.");return
        self.db.backup("vor_angebotsreihenfolge_aendern")
        if not self.db.move_offer_item(pid,direction):return
        self.select_offer()
        for row in range(self.pos.rowCount()):
            item=self.pos.item(row,0)
            if item and item.data(Qt.UserRole)==pid:
                self.pos.selectRow(row);self.show_position_detail();break

    def import_ods(self):
        if not self.current_offer:
            QMessageBox.information(self,"LV-Positionen hinzufügen",
                "Diese Funktion ergänzt Positionen in ein bereits vorhandenes Angebot.");return
        project_id=self.db.offer(self.current_offer)["project_id"]
        selected,source_type=pick_lv_positions(self,self.db,project_id)
        if not selected:return
        existing={str(p["position_no"] or "").strip() for p in self.db.positions(self.current_offer)}
        duplicates=[p["position_no"] for p in selected if p["position_no"] in existing]
        if duplicates:
            shown=", ".join(duplicates[:12])+(" …" if len(duplicates)>12 else "")
            if QMessageBox.question(self,"Doppelte Positionsnummern",
                f"Folgende Positionsnummern existieren bereits:\n{shown}\n\n"
                "Diese Positionen überspringen und die übrigen importieren?",
                QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:
                return
            selected=[p for p in selected if p["position_no"] not in existing]
        if not selected:
            QMessageBox.information(self,"LV-Import","Nach dem Überspringen doppelter Positionen bleibt nichts zu importieren.");return
        self.db.backup(f"vor_{source_type.lower()}_import")
        self._add_lv_positions(self.current_offer,selected,source_type)
        self.select_offer()
        QMessageBox.information(self,"LV-Import",f"{len(selected)} Position(en) wurden in das Angebot übernommen.")

    def _add_lv_positions(self,oid,selected,source_type):
        for p in selected:
            self.db.add_position(oid,(
                None,p["position_no"],p["short_text"],p["long_text"],"",
                p["quantity"],p["unit"],p["unit_price"],
                p.get("title_no",""),p.get("title_text",""),
                p.get("subtitle_no",""),p.get("subtitle_text","")
            ),source_type)

    def new_offer_from_lv(self):
        projects=self.db.projects_search("","Aktiv") or self.db.projects_search("","Alle")
        if not projects:
            QMessageBox.information(self,"Angebot aus LV","Bitte zuerst einen Kunden und ein Projekt anlegen.");return
        labels=[f'{p["number"]} – {one_line(p["name"])} – {one_line(p["company"])}' for p in projects]
        preferred=getattr(self,"context_project_id",None)
        start=next((i for i,p in enumerate(projects) if p["id"]==preferred),0)
        label,ok=QInputDialog.getItem(self,"Angebot aus LV","Für welches Projekt?",labels,start,False)
        if not ok:return
        project_id=projects[labels.index(label)]["id"]
        selected,source_type=pick_lv_positions(self,self.db,project_id)
        if not selected:return
        has_offers=bool(self.db.project_offers(project_id))
        title,ok=QInputDialog.getText(self,"Angebot aus LV","Bezeichnung des neuen Angebots:",
            text="Nachtragsangebot" if has_offers else "Angebot aus LV")
        if not ok:return
        self.db.backup("vor_angebot_aus_lv")
        oid=self.db.add_offer(project_id,title.strip() or "Angebot aus LV","Erstellt aus Projekt-LV")
        try:self._add_lv_positions(oid,selected,source_type)
        except Exception as e:
            try:self.db.delete_offer(oid)
            except Exception:pass
            QMessageBox.warning(self,"Angebot aus LV",f"Das Angebot konnte nicht vollständig angelegt werden.\n\n{e}");return
        self.refresh_and_select(oid)

    def import_services(self):
        oid=self.current_offer or self.offer_id()
        if not oid:
            QMessageBox.information(self,"Leistungsbibliothek","Bitte zuerst ein Angebot auswählen.");return
        if self.current_offer!=oid:
            self.select_offer_by_id(oid)
        d=ServiceLibraryDialog(self.db,self)
        if not d.exec():return
        imported=list(range(self.insert_services(d.selected_ids())))
        QMessageBox.information(self,"Leistungsbibliothek",
            f"{len(imported)} Position(en) wurden als unabhängige Kopien in das Angebot übernommen.\n\n"
            "Kurztext, Langtext, Einheit und Standard-EP wurden kopiert; die Menge bleibt projektspezifisch bei 0.")

    def edit_position(self):
        pid=self.pos_id()
        if not pid:return
        row=self.db.position(pid)
        if (row["source_type"] or "").strip()=="Textblock":
            d=OfferTextDialog(self,row)
            if d.exec():
                self.db.backup("vor_angebotstext_bearbeiten")
                self.db.update_offer_text(pid,*d.data());self.select_offer()
            return
        table_row=self._row_of_position(pid)
        if table_row is not None:self.open_offer_formula_editor(table_row,1,focus="short")

    def selected_position_ids(self):
        ids=[]
        model=self.pos.selectionModel()
        if not model:return ids
        for idx in model.selectedRows():
            it=self.pos.item(idx.row(),0)
            if not it:continue
            data=it.data(Qt.UserRole)
            if isinstance(data,list):
                ids.extend(data)
            elif data is not None:
                ids.append(data)
        return list(dict.fromkeys(ids))

    def create_offer_from_selected_positions(self):
        oid=self.offer_id()
        if not oid:
            QMessageBox.information(self,"Neues Angebot aus Auswahl",
                "Bitte zuerst ein bestehendes Angebot auswählen.");return

        ids=self.selected_position_ids()
        if not ids:
            QMessageBox.information(self,"Neues Angebot aus Auswahl",
                "Bitte mindestens eine echte Angebotsposition markieren.\n\n"
                "Mehrere Positionen können mit Strg oder Shift ausgewählt werden.");return

        source=self.db.offer(oid)
        d=OfferSubsetDialog(source,len(ids),self)
        if not d.exec():return
        title,notes=d.data()

        self.db.backup("vor_teilangebot_aus_angebotsauswahl")
        new_oid,count,err=self.db.create_offer_from_offer_positions(oid,ids,title,notes)
        if err:
            QMessageBox.warning(self,"Neues Angebot aus Auswahl",
                f"Das neue Angebot konnte nicht erstellt werden.\n\n{err}");return

        self.refresh_and_select(new_oid)
        target=self.db.offer(new_oid)
        QMessageBox.information(self,"Neues Angebot erstellt",
            f'Angebot {target["number"]} wurde im gleichen Projekt angelegt.\n\n'
            f'Übernommen: {count} Position(en)\n\n'
            "Das ursprüngliche Angebot bleibt unverändert. "
            "Das neue Angebot steht jetzt auch im Aufmaß unter „Position aus Angebot übernehmen“ zur Verfügung.")

    def copy_offer_position(self):
        pid=self.pos_id()
        if not pid:
            QMessageBox.information(self,"Position kopieren","Bitte zuerst eine Angebotsposition auswählen.");return
        offer=self.db.offer(self.current_offer)
        d=PositionCopyDialog(self.db,offer["project_id"],self)
        # Das aktuelle Angebot bleibt als mögliches Ziel vorhanden; sinnvoll für Duplikate.
        if not d.exec():return
        target_oid,title=d.data()
        self.db.backup("vor_position_kopieren")
        created_offer=False
        if target_oid is None:
            target_oid=self.db.add_offer(offer["project_id"],title or "Nachtrag / Zusatzangebot","Position kopiert")
            created_offer=True
        new_pid,err=self.db.copy_offer_position(pid,target_oid)
        if err:
            QMessageBox.warning(self,"Position kopieren",err);return
        target=self.db.offer(target_oid)
        QMessageBox.information(self,"Position kopiert",
            f'Die Position wurde in Angebot {target["number"]} kopiert.\n\n'
            f'{"Das neue Angebot wurde angelegt. " if created_offer else ""}'
            "Original und Kopie sind anschließend unabhängig voneinander bearbeitbar.")
        if created_offer:self.refresh_and_select(target_oid)
        elif target_oid==self.current_offer:self.select_offer()

    def delete_offer(self):
        oid=self.offer_id()
        if not oid:
            QMessageBox.information(self,"Angebot löschen","Bitte zuerst links ein Angebot auswählen.")
            return
        offer=self.db.offer(oid)
        used=self.db.offer_measurement_count(oid)
        if used:
            QMessageBox.warning(self,"Angebot geschützt",
                f'Das Angebot {offer["number"]} kann nicht gelöscht werden.\n\n'
                f'{used} Position(en) dieses Angebots werden bereits im Aufmaß verwendet.\n'
                'Die Positionen werden im Aufmaß unter dem aktuellen Projekt des Angebots angezeigt.\n'
                'Entferne sie dort zuerst bewusst mit „Position aus Aufmaß entfernen“.')
            return
        if QMessageBox.question(self,"Angebot löschen",
            f'Angebot {offer["number"]} einschließlich aller Angebotspositionen wirklich löschen?\n\n'
            'Diese Aktion kann nicht rückgängig gemacht werden.',
            QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            self.db.backup("vor_angebot_loeschen")
            ok,_=self.db.delete_offer(oid)
            if ok:self.refresh()

    def delete_position(self):
        pid=self.pos_id()
        if not pid:
            QMessageBox.information(self,"Position löschen","Bitte zuerst rechts eine Angebotsposition auswählen.")
            return
        used=self.db.position_measurement_count(pid)
        if used:
            QMessageBox.warning(self,"Position geschützt",
                "Diese Angebotsposition ist bereits mit dem Aufmaß verbunden und kann deshalb nicht gelöscht werden.\n\n"
                "Entferne sie zuerst bewusst aus dem Aufmaß.")
            return
        if QMessageBox.question(self,"Position löschen",
            "Ausgewählte Angebotsposition wirklich löschen?",
            QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            self.db.backup("vor_angebotsposition_loeschen")
            ok,_=self.db.delete_position(pid)
            if ok:self.select_offer()


# --- E-Rechnung: ZUGFeRD / Factur-X, Profil EN 16931 --------------------------------------------
ZUGFERD_UNIT_CODES={"":"C62","stk":"H87","stk.":"H87","stück":"H87","st":"H87","st.":"H87","m":"MTR","lfm":"MTR","lfdm":"MTR",
    "m²":"MTK","m2":"MTK","qm":"MTK","m³":"MTQ","m3":"MTQ","cbm":"MTQ","std":"HUR","std.":"HUR","h":"HUR","kg":"KGM","t":"TNE",
    "pauschal":"LS","psch":"LS","psch.":"LS","pausch.":"LS","l":"LTR","km":"KMT","tag":"DAY","tage":"DAY","cm":"CMT","mm":"MMT"}
ZUGFERD_TYPE_CODES={"Schlussrechnung":"877","Teilrechnung":"875","Abschlagsrechnung":"875"}

def einvoice_settings():
    return QSettings(str(DATA_ROOT/"settings"/"erechnung.ini"),QSettings.IniFormat)

def einvoice_enabled():
    return str(einvoice_settings().value("enabled","true")).lower() not in ("false","0","no")

def _zf_money(value):
    from decimal import Decimal,ROUND_HALF_UP
    return Decimal(str(value or 0)).quantize(Decimal("0.01"),rounding=ROUND_HALF_UP)

def _zf_date(value):
    text=str(value or "").strip()[:10]
    for fmt in ("%Y-%m-%d","%d.%m.%Y"):
        try:return datetime.strptime(text,fmt).strftime("%Y%m%d")
        except ValueError:pass
    return None

def zugferd_invoice_data(db,iid):
    """Alle Angaben der E-Rechnung. Rückgabe: (Daten, fehlende Pflichtangaben, Hinweise)."""
    from decimal import Decimal
    inv=db.invoice(iid);company=db.company_settings();missing=[];hints=[]
    customer=db.conn.execute("SELECT c.* FROM customers c JOIN projects p ON p.customer_id=c.id WHERE p.id=?",(inv["project_id"],)).fetchone()
    def co(key):return str((company[key] if company and key in company.keys() else "") or "").strip()
    def cu(key):return str((customer[key] if customer and key in customer.keys() else "") or "").strip()
    reverse=str(inv["tax_mode"] or "").startswith("Steuerschuldnerschaft")
    rate=Decimal("0") if reverse else Decimal(str(inv["vat_rate"] or 0))
    category="AE" if reverse else ("S" if rate>0 else "E")
    cumulative=bool(inv["deduct_previous"]) and inv["invoice_type"] in ("Teilrechnung","Schlussrechnung")
    lines=[]
    for p in db.invoice_positions(iid):
        price=Decimal(str(p["unit_price"] or 0));unit=ZUGFERD_UNIT_CODES.get(str(p["unit"] or "").strip().lower(),"C62")
        if cumulative:quantity=Decimal(str(p["cumulative_quantity"] or 0));net=_zf_money(quantity*price)
        else:
            net=_zf_money(p["line_total"]);quantity=Decimal(str(p["new_quantity"] or 0))
            if _zf_money(quantity*price)!=net:
                quantity=Decimal(str(p["cumulative_quantity"] or 0))
                if _zf_money(quantity*price)!=net:quantity=Decimal(1);price=net;unit="LS"
        if quantity==0 and net==0:continue
        if price<0:price=-price;quantity=-quantity
        lines.append({"no":str(p["position_no"] or "").strip(),"name":one_line(p["short_text"]) or "Position",
                      "description":str(p["long_text"] or "").strip() if "long_text" in p.keys() else "",
                      "quantity":quantity,"unit":unit,"price":price,"net":net})
    line_total=sum((x["net"] for x in lines),Decimal("0.00"))
    tax=_zf_money(line_total*rate/Decimal(100));grand=line_total+tax
    settlement=db.cumulative_invoice_settlement(iid)
    prepaid=_zf_money(settlement["settled"]) if cumulative else Decimal("0.00")
    due=grand-prepaid
    if not lines:missing.append("Die Rechnung enthält keine Positionen mit Menge.")
    app_net=_zf_money(settlement["cumulative_net"])
    if lines and app_net!=line_total:
        missing.append(f"Rundungsabweichung zwischen Rechnungssumme ({money(app_net)}) und Summe der Positionen ({money(line_total)}).")
    seller_vat=co("vat_id").replace(" ","").upper();seller_tax=co("tax_no")
    for key,label in (("company_name","Firmenname"),("street","Straße"),("zip","PLZ"),("city","Ort")):
        if not co(key):missing.append(f"Eigene Firmendaten: {label} fehlt (Einstellungen).")
    if not seller_vat and not seller_tax:missing.append("Eigene Firmendaten: USt-IdNr. oder Steuernummer fehlt (Einstellungen).")
    if not cu("company"):missing.append("Kunde: Name fehlt.")
    for key,label in (("street","Straße"),("zip","PLZ"),("city","Ort")):
        if not cu(key):hints.append(f"Kunde: {label} fehlt.")
    buyer_vat=cu("vat_id").replace(" ","").upper()
    for label,value in (("Eigene USt-IdNr.",seller_vat),("USt-IdNr. des Kunden",buyer_vat)):
        if value and not (len(value)>4 and value[:2].isalpha()):
            missing.append(f"{label} muss mit dem Länderkennzeichen beginnen, z. B. DE123456789 (jetzt: {value}).")
    if reverse and not buyer_vat:
        missing.append("Kunde: USt-IdNr. fehlt – bei § 13b in der E-Rechnung Pflicht (Kunde bearbeiten).")
    issue=_zf_date(inv["created_at"])
    if not issue:missing.append("Rechnungsdatum fehlt.")
    iban=co("iban").replace(" ","").upper()
    if not iban:hints.append("Eigene Firmendaten: IBAN fehlt – die E-Rechnung enthält dann keine Bankverbindung.")
    start=_zf_date(inv["performance_from"]);end=_zf_date(inv["performance_to"])
    if not start and not end:hints.append("Leistungszeitraum fehlt.")
    terms=[]
    if inv["due_date"]:terms.append(f'Zahlbar ohne Abzug bis {de_date(inv["due_date"])}.')
    skonto=float(inv["skonto_percent"] or 0)
    if skonto>0:terms.append(f'{de_num(skonto)} % Skonto bei Zahlung bis {de_date(inv["skonto_due_date"])}.')
    retention=_zf_money(settlement["security"])+_zf_money(settlement["construction"])
    if inv["security_enabled"] and settlement["security"]:
        terms.append(f'Sicherheitseinbehalt {de_num(inv["security_percent"])} %: {money(settlement["security"])}.')
    if inv["construction_enabled"] and settlement["construction"]:
        terms.append(f'Abzug {inv["construction_label"] or "Bauwesen"} {de_num(inv["construction_percent"])} %: {money(settlement["construction"])}.')
    if retention>0:
        terms.append(f'Sofort zahlbar nach Einbehalten: {money(settlement["payable"])}.')
        hints.append("Einbehalte kennt die Norm nicht als eigenes Feld: Sie stehen als Text in den Zahlungsbedingungen, "
                     "der fällige Betrag in den Rechnungsdaten ist der Betrag vor Einbehalt.")
    if not terms and not _zf_date(inv["due_date"]):terms.append("Zahlbar sofort ohne Abzug.")
    notes=[]
    label=inv["invoice_type"]
    if inv["invoice_type"]=="Teilrechnung":label=f'{max(1,int(inv["installment_no"] or 1))}. Teilrechnung'
    notes.append(" – ".join(x for x in (label,one_line(inv["title"])) if x))
    if cumulative:
        notes.append("Kumulierte Abrechnung: Die Positionen zeigen den gesamten bisherigen Leistungsstand. "
                     "Zahlungen und Skonti früherer Rechnungen sind als bereits gezahlter Betrag abgezogen.")
    if str(inv["notes"] or "").strip():notes.append(str(inv["notes"]).strip())
    data={"number":str(inv["number"]),"type_code":ZUGFERD_TYPE_CODES.get(inv["invoice_type"],"380"),"issue_date":issue,
          "notes":notes,"buyer_reference":cu("buyer_reference"),
          "seller":{"name":co("company_name"),"street":co("street"),"zip":co("zip"),"city":co("city"),"vat_id":seller_vat,
                    "tax_no":seller_tax,"contact":co("managing_director"),"phone":co("phone"),"email":co("email")},
          "buyer":{"name":cu("company"),"contact":cu("contact"),"street":cu("street"),"zip":cu("zip"),"city":cu("city"),
                   "vat_id":buyer_vat,"email":cu("email")},
          "project_no":str(inv["project_number"] or ""),"project_name":one_line(inv["project_name"]),
          "period_start":start,"period_end":end,"iban":iban,"bic":co("bic").replace(" ","").upper(),
          "category":category,"rate":rate,"due_date":_zf_date(inv["due_date"]),"terms":" ".join(terms),
          "lines":lines,"line_total":line_total,"tax":tax,"grand":grand,"prepaid":prepaid,"due":due,
          "title":f'{inv["invoice_type"]} {inv["number"]}'}
    return data,missing,hints

def zugferd_xml(d):
    """Factur-X/ZUGFeRD-XML (UN/CEFACT CII) im Profil EN 16931."""
    from xml.sax.saxutils import escape
    def t(value):return escape(str(value))
    def amount(value):return f"{value:.2f}"
    def number(value):
        text=f"{value:.4f}".rstrip("0").rstrip(".");return text or "0"
    def date(value):return f'<udt:DateTimeString format="102">{value}</udt:DateTimeString>'
    def tax_block(with_amounts):
        out="<ram:ApplicableTradeTax>"
        if with_amounts:out+=f'<ram:CalculatedAmount>{amount(d["tax"])}</ram:CalculatedAmount>'
        out+="<ram:TypeCode>VAT</ram:TypeCode>"
        if with_amounts and d["category"]=="AE":
            out+="<ram:ExemptionReason>Steuerschuldnerschaft des Leistungsempfängers (§ 13b UStG) – Reverse charge</ram:ExemptionReason>"
        if with_amounts and d["category"]=="E":
            out+="<ram:ExemptionReason>Es wird keine Umsatzsteuer berechnet.</ram:ExemptionReason>"
        if with_amounts:out+=f'<ram:BasisAmount>{amount(d["line_total"])}</ram:BasisAmount>'
        out+=f'<ram:CategoryCode>{d["category"]}</ram:CategoryCode>'
        if with_amounts and d["category"]=="AE":out+="<ram:ExemptionReasonCode>VATEX-EU-AE</ram:ExemptionReasonCode>"
        return out+f'<ram:RateApplicablePercent>{number(d["rate"])}</ram:RateApplicablePercent></ram:ApplicableTradeTax>'
    def party(tag,p,seller):
        out=f"<ram:{tag}>"
        if seller and not p.get("vat_id") and p.get("tax_no"):out+=f"<ram:ID>{t(p['tax_no'])}</ram:ID>"
        out+=f"<ram:Name>{t(p['name'])}</ram:Name>"
        if p.get("contact") or p.get("phone") or (seller and p.get("email")):
            out+="<ram:DefinedTradeContact>"
            if p.get("contact"):out+=f"<ram:PersonName>{t(p['contact'])}</ram:PersonName>"
            if p.get("phone"):out+=f"<ram:TelephoneUniversalCommunication><ram:CompleteNumber>{t(p['phone'])}</ram:CompleteNumber></ram:TelephoneUniversalCommunication>"
            if p.get("email"):out+=f"<ram:EmailURIUniversalCommunication><ram:URIID>{t(p['email'])}</ram:URIID></ram:EmailURIUniversalCommunication>"
            out+="</ram:DefinedTradeContact>"
        out+="<ram:PostalTradeAddress>"
        if p.get("zip"):out+=f"<ram:PostcodeCode>{t(p['zip'])}</ram:PostcodeCode>"
        if p.get("street"):out+=f"<ram:LineOne>{t(p['street'])}</ram:LineOne>"
        if p.get("city"):out+=f"<ram:CityName>{t(p['city'])}</ram:CityName>"
        out+="<ram:CountryID>DE</ram:CountryID></ram:PostalTradeAddress>"
        if p.get("email"):out+=f'<ram:URIUniversalCommunication><ram:URIID schemeID="EM">{t(p["email"])}</ram:URIID></ram:URIUniversalCommunication>'
        if p.get("vat_id"):out+=f'<ram:SpecifiedTaxRegistration><ram:ID schemeID="VA">{t(p["vat_id"])}</ram:ID></ram:SpecifiedTaxRegistration>'
        if p.get("tax_no"):out+=f'<ram:SpecifiedTaxRegistration><ram:ID schemeID="FC">{t(p["tax_no"])}</ram:ID></ram:SpecifiedTaxRegistration>'
        return out+f"</ram:{tag}>"
    x='<?xml version="1.0" encoding="UTF-8"?>\n'
    x+=('<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" '
        'xmlns:qdt="urn:un:unece:uncefact:data:standard:QualifiedDataType:100" '
        'xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100" '
        'xmlns:xs="http://www.w3.org/2001/XMLSchema" '
        'xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">')
    x+=("<rsm:ExchangedDocumentContext><ram:GuidelineSpecifiedDocumentContextParameter>"
        "<ram:ID>urn:cen.eu:en16931:2017</ram:ID></ram:GuidelineSpecifiedDocumentContextParameter></rsm:ExchangedDocumentContext>")
    x+=f'<rsm:ExchangedDocument><ram:ID>{t(d["number"])}</ram:ID><ram:TypeCode>{d["type_code"]}</ram:TypeCode>'
    x+=f'<ram:IssueDateTime>{date(d["issue_date"])}</ram:IssueDateTime>'
    for note in d["notes"]:
        if note:x+=f"<ram:IncludedNote><ram:Content>{t(note)}</ram:Content></ram:IncludedNote>"
    x+="</rsm:ExchangedDocument><rsm:SupplyChainTradeTransaction>"
    for index,line in enumerate(d["lines"],1):
        x+=f"<ram:IncludedSupplyChainTradeLineItem><ram:AssociatedDocumentLineDocument><ram:LineID>{index}</ram:LineID></ram:AssociatedDocumentLineDocument>"
        x+="<ram:SpecifiedTradeProduct>"
        if line["no"]:x+=f"<ram:SellerAssignedID>{t(line['no'])}</ram:SellerAssignedID>"
        x+=f"<ram:Name>{t(line['name'])}</ram:Name>"
        if line["description"]:x+=f"<ram:Description>{t(line['description'])}</ram:Description>"
        x+="</ram:SpecifiedTradeProduct>"
        x+=f"<ram:SpecifiedLineTradeAgreement><ram:NetPriceProductTradePrice><ram:ChargeAmount>{number(line['price'])}</ram:ChargeAmount></ram:NetPriceProductTradePrice></ram:SpecifiedLineTradeAgreement>"
        x+=f'<ram:SpecifiedLineTradeDelivery><ram:BilledQuantity unitCode="{line["unit"]}">{number(line["quantity"])}</ram:BilledQuantity></ram:SpecifiedLineTradeDelivery>'
        x+=f"<ram:SpecifiedLineTradeSettlement>{tax_block(False)}<ram:SpecifiedTradeSettlementLineMonetarySummation><ram:LineTotalAmount>{amount(line['net'])}</ram:LineTotalAmount></ram:SpecifiedTradeSettlementLineMonetarySummation></ram:SpecifiedLineTradeSettlement>"
        x+="</ram:IncludedSupplyChainTradeLineItem>"
    x+="<ram:ApplicableHeaderTradeAgreement>"
    if d["buyer_reference"]:x+=f"<ram:BuyerReference>{t(d['buyer_reference'])}</ram:BuyerReference>"
    x+=party("SellerTradeParty",d["seller"],True)+party("BuyerTradeParty",d["buyer"],False)
    if d["project_no"]:
        x+=f"<ram:SpecifiedProcuringProject><ram:ID>{t(d['project_no'])}</ram:ID><ram:Name>{t(d['project_name'] or d['project_no'])}</ram:Name></ram:SpecifiedProcuringProject>"
    x+="</ram:ApplicableHeaderTradeAgreement><ram:ApplicableHeaderTradeDelivery>"
    if d["period_end"] or d["period_start"]:
        x+=f"<ram:ActualDeliverySupplyChainEvent><ram:OccurrenceDateTime>{date(d['period_end'] or d['period_start'])}</ram:OccurrenceDateTime></ram:ActualDeliverySupplyChainEvent>"
    x+="</ram:ApplicableHeaderTradeDelivery><ram:ApplicableHeaderTradeSettlement>"
    x+=f"<ram:PaymentReference>{t(d['number'])}</ram:PaymentReference><ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>"
    if d["iban"]:
        x+=f"<ram:SpecifiedTradeSettlementPaymentMeans><ram:TypeCode>58</ram:TypeCode><ram:PayeePartyCreditorFinancialAccount><ram:IBANID>{t(d['iban'])}</ram:IBANID></ram:PayeePartyCreditorFinancialAccount>"
        if d["bic"]:x+=f"<ram:PayeeSpecifiedCreditorFinancialInstitution><ram:BICID>{t(d['bic'])}</ram:BICID></ram:PayeeSpecifiedCreditorFinancialInstitution>"
        x+="</ram:SpecifiedTradeSettlementPaymentMeans>"
    x+=tax_block(True)
    if d["period_start"] and d["period_end"]:
        x+=f"<ram:BillingSpecifiedPeriod><ram:StartDateTime>{date(d['period_start'])}</ram:StartDateTime><ram:EndDateTime>{date(d['period_end'])}</ram:EndDateTime></ram:BillingSpecifiedPeriod>"
    if d["terms"] or d["due_date"]:
        x+="<ram:SpecifiedTradePaymentTerms>"
        if d["terms"]:x+=f"<ram:Description>{t(d['terms'])}</ram:Description>"
        if d["due_date"]:x+=f"<ram:DueDateDateTime>{date(d['due_date'])}</ram:DueDateDateTime>"
        x+="</ram:SpecifiedTradePaymentTerms>"
    x+=(f"<ram:SpecifiedTradeSettlementHeaderMonetarySummation><ram:LineTotalAmount>{amount(d['line_total'])}</ram:LineTotalAmount>"
        f"<ram:TaxBasisTotalAmount>{amount(d['line_total'])}</ram:TaxBasisTotalAmount>"
        f'<ram:TaxTotalAmount currencyID="EUR">{amount(d["tax"])}</ram:TaxTotalAmount>'
        f"<ram:GrandTotalAmount>{amount(d['grand'])}</ram:GrandTotalAmount>")
    if d["prepaid"]:x+=f"<ram:TotalPrepaidAmount>{amount(d['prepaid'])}</ram:TotalPrepaidAmount>"
    x+=f"<ram:DuePayableAmount>{amount(d['due'])}</ram:DuePayableAmount></ram:SpecifiedTradeSettlementHeaderMonetarySummation>"
    x+="</ram:ApplicableHeaderTradeSettlement></rsm:SupplyChainTradeTransaction></rsm:CrossIndustryInvoice>"
    return x.encode("utf-8")

def _zugferd_xmp(title,author,creator,producer,created):
    from xml.sax.saxutils import escape
    def prop(name,description):
        return ('<rdf:li rdf:parseType="Resource"><pdfaProperty:name>'+name+'</pdfaProperty:name>'
                '<pdfaProperty:valueType>Text</pdfaProperty:valueType><pdfaProperty:category>external</pdfaProperty:category>'
                '<pdfaProperty:description>'+description+'</pdfaProperty:description></rdf:li>')
    xmp=('<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>\n<x:xmpmeta xmlns:x="adobe:ns:meta/">\n'
         '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n'
         '<rdf:Description rdf:about="" xmlns:pdfaid="http://www.aiim.org/pdfa/ns/id/"><pdfaid:part>3</pdfaid:part>'
         '<pdfaid:conformance>B</pdfaid:conformance></rdf:Description>\n'
         '<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title><rdf:Alt>'
         '<rdf:li xml:lang="x-default">'+escape(title)+'</rdf:li></rdf:Alt></dc:title><dc:creator><rdf:Seq><rdf:li>'+escape(author)+
         '</rdf:li></rdf:Seq></dc:creator></rdf:Description>\n'
         '<rdf:Description rdf:about="" xmlns:pdf="http://ns.adobe.com/pdf/1.3/"><pdf:Producer>'+escape(producer)+'</pdf:Producer></rdf:Description>\n'
         '<rdf:Description rdf:about="" xmlns:xmp="http://ns.adobe.com/xap/1.0/"><xmp:CreatorTool>'+escape(creator)+'</xmp:CreatorTool>'
         '<xmp:CreateDate>'+created+'</xmp:CreateDate><xmp:ModifyDate>'+created+'</xmp:ModifyDate></rdf:Description>\n'
         '<rdf:Description rdf:about="" xmlns:pdfaExtension="http://www.aiim.org/pdfa/ns/extension/" '
         'xmlns:pdfaSchema="http://www.aiim.org/pdfa/ns/schema#" xmlns:pdfaProperty="http://www.aiim.org/pdfa/ns/property#">'
         '<pdfaExtension:schemas><rdf:Bag><rdf:li rdf:parseType="Resource"><pdfaSchema:schema>Factur-X PDFA Extension Schema</pdfaSchema:schema>'
         '<pdfaSchema:namespaceURI>urn:factur-x:pdfa:CrossIndustryDocument:invoice:1p0#</pdfaSchema:namespaceURI>'
         '<pdfaSchema:prefix>fx</pdfaSchema:prefix><pdfaSchema:property><rdf:Seq>'
         +prop("DocumentFileName","The name of the embedded XML document")+prop("DocumentType","The type of the hybrid document in capital letters, e.g. INVOICE or ORDER")
         +prop("Version","The actual version of the standard applying to the embedded XML document")
         +prop("ConformanceLevel","The conformance level of the embedded XML document")+
         '</rdf:Seq></pdfaSchema:property></rdf:li></rdf:Bag></pdfaExtension:schemas></rdf:Description>\n'
         '<rdf:Description rdf:about="" xmlns:fx="urn:factur-x:pdfa:CrossIndustryDocument:invoice:1p0#"><fx:DocumentType>INVOICE</fx:DocumentType>'
         '<fx:DocumentFileName>factur-x.xml</fx:DocumentFileName><fx:Version>1.0</fx:Version>'
         '<fx:ConformanceLevel>EN 16931</fx:ConformanceLevel></rdf:Description>\n'
         '</rdf:RDF>\n</x:xmpmeta>\n<?xpacket end="w"?>')
    return xmp.encode("utf-8")

def zugferd_embed(pdf_path,xml_bytes,title,author):
    """Macht aus dem fertigen Rechnungs-PDF ein PDF/A-3 mit eingebetteter factur-x.xml."""
    import hashlib
    from PySide6.QtGui import QColorSpace
    from pypdf import PdfReader,PdfWriter
    from pypdf.generic import (ArrayObject,ByteStringObject,DecodedStreamObject,DictionaryObject,NameObject,NumberObject,
                               TextStringObject,create_string_object)
    reader=PdfReader(str(pdf_path));writer=PdfWriter(clone_from=reader);root=writer._root_object
    now=datetime.now().astimezone();offset=now.strftime("%z") or "+0000"
    pdf_date=now.strftime("D:%Y%m%d%H%M%S")+f"{offset[:3]}'{offset[3:]}'"
    xmp_date=now.strftime("%Y-%m-%dT%H:%M:%S")+f"{offset[:3]}:{offset[3:]}"
    creator=f"{APP_NAME} {APP_VERSION}";producer="Qt / pypdf"
    embedded=DecodedStreamObject();embedded.set_data(xml_bytes);embedded=embedded.flate_encode()
    embedded.update({NameObject("/Type"):NameObject("/EmbeddedFile"),NameObject("/Subtype"):NameObject("/text/xml"),
        NameObject("/Params"):DictionaryObject({NameObject("/CheckSum"):ByteStringObject(hashlib.md5(xml_bytes).digest()),
            NameObject("/ModDate"):TextStringObject(pdf_date),NameObject("/Size"):NumberObject(len(xml_bytes))})})
    embedded_ref=writer._add_object(embedded)
    filespec=DictionaryObject({NameObject("/Type"):NameObject("/Filespec"),NameObject("/AFRelationship"):NameObject("/Alternative"),
        NameObject("/Desc"):TextStringObject("Factur-X/ZUGFeRD-Rechnung"),NameObject("/F"):create_string_object("factur-x.xml"),
        NameObject("/UF"):create_string_object("factur-x.xml"),
        NameObject("/EF"):DictionaryObject({NameObject("/F"):embedded_ref,NameObject("/UF"):embedded_ref})})
    filespec_ref=writer._add_object(filespec)
    names=root.get("/Names");names=names.get_object() if names is not None else DictionaryObject()
    names[NameObject("/EmbeddedFiles")]=DictionaryObject({NameObject("/Names"):ArrayObject([create_string_object("factur-x.xml"),filespec_ref])})
    root[NameObject("/Names")]=names;root[NameObject("/AF")]=ArrayObject([filespec_ref])
    if "/OutputIntents" not in root:
        icc=DecodedStreamObject();icc.set_data(bytes(QColorSpace(QColorSpace.SRgb).iccProfile()));icc=icc.flate_encode()
        icc.update({NameObject("/N"):NumberObject(3)})
        intent=DictionaryObject({NameObject("/Type"):NameObject("/OutputIntent"),NameObject("/S"):NameObject("/GTS_PDFA1"),
            NameObject("/OutputConditionIdentifier"):TextStringObject("sRGB IEC61966-2.1"),NameObject("/Info"):TextStringObject("sRGB IEC61966-2.1"),
            NameObject("/RegistryName"):TextStringObject("http://www.color.org"),NameObject("/DestOutputProfile"):writer._add_object(icc)})
        root[NameObject("/OutputIntents")]=ArrayObject([writer._add_object(intent)])
    metadata=DecodedStreamObject();metadata.set_data(_zugferd_xmp(title,author,creator,producer,xmp_date))
    metadata.update({NameObject("/Type"):NameObject("/Metadata"),NameObject("/Subtype"):NameObject("/XML")})
    root[NameObject("/Metadata")]=writer._add_object(metadata)
    writer._info=None
    writer.add_metadata({"/Title":title,"/Author":author,"/Creator":creator,"/Producer":producer,
                         "/CreationDate":pdf_date,"/ModDate":pdf_date})
    writer.pdf_header="%PDF-1.7"
    identifier=ByteStringObject(hashlib.md5((title+pdf_date).encode("utf-8")).digest())
    writer._ID=ArrayObject([identifier,identifier])
    temporary=Path(str(pdf_path)+".erechnung.tmp")
    with open(temporary,"wb") as handle:writer.write(handle)
    os.replace(temporary,pdf_path)

def create_einvoice_pdf(db,iid,pdf_path):
    """Bettet die E-Rechnung in das PDF ein. Rückgabe: (eingebettet, Meldungstext)."""
    if not einvoice_enabled():return False,""
    try:
        data,missing,hints=zugferd_invoice_data(db,iid)
        if missing:
            return False,("Das PDF wurde als normale Rechnung erstellt – für eine E-Rechnung (ZUGFeRD) fehlen noch Angaben:\n\n• "
                          +"\n• ".join(missing))
        zugferd_embed(pdf_path,zugferd_xml(data),data["title"],data["seller"]["name"])
        text="Das PDF ist eine E-Rechnung (ZUGFeRD, Profil EN 16931): Die Rechnungsdaten sind maschinenlesbar eingebettet."
        if hints:text+="\n\nHinweise:\n• "+"\n• ".join(hints)
        return True,text
    except Exception as error:
        return False,"Das PDF wurde als normale Rechnung erstellt – die E-Rechnung konnte nicht eingebettet werden:\n"+str(error)


class PartialInvoiceDialog(QDialog):
    def __init__(self,db,parent=None,row=None,project_id=None,source_mode="Aufmaß"):
        super().__init__(parent);self.db=db;self.row=row;self.source_mode=source_mode
        self.setWindowTitle("Rechnungsentwurf bearbeiten" if row else
                            ("Rechnung aus Aufmaß erzeugen" if source_mode=="Aufmaß" else "Freie Rechnung"))
        self.setMinimumWidth(590)
        f=QFormLayout(self)

        self.project=QComboBox()
        projects=db.invoice_projects() if source_mode=="Aufmaß" else db.all_invoice_projects()
        for p in projects:
            label=f'{one_line(p["number"])} – {one_line(p["name"])} – {one_line(p["company"])}'
            self.project.addItem(label,p["id"])
            self.project.setItemData(self.project.count()-1,label,Qt.ToolTipRole)
        self.project.setMinimumWidth(420)
        self.project.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.project.setMinimumContentsLength(45)
        if project_id is not None:
            self.project.setCurrentIndex(max(self.project.findData(project_id),0))
        self.invoice_type=QComboBox();self.invoice_type.addItems(
            ["Rechnung","Teilrechnung","Abschlagsrechnung","Schlussrechnung"])
        self.invoice_type.setCurrentText(row["invoice_type"] if row else "Rechnung")
        self.installment_no=QSpinBox();self.installment_no.setRange(1,999);self.installment_no.setSuffix(". Teilrechnung")
        self.deduct_previous=QCheckBox("Vorherige freigegebene Teilrechnungen kumulativ abziehen")
        self.deduct_previous.setChecked(True)
        self.title=QLineEdit(row["invoice_type"] if row else "Rechnung")
        self.due=QDateEdit(QDate.currentDate().addDays(14));self.due.setCalendarPopup(True);self.due.setDisplayFormat("dd.MM.yyyy")
        self.tax_mode=QComboBox()
        self.tax_mode.addItems(["Normale Umsatzsteuer","Steuerschuldnerschaft §13b"])
        self.vat=QDoubleSpinBox();self.vat.setRange(0,100);self.vat.setDecimals(2);self.vat.setValue(19);self.vat.setSuffix(" %")
        self.performance_from=QDateEdit(QDate.currentDate());self.performance_from.setCalendarPopup(True);self.performance_from.setDisplayFormat("dd.MM.yyyy")
        self.performance_to=QDateEdit(QDate.currentDate());self.performance_to.setCalendarPopup(True);self.performance_to.setDisplayFormat("dd.MM.yyyy")
        self.skonto=QDoubleSpinBox();self.skonto.setRange(0,100);self.skonto.setDecimals(2);self.skonto.setSuffix(" %")
        self.skonto_due=QDateEdit(QDate.currentDate().addDays(7));self.skonto_due.setCalendarPopup(True);self.skonto_due.setDisplayFormat("dd.MM.yyyy")

        self.security_enabled=QCheckBox("Sicherheitseinbehalt anwenden")
        self.security_percent=QDoubleSpinBox();self.security_percent.setRange(0,100);self.security_percent.setDecimals(2);self.security_percent.setValue(5);self.security_percent.setSuffix(" %")
        self.construction_enabled=QCheckBox("Weiteren Bau-Abzug anwenden")
        self.construction_label=QLineEdit("Bauwesen")
        self.construction_percent=QDoubleSpinBox();self.construction_percent.setRange(0,100);self.construction_percent.setDecimals(2);self.construction_percent.setValue(1.8);self.construction_percent.setSuffix(" %")
        self.notes=QTextEdit()

        f.addRow("Projekt *",self.project)
        f.addRow("Rechnungsart *",self.invoice_type)
        f.addRow("Laufende Stufe",self.installment_no)
        self.installment_label=f.labelForField(self.installment_no)
        f.addRow("Kumulative Abrechnung",self.deduct_previous)
        self.cumulative_label=f.labelForField(self.deduct_previous)
        f.addRow("Bezeichnung",self.title)
        f.addRow("Leistungszeitraum von",self.performance_from)
        f.addRow("Leistungszeitraum bis",self.performance_to)
        f.addRow("Steuerart",self.tax_mode)
        f.addRow("MwSt.",self.vat)
        f.addRow("Skonto",self.skonto)
        f.addRow("Skonto bis",self.skonto_due)

        deductions=QGroupBox("Optionale Rechnungsabzüge")
        dg=QFormLayout(deductions)
        dg.addRow("",self.security_enabled)
        dg.addRow("Sicherheitseinbehalt",self.security_percent)
        dg.addRow("",self.construction_enabled)
        dg.addRow("Bezeichnung",self.construction_label)
        dg.addRow("Bau-Abzug",self.construction_percent)
        f.addRow(deductions)

        f.addRow("Fällig am",self.due)
        f.addRow("Hinweis / Text",self.notes)

        if row:
            i=self.project.findData(row["project_id"]);self.project.setCurrentIndex(max(i,0))
            self.project.setEnabled(False)  # Projektwechsel würde die Positionslogik brechen
            self.invoice_type.setEnabled(False)
            self.installment_no.setValue(int(row["installment_no"] or 1))
            self.deduct_previous.setChecked(bool(row["deduct_previous"]))
            self.title.setText(row["title"] or "Teilrechnung")
            def set_date(widget,value):
                q=QDate.fromString(value or "","yyyy-MM-dd")
                if q.isValid():widget.setDate(q)
            set_date(self.due,row["due_date"])
            set_date(self.performance_from,row["performance_from"])
            set_date(self.performance_to,row["performance_to"])
            set_date(self.skonto_due,row["skonto_due_date"])
            self.vat.setValue(float(row["vat_rate"] or 0))
            self.skonto.setValue(float(row["skonto_percent"] or 0))
            self.security_enabled.setChecked(bool(row["security_enabled"]))
            self.security_percent.setValue(float(row["security_percent"] or 5))
            self.construction_enabled.setChecked(bool(row["construction_enabled"]))
            self.construction_percent.setValue(float(row["construction_percent"] or 1.8))
            self.construction_label.setText(row["construction_label"] or "Bauwesen")
            i=self.tax_mode.findText(row["tax_mode"] or "Normale Umsatzsteuer")
            self.tax_mode.setCurrentIndex(max(i,0))
            self.notes.setPlainText(row["notes"] or "")

        self.tax_mode.currentTextChanged.connect(self.tax_changed)
        self.invoice_type.currentTextChanged.connect(self.invoice_type_changed)
        self.project.currentIndexChanged.connect(self.invoice_type_changed)
        self.security_enabled.toggled.connect(self.deduction_changed)
        self.construction_enabled.toggled.connect(self.deduction_changed)
        bb=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept);bb.rejected.connect(self.reject);f.addRow(bb)
        self.tax_changed()
        self.invoice_type_changed()

    def tax_changed(self):
        reverse=self.tax_mode.currentText().startswith("Steuerschuldnerschaft")
        self.vat.setEnabled(not reverse)
        if reverse:self.vat.setValue(0)
        self.deduction_changed()

    def deduction_changed(self):
        self.security_percent.setEnabled(self.security_enabled.isChecked())
        active=self.construction_enabled.isChecked()
        self.construction_percent.setEnabled(active)
        self.construction_label.setEnabled(active)

    def invoice_type_changed(self):
        old_title=self.title.text().strip()
        standard=("","Rechnung","Teilrechnung","Abschlagsrechnung","Schlussrechnung")
        if old_title in standard:self.title.setText(self.invoice_type.currentText())
        is_partial=self.invoice_type.currentText()=="Teilrechnung"
        cumulative=self.invoice_type.currentText() in ("Teilrechnung","Schlussrechnung")
        self.installment_label.setVisible(is_partial)
        self.installment_no.setVisible(is_partial)
        self.cumulative_label.setVisible(cumulative)
        self.deduct_previous.setVisible(cumulative)
        self.installment_no.setEnabled(is_partial)
        self.deduct_previous.setEnabled(cumulative)
        if not cumulative:self.deduct_previous.setChecked(False)
        elif self.invoice_type.currentText()=="Teilrechnung":
            self.deduct_previous.setChecked(True)
            pid=self.project.currentData()
            if pid is not None:self.installment_no.setValue(self.db.next_installment_no(pid))

    def data(self):
        return (
            self.project.currentData(),
            self.title.text().strip(),
            self.due.date().toString("yyyy-MM-dd"),
            self.vat.value(),
            self.tax_mode.currentText(),
            self.performance_from.date().toString("yyyy-MM-dd"),
            self.performance_to.date().toString("yyyy-MM-dd"),
            self.skonto.value(),
            self.skonto_due.date().toString("yyyy-MM-dd"),
            self.security_enabled.isChecked(),
            self.security_percent.value(),
            self.construction_enabled.isChecked(),
            self.construction_percent.value(),
            self.construction_label.text().strip() or "Bauwesen",
            self.notes.toPlainText().strip()
        )

    def new_invoice_data(self):
        old=self.data()
        return (old[0],self.invoice_type.currentText(),self.source_mode,
                self.installment_no.value(),self.deduct_previous.isChecked(),*old[1:])

class HistoricalInvoiceDialog(QDialog):
    """Erfasst einen unveränderten, außerhalb von Aufmaßwerk erstellten Beleg."""
    def __init__(self,db,parent=None,project_id=None):
        super().__init__(parent);self.db=db
        self.setWindowTitle("Vorhandene Teil-/Abschlagsrechnung übernehmen")
        self.setMinimumWidth(660)
        f=QFormLayout(self)
        info=QLabel(
            "Dieser Beleg wurde bereits außerhalb von Aufmaßwerk ausgestellt. "
            "Seine Originalnummer bleibt erhalten und verändert den Aufmaßwerk-Nummernkreis nicht."
        );info.setWordWrap(True);f.addRow(info)
        self.project=QComboBox()
        for p in db.all_invoice_projects():
            self.project.addItem(
                f'{one_line(p["number"])} – {one_line(p["name"])} – {one_line(p["company"])}',p["id"])
        if project_id is not None:self.project.setCurrentIndex(max(0,self.project.findData(project_id)))
        self.invoice_type=QComboBox();self.invoice_type.addItems(["Teilrechnung","Abschlagsrechnung"])
        self.number=QLineEdit();self.number.setPlaceholderText("Originalnummer des bereits versandten Belegs")
        self.invoice_date=QDateEdit(QDate.currentDate());self.invoice_date.setCalendarPopup(True);self.invoice_date.setDisplayFormat("dd.MM.yyyy")
        self.installment_no=QSpinBox();self.installment_no.setRange(1,999);self.installment_no.setSuffix(". Teilrechnung")
        self.net=QDoubleSpinBox();self.net.setRange(0,999999999);self.net.setDecimals(2);self.net.setSuffix(" €")
        self.vat=QDoubleSpinBox();self.vat.setRange(0,100);self.vat.setDecimals(2);self.vat.setValue(19);self.vat.setSuffix(" %")
        self.gross=QDoubleSpinBox();self.gross.setRange(0,999999999);self.gross.setDecimals(2);self.gross.setSuffix(" €")
        calculate=QPushButton("Brutto aus Netto und MwSt. berechnen")
        calculate.clicked.connect(lambda:self.gross.setValue(self.net.value()*(1+self.vat.value()/100)))
        gross_row=QHBoxLayout();gross_row.addWidget(self.gross,1);gross_row.addWidget(calculate)
        self.paid=QDoubleSpinBox();self.paid.setRange(0,999999999);self.paid.setDecimals(2);self.paid.setSuffix(" €")
        self.discount=QDoubleSpinBox();self.discount.setRange(0,999999999);self.discount.setDecimals(2);self.discount.setSuffix(" €")
        full=QPushButton("Ohne Skonto vollständig bezahlt")
        full.clicked.connect(self.set_fully_paid)
        paid_row=QHBoxLayout();paid_row.addWidget(self.paid,1);paid_row.addWidget(full)
        rest_discount=QPushButton("Offenen Rest als Skonto übernehmen")
        rest_discount.clicked.connect(self.set_remaining_as_discount)
        discount_row=QHBoxLayout();discount_row.addWidget(self.discount,1);discount_row.addWidget(rest_discount)
        self.remaining=QLabel()
        self.paid.valueChanged.connect(self.update_remaining)
        self.discount.valueChanged.connect(self.update_remaining)
        self.gross.valueChanged.connect(self.update_remaining)
        self.payment_date=QDateEdit(QDate.currentDate());self.payment_date.setCalendarPopup(True);self.payment_date.setDisplayFormat("dd.MM.yyyy")
        self.pdf=QLineEdit();self.pdf.setReadOnly(True);self.pdf.setPlaceholderText("optional: ursprüngliche PDF-Rechnung")
        browse=icon_button("open","Original-PDF auswählen",self.choose_pdf)
        pdf_row=QHBoxLayout();pdf_row.addWidget(self.pdf,1);pdf_row.addWidget(browse)
        self.notes=QTextEdit();self.notes.setMaximumHeight(90)
        f.addRow("Projekt *",self.project);f.addRow("Belegart *",self.invoice_type)
        f.addRow("Originale Rechnungsnummer *",self.number);f.addRow("Rechnungsdatum *",self.invoice_date)
        f.addRow("Laufende Stufe",self.installment_no);self.installment_label=f.labelForField(self.installment_no)
        f.addRow("Nettobetrag *",self.net);f.addRow("MwSt.",self.vat);f.addRow("Bruttobetrag *",gross_row)
        f.addRow("Tatsächlich gezahlt",paid_row);f.addRow("Skontobetrag",discount_row)
        f.addRow("Danach noch offen",self.remaining);f.addRow("Zahlungsdatum",self.payment_date)
        f.addRow("Original-PDF",pdf_row);f.addRow("Interner Hinweis",self.notes)
        warning=QLabel(
            "Aufmaßwerk erzeugt für diesen historischen Beleg kein neues Rechnungs-PDF. "
            "Tatsächliche Zahlung und gewährtes Skonto werden getrennt dokumentiert und gemeinsam in Folgeabrechnungen berücksichtigt."
        );warning.setWordWrap(True);f.addRow(warning)
        bb=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Save).setText("Vorhandenen Beleg übernehmen")
        bb.accepted.connect(self.accept);bb.rejected.connect(self.reject);f.addRow(bb)
        self.invoice_type.currentTextChanged.connect(self.type_changed);self.type_changed()
        self.update_remaining()

    def set_fully_paid(self):
        self.paid.setValue(self.gross.value());self.discount.setValue(0)

    def set_remaining_as_discount(self):
        self.discount.setValue(max(0.0,self.gross.value()-self.paid.value()))

    def update_remaining(self):
        remaining=max(0.0,self.gross.value()-self.paid.value()-self.discount.value())
        self.remaining.setText(f"<b>{money(remaining)}</b>")

    def type_changed(self):
        partial=self.invoice_type.currentText()=="Teilrechnung"
        self.installment_no.setVisible(partial);self.installment_label.setVisible(partial)

    def choose_pdf(self):
        path,_=QFileDialog.getOpenFileName(self,"Original-PDF auswählen",str(Path.home()),"PDF-Dateien (*.pdf)")
        if path:self.pdf.setText(path)

    def accept(self):
        if self.project.currentData() is None:
            QMessageBox.warning(self,"Vorhandener Beleg","Bitte ein Projekt auswählen.");return
        if not self.number.text().strip():
            QMessageBox.warning(self,"Vorhandener Beleg","Bitte die originale Rechnungsnummer eingeben.");return
        if self.net.value()<=0 or self.gross.value()<=0:
            QMessageBox.warning(self,"Vorhandener Beleg","Bitte Netto- und Bruttobetrag eingeben.");return
        if self.net.value()>self.gross.value()+0.01:
            QMessageBox.warning(self,"Vorhandener Beleg","Netto darf nicht größer als Brutto sein.");return
        if self.paid.value()+self.discount.value()>self.gross.value()+0.01:
            QMessageBox.warning(self,"Vorhandener Beleg","Tatsächliche Zahlung und Skonto dürfen zusammen Brutto nicht überschreiten.");return
        super().accept()

    def data(self):
        return (self.project.currentData(),self.invoice_type.currentText(),self.number.text().strip(),
                self.invoice_date.date().toString("yyyy-MM-dd"),self.installment_no.value(),
                self.net.value(),self.gross.value(),self.vat.value(),self.paid.value(),self.discount.value(),
                self.payment_date.date().toString("yyyy-MM-dd"),self.pdf.text().strip(),
                self.notes.toPlainText().strip())

class PaymentDialog(QDialog):
    def __init__(self,db,iid,parent=None):
        super().__init__(parent);self.db=db;self.iid=iid;self.inv=db.invoice(iid);self.setMinimumWidth(600)
        self.setWindowTitle("Zahlungseingang")
        f=QFormLayout(self)
        self.invoice_sum=QLabel(money(self.inv["gross_total"]))
        self.payable_sum=QLabel(money(self.inv["payable_total"]))
        self.open_before=QLabel(money(db.invoice_open_amount(iid)))
        self.date=QDateEdit(QDate.currentDate());self.date.setCalendarPopup(True);self.date.setDisplayFormat("dd.MM.yyyy")
        self.open_after=QLabel()
        self.paid=QDoubleSpinBox();self.discount=QDoubleSpinBox();self.adjustment=QDoubleSpinBox()
        for x in [self.paid,self.discount,self.adjustment]:
            x.setMaximum(999999999);x.setDecimals(2);x.setSuffix(" €");x.valueChanged.connect(self.recalc)
        self.paid.setValue(db.invoice_open_amount(iid))
        self.adjustment_type=QComboBox()
        self.adjustment_type.addItems(["Kein Ausgleich","Kürzung Auftraggeber","Mangelabzug","Sicherheitseinbehalt","Rundungsdifferenz","Sonstiger Abzug"])
        self.reason=QLineEdit()
        for a,b in [("Rechnungsbetrag",self.invoice_sum),("Zahlbetrag nach Rechnungsabzügen",self.payable_sum),
                    ("Offen vor Zahlung",self.open_before),("Zahlungsdatum",self.date),
                    ("Bezahlter Betrag",self.paid),("Skonto",self.discount),("Ausgleich / Abzug",self.adjustment),
                    ("Art des Ausgleichs",self.adjustment_type),("Begründung",self.reason),("Offen nach Buchung",self.open_after)]:f.addRow(a,b)
        hint=QLabel("Nur ein echter offener Rest bleibt später mahnbar. Skonto und dokumentierte Ausgleichsbeträge mindern den offenen Betrag.")
        hint.setWordWrap(True);f.addRow("",hint)
        bb=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel);bb.accepted.connect(self.accept);bb.rejected.connect(self.reject);f.addRow(bb)
        self.recalc()
    def accept(self):
        valid,error=self.db.validate_discount(
            self.iid,self.date.date().toString("yyyy-MM-dd"),self.discount.value())
        if not valid:
            QMessageBox.warning(self,"Skonto nicht zulässig",error)
            return
        super().accept()
    def recalc(self):
        before=self.db.invoice_open_amount(self.iid)
        after=max(0.0,before-self.paid.value()-self.discount.value()-self.adjustment.value())
        self.open_after.setText(f"<b>{money(after)}</b>")
    def data(self):
        typ="" if self.adjustment.value()<=0 else self.adjustment_type.currentText()
        return (self.date.date().toString("yyyy-MM-dd"),self.paid.value(),self.discount.value(),
                self.adjustment.value(),typ,self.reason.text().strip())

class InvoicePositionAddDialog(QDialog):
    def __init__(self,db,iid,parent=None):
        super().__init__(parent);self.db=db;self.iid=iid
        self.setWindowTitle("Position zum Rechnungsentwurf hinzufügen")
        self.setMinimumSize(820,500)
        l=QVBoxLayout(self)
        info=QLabel("Es werden nur Aufmaßpositionen angezeigt, die noch nicht in diesem Entwurf enthalten sind und noch eine abrechenbare Menge besitzen.")
        info.setWordWrap(True);l.addWidget(info)
        self.table=QTableWidget(0,7)
        self.table.setHorizontalHeaderLabels(["Pos.","Kurztext","Kumuliert","Bereits berechnet","Neu","Einheit","EP"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        l.addWidget(self.table)
        rows=db.available_positions_for_invoice(iid);self.table.setRowCount(len(rows))
        if not rows:
            info.setText("Derzeit gibt es keine weitere Position zum Hinzufügen. "
                         "Entweder ist die offene Aufmaßposition bereits in diesem Entwurf enthalten "
                         "oder es gibt keine noch abrechenbare Menge.")
        for r,p in enumerate(rows):
            current=float(p["current_quantity"] or 0);previous=float(p["billed_quantity"] or 0)
            vals=[p["position_no"],p["short_text"],de_num(current,3),de_num(previous,3),
                  de_num(current-previous,3),p["unit"],money(p["unit_price"])]
            for c,v in enumerate(vals):
                it=QTableWidgetItem(v)
                if c==0:it.setData(Qt.UserRole,p["measurement_position_id"])
                self.table.setItem(r,c,it)
        bb=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept);bb.rejected.connect(self.reject);l.addWidget(bb)

    def selected_ids(self):
        return [self.table.item(i.row(),0).data(Qt.UserRole) for i in self.table.selectionModel().selectedRows()]

class InvoiceReleasePreviewDialog(QDialog):
    def __init__(self,db,iid,parent=None):
        super().__init__(parent);self.setWindowTitle("Rechnungsvorschau vor Freigabe")
        self.setMinimumSize(900,620);inv=db.invoice(iid);rows=db.invoice_positions(iid)
        l=QVBoxLayout(self)
        head=QLabel(f'<h2>{inv["invoice_type"]} {inv["number"]}</h2>'
                    f'Projekt: <b>{inv["project_number"]} – {inv["project_name"]}</b><br>'
                    f'Kunde: {inv["company"]} · Status: <b>{inv["status"]}</b>')
        head.setWordWrap(True);l.addWidget(head)
        table=QTableWidget(len(rows),6);table.setHorizontalHeaderLabels(
            ["Pos.","Kurztext","Menge","Einheit","EP","Gesamt"])
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        for r,p in enumerate(rows):
            vals=[p["position_no"],p["short_text"],de_num(p["new_quantity"],3),p["unit"],
                  money(p["unit_price"]),money(p["line_total"])]
            for c,v in enumerate(vals):table.setItem(r,c,QTableWidgetItem(v))
        l.addWidget(table)
        l.addWidget(QLabel(f'Netto: <b>{money(inv["net_total"])}</b> · '
                           f'MwSt.: {de_num(inv["vat_rate"])} % · '
                           f'Brutto: <b>{money(inv["gross_total"])}</b>'))
        if inv["deduct_previous"] and inv["invoice_type"] in ("Teilrechnung","Schlussrechnung"):
            previous=[x for x in db.previous_final_invoices(inv["project_id"],iid)
                      if x["invoice_type"]=="Teilrechnung" or
                         (inv["invoice_type"]=="Schlussrechnung" and x["invoice_type"]=="Abschlagsrechnung")]
            if previous:
                lines=["<b>Vorherige Teil-/Abschlagsrechnungen und Zahlungseingänge:</b>"]
                for p in previous:
                    paid=float(p["paid_total"] or 0);discount=float(p["discount_total"] or 0)
                    adjustment=float(p["adjustment_total"] or 0)
                    basis=float(p["payable_total"] if p["payable_total"] is not None else p["gross_total"] or 0)
                    open_amount=max(0.0,basis-paid-discount-adjustment)
                    label=(f'{int(p["installment_no"] or 1)}. Teilrechnung' if p["invoice_type"]=="Teilrechnung"
                           else "Abschlagsrechnung")
                    lines.append(f'{label} {p["number"]}: '
                                 f'gezahlt {money(paid)}, Skonto {money(discount)}, '
                                 f'sonstiger Ausgleich {money(adjustment)}, offen {money(open_amount)}')
                info=QLabel("<br>".join(lines));info.setWordWrap(True);l.addWidget(info)
        warn=QLabel("Bitte prüfen Sie alle Angaben. Erst „Rechnung freigeben“ schützt die Rechnung vor weiteren Änderungen.")
        warn.setWordWrap(True);l.addWidget(warn)
        buttons=QHBoxLayout();back=icon_button("back","Zurück zum Rechnungsentwurf");release=QPushButton("Rechnung freigeben")
        back.clicked.connect(self.reject);release.clicked.connect(self.accept)
        pdf_preview=QPushButton("📄  PDF-Vorschau");pdf_preview.setToolTip("Die Rechnung so ansehen, wie der Kunde sie als PDF erhält")
        pdf_preview.clicked.connect(lambda:parent.preview_invoice() if hasattr(parent,"preview_invoice") else None)
        buttons.addWidget(back);buttons.addWidget(pdf_preview);buttons.addStretch();buttons.addWidget(release);l.addLayout(buttons)

class ProjectBillingResetDialog(QDialog):
    def __init__(self,db,parent=None,preferred_project_id=None):
        super().__init__(parent);self.db=db
        self.setWindowTitle("Projektabrechnung auf 0 setzen")
        self.setMinimumWidth(650)
        f=QFormLayout(self)
        self.project=QComboBox()
        for p in db.all_invoice_projects():
            invoice_count=db.conn.execute(
                "SELECT COUNT(*) FROM invoices WHERE project_id=?",(p["id"],)).fetchone()[0]
            label=(f'{one_line(p["number"])} – {one_line(p["name"])} – '
                   f'{one_line(p["company"])} ({invoice_count} Rechnung(en))')
            self.project.addItem(label,p["id"])
            self.project.setItemData(self.project.count()-1,label,Qt.ToolTipRole)
        if preferred_project_id is not None:
            idx=self.project.findData(preferred_project_id)
            if idx>=0:self.project.setCurrentIndex(idx)
        self.project.setMinimumWidth(520)
        info=QLabel("Wählen Sie das Projekt, dessen komplette Testabrechnung entfernt werden soll. "
                    "Eine vorherige Markierung in der Rechnungsliste ist nicht erforderlich.")
        info.setWordWrap(True)
        f.addRow("Projekt *",self.project);f.addRow("",info)
        bb=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText("Projekt auswählen")
        bb.accepted.connect(self.accept);bb.rejected.connect(self.reject);f.addRow(bb)

    def project_id(self):
        return self.project.currentData()

LIBRARY_AUTO_CATEGORIES=("Aus Angeboten","Aus LV")

def _library_key(short_text,unit):
    return (one_line(short_text).lower(),one_line(unit).lower())

def collect_offer_positions(db,offer_id=None,position_id=None):
    """Angebotspositionen dauerhaft in die Leistungsbibliothek übernehmen.
    Selbst angelegte Leistungen werden nie verändert; automatisch gesammelte
    erhalten den neuesten Preis (0,00 € überschreibt keinen Preis)."""
    try:
        where="COALESCE(op.source_type,'') NOT IN ('Textblock','Titel') AND TRIM(COALESCE(op.short_text,''))<>''"
        args=[]
        if offer_id is not None:where+=" AND op.offer_id=?";args.append(offer_id)
        if position_id is not None:where+=" AND op.id=?";args.append(position_id)
        rows=db.conn.execute(f"""SELECT op.*,o.number AS offer_number FROM offer_positions op
          JOIN offers o ON o.id=op.offer_id WHERE {where} ORDER BY o.id,op.id""",args).fetchall()
        if not rows:return 0
        library={}
        for s in db.conn.execute("SELECT id,short_text,unit,category,long_text,sales_price FROM services").fetchall():
            library.setdefault(_library_key(s["short_text"],s["unit"]),s)
        added=0
        for p in rows:
            key=_library_key(p["short_text"],p["unit"]);price=float(p["unit_price"] or 0)
            source=f'Angebot {p["offer_number"]}'
            existing=library.get(key)
            if existing is None:
                category="Aus LV" if (p["source_type"] or "") in ("LV","PDF","ODS","Excel") else "Aus Angeboten"
                number=db.next_number("services","L")
                cur=db.conn.execute("""INSERT INTO services
                  (number,short_text,long_text,unit,purchase_price,sales_price,wage_share,material_share,active,category,source)
                  VALUES(?,?,?,?,0,?,0,0,1,?,?)""",(number,one_line(p["short_text"]),p["long_text"] or "",
                  (p["unit"] or "Stk.").strip(),price,category,source))
                library[key]={"id":cur.lastrowid,"category":category};added+=1
            elif (existing["category"] or "") in LIBRARY_AUTO_CATEGORIES:
                if price>0:
                    db.conn.execute("UPDATE services SET sales_price=?,source=? WHERE id=?",(price,source,existing["id"]))
                if (p["long_text"] or "").strip():
                    db.conn.execute("""UPDATE services SET long_text=? WHERE id=? AND TRIM(COALESCE(long_text,''))=''""",
                                    (p["long_text"],existing["id"]))
        db.conn.commit();return added
    except Exception:
        return 0

# Vor dem Löschen eines Angebots oder einer Position noch einsammeln.
_delete_offer_original=DB.delete_offer
def _delete_offer_keeping_library(self,oid):
    collect_offer_positions(self,offer_id=oid);return _delete_offer_original(self,oid)
DB.delete_offer=_delete_offer_keeping_library
_delete_position_original=DB.delete_position
def _delete_position_keeping_library(self,pid):
    collect_offer_positions(self,position_id=pid);return _delete_position_original(self,pid)
DB.delete_position=_delete_position_keeping_library

def invoice_title_key(p):
    return ((p["title_no"] or "").strip(),(p["title_text"] or "").strip())

def invoice_title_label(key):
    return f"Titel {key[0]}  {key[1]}".strip() if any(key) else "Positionen ohne Titel"

def read_einvoice(path):
    """Liest Lieferant, Nummer, Datum und Beträge aus einer E-Rechnung. None, wenn die Datei keine ist."""
    import xml.etree.ElementTree as ET
    path=Path(path);raw=None
    try:
        if path.suffix.lower()==".xml":raw=path.read_bytes()
        elif path.suffix.lower()==".pdf":
            from pypdf import PdfReader
            for name,contents in PdfReader(str(path)).attachments.items():
                if str(name).lower().endswith(".xml") and contents:raw=contents[0];break
        if not raw:return None
        root=ET.fromstring(raw)
    except Exception:
        return None
    def local(element):return element.tag.rsplit("}",1)[-1]
    def find(node,*names):
        """Erstes Element entlang der lokalen Namen, unabhängig vom Namensraum."""
        if not names:return node
        for element in node.iter():
            if local(element)==names[0] and element is not node:
                hit=find(element,*names[1:])
                if hit is not None:return hit
        return None
    def text(*names):
        element=find(root,*names);return (element.text or "").strip() if element is not None else ""
    def amount(*names):
        try:return float(text(*names))
        except ValueError:return None
    def iso(value):
        value=value.strip()
        for fmt in ("%Y%m%d","%Y-%m-%d"):
            try:return datetime.strptime(value[:10] if "-" in value else value[:8],fmt).strftime("%Y-%m-%d")
            except ValueError:pass
        return None
    kind=local(root)
    if kind in ("CrossIndustryInvoice","CrossIndustryDocument"):
        data={"supplier":text("SellerTradeParty","Name"),
              "invoice_no":text("ExchangedDocument","ID") or text("HeaderExchangedDocument","ID"),
              "invoice_date":iso(text("ExchangedDocument","IssueDateTime","DateTimeString") or text("HeaderExchangedDocument","IssueDateTime","DateTimeString")),
              "net":amount("SpecifiedTradeSettlementHeaderMonetarySummation","TaxBasisTotalAmount") or amount("SpecifiedTradeSettlementMonetarySummation","TaxBasisTotalAmount"),
              "gross":amount("SpecifiedTradeSettlementHeaderMonetarySummation","GrandTotalAmount") or amount("SpecifiedTradeSettlementMonetarySummation","GrandTotalAmount"),
              "due_date":iso(text("SpecifiedTradePaymentTerms","DueDateDateTime","DateTimeString")),
              "vat_rate":amount("ApplicableHeaderTradeSettlement","ApplicableTradeTax","RateApplicablePercent")}
        if data["vat_rate"] is None:data["vat_rate"]=amount("ApplicableSupplyChainTradeSettlement","ApplicableTradeTax","ApplicablePercent")
    elif kind in ("Invoice","CreditNote"):
        data={"supplier":text("AccountingSupplierParty","PartyLegalEntity","RegistrationName") or text("AccountingSupplierParty","PartyName","Name"),
              "invoice_no":(root.find("{*}ID").text or "").strip() if root.find("{*}ID") is not None else "",
              "invoice_date":iso(text("IssueDate")),"net":amount("LegalMonetaryTotal","TaxExclusiveAmount"),
              "gross":amount("LegalMonetaryTotal","TaxInclusiveAmount"),"due_date":iso(text("DueDate")) if find(root,"DueDate") is not None else None,
              "vat_rate":amount("TaxTotal","TaxSubtotal","TaxCategory","Percent")}
    else:return None
    if not data["supplier"] and data["net"] is None:return None
    return data


class IncomingInvoiceDialog(QDialog):
    """Eine Lieferanten-/Nachunternehmerrechnung einem Projekt zuordnen."""
    def __init__(self,db,parent=None,row=None,project_id=None):
        super().__init__(parent);self.db=db;self.row=row;self.document_path=None;self._syncing=False
        self.setWindowTitle("Eingangsrechnung bearbeiten" if row else "Eingangsrechnung erfassen");self.setMinimumWidth(620)
        form=QFormLayout(self)
        self.project=QComboBox();current=row["project_id"] if row else project_id
        for p in db.projects():
            if p["status"]=="Archiviert" and p["id"]!=current:continue
            self.project.addItem(f'{one_line(p["number"])} – {one_line(p["name"])} – {one_line(p["company"])}',p["id"])
        if current is not None and self.project.findData(current)>=0:self.project.setCurrentIndex(self.project.findData(current))
        self.supplier=QComboBox();self.supplier.setEditable(True);self.supplier.addItems(db.incoming_suppliers())
        self.supplier.setCurrentText(row["supplier"] if row else "")
        self.supplier.lineEdit().setPlaceholderText("Lieferant oder Nachunternehmer")
        self.invoice_no=QLineEdit(row["invoice_no"] or "" if row else "")
        self.invoice_date=QDateEdit();self.invoice_date.setCalendarPopup(True);self.invoice_date.setDisplayFormat("dd.MM.yyyy")
        self.invoice_date.setDate(QDate.fromString(str(row["invoice_date"])[:10],"yyyy-MM-dd") if row else QDate.currentDate())
        self.category=QComboBox();self.category.setEditable(True);self.category.addItems(INCOMING_CATEGORIES)
        self.category.setCurrentText(row["category"] if row else "Material")
        def amount():
            box=QDoubleSpinBox();box.setDecimals(2);box.setRange(-99999999,99999999);box.setSuffix(" €")
            box.setGroupSeparatorShown(True);return box
        self.net=amount();self.gross=amount()
        self.vat=QDoubleSpinBox();self.vat.setDecimals(1);self.vat.setRange(0,100);self.vat.setSuffix(" %")
        self.vat.setValue(float(row["vat_rate"]) if row else 19.0)
        self.net.setValue(float(row["net_amount"]) if row else 0.0);self.gross.setValue(float(row["gross_amount"]) if row else 0.0)
        self.net.valueChanged.connect(self._net_changed);self.vat.valueChanged.connect(self._net_changed)
        self.gross.valueChanged.connect(self._gross_changed)
        amounts=QHBoxLayout();amounts.addWidget(QLabel("Netto"));amounts.addWidget(self.net,1)
        amounts.addWidget(QLabel("MwSt."));amounts.addWidget(self.vat);amounts.addWidget(QLabel("Brutto"));amounts.addWidget(self.gross,1)
        def optional_date(label,value,default_days=0):
            check=QCheckBox(label);edit=QDateEdit();edit.setCalendarPopup(True);edit.setDisplayFormat("dd.MM.yyyy")
            edit.setDate(QDate.fromString(str(value)[:10],"yyyy-MM-dd") if value else QDate.currentDate().addDays(default_days))
            check.setChecked(bool(value));edit.setEnabled(bool(value));check.toggled.connect(edit.setEnabled)
            line=QHBoxLayout();line.addWidget(check);line.addWidget(edit);line.addStretch();return check,edit,line
        self.due_check,self.due_date,due_line=optional_date("Fällig am",row["due_date"] if row else None,14)
        self.paid_check,self.paid_date,paid_line=optional_date("Bezahlt am",row["paid_date"] if row else None)
        self.note=QLineEdit(row["note"] or "" if row else "");self.note.setPlaceholderText("z. B. Lieferschein-Nr., wofür")
        self.document_label=QLabel();self.document_label.setWordWrap(True)
        choose=QPushButton("Beleg auswählen …");choose.clicked.connect(self.choose_document)
        choose.setToolTip("Eingescannte Rechnung (PDF oder Bild) auswählen. Sie wird in die Dokumente des Projekts kopiert.")
        doc_line=QHBoxLayout();doc_line.addWidget(self.document_label,1);doc_line.addWidget(choose)
        scanner=shutil.which("simple-scan")
        if scanner:
            scan=QPushButton("Scanner öffnen");scan.setToolTip("Öffnet das Scan-Programm. Dort scannen, als PDF speichern und danach hier „Beleg auswählen“.")
            scan.clicked.connect(lambda:subprocess.Popen([scanner],env=desktop_process_environment(),start_new_session=True,
                                                         stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
            doc_line.addWidget(scan)
        self._show_document_name()
        form.addRow("Projekt",self.project);form.addRow("Lieferant",self.supplier)
        form.addRow("Rechnungs-Nr.",self.invoice_no);form.addRow("Rechnungsdatum",self.invoice_date)
        form.addRow("Art der Kosten",self.category);form.addRow("Betrag",amounts)
        form.addRow("",due_line);form.addRow("",paid_line);form.addRow("Notiz",self.note);form.addRow("Beleg",doc_line)
        buttons=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText("Speichern");buttons.button(QDialogButtonBox.Cancel).setText("Abbrechen")
        buttons.accepted.connect(self.accept);buttons.rejected.connect(self.reject);form.addRow(buttons)

    def _net_changed(self,*_):
        if self._syncing:return
        self._syncing=True;self.gross.setValue(round(self.net.value()*(1+self.vat.value()/100.0),2));self._syncing=False

    def _gross_changed(self,*_):
        if self._syncing:return
        self._syncing=True;self.net.setValue(round(self.gross.value()/(1+self.vat.value()/100.0),2));self._syncing=False

    def _show_document_name(self):
        if self.document_path:self.document_label.setText(f"Neu: {Path(self.document_path).name}");return
        name=""
        if self.row and self.row["document_id"]:
            doc=self.db.conn.execute("SELECT filename FROM project_documents WHERE id=?",(self.row["document_id"],)).fetchone()
            name=doc["filename"] if doc else ""
        self.document_label.setText(name or "Kein Beleg hinterlegt")

    def choose_document(self):
        path,_=QFileDialog.getOpenFileName(self,"Beleg zur Eingangsrechnung auswählen","",
            "Belege (*.pdf *.xml *.jpg *.jpeg *.png *.tif *.tiff *.webp);;Alle Dateien (*)")
        if path:self.document_path=path;self._show_document_name();self.apply_einvoice(path)

    def apply_einvoice(self,path):
        """Ist der Beleg eine E-Rechnung, die Felder daraus füllen."""
        data=read_einvoice(path)
        if not data:return False
        if data["supplier"]:self.supplier.setCurrentText(data["supplier"])
        if data["invoice_no"]:self.invoice_no.setText(data["invoice_no"])
        if data["invoice_date"]:self.invoice_date.setDate(QDate.fromString(data["invoice_date"],"yyyy-MM-dd"))
        if data["due_date"]:
            self.due_check.setChecked(True);self.due_date.setDate(QDate.fromString(data["due_date"],"yyyy-MM-dd"))
        self._syncing=True
        if data["vat_rate"] is not None:self.vat.setValue(data["vat_rate"])
        if data["net"] is not None:self.net.setValue(data["net"])
        if data["gross"] is not None:self.gross.setValue(data["gross"])
        elif data["net"] is not None:self.gross.setValue(round(data["net"]*(1+self.vat.value()/100.0),2))
        self._syncing=False
        self.document_label.setText(f"Neu: {Path(path).name}  ·  E-Rechnung erkannt, Angaben übernommen – bitte prüfen")
        return True

    def accept(self):
        if self.project.currentData() is None:
            QMessageBox.warning(self,"Eingangsrechnung","Bitte ein Projekt auswählen.");return
        if not self.supplier.currentText().strip():
            QMessageBox.warning(self,"Eingangsrechnung","Bitte den Lieferanten angeben.");self.supplier.setFocus();return
        if abs(self.net.value())<0.005:
            QMessageBox.warning(self,"Eingangsrechnung","Bitte den Rechnungsbetrag angeben.");self.net.setFocus();return
        super().accept()

    def data(self):
        return {"project_id":self.project.currentData(),"supplier":self.supplier.currentText().strip(),
                "invoice_no":self.invoice_no.text().strip(),"invoice_date":self.invoice_date.date().toString("yyyy-MM-dd"),
                "category":self.category.currentText().strip() or "Sonstiges","net_amount":self.net.value(),
                "vat_rate":self.vat.value(),"gross_amount":self.gross.value(),
                "due_date":self.due_date.date().toString("yyyy-MM-dd") if self.due_check.isChecked() else None,
                "paid_date":self.paid_date.date().toString("yyyy-MM-dd") if self.paid_check.isChecked() else None,
                "note":self.note.text().strip(),"document_id":self.row["document_id"] if self.row else None}


class IncomingInvoicesPanel(QWidget):
    """Liste der Eingangsrechnungen, wahlweise für ein Projekt oder alle."""
    HEADERS=["Datum","Lieferant","Rechnungs-Nr.","Projekt","Art","Netto","Brutto","Fällig","Bezahlt am","Status","Beleg"]
    def __init__(self,db,parent=None):
        super().__init__(parent);self.db=db
        o=QVBoxLayout(self);o.setContentsMargins(0,0,0,0)
        bar=QHBoxLayout();bar.addWidget(QLabel("Projekt:"));self.project=QComboBox();self.project.setMinimumWidth(460)
        self.project.currentIndexChanged.connect(self.refresh);bar.addWidget(self.project)
        self.search=QLineEdit();self.search.setPlaceholderText("Lieferant, Nummer oder Notiz suchen …");self.search.textChanged.connect(self.refresh)
        bar.addWidget(self.search,1)
        self.only_open=QCheckBox("Nur offene");self.only_open.toggled.connect(self.refresh);bar.addWidget(self.only_open)
        add=QPushButton("+ Eingangsrechnung");add.setObjectName("ctaButton");add.clicked.connect(self.add);bar.addWidget(add);o.addLayout(bar)
        actions=QHBoxLayout()
        self.edit_button=QPushButton("Bearbeiten");self.edit_button.clicked.connect(self.edit)
        self.paid_button=QPushButton("Als bezahlt markieren");self.paid_button.clicked.connect(self.toggle_paid)
        self.paid_button.setMinimumWidth(210)
        self.document_button=QPushButton("Beleg öffnen");self.document_button.clicked.connect(self.open_document)
        self.delete_button=QPushButton("Löschen");self.delete_button.clicked.connect(self.delete)
        for w in (self.edit_button,self.paid_button,self.document_button,self.delete_button):actions.addWidget(w)
        actions.addStretch();o.addLayout(actions)
        self.table=QTableWidget(0,len(self.HEADERS));self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows);self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers);self.table.doubleClicked.connect(lambda *_:self.edit())
        self.table.itemSelectionChanged.connect(self._update_buttons);o.addWidget(self.table,1)
        self.summary=QLabel();self.summary.setTextFormat(Qt.RichText);o.addWidget(self.summary)
        self._fill_projects();self._update_buttons()

    def _fill_projects(self,keep=None):
        keep=self.project.currentData() if keep is None else keep
        self.project.blockSignals(True);self.project.clear();self.project.addItem("Alle Projekte",None)
        for p in self.db.projects():
            self.project.addItem(f'{one_line(p["number"])} – {one_line(p["name"])} – {one_line(p["company"])}',p["id"])
        index=self.project.findData(keep) if keep is not None else 0
        self.project.setCurrentIndex(index if index>=0 else 0);self.project.blockSignals(False)

    def set_project(self,project_id):
        self._fill_projects(project_id);self.refresh()

    def selected_id(self):
        row=self.table.currentRow();item=self.table.item(row,0) if row>=0 else None
        return item.data(Qt.UserRole) if item is not None and self.table.selectionModel().hasSelection() else None

    def select_id(self,eid):
        for row in range(self.table.rowCount()):
            if self.table.item(row,0).data(Qt.UserRole)==eid:self.table.selectRow(row);return

    def refresh(self,*_):
        keep=self.selected_id()
        rows=self.db.incoming_invoices(self.project.currentData(),self.search.text().strip())
        if self.only_open.isChecked():rows=[r for r in rows if not r["paid_date"]]
        self.table.setRowCount(len(rows))
        for r,x in enumerate(rows):
            cells=[de_date(x["invoice_date"]),x["supplier"],x["invoice_no"] or "",f'{x["project_number"]} – {one_line(x["project_name"])}',
                   x["category"],money(x["net_amount"]),money(x["gross_amount"]),de_date(x["due_date"]),de_date(x["paid_date"]),
                   incoming_status(x),"📎" if x["document_id"] else ""]
            for c,value in enumerate(cells):
                item=QTableWidgetItem(value)
                if c in (5,6):item.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
                if c==10:item.setTextAlignment(Qt.AlignCenter)
                if c==0:item.setData(Qt.UserRole,x["id"])
                self.table.setItem(r,c,item)
        header=self.table.horizontalHeader();header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1,QHeaderView.Stretch)
        self.table.setColumnHidden(3,self.project.currentData() is not None)
        net=sum(float(x["net_amount"] or 0) for x in rows);open_gross=sum(float(x["gross_amount"] or 0) for x in rows if not x["paid_date"])
        self.summary.setText(f'{len(rows)} Eingangsrechnung(en) · Summe netto: <b>{money(net)}</b> · noch zu bezahlen (brutto): <b>{money(open_gross)}</b>'
                             if rows else "Noch keine Eingangsrechnungen erfasst. Mit „+ Eingangsrechnung“ eine Lieferantenrechnung zum Projekt eintragen.")
        if keep is not None:self.select_id(keep)
        self._update_buttons()

    def _update_buttons(self):
        row=self.db.incoming_invoice(self.selected_id()) if self.selected_id() else None
        for w in (self.edit_button,self.paid_button,self.delete_button):w.setEnabled(row is not None)
        self.document_button.setEnabled(bool(row and row["document_id"]))
        self.paid_button.setText("Bezahlung zurücknehmen" if row and row["paid_date"] else "Als bezahlt markieren")

    def _save(self,dialog,eid=None):
        data=dialog.data()
        if dialog.document_path:
            try:
                description=" ".join(x for x in ("Eingangsrechnung",data["supplier"],data["invoice_no"]) if x)
                data["document_id"]=self.db.add_project_document(data["project_id"],dialog.document_path,description)
            except Exception as error:
                QMessageBox.warning(self,"Beleg","Der Beleg konnte nicht in die Projektdokumente kopiert werden:\n"+str(error))
        eid=self.db.save_incoming_invoice(eid,data);self.refresh();self.select_id(eid);return eid

    def add(self):
        dialog=IncomingInvoiceDialog(self.db,self,None,self.project.currentData())
        if dialog.exec():self._save(dialog)

    def edit(self):
        eid=self.selected_id();row=self.db.incoming_invoice(eid) if eid else None
        if not row:return
        dialog=IncomingInvoiceDialog(self.db,self,row)
        if dialog.exec():self._save(dialog,eid)

    def toggle_paid(self):
        eid=self.selected_id();row=self.db.incoming_invoice(eid) if eid else None
        if not row:return
        self.db.conn.execute("UPDATE incoming_invoices SET paid_date=? WHERE id=?",
                             (None if row["paid_date"] else date.today().isoformat(),eid));self.db.conn.commit()
        self.refresh()

    def open_document(self):
        eid=self.selected_id();row=self.db.incoming_invoice(eid) if eid else None
        if not row or not row["document_id"]:return
        try:path=self.db.project_document_path(row["document_id"])
        except ValueError:path=None
        if path is None or not path.is_file():
            QMessageBox.information(self,"Beleg","Der Beleg ist in den Projektdokumenten nicht mehr vorhanden.");return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def delete(self):
        eid=self.selected_id();row=self.db.incoming_invoice(eid) if eid else None
        if not row:return
        extra="\n\nDer Beleg bleibt in den Dokumenten des Projekts erhalten." if row["document_id"] else ""
        if QMessageBox.question(self,"Eingangsrechnung löschen",
            f'Eingangsrechnung von {row["supplier"]} über {money(row["gross_amount"])} wirklich löschen?'+extra,
            QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:return
        self.db.backup("vor_eingangsrechnung_loeschen");self.db.delete_incoming_invoice(eid);self.refresh()


class InvoicesPage(QWidget):
    def show_view(self,index):
        """0 = Ausgangsrechnungen, 1 = Eingangsrechnungen."""
        self.view_stack.setCurrentIndex(index)
        self.view_out_btn.setChecked(index==0);self.view_in_btn.setChecked(index==1)
        if index==1:self.incoming.set_project(self.project.currentData())

    def show_incoming(self,project_id=None,record_id=None):
        self.view_stack.setCurrentIndex(1);self.view_out_btn.setChecked(False);self.view_in_btn.setChecked(True)
        self.incoming.set_project(project_id)
        if record_id is not None:self.incoming.select_id(record_id)

    def __init__(self,db):
        super().__init__();self.db=db;self.loading_positions=False
        outer=QVBoxLayout(self);head=QHBoxLayout();t=QLabel("Rechnungen");t.setObjectName("pageTitle");head.addWidget(t)
        head.addSpacing(24)
        self.view_out_btn=QPushButton("🧾  Ausgangsrechnungen");self.view_in_btn=QPushButton("📥  Eingangsrechnungen")
        self.view_in_btn.setToolTip("Rechnungen von Lieferanten und Nachunternehmern je Projekt – für den Kostenüberblick")
        for index,button in enumerate((self.view_out_btn,self.view_in_btn)):
            button.setCheckable(True);button.setMinimumHeight(34);button.setMinimumWidth(210)
            button.setStyleSheet("QPushButton:checked{font-weight:bold;border-bottom:3px solid palette(highlight);}")
            button.clicked.connect(lambda _checked=False,i=index:self.show_view(i));head.addWidget(button)
        self.view_out_btn.setChecked(True);head.addStretch();outer.addLayout(head)
        self.view_stack=QStackedWidget();outer.addWidget(self.view_stack,1)
        outgoing=QWidget();o=QVBoxLayout(outgoing);o.setContentsMargins(0,0,0,0);self.view_stack.addWidget(outgoing)
        self.incoming=IncomingInvoicesPanel(db,self);self.view_stack.addWidget(self.incoming)
        top=QHBoxLayout();top.addStretch();top.addWidget(QLabel("Projekt:"));self.project=QComboBox()
        for p in db.all_invoice_projects():
            self.project.addItem(f'{one_line(p["number"])} – {one_line(p["name"])} – {one_line(p["company"])}',p["id"])
        self.project.setMinimumWidth(560);self.project.currentIndexChanged.connect(self.refresh)
        top.addWidget(self.project);o.addLayout(top)

        bar=QHBoxLayout();bar.addWidget(QLabel("Rechnung:"));self.invoice_selector=QComboBox()
        self.invoice_selector.setMinimumWidth(340);self.invoice_selector.currentIndexChanged.connect(self.select_invoice_from_combo)
        bar.addWidget(self.invoice_selector)
        self.search=QLineEdit();self.search.setPlaceholderText("Rechnung suchen …");self.search.textChanged.connect(self.refresh)
        bar.addWidget(self.search)
        from_measure=QPushButton("Rechnung aus Aufmaß erzeugen");from_measure.clicked.connect(self.new_from_measurement)
        free=QPushButton("Freie Rechnung");free.clicked.connect(self.new_free_invoice)
        historical=QPushButton("Vorhandenen Beleg übernehmen");historical.clicked.connect(self.import_historical_invoice)
        historical.setToolTip("Bereits ausgestellte Teil- oder Abschlagsrechnung mit Originalnummer übernehmen")
        self.search.setVisible(False)
        new_invoice=QPushButton("+ Neue Rechnung");new_invoice.setObjectName("ctaButton")
        new_menu=QMenu(new_invoice)
        new_menu.addAction("Rechnung aus Aufmaß …",self.new_from_measurement)
        new_menu.addAction("Freie Rechnung …",self.new_free_invoice)
        new_menu.addAction("Vorhandenen Beleg übernehmen (Teil-/Abschlagsrechnung) …",self.import_historical_invoice)
        new_invoice.setMenu(new_menu)
        bar.addWidget(new_invoice);bar.addStretch();o.addLayout(bar)

        actions=QHBoxLayout()
        edit_draft=icon_button("edit","Rechnungsentwurf bearbeiten",self.edit_draft)
        final=QPushButton("Vorschau && Freigabe");final.clicked.connect(self._preview_or_finalize)
        self.final_button=final;self.edit_draft_button=edit_draft
        dele=icon_button("delete","Rechnungsentwurf löschen",self.delete_invoice)
        reset=QPushButton("Projektabrechnung auf 0 setzen");reset.clicked.connect(self.reset_project_invoices)
        reset.setToolTip("Löscht für das gewählte Projekt alle Rechnungen und Zahlungen und setzt den Abrechnungsstand zurück.")
        for w in (edit_draft,final,dele):actions.addWidget(w)
        # Löscht alle Rechnungen und Zahlungen eines Projekts: bewusst versteckt und gesichert.
        more=QPushButton("Weitere");more_menu=QMenu(more)
        more_menu.addAction("E-Rechnung prüfen …",self.check_einvoice);more_menu.addSeparator()
        more_menu.addAction("Projektabrechnung auf 0 setzen …",self._confirm_reset);more.setMenu(more_menu)
        actions.addStretch();actions.addWidget(more);o.addLayout(actions)

        # Unsichtbare ID-Auswahltabelle: Die sichtbare Auswahl erfolgt oben wie
        # im Aufmaß über Projekt und Rechnung.
        self.table=QTableWidget(0,6)
        self.table.setHorizontalHeaderLabels(["Nr.","Typ","Projekt","Kunde","Brutto","Status"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows);self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.select_invoice)

        sp=QSplitter(Qt.Vertical)
        upper=QWidget();ul=QVBoxLayout(upper)
        ul.setSpacing(3)
        self.meta=compact_hint("Bitte eine Rechnung auswählen.");ul.addWidget(self.meta)
        self.pos=QTableWidget(0,8);self.pos.setHorizontalHeaderLabels(
            ["Pos.","Kurztext","Kumulierte Menge","Zuwachs dieser Rechnung","Einheit","EP","Betrag dieser Rechnung","Gesamt kumuliert"])

        self.pos.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.pos.setEditTriggers(QAbstractItemView.DoubleClicked|QAbstractItemView.EditKeyPressed)
        self.pos.itemChanged.connect(self.invoice_position_changed)
        self.pos.itemSelectionChanged.connect(self.load_invoice_position_editor)
        self.pos.cellClicked.connect(lambda _row,_column:self.load_invoice_position_editor())
        ul.addWidget(self.pos)

        self.position_editor=QGroupBox("Ausgewählte Rechnungsposition bearbeiten")
        editor=QGridLayout(self.position_editor)
        self.edit_position_no=QLineEdit();self.edit_short_text=QLineEdit()
        self.edit_cumulative=QDoubleSpinBox();self.edit_cumulative.setDecimals(3)
        self.edit_cumulative.setRange(0,999999999);self.edit_cumulative.setReadOnly(True)
        self.edit_cumulative.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.edit_increment=QDoubleSpinBox();self.edit_increment.setDecimals(3);self.edit_increment.setRange(0,999999999)
        self.edit_unit=QComboBox();self.edit_unit.setEditable(True)
        self.edit_unit.addItems(["Stk.","m","m²","m³","lfm","Std.","kg","t","pauschal"])
        self.edit_unit_price=QDoubleSpinBox();self.edit_unit_price.setDecimals(2)
        self.edit_unit_price.setRange(-99999999,99999999);self.edit_unit_price.setSuffix(" €")
        editor.addWidget(QLabel("Pos."),0,0);editor.addWidget(self.edit_position_no,0,1)
        editor.addWidget(QLabel("Kurztext"),0,2);editor.addWidget(self.edit_short_text,0,3,1,5)
        editor.addWidget(QLabel("Kumulierte Menge"),1,0);editor.addWidget(self.edit_cumulative,1,1)
        editor.addWidget(QLabel("Zuwachs dieser Rechnung"),1,2);editor.addWidget(self.edit_increment,1,3)
        editor.addWidget(QLabel("Einheit"),1,4);editor.addWidget(self.edit_unit,1,5)
        editor.addWidget(QLabel("Einheitspreis"),1,6);editor.addWidget(self.edit_unit_price,1,7)
        save_position=icon_button("save","Änderungen an Rechnungsposition speichern",self.save_invoice_position_editor)
        close_position=icon_button("cancel","Bearbeitungsleiste schließen",self.close_invoice_position_editor)
        editor.addWidget(close_position,2,5,1,2);editor.addWidget(save_position,2,7)
        self.position_editor.setEnabled(False);self.position_editor.setVisible(False);ul.addWidget(self.position_editor)
        posbuttons=QHBoxLayout()
        syncpos=QPushButton("Entwurf aus Aufmaß aktualisieren");syncpos.clicked.connect(self.sync_draft)
        addpos=QPushButton("Aufmaßposition hinzufügen");addpos.clicked.connect(self.add_position_to_draft)
        manualpos=QPushButton("+ Manuelle Position");manualpos.clicked.connect(self.add_manual_position)
        removepos=icon_button("delete","Position aus Rechnungsentwurf entfernen",self.remove_position_from_draft)
        poshint=QLabel("Entwürfe sind direkt editierbar. Freigegebene Rechnungen bleiben unverändert.")
        poshint.setWordWrap(True)
        posbuttons.addWidget(syncpos);posbuttons.addWidget(addpos);posbuttons.addWidget(manualpos);posbuttons.addWidget(removepos);posbuttons.addWidget(poshint,1);ul.addLayout(posbuttons)
        self.draft_widgets=[syncpos,addpos,manualpos,removepos,poshint]
        sp.addWidget(upper)

        lower=QWidget();ll=QVBoxLayout(lower)
        details=QGroupBox("Details / Summen");dl=QVBoxLayout(details)
        self.summary=QLabel();self.summary.setWordWrap(True);dl.addWidget(self.summary);ll.addWidget(details)
        pr=QHBoxLayout();pay=QPushButton("Zahlungseingang");pay.clicked.connect(self.payment)
        reminder=QPushButton("Mahnung erstellen");reminder.clicked.connect(self.create_reminder)
        preview=icon_button("preview","Rechnungsvorschau öffnen",self.preview_invoice)
        pdf=icon_button("pdf","Rechnung als PDF ausgeben",self.create_pdf)
        email=icon_button("email","Rechnung per E-Mail senden",self.send_invoice_email)
        # Aus dem früheren Modul Zahlungen: Ausgleich und Buchung löschen.
        adjust=QPushButton("+ Ausgleich");adjust.clicked.connect(self.add_adjustment)
        adjust.setToolTip("Kürzung Auftraggeber, Mangelabzug, Rundungsdifferenz o. Ä. erfassen")
        delete_payment=icon_button("delete","Markierte Zahlungs-/Ausgleichsbuchung löschen",self.delete_payment)
        pr.addWidget(pay);pr.addWidget(adjust);pr.addWidget(delete_payment);pr.addSpacing(16);pr.addWidget(reminder);pr.addStretch();ll.addLayout(pr)
        actions.insertWidget(3,pdf)
        self.payments=QTableWidget(0,6);self.payments.setHorizontalHeaderLabels(
            ["Datum","Bezahlt","Skonto","Ausgleich","Art","Begründung"])
        self.payments.setEditTriggers(QAbstractItemView.NoEditTriggers);ll.addWidget(self.payments)
        self.payments.setSelectionBehavior(QAbstractItemView.SelectRows);self.payments.setSelectionMode(QAbstractItemView.SingleSelection)
        sp.addWidget(lower);sp.setSizes([520,260]);o.addWidget(sp)
        self.refresh()
    def refresh(self):
        keep_iid=self.iid();project_id=self.project.currentData()

        # Projekte können in der bereits laufenden Anwendung neu angelegt
        # werden. Deshalb wird nicht nur die Rechnungsliste, sondern auch diese
        # Projektauswahl bei jedem Öffnen der Seite erneut aus der DB gelesen.
        # Blockierte Signale verhindern dabei rekursive refresh()-Aufrufe.
        projects=self.db.all_invoice_projects()
        self.project.blockSignals(True)
        self.project.clear()
        selected_index=-1
        for index,p in enumerate(projects):
            self.project.addItem(
                f'{one_line(p["number"])} – {one_line(p["name"])} – {one_line(p["company"])}',p["id"])
            if p["id"]==project_id:selected_index=index
        if selected_index>=0:self.project.setCurrentIndex(selected_index)
        self.project.blockSignals(False)
        project_id=self.project.currentData()

        rows=[x for x in self.db.invoices(self.search.text())
              if project_id is None or x["project_id"]==project_id]
        self.table.blockSignals(True);self.invoice_selector.blockSignals(True)
        self.table.setRowCount(len(rows));self.invoice_selector.clear()
        for r,x in enumerate(rows):
            vals=[x["number"],x["invoice_type"],f'{x["project_number"]} – {one_line(x["project_name"])}',one_line(x["company"]),money(x["gross_total"]),x["status"]]
            for c,v in enumerate(vals):
                it=QTableWidgetItem(v);it.setData(Qt.UserRole,x["id"]) if c==0 else None;self.table.setItem(r,c,it)
            self.invoice_selector.addItem(
                f'{x["number"]} – {x["invoice_type"]}'
                f'{" – historisch übernommen" if x["is_historical"] else ""}'
                f' – {money(x["gross_total"])} – {x["status"]}',x["id"])
        self.table.blockSignals(False);self.invoice_selector.blockSignals(False)
        self.pos.setRowCount(0);self.position_editor.setEnabled(False);self.position_editor.setVisible(False)
        self.payments.setRowCount(0);self.meta.setText("Bitte eine Rechnung auswählen.");self.summary.setText("")
        if rows:
            target=keep_iid if any(x["id"]==keep_iid for x in rows) else rows[0]["id"]
            idx=self.invoice_selector.findData(target);self.invoice_selector.setCurrentIndex(max(idx,0))
            self.select_invoice_from_combo()
    def iid(self):
        r=self.table.currentRow();return self.table.item(r,0).data(Qt.UserRole) if r>=0 and self.table.item(r,0) else None

    def refresh_keep_invoice(self,iid):
        inv=self.db.invoice(iid)
        if inv:
            pidx=self.project.findData(inv["project_id"])
            if pidx>=0:
                self.project.blockSignals(True);self.project.setCurrentIndex(pidx);self.project.blockSignals(False)
        self.refresh()
        for r in range(self.table.rowCount()):
            item=self.table.item(r,0)
            if item and item.data(Qt.UserRole)==iid:
                self.table.selectRow(r)
                self.invoice_selector.blockSignals(True)
                self.invoice_selector.setCurrentIndex(max(0,self.invoice_selector.findData(iid)));self.invoice_selector.blockSignals(False)
                self.select_invoice()
                return
    def select_invoice_from_combo(self):
        iid=self.invoice_selector.currentData()
        if iid is None:return
        for r in range(self.table.rowCount()):
            item=self.table.item(r,0)
            if item and item.data(Qt.UserRole)==iid:
                self.table.selectRow(r)
                self.invoice_selector.blockSignals(True)
                self.invoice_selector.setCurrentIndex(max(0,self.invoice_selector.findData(iid)));self.invoice_selector.blockSignals(False)
                self.select_invoice()
                return
    def new_from_measurement(self):
        if not self.db.invoice_projects():
            QMessageBox.information(self,"Rechnung aus Aufmaß","Es gibt noch kein Projekt mit Aufmaßpositionen.");return
        d=PartialInvoiceDialog(self.db,self,source_mode="Aufmaß")
        if d.exec():
            self.db.backup("vor_rechnung_aus_aufmass")
            iid,err=self.db.create_invoice(*d.new_invoice_data())
            if err:QMessageBox.information(self,"Rechnung aus Aufmaß",err);return
            self.refresh_keep_invoice(iid)
    def new_free_invoice(self):
        if not self.db.all_invoice_projects():
            QMessageBox.information(self,"Freie Rechnung","Bitte zuerst ein Projekt anlegen.");return
        d=PartialInvoiceDialog(self.db,self,source_mode="Frei")
        if d.exec():
            self.db.backup("vor_freier_rechnung")
            iid,err=self.db.create_invoice(*d.new_invoice_data())
            if err:QMessageBox.information(self,"Freie Rechnung",err);return
            self.db.add_manual_invoice_position(iid)
            self.refresh_keep_invoice(iid)
    def import_historical_invoice(self):
        if not self.db.all_invoice_projects():
            QMessageBox.information(self,"Vorhandener Beleg","Bitte zuerst Kunde und Projekt anlegen.");return
        d=HistoricalInvoiceDialog(self.db,self,self.project.currentData())
        if not d.exec():return
        project_id,invoice_type,number,invoice_date,installment_no,net,gross,vat,paid,discount,payment_date,pdf,notes=d.data()
        copied_pdf=""
        if pdf:
            source=Path(pdf)
            safe=re.sub(r"[^A-Za-z0-9ÄÖÜäöüß._-]+","_",number).strip("._") or "Altbeleg"
            target=HISTORICAL_INVOICE_DIR/f"{safe}_{invoice_type}.pdf"
            if target.exists():target=HISTORICAL_INVOICE_DIR/f"{safe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            try:
                shutil.copy2(source,target);copied_pdf=str(target.resolve())
            except Exception as exc:
                QMessageBox.warning(self,"Original-PDF",f"Die PDF-Datei konnte nicht kopiert werden:\n{exc}");return
        self.db.backup("vor_historischem_rechnungsimport")
        iid,err=self.db.import_historical_invoice(
            project_id,invoice_type,number,invoice_date,installment_no,net,gross,vat,
            paid,discount,payment_date,copied_pdf,notes)
        if err:
            if copied_pdf:
                try:Path(copied_pdf).unlink()
                except OSError:pass
            QMessageBox.warning(self,"Vorhandener Beleg",err);return
        if copied_pdf:
            file_generated_document(self.db,project_id,copied_pdf,Path(copied_pdf).name,
                f"{invoice_type} {number} – übernommener Originalbeleg")
        self.refresh_keep_invoice(iid)
        QMessageBox.information(self,"Vorhandener Beleg übernommen",
            f'{invoice_type} {number} wurde mit ihrer Originalnummer übernommen.\n\n'
            "Der Aufmaßwerk-Rechnungsnummernkreis blieb unverändert.")
    def select_invoice(self):
        iid=self.iid()
        if not iid:return
        inv=self.db.invoice(iid)
        rows=self.db.invoice_positions(iid);self.loading_positions=True
        display=[];last=None
        for p in rows:
            key=invoice_title_key(p)
            if any(key) and key!=last:
                subtotal=sum(float(q["cumulative_quantity"] or 0)*float(q["unit_price"] or 0) for q in rows if invoice_title_key(q)==key)
                display.append(("title",key,subtotal))
            last=key;display.append(("position",p))
        self.pos.setRowCount(len(display))
        for r,entry in enumerate(display):
            if entry[0]=="title":
                # Titel = Gliederung, nicht editierbar.
                _,key,subtotal=entry
                for c,v in enumerate([f"TITEL {key[0]}".strip(),key[1],"","","","","",money(subtotal)]):
                    it=QTableWidgetItem(v);f=it.font();f.setBold(True);it.setFont(f);it.setFlags(Qt.ItemIsEnabled)
                    self.pos.setItem(r,c,it)
                continue
            p=entry[1]
            vals=[p["position_no"],p["short_text"],de_num(p["cumulative_quantity"],3),
                  de_num(p["new_quantity"],3),p["unit"],de_num(p["unit_price"]),de_num(p["line_total"]),
                  de_num(float(p["cumulative_quantity"] or 0)*float(p["unit_price"] or 0))]
            for c,v in enumerate(vals):
                it=QTableWidgetItem(v)
                if c==0:it.setData(Qt.UserRole,p["id"])
                if c in (2,7):it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                if inv["status"]!="Entwurf":it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                self.pos.setItem(r,c,it)
        self.loading_positions=False
        self.position_editor.setEnabled(False);self.position_editor.setVisible(False)
        previous=self.db.project_billed_net_before_invoice(inv["project_id"],iid)
        cumulative=self.db.invoice_cumulative_net(iid)
        open_amt=self.db.invoice_open_amount(iid)
        historical_note=("<br><b>Historischer Originalbeleg – außerhalb von Aufmaßwerk erstellt.</b>"
                         if inv["is_historical"] else "")
        self.meta.setText(f'<b>{inv["number"]} · {inv["invoice_type"]}</b>{historical_note}<br>'
                          f'Projekt: {inv["project_number"]} – {inv["project_name"]}<br>Kunde: {inv["company"]}<br>Status: {inv["status"]}')
        settlement=self.db.cumulative_invoice_settlement(iid)
        sec=settlement["security"]
        bau=settlement["construction"]
        deduction_lines=""
        if inv["security_enabled"]:
            deduction_lines += f'<br>− Sicherheitseinbehalt {de_num(inv["security_percent"])} %: {money(sec)}'
        if inv["construction_enabled"]:
            deduction_lines += f'<br>− {inv["construction_label"] or "Bauwesen"} {de_num(inv["construction_percent"])} %: {money(bau)}'
        prior_lines=""
        if inv["deduct_previous"] and inv["invoice_type"] in ("Teilrechnung","Schlussrechnung"):
            for p in self.db.previous_final_invoices(inv["project_id"],iid):
                eligible=(p["invoice_type"]=="Teilrechnung" or
                          (inv["invoice_type"]=="Schlussrechnung" and p["invoice_type"]=="Abschlagsrechnung"))
                if not eligible:continue
                paid=float(p["paid_total"] or 0);discount=float(p["discount_total"] or 0)
                adjustment=float(p["adjustment_total"] or 0)
                basis=float(p["payable_total"] if p["payable_total"] is not None else p["gross_total"] or 0)
                remaining=max(0.0,basis-paid-discount-adjustment)
                label=(f'{int(p["installment_no"] or 1)}. Teilrechnung' if p["invoice_type"]=="Teilrechnung"
                       else "Abschlagsrechnung")
                prior_lines+=(f'<br>{label} {p["number"]}: '
                              f'fortgeschrieben {money(paid+discount)} (gezahlt {money(paid)} · Skonto {money(discount)}) · '
                              f'Ausgleich nur Forderungslogik {money(adjustment)} · offen {money(remaining)}')
        self.summary.setText(f'<b>Kumulierte Leistung netto:</b> {money(settlement["cumulative_net"])}<br>'
                             f'MwSt. {de_num(inv["vat_rate"])} % · kumuliert brutto: <b>{money(settlement["cumulative_net"]+settlement["vat"])}</b>'
                             f'{deduction_lines}<br>'
                             f'= <b>Zahlbetrag: {money(inv["payable_total"])}</b><br>'
                             f'Offener Zahlungsbetrag: <b>{money(open_amt)}</b><br>'
                             f'Fällig: <b>{de_date(inv["due_date"])}</b> · '
                             f'{self.db.days_overdue(iid)} Tage überfällig'
                             f'{prior_lines}')
        pays=self.db.payments(iid);self.payments.setRowCount(len(pays))
        for r,p in enumerate(pays):
            vals=[p["payment_date"],money(p["paid_amount"]),money(p["discount_amount"]),money(p["adjustment_amount"]),
                  p["adjustment_type"] or "",p["adjustment_reason"] or ""]
            for c,v in enumerate(vals):
                it=QTableWidgetItem(v)
                if c==0:it.setData(Qt.UserRole,p["id"])
                self.payments.setItem(r,c,it)
        draft=inv["status"]=="Entwurf"
        for widget in self.draft_widgets:widget.setVisible(draft)
        self.edit_draft_button.setVisible(draft)
        self.final_button.setText("Vorschau && Freigabe" if draft else "Vorschau")
        # Spalten nach Inhalt, der Kurztext bekommt den restlichen Platz (nach dem
        # Wiederherstellen gespeicherter Spaltenbreiten erneut setzen).
        header=self.pos.horizontalHeader()
        for column in range(self.pos.columnCount()):
            header.setSectionResizeMode(column,QHeaderView.Stretch if column==1 else QHeaderView.ResizeToContents)
    def selected_invoice_position_id(self):
        if not self.pos.selectedItems():return None
        r=self.pos.currentRow()
        return self.pos.item(r,0).data(Qt.UserRole) if r>=0 and self.pos.item(r,0) else None

    def load_invoice_position_editor(self):
        if self.loading_positions:return
        iid=self.iid();ipid=self.selected_invoice_position_id()
        inv=self.db.invoice(iid) if iid else None
        row=next((p for p in self.db.invoice_positions(iid) if p["id"]==ipid),None) if iid and ipid else None
        editable=bool(inv and row and inv["status"]=="Entwurf")
        self.position_editor.setEnabled(editable)
        self.position_editor.setVisible(editable)
        if not editable:return
        self.edit_position_no.setText(row["position_no"] or "")
        self.edit_short_text.setText(row["short_text"] or "")
        self.edit_cumulative.setValue(float(row["cumulative_quantity"] or 0))
        self.edit_increment.setValue(float(row["new_quantity"] or 0))
        self.edit_unit.setCurrentText(row["unit"] or "")
        self.edit_unit_price.setValue(float(row["unit_price"] or 0))

    def close_invoice_position_editor(self):
        self.position_editor.setVisible(False)
        self.position_editor.setEnabled(False)
        self.pos.clearSelection()

    def save_invoice_position_editor(self):
        iid=self.iid();ipid=self.selected_invoice_position_id()
        inv=self.db.invoice(iid) if iid else None
        if not inv or inv["status"]!="Entwurf" or not ipid:
            QMessageBox.information(self,"Rechnungsposition","Bitte eine Position in einem Rechnungsentwurf auswählen.");return
        self.db.backup("vor_rechnungsposition_bearbeiten")
        qty=self.edit_increment.value();price=self.edit_unit_price.value()
        ok,err=self.db.update_invoice_position(
            ipid,self.edit_position_no.text().strip(),self.edit_short_text.text().strip(),
            qty,self.edit_unit.currentText().strip(),price,qty*price)
        if not ok:
            QMessageBox.warning(self,"Rechnungsposition",err);return
        self.refresh_keep_invoice(iid)

    def invoice_position_changed(self,item):
        if self.loading_positions:return
        iid=self.iid();inv=self.db.invoice(iid) if iid else None
        if not inv or inv["status"]!="Entwurf":return
        r=item.row();first=self.pos.item(r,0)
        if not first:return
        try:
            values=[self.pos.item(r,c).text() if self.pos.item(r,c) else "" for c in range(7)]
            qty=parse_de_number(values[3]);price=parse_de_number(values[5]);total=parse_de_number(values[6])
        except ValueError:
            QMessageBox.warning(self,"Rechnungsposition","Bitte Menge, EP und Gesamt als gültige Zahlen eingeben.")
            self.refresh_keep_invoice(iid);return
        # Menge oder EP berechnen den Gesamtwert neu; nur eine direkte Änderung in
        # der Spalte Gesamt bleibt als bewusster manueller Gesamtbetrag erhalten.
        manual_total=total if item.column()==6 else qty*price
        ok,err=self.db.update_invoice_position(first.data(Qt.UserRole),values[0],values[1],qty,values[4],price,manual_total)
        if not ok:QMessageBox.warning(self,"Rechnungsposition",err)
        self.refresh_keep_invoice(iid)

    def add_manual_position(self):
        iid=self.iid();inv=self.db.invoice(iid) if iid else None
        if not inv or inv["status"]!="Entwurf":
            QMessageBox.information(self,"Manuelle Position","Bitte zuerst einen Rechnungsentwurf auswählen.");return
        self.db.backup("vor_manueller_rechnungsposition")
        ipid,err=self.db.add_manual_invoice_position(iid)
        if err:QMessageBox.warning(self,"Manuelle Position",err);return
        self.refresh_keep_invoice(iid)

    def sync_draft(self):
        iid=self.iid()
        if not iid:
            QMessageBox.information(self,"Entwurf aktualisieren","Bitte zuerst eine Rechnung auswählen.");return
        inv=self.db.invoice(iid)
        if inv["status"]!="Entwurf":
            QMessageBox.information(self,"Entwurf aktualisieren",
                "Eine festgeschriebene Rechnung bleibt als historischer Stand unverändert.");return
        self.db.backup("vor_rechnungsentwurf_sync")
        ok,err=self.db.sync_invoice_with_measurement(iid)
        if not ok:
            QMessageBox.warning(self,"Entwurf aktualisieren",err);return
        self.refresh_keep_invoice(iid)

    def edit_draft(self):
        iid=self.iid()
        if not iid:
            QMessageBox.information(self,"Entwurf bearbeiten","Bitte zuerst eine Rechnung auswählen.");return
        inv=self.db.invoice(iid)
        if inv["status"]!="Entwurf":
            QMessageBox.information(self,"Entwurf bearbeiten","Nur Rechnungen im Status Entwurf können bearbeitet werden.");return
        d=PartialInvoiceDialog(self.db,self,inv)
        if d.exec():
            project,title,due,vat,tax_mode,pfrom,pto,skonto,skonto_due,security_enabled,security_percent,construction_enabled,construction_percent,construction_label,notes=d.data()
            self.db.backup("vor_rechnungsentwurf_bearbeiten")
            ok,err=self.db.update_invoice_draft(
                iid,title,due,vat,tax_mode,pfrom,pto,skonto,skonto_due,
                security_enabled,security_percent,construction_enabled,construction_percent,
                construction_label,notes,d.installment_no.value(),d.deduct_previous.isChecked())
            if not ok:QMessageBox.warning(self,"Entwurf bearbeiten",err);return
            self.refresh_keep_invoice(iid)

    def add_position_to_draft(self):
        iid=self.iid()
        if not iid:
            QMessageBox.information(self,"Position hinzufügen","Bitte zuerst einen Rechnungsentwurf auswählen.");return
        inv=self.db.invoice(iid)
        if inv["status"]!="Entwurf":
            QMessageBox.information(self,"Position hinzufügen","Positionen können nur in einem Entwurf verändert werden.");return
        d=InvoicePositionAddDialog(self.db,iid,self)
        if d.exec():
            ids=d.selected_ids()
            if not ids:
                QMessageBox.information(self,"Position hinzufügen","Bitte mindestens eine Position auswählen.");return
            self.db.backup("vor_rechnungsposition_hinzufuegen")
            errors=[]
            for mpid in ids:
                ok,err=self.db.add_invoice_position(iid,mpid)
                if not ok:errors.append(err)
            if errors:QMessageBox.warning(self,"Position hinzufügen","\n".join(errors))
            self.refresh_keep_invoice(iid)

    def remove_position_from_draft(self):
        iid=self.iid();ipid=self.selected_invoice_position_id()
        if not iid or not ipid:
            QMessageBox.information(self,"Position entfernen","Bitte zuerst rechts eine Rechnungsposition auswählen.");return
        inv=self.db.invoice(iid)
        if inv["status"]!="Entwurf":
            QMessageBox.information(self,"Position entfernen","Positionen einer festgeschriebenen Rechnung sind geschützt.");return
        if QMessageBox.question(self,"Position entfernen",
            "Ausgewählte Position aus diesem Rechnungsentwurf entfernen?\n\n"
            "Das Aufmaß und die Angebotsposition bleiben unverändert.\n"
            "Die Position bleibt auch bei „Entwurf aus Aufmaß aktualisieren“ ausgeschlossen.\n\n"
            "Über „Position hinzufügen“ kann sie später wieder aufgenommen werden.",
            QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:return
        self.db.backup("vor_rechnungsposition_entfernen")
        ok,err=self.db.remove_invoice_position(ipid)
        if not ok:QMessageBox.warning(self,"Position entfernen",err);return
        # Nur die markierte Position wurde entfernt. Auswahl und Detailansicht
        # derselben Rechnung bleiben sichtbar, damit nicht der Eindruck entsteht,
        # alle Positionen seien verschwunden.
        self.refresh_keep_invoice(iid)

    def reset_project_invoices(self):
        iid=self.iid()
        selected_inv=self.db.invoice(iid) if iid else None
        if not self.db.all_invoice_projects():
            QMessageBox.information(self,"Projektabrechnung auf 0 setzen","Es ist noch kein Projekt vorhanden.");return
        choose=ProjectBillingResetDialog(
            self.db,self,selected_inv["project_id"] if selected_inv else None)
        if not choose.exec():return
        project_id=choose.project_id()
        project=self.db.project(project_id)
        count=self.db.conn.execute(
            "SELECT COUNT(*) FROM invoices WHERE project_id=?",(project_id,)).fetchone()[0]
        if count==0:
            QMessageBox.information(self,"Projektabrechnung auf 0 setzen",
                f'Für das Projekt {project["number"]} sind bereits keine Rechnungen mehr vorhanden.');return
        payment_count=self.db.conn.execute("""SELECT COUNT(*) FROM payments WHERE invoice_id IN
          (SELECT id FROM invoices WHERE project_id=?)""",(project_id,)).fetchone()[0]
        if QMessageBox.question(self,"Projektabrechnung auf 0 setzen",
            f'Für das Projekt {project["number"]} – {one_line(project["name"])} werden ALLE {count} Rechnung(en) einschließlich '
            f'{payment_count} Zahlungseingang/-eingängen gelöscht.\n\n'
            'Anschließend wird der gesamte Abrechnungsstand im Aufmaß auf 0 zurückgesetzt.\n'
            'Angebot und Aufmaß bleiben erhalten.\n\n'
            'Der globale Rechnungsnummernkreis wird nicht zurückgesetzt.\n'
            'Vorher wird automatisch eine Datensicherung angelegt.\n\n'
            'Wirklich fortfahren?',
            QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:return
        self.db.backup("vor_projektabrechnung_auf_null")
        ok,stats,err=self.db.reset_project_invoices(project_id)
        if not ok:
            QMessageBox.critical(self,"Nullstellung nicht abgeschlossen",
                "Die Projektabrechnung konnte nicht vollständig zurückgesetzt werden.\n\n"
                f"Grund: {err}\n\nDie zuvor angelegte Datensicherung bleibt verfügbar.")
            self.refresh();return
        remaining=self.db.conn.execute("SELECT COUNT(*) FROM invoices WHERE project_id=?",
                                       (project_id,)).fetchone()[0]
        if remaining:
            QMessageBox.critical(self,"Nullstellung nicht abgeschlossen",
                f"Es sind noch {remaining} Rechnung(en) vorhanden. Es wird keine Erfolgsmeldung ausgegeben.")
            self.refresh();return
        QMessageBox.information(self,"Projektabrechnung auf 0 gesetzt",
            f'{stats["invoices"]} Rechnung(en), {stats["positions"]} Rechnungsposition(en), '
            f'{stats["payments"]} Zahlungseingang/-eingänge und {stats["reminders"]} Mahnung(en) wurden entfernt.\n'
            'Der Abrechnungsstand des Projekts steht wieder auf 0.\n'
            'Angebot und Aufmaß sind unverändert erhalten geblieben.')
        self.refresh()

    def finalize(self):
        iid=self.iid()
        if not iid:return
        inv=self.db.invoice(iid)
        if inv["status"]!="Entwurf":
            QMessageBox.information(self,"Rechnung freigeben","Diese Rechnung ist bereits freigegeben.");return
        if not InvoiceReleasePreviewDialog(self.db,iid,self).exec():return
        self.db.backup("vor_rechnung_freigeben")
        ok,err=self.db.finalize_invoice(iid)
        if not ok:QMessageBox.warning(self,"Rechnung freigeben",err);return
        self.refresh_keep_invoice(iid)
        QMessageBox.information(self,"Rechnung freigegeben","Die Rechnung wurde bewusst freigegeben und hat jetzt den Status Offen.")
    def delete_invoice(self):
        iid=self.iid()
        if not iid:return
        self.db.backup("vor_rechnungsentwurf_loeschen")
        ok,err=self.db.delete_invoice(iid)
        if not ok:QMessageBox.warning(self,"Löschen",err);return
        self.refresh()
    def preview_invoice(self):
        iid=self.iid()
        if not iid:
            QMessageBox.information(self,"Rechnungsvorschau","Bitte zuerst eine Rechnung auswählen.");return
        inv=self.db.invoice(iid)
        if inv["is_historical"]:
            path=(inv["source_pdf"] or "").strip()
            if path and Path(path).is_file():open_desktop_file(path,self,"Historischer Originalbeleg")
            else:QMessageBox.information(self,"Historischer Originalbeleg",
                "Für diesen übernommenen Beleg wurde kein Original-PDF hinterlegt.")
            return
        # Bei einer freigegebenen Rechnung zeigt die Vorschau exakt das
        # endgültige Dokument. Nur ein Entwurf erhält einen Vorschauhinweis.
        self.create_pdf(preview=inv["status"]=="Entwurf",view_only=True)

    def send_invoice_email(self):
        iid=self.iid()
        if not iid:
            QMessageBox.information(self,"E-Mail senden","Bitte zuerst eine Rechnung auswählen.");return
        inv=self.db.invoice(iid)
        if inv["is_historical"]:
            QMessageBox.information(self,"Historischer Originalbeleg",
                "Aufmaßwerk versendet den bereits außerhalb des Programms ausgestellten Beleg nicht erneut.");return
        if inv["status"]=="Entwurf":
            QMessageBox.information(self,"E-Mail senden",
                "Ein Rechnungsentwurf kann nicht als Rechnung versendet werden.\n\n"
                "Bitte die Rechnung zuerst über „Vorschau & Freigabe“ freigeben.");return
        path=self.create_pdf(open_after=False,automatic=True)
        if not path:return
        compose_email_with_pdf(self,path,inv["customer_email"],f'{inv["invoice_type"]} {inv["number"]}',
            "Guten Tag,\n\nanbei erhalten Sie unsere Rechnung als PDF.\n\nMit freundlichen Grüßen")
        file_generated_document(self.db,inv["project_id"],path,f'{inv["invoice_type"]}_{inv["number"]}_versendet_{date.today().isoformat()}.pdf',
            f'{inv["invoice_type"]} {inv["number"]} – per E-Mail versendet am {today_de()}')

    def create_pdf(self, checked=False, preview=False, open_after=True,view_only=False,automatic=False):
        iid=self.iid()
        if not iid:
            QMessageBox.information(self,"PDF","Bitte zuerst eine Rechnung auswählen.");return
        inv=self.db.invoice(iid);rows=self.db.invoice_positions(iid);previous_invoices=self.db.previous_final_invoices(inv["project_id"],iid)
        if inv["is_historical"]:
            QMessageBox.information(self,"Historischer Originalbeleg",
                "Für übernommene Rechnungen erzeugt Aufmaßwerk kein neues Rechnungs-PDF.\n\n"
                "Über die Vorschau kann ein hinterlegtes Original-PDF geöffnet werden.")
            return None
        company=self.db.company_settings()
        if preview or view_only:
            path=str(PREVIEW_DIR / f'VORSCHAU_{inv["number"]}_{inv["invoice_type"]}.pdf')
        elif automatic:
            path=str(DOCUMENT_DIR / f'{inv["number"]}_{inv["invoice_type"]}.pdf')
        else:
            default_path=DOCUMENT_DIR / f'{inv["number"]}_{inv["invoice_type"]}.pdf'
            path,_=QFileDialog.getSaveFileName(self,"Rechnung als PDF speichern",str(default_path),"PDF-Dateien (*.pdf)")
            if not path:return
            if not path.lower().endswith(".pdf"):path += ".pdf"

        writer=QPdfWriter(path);writer.setPageSize(QPageSize(QPageSize.A4));writer.setResolution(96)
        writer.setTitle(f'{inv["number"]} - {inv["invoice_type"]}');writer.setCreator(f"{APP_NAME} {APP_VERSION}")
        painter=QPainter(writer)
        if not painter.isActive():QMessageBox.critical(self,"PDF","Die PDF-Datei konnte nicht erstellt werden.");return None
        page=writer.pageLayout().paintRectPixels(writer.resolution());left=48;right=48;top=42;bottom=46;width=page.width()-left-right;y=top;page_no=1
        letterhead=Letterhead("invoice",writer);letterhead.draw(painter,True)
        def val(k):return (company[k] if company and k in company.keys() else "") or ""
        def font(size=9,bold=False):
            f=QFont("DejaVu Sans",size);f.setBold(bold);return f
        def txt(x,y0,w,h,text,size=9,bold=False,align=Qt.AlignLeft|Qt.AlignVCenter):
            painter.setFont(font(size,bold));painter.drawText(QRectF(x,y0,w,h),align|Qt.TextWordWrap,str(text or ""))
        def line(y0):painter.drawLine(left,y0,left+width,y0)
        def footer():
            if letterhead.active:
                txt(left+width*0.84,letterhead.page_number_y(),width*0.16,14,f"Seite {page_no}",7,False,Qt.AlignRight|Qt.AlignVCenter);return
            fy=page.height()-64
            legal=" | ".join([x for x in [val("registry"), ("Geschäftsführer: "+val("managing_director")) if val("managing_director") else ""] if x])
            taxes=" | ".join([x for x in [("Steuernummer: "+val("tax_no")) if val("tax_no") else "", ("USt-IdNr.: "+val("vat_id")) if val("vat_id") else ""] if x])
            bank=" | ".join([x for x in [val("bank"), ("IBAN: "+val("iban")) if val("iban") else "", ("BIC: "+val("bic")) if val("bic") else ""] if x])
            txt(left,fy,width*0.82,15,legal,6,False,Qt.AlignLeft|Qt.AlignTop)
            txt(left,fy+15,width*0.82,15,taxes,6,False,Qt.AlignLeft|Qt.AlignTop)
            txt(left,fy+30,width*0.82,15,bank,6,False,Qt.AlignLeft|Qt.AlignTop)
            txt(left+width*0.84,fy,width*0.16,45,f"Seite {page_no}",7,False,Qt.AlignRight|Qt.AlignVCenter)
        def new_page():
            nonlocal y,page_no
            footer();writer.newPage();page_no+=1;y=top
            letterhead.draw(painter,False);y=letterhead.content_top(y)
            if not letterhead.active:draw_pdf_brand(painter,val("logo_path"),val("company_name"),left,y,width*.42,32,11,width*.58)
            txt(left+width*0.67,y,width*0.33,22,f'{inv["invoice_type"]} {inv["number"]}',10,True,Qt.AlignRight|Qt.AlignVCenter);y+=38;line(y);y+=12
        def ensure(h):
            nonlocal y
            if y+h>letterhead.limit(page.height()-bottom-26):new_page()
        def text_height(text,w,size,bold=False,min_h=18):
            painter.setFont(font(size,bold))
            rect=painter.boundingRect(QRectF(0,0,w,1000),Qt.AlignLeft|Qt.AlignTop|Qt.TextWordWrap,str(text or ""))
            return max(min_h,int(rect.height())+4)
        def invoice_sequence():
            return max(1,int(inv["installment_no"] or 1))
        seq=invoice_sequence();doc_title=f"{seq}. Teilrechnung" if inv["invoice_type"]=="Teilrechnung" else inv["invoice_type"]

        # Briefbogen: vollständige Wortmarke links, Firmendaten separat rechts.
        # Ein vorhandenes Logo enthält üblicherweise bereits den Firmennamen und
        # wird deshalb nicht noch einmal mit schwarzem Text daneben gedoppelt.
        # Mit hinterlegtem PDF-Briefbogen übernimmt dieser Kopf und Firmendaten.
        if letterhead.active:y=letterhead.content_top(y)
        else:
            header_y=y;draw_pdf_brand(painter,val("logo_path"),val("company_name"),left,header_y,width*.55,70,18,width*.55)
            info_x=left+width*.69;info_w=width*.31;info_y=header_y
            header_color=QColor(val("invoice_header_color") or "#a40000")
            if not header_color.isValid():header_color=QColor("#a40000")
            painter.setPen(header_color)
            company_info_h=text_height(val("company_name") or APP_NAME,info_w,8,True,17)
            txt(info_x,info_y,info_w,company_info_h,val("company_name") or APP_NAME,8,True,Qt.AlignLeft|Qt.AlignTop)
            painter.setPen(Qt.black);info_y+=company_info_h+2
            for info in [val("street"),(val("zip")+" "+val("city")).strip(),val("phone"),val("email"),val("website")]:
                if info:
                    txt(info_x,info_y,info_w,14,info,7,False,Qt.AlignLeft|Qt.AlignTop);info_y+=14
            y=max(header_y+82,info_y+4)
        if preview and inv["status"]=="Entwurf":
            txt(left,y,width,20,"ENTWURF – RECHNUNGSVORSCHAU",11,True,Qt.AlignCenter|Qt.AlignVCenter);y+=22
        line(y);y+=18

        # Recipient and invoice metadata
        sender_line=" · ".join([x for x in [val("company_name"),val("street"),(val("zip")+" "+val("city")).strip()] if x])
        sender_h=text_height(sender_line,width*0.56,6,False,16)
        txt(left,y,width*0.56,sender_h,sender_line,6,False,Qt.AlignLeft|Qt.AlignTop);y+=sender_h+3
        recipient=[inv["company"],inv["customer_contact"],inv["customer_street"],f'{inv["customer_zip"] or ""} {inv["customer_city"] or ""}'.strip()]
        ry=y
        for item in recipient:
            if item:txt(left,ry,width*0.54,17,item,9,item==inv["company"]);ry+=17
        meta_x=left+width*0.60;meta_w=width*0.40
        meta=[("Kunden-Nr.",inv["customer_number"]),("Projekt-Nr.",inv["project_number"]),("Beleg-Nr.",inv["number"]),
              ("Datum",de_date(inv["created_at"])),("Fällig",de_date(inv["due_date"]))]
        my=y
        for k,v in meta:
            txt(meta_x,my,meta_w*0.42,16,k,8,True);txt(meta_x+meta_w*0.43,my,meta_w*0.57,16,v,8);my+=16
        y=max(ry,my)+16
        title_h=text_height(f'{doc_title} {inv["number"]}',width*.72,16,True,30)
        txt(left,y,width*.72,title_h,f'{doc_title} {inv["number"]}',16,True,Qt.AlignLeft|Qt.AlignTop);y+=title_h
        project_text=f'Projektbezeichnung: {inv["project_name"]}'
        project_h=text_height(project_text,width,10,True,20)
        txt(left,y,width,project_h,project_text,10,True,Qt.AlignLeft|Qt.AlignTop);y+=project_h
        if inv["site"]:txt(left,y,width,18,f'Baustelle: {inv["site"]}',9);y+=18
        if inv["performance_from"] or inv["performance_to"]:
            txt(left,y,width,18,f'Ausführungszeitpunkt: {de_date(inv["performance_from"])} - {de_date(inv["performance_to"])}',9);y+=18
        y+=8

        # Positions
        painter.fillRect(QRectF(left,y,width,25),Qt.lightGray)
        txt(left+3,y,width*.08,25,"Pos.",8,True);txt(left+width*.08+3,y,width*.47,25,"Kumulierte Menge / Bezeichnung",8,True)
        txt(left+width*.57,y,width*.12,25,"Einheit",8,True);txt(left+width*.69,y,width*.14,25,"Einzelpreis",8,True,Qt.AlignRight|Qt.AlignVCenter)
        txt(left+width*.83,y,width*.17-3,25,"Gesamtpreis",8,True,Qt.AlignRight|Qt.AlignVCenter);y+=27
        def text_height(text,w,size,bold=False,min_h=18):
            painter.setFont(font(size,bold))
            rect=painter.boundingRect(QRectF(0,0,w,1000),Qt.AlignLeft|Qt.AlignTop|Qt.TextWordWrap,str(text or ""))
            return max(min_h,int(rect.height())+4)

        last_title=None
        for p in rows:
            key=invoice_title_key(p)
            if any(key) and key!=last_title:
                ensure(64);painter.fillRect(QRectF(left,y,width,22),QColor(235,235,235))
                txt(left+3,y,width-6,22,invoice_title_label(key),9,True);y+=26
            last_title=key
            longtext=(p["long_text"] or "").strip()
            short_w=width*.30
            long_w=width*.58
            short_h=text_height(p["short_text"],short_w,8,True,24)
            long_h=text_height(longtext,long_w,7,False,0) if longtext else 0
            content_h=max(30,short_h)+long_h+(7 if longtext else 2)
            row_h=content_h+8
            ensure(row_h+5)

            row_top=y
            txt(left+3,row_top,width*.08-4,30,p["position_no"],8)
            txt(left+width*.08+3,row_top,width*.16,30,f'{de_num(p["cumulative_quantity"],3)} {p["unit"]}',8)
            txt(left+width*.25,row_top,short_w,short_h,p["short_text"],8,True,Qt.AlignLeft|Qt.AlignTop)
            txt(left+width*.57,row_top,width*.12,30,p["unit"],8)
            txt(left+width*.69,row_top,width*.14,30,money(p["unit_price"]),8,False,Qt.AlignRight|Qt.AlignVCenter)
            cumulative_line=float(p["cumulative_quantity"] or 0)*float(p["unit_price"] or 0)
            txt(left+width*.83,row_top,width*.17-3,30,money(cumulative_line),8,False,Qt.AlignRight|Qt.AlignVCenter)

            text_y=row_top+short_h+2
            if longtext:
                txt(left+width*.25,text_y,long_w,long_h,longtext,7,False,Qt.AlignLeft|Qt.AlignTop)

            # Separator only after every text block is finished.
            y=row_top+row_h
            line(y);y+=5
        y+=14

        # Settlement / cumulative reconciliation
        cumulative_mode=bool(inv["deduct_previous"]) and inv["invoice_type"] in ("Teilrechnung","Schlussrechnung")
        if cumulative_mode:
            previous_invoices=[x for x in previous_invoices
                if x["invoice_type"]=="Teilrechnung" or
                   (inv["invoice_type"]=="Schlussrechnung" and x["invoice_type"]=="Abschlagsrechnung")]
        else:previous_invoices=[]
        try:
            historical_import=bool(self.db.conn.execute("""SELECT 1 FROM migration_id_map
              WHERE entity='invoice' AND target_id=?""",(iid,)).fetchone())
        except sqlite3.OperationalError:
            historical_import=False
        settlement=self.db.cumulative_invoice_settlement(iid)
        current_net=float(inv["net_total"] or 0)
        cumulative_net=settlement["cumulative_net"]
        vat=settlement["vat"];gross=cumulative_net+vat
        # Der Summenblock darf nicht auf halber Höhe in die feste Fußzeile
        # hineinlaufen. Seine Höhe hängt von vorherigen Rechnungen und Abzügen ab.
        summary_height=190+len(previous_invoices)*88
        if cumulative_mode:summary_height+=52
        if inv["security_enabled"]:summary_height+=20
        if inv["construction_enabled"]:summary_height+=20
        if float(inv["skonto_percent"] or 0)>0:summary_height+=60
        if str(inv["tax_mode"] or "").startswith("Steuerschuldnerschaft"):summary_height+=20
        if inv["notes"]:summary_height+=45
        if val("footer_note"):summary_height+=35
        groups=[]
        for p in rows:
            if invoice_title_key(p) not in groups:groups.append(invoice_title_key(p))
        # Nur sinnvoll ab zwei Gruppen; ein einzelner Titel wäre gleich „Kumulierte Leistung netto“.
        show_titles=len(groups)>1 and any(any(key) for key in groups)
        if show_titles:summary_height+=22*len(groups)+12
        ensure(summary_height)
        txt(left,y,width,22,"Zusammenstellung",11,True);y+=25
        if show_titles:
            for key in groups:
                amount=sum(float(q["cumulative_quantity"] or 0)*float(q["unit_price"] or 0) for q in rows if invoice_title_key(q)==key)
                txt(left+14,y,width*.70,19,invoice_title_label(key),9)
                txt(left+width*.74,y,width*.26,19,money(amount),9,False,Qt.AlignRight|Qt.AlignVCenter);y+=21
            line(y);y+=6
        txt(left,y,width*.72,20,"Kumulierte Leistung netto",9,True);txt(left+width*.74,y,width*.26,20,money(cumulative_net),9,True,Qt.AlignRight|Qt.AlignVCenter);y+=21
        for prev in previous_invoices:
            ensure(100)
            paid=float(prev["paid_total"] or 0);discount=float(prev["discount_total"] or 0)
            settled=paid+discount
            if prev["invoice_type"]=="Teilrechnung":
                no=max(1,int(prev["installment_no"] or 1))
                label=f'abzüglich Zahlung + Skonto {no}. Teilrechnung {prev["number"]}'
            else:
                label=f'abzüglich Zahlung + Skonto Abschlagsrechnung {prev["number"]}'
            txt(left+14,y,width*.70,19,label,8);txt(left+width*.74,y,width*.26,19,"- "+money(settled),8,False,Qt.AlignRight|Qt.AlignVCenter);y+=20
            adjustment=float(prev["adjustment_total"] or 0)
            basis=float(prev["payable_total"] if prev["payable_total"] is not None else prev["gross_total"] or 0)
            open_amount=max(0.0,basis-paid-discount-adjustment)
            txt(left+28,y,width*.68,16,"tatsächlich gezahlt",7)
            txt(left+width*.74,y,width*.26,16,money(paid),7,False,Qt.AlignRight|Qt.AlignVCenter);y+=16
            txt(left+28,y,width*.68,16,"Skontobetrag",7)
            txt(left+width*.74,y,width*.26,16,money(discount),7,False,Qt.AlignRight|Qt.AlignVCenter);y+=16
            if adjustment>0.005:
                txt(left+28,y,width*.68,16,"Ausgleich (nur Forderungslogik, hier nicht abgezogen)",7)
                txt(left+width*.74,y,width*.26,16,money(adjustment),7,False,Qt.AlignRight|Qt.AlignVCenter);y+=16
            txt(left+28,y,width*.68,16,"noch offen",7,open_amount>0.005)
            txt(left+width*.74,y,width*.26,16,money(open_amount),7,open_amount>0.005,Qt.AlignRight|Qt.AlignVCenter);y+=18
        line(y);y+=5
        if str(inv["tax_mode"] or "").startswith("Steuerschuldnerschaft"):
            txt(left,y,width*.72,20,"0,00 % MwSt. - Steuerschuldnerschaft des Leistungsempfängers",8)
            txt(left+width*.74,y,width*.26,20,money(0),8,False,Qt.AlignRight|Qt.AlignVCenter);y+=21
        else:
            txt(left,y,width*.72,20,f'{de_num(inv["vat_rate"])} % MwSt.',8);txt(left+width*.74,y,width*.26,20,money(vat),8,False,Qt.AlignRight|Qt.AlignVCenter);y+=21
        line(y);y+=5
        gross_label="Kumulierte Rechnungssumme" if cumulative_mode else "Rechnungsbetrag"
        txt(left,y,width*.72,24,gross_label,11,True)
        txt(left+width*.74,y,width*.26,24,money(gross),11,True,Qt.AlignRight|Qt.AlignVCenter);y+=28

        # Der Zahlbetrag enthält bei kumulativen Rechnungen bereits die echten
        # Zahlungen und anerkannten Skonti früherer Teilrechnungen. Dieser
        # Gesamtabzug muss direkt im Summenblock sichtbar sein, damit sich der
        # Betrag ohne Rücksprung zur ausführlichen Zusammenstellung prüfen lässt.
        previous_settled=float(settlement["settled"] or 0)
        subtotal_after_previous=gross-previous_settled
        if cumulative_mode:
            deduction_title=("abzüglich Zahlungen und Skonto aus Teil- und Abschlagsrechnungen"
                             if inv["invoice_type"]=="Schlussrechnung"
                             else "abzüglich Zahlungen und Skonto aus vorherigen Teilrechnungen")
            txt(left+14,y,width*.70,19,deduction_title,8)
            txt(left+width*.74,y,width*.26,19,"- "+money(previous_settled),8,False,Qt.AlignRight|Qt.AlignVCenter);y+=20
            line(y);y+=5
            subtotal_title=("Zwischensumme nach Teil- und Abschlagsrechnungen"
                            if inv["invoice_type"]=="Schlussrechnung"
                            else "Zwischensumme nach vorherigen Teilrechnungen")
            txt(left,y,width*.72,22,subtotal_title,9,True)
            txt(left+width*.74,y,width*.26,22,money(subtotal_after_previous),9,True,Qt.AlignRight|Qt.AlignVCenter);y+=26

        # Optionale Bau-/Vertragsabzüge. Prozentbasis ist bewusst der Netto-Betrag.
        security_amount=settlement["security"]
        construction_amount=settlement["construction"]
        if inv["security_enabled"]:
            txt(left+14,y,width*.70,19,f'abzüglich {de_num(inv["security_percent"])} % Sicherheitseinbehalt',8)
            txt(left+width*.74,y,width*.26,19,"- "+money(security_amount),8,False,Qt.AlignRight|Qt.AlignVCenter);y+=20
        if inv["construction_enabled"]:
            label=(inv["construction_label"] or "Bauwesen")
            txt(left+14,y,width*.70,19,f'abzüglich {de_num(inv["construction_percent"])} % {label}',8)
            txt(left+width*.74,y,width*.26,19,"- "+money(construction_amount),8,False,Qt.AlignRight|Qt.AlignVCenter);y+=20

        payable=settlement["payable"]
        if cumulative_mode or inv["security_enabled"] or inv["construction_enabled"]:
            line(y);y+=5
            txt(left,y,width*.72,22,"Zahlbetrag",10,True)
            txt(left+width*.74,y,width*.26,22,money(payable),10,True,Qt.AlignRight|Qt.AlignVCenter);y+=26

        # Skonto wird auf den tatsächlichen Zahlbetrag nach den aktivierten Abzügen berechnet.
        sk=float(inv["skonto_percent"] or 0)
        if sk>0:
            sk_amount=payable*sk/100.0;sk_pay=payable-sk_amount
            txt(left,y,width,18,f'Zahlbar bis zum {de_date(inv["skonto_due_date"])} mit {de_num(sk)} % Skonto',8);y+=18
            txt(left,y,width*.72,18,f'abzüglich {de_num(sk)} % Skonto vom Zahlbetrag',8)
            txt(left+width*.74,y,width*.26,18,"- "+money(sk_amount),8,False,Qt.AlignRight|Qt.AlignVCenter);y+=18
            line(y);y+=4
            txt(left,y,width*.72,18,"Skontierter Zahlbetrag",8,True);txt(left+width*.74,y,width*.26,18,money(sk_pay),8,True,Qt.AlignRight|Qt.AlignVCenter);y+=20
        txt(left,y,width,18,f'Ohne Abzug zahlbar bis zum: {de_date(inv["due_date"])}',8);y+=20
        if str(inv["tax_mode"] or "").startswith("Steuerschuldnerschaft"):
            txt(left,y,width,18,"Steuerschuldnerschaft des Leistungsempfängers (§ 13b UStG)",8,True);y+=20
        if inv["notes"]:ensure(45);txt(left,y,width,38,inv["notes"],8);y+=40
        if val("footer_note"):ensure(35);txt(left,y,width,30,val("footer_note"),7);y+=32
        footer();painter.end()
        einvoice_ok,einvoice_text=(False,"") if (preview or view_only) else create_einvoice_pdf(self.db,iid,path)
        self.last_einvoice=(einvoice_ok,einvoice_text)
        if preview or view_only:
            if open_after:
                open_desktop_file(path,self,"Rechnungsvorschau" if preview else "Rechnung")
        elif automatic:
            # Freigabe und E-Mail laufen ohne Rückfrage; nur fehlende Angaben werden gemeldet.
            if einvoice_text and not einvoice_ok:QMessageBox.warning(self,"E-Rechnung",einvoice_text)
        elif not automatic:
            QMessageBox.information(self,"PDF erstellt",f"Die Rechnung wurde gespeichert:\n\n{path}"+(f"\n\n{einvoice_text}" if einvoice_text else ""))
            file_generated_document(self.db,inv["project_id"],path,f'{inv["invoice_type"]}_{inv["number"]}.pdf',
                f'{inv["invoice_type"]} {inv["number"]} – erstellt am {today_de()}')
        return str(Path(path).resolve())

    def check_einvoice(self):
        iid=self.iid()
        if not iid:
            QMessageBox.information(self,"E-Rechnung","Bitte zuerst eine Rechnung auswählen.");return
        inv=self.db.invoice(iid)
        if inv["is_historical"]:
            QMessageBox.information(self,"E-Rechnung","Übernommene Originalbelege werden nicht neu als E-Rechnung erzeugt.");return
        data,missing,hints=zugferd_invoice_data(self.db,iid)
        if missing:text="Für die E-Rechnung fehlen noch Angaben:\n\n• "+"\n• ".join(missing)
        else:
            text=(f'Alle Pflichtangaben sind vorhanden. Beim Ausgeben wird {inv["invoice_type"]} {inv["number"]} als E-Rechnung '
                  f'(ZUGFeRD, Profil EN 16931) erzeugt.\n\nPositionen: {len(data["lines"])} · netto {money(data["line_total"])} · '
                  f'Steuer {money(data["tax"])} · brutto {money(data["grand"])}'
                  +(f' · bereits gezahlt {money(data["prepaid"])}' if data["prepaid"] else "")+f' · fällig {money(data["due"])}')
        if hints:text+="\n\nHinweise:\n• "+"\n• ".join(hints)
        if not einvoice_enabled():text+="\n\nAchtung: Die E-Rechnung ist in den Einstellungen ausgeschaltet."
        (QMessageBox.warning if missing else QMessageBox.information)(self,"E-Rechnung prüfen",text)

    def create_reminder(self):
        iid=self.iid()
        if not iid:
            QMessageBox.information(self,"Mahnung erstellen","Bitte zuerst eine Rechnung auswählen.");return
        if create_reminder_with_pdf(self,self.db,iid):self.refresh_keep_invoice(iid)

    def write_reminder_pdf(self,path,iid,level,reminder_date,new_due,note,open_amount):
        inv=self.db.invoice(iid);company=self.db.company_settings()
        label="Zahlungserinnerung" if int(level)==0 else f"{int(level)}. Mahnung"
        writer=QPdfWriter(str(path));writer.setPageSize(QPageSize(QPageSize.A4));writer.setResolution(96)
        writer.setTitle(f'{label} zu Rechnung {inv["number"]}');writer.setCreator(f'{APP_NAME} {APP_VERSION}')
        painter=QPainter(writer)
        if not painter.isActive():return False,"PDF-Datei konnte nicht geöffnet werden."
        page=writer.pageLayout().paintRectPixels(writer.resolution());left=55;width=page.width()-110;y=55
        letterhead=Letterhead("reminder",writer);letterhead.draw(painter,True)
        def val(k):return (company[k] if company and k in company.keys() else "") or ""
        def draw(text,h=24,size=9,bold=False,align=Qt.AlignLeft|Qt.AlignVCenter):
            nonlocal y
            f=QFont("DejaVu Sans",size);f.setBold(bold);painter.setFont(f)
            painter.drawText(QRectF(left,y,width,h),align|Qt.TextWordWrap,str(text or ""));y+=h
        if letterhead.active:y=letterhead.content_top(y)
        else:
            draw_pdf_brand(painter,val("logo_path"),val("company_name"),left,y,width*.22,34,18,width)
            y+=34
            draw(" · ".join(x for x in [val("street"),(val("zip")+" "+val("city")).strip(),val("phone"),val("email")] if x),18,7)
            painter.drawLine(left,y,left+width,y);y+=24
        draw(inv["company"],22,10,True);draw(inv["customer_contact"],18)
        draw(inv["customer_street"],18);draw(f'{inv["customer_zip"] or ""} {inv["customer_city"] or ""}'.strip(),18)
        y+=28;draw(label,36,17,True)
        draw(f'Mahndatum: {de_date(reminder_date)}',20)
        y+=14
        draw(f'Sehr geehrte Damen und Herren,',22)
        intro=("bei der Durchsicht unseres Kontos konnten wir noch keinen vollständigen Ausgleich "
               "der folgenden Rechnung feststellen.")
        draw(intro,46,9)
        y+=10
        rows=[("Rechnungsnummer",inv["number"]),("Rechnungsdatum",de_date(inv["created_at"])),
              ("Ursprünglich fällig",de_date(inv["due_date"])),("Projekt",f'{inv["project_number"]} – {inv["project_name"]}'),
              ("Noch offener Betrag",money(open_amount)),("Neue Zahlungsfrist",de_date(new_due))]
        for key,value in rows:
            f=QFont("DejaVu Sans",9);f.setBold(True);painter.setFont(f);painter.drawText(QRectF(left,y,width*.35,22),Qt.AlignLeft|Qt.AlignVCenter,key)
            f.setBold(False);painter.setFont(f);painter.drawText(QRectF(left+width*.36,y,width*.64,22),Qt.AlignLeft|Qt.AlignVCenter|Qt.TextWordWrap,str(value));y+=24
        y+=18;draw(note,70,9)
        draw("Bitte berücksichtigen Sie diese Nachricht als gegenstandslos, falls Ihre Zahlung inzwischen eingegangen ist.",40,8)
        y+=18;draw("Mit freundlichen Grüßen",22);draw(val("company_name") or APP_NAME,22,9,True)
        footer=" | ".join(x for x in [val("bank"),("IBAN: "+val("iban")) if val("iban") else "",("BIC: "+val("bic")) if val("bic") else "",val("tax_no")] if x)
        if not letterhead.active:
            painter.setFont(QFont("DejaVu Sans",6));painter.drawText(QRectF(left,page.height()-55,width,30),Qt.AlignLeft|Qt.AlignVCenter|Qt.TextWordWrap,footer)
        painter.end();return True,None

    def _preview_or_finalize(self):
        iid=self.iid();inv=self.db.invoice(iid) if iid else None
        if inv and inv["status"]=="Entwurf":self.finalize()
        else:self.preview_invoice()

    def _confirm_reset(self):
        project=self.db.project(self.project.currentData()) if self.project.currentData() else None
        if not project:return
        text,ok=QInputDialog.getText(self,"Projektabrechnung auf 0 setzen",
            f"ACHTUNG: Das löscht ALLE Rechnungen und Zahlungen von Projekt {project['number']}.\n\n"
            "Zur Bestätigung bitte die Projektnummer eintippen:")
        if not ok:return
        if text.strip()!=str(project["number"]):
            QMessageBox.information(self,"Projektabrechnung","Die Projektnummer stimmt nicht – es wurde nichts gelöscht.");return
        self.reset_project_invoices()

    # Ausgleich und Buchung löschen nutzen die bewährten Abläufe des früheren Moduls Zahlungen.
    def current_invoice_id(self):return self.iid()
    def current_payment_id(self):
        r=self.payments.currentRow();item=self.payments.item(r,0) if r>=0 else None
        return item.data(Qt.UserRole) if item and self.payments.selectionModel().hasSelection() else None
    def add_adjustment(self):PaymentsPage.add_adjustment(self)
    def delete_payment(self):PaymentsPage.delete_payment(self)

    def payment(self):
        iid=self.iid()
        if not iid:return
        inv=self.db.invoice(iid)
        if inv["status"]=="Entwurf":
            QMessageBox.information(self,"Zahlungseingang","Bitte die Teilrechnung zuerst festschreiben.");return
        if self.db.invoice_open_amount(iid)<=0.005:
            QMessageBox.information(self,"Zahlungseingang","Diese Rechnung ist bereits vollständig ausgeglichen.");return
        d=PaymentDialog(self.db,iid,self)
        if d.exec():
            self.db.backup("vor_zahlungseingang")
            self.db.add_payment(iid,*d.data());self.refresh()

class CompanySettingsPage(QWidget):
    FIELDS=[("company_name","Firmenname"),("street","Straße / Hausnummer"),("zip","PLZ"),("city","Ort"),
            ("phone","Telefon"),("email","E-Mail"),("website","Webseite"),("tax_no","Steuernummer"),
            ("vat_id","USt-IdNr."),("registry","Handelsregister"),("managing_director","Geschäftsführer / Inhaber"),
            ("bank","Bank"),("iban","IBAN"),("bic","BIC")]
    def __init__(self,db):
        super().__init__();self.db=db;l=QVBoxLayout(self);t=QLabel("Firmen- & Rechnungsdaten");t.setObjectName("pageTitle")
        title_row=QHBoxLayout();title_row.addWidget(t);title_row.addStretch()
        manual=QPushButton("📖  Bedienungsanleitung");manual.setToolTip("Öffnet die Anleitung als PDF: vom Kunden über Angebot und Aufmaß bis zur Rechnung")
        manual.clicked.connect(self.open_manual);title_row.addWidget(manual);l.addLayout(title_row)
        hint=QLabel("Diese Angaben werden im Briefkopf und Fußbereich der PDF-Rechnungen verwendet.");hint.setWordWrap(True);l.addWidget(hint)
        language_box=QGroupBox(ui("ui_language"))
        language_layout=QFormLayout(language_box)
        self.language_selector=QComboBox()
        self.language_selector.addItem("Deutsch","de");self.language_selector.addItem("العربية","ar");self.language_selector.addItem("English","en")
        language_settings=QSettings(str(DATA_ROOT / "settings" / "window.ini"),QSettings.IniFormat)
        language_index=self.language_selector.findData(language_settings.value("appearance/language",UI_LANGUAGE,type=str))
        self.language_selector.setCurrentIndex(max(0,language_index))
        language_layout.addRow(ui("ui_language"),self.language_selector)
        language_hint=QLabel(ui("restart_language"));language_hint.setWordWrap(True)
        language_layout.addRow("",language_hint);l.addWidget(language_box)
        self.language_selector.currentIndexChanged.connect(self.change_language)

        appearance=QGroupBox("Erscheinungsbild")
        appearance_layout=QFormLayout(appearance)
        self.theme_selector=QComboBox()
        for theme_id,data in THEMES.items():self.theme_selector.addItem(data["label"],theme_id)
        current_theme=QApplication.instance().property("appTheme") or DEFAULT_THEME
        current_index=self.theme_selector.findData(current_theme)
        if current_index>=0:self.theme_selector.setCurrentIndex(current_index)
        self.theme_selector.setToolTip("Farbschema für die gesamte Aufmaßwerk-Oberfläche auswählen")
        self.theme_selector.setAccessibleName("Erscheinungsbild auswählen")
        appearance_layout.addRow("Design",self.theme_selector)
        appearance_hint=QLabel("Die Änderung wird sofort angewendet und für den nächsten Programmstart gespeichert.")
        appearance_hint.setWordWrap(True);appearance_layout.addRow("",appearance_hint)
        l.addWidget(appearance)
        self.theme_selector.currentIndexChanged.connect(self.change_theme)
        form=QFormLayout();self.widgets={}
        row=db.company_settings()
        for key,label in self.FIELDS:
            w=QLineEdit();w.setText((row[key] if row else "") or "");self.widgets[key]=w;form.addRow(label,w)
        self.footer=QTextEdit();self.footer.setPlainText((row["footer_note"] if row else "") or "");form.addRow("Zusätzlicher Fußtext",self.footer)
        self.logo_path=(row["logo_path"] if row and "logo_path" in row.keys() else "") or ""
        logo_row=QWidget();logo_layout=QHBoxLayout(logo_row);logo_layout.setContentsMargins(0,0,0,0)
        self.logo_preview=QLabel();self.logo_preview.setFixedSize(180,70);self.logo_preview.setAlignment(Qt.AlignCenter)
        choose_logo=QPushButton("Logo auswählen …");choose_logo.clicked.connect(self.choose_logo)
        remove_logo=QPushButton("Logo entfernen");remove_logo.clicked.connect(self.remove_logo)
        logo_layout.addWidget(self.logo_preview);logo_layout.addWidget(choose_logo);logo_layout.addWidget(remove_logo);logo_layout.addStretch()
        form.addRow("Firmenlogo (PNG/JPG)",logo_row);self.update_logo_preview()
        self.invoice_header_color=(row["invoice_header_color"] if row and "invoice_header_color" in row.keys() else "#a40000") or "#a40000"
        color_row=QWidget();color_layout=QHBoxLayout(color_row);color_layout.setContentsMargins(0,0,0,0)
        self.color_preview=QLabel();self.color_preview.setFixedSize(54,28)
        choose_color=QPushButton("Farbe auswählen …");choose_color.clicked.connect(self.choose_invoice_header_color)
        reset_color=QPushButton("Standardrot");reset_color.clicked.connect(lambda:self.set_invoice_header_color("#a40000"))
        color_layout.addWidget(self.color_preview);color_layout.addWidget(choose_color);color_layout.addWidget(reset_color);color_layout.addStretch()
        form.addRow("Firmenschriftzug auf Rechnungen",color_row);self.update_color_preview()
        l.addLayout(form);b=icon_button("save","Firmenangaben speichern",self.save);l.addWidget(b,0,Qt.AlignLeft)
        einvoice_box=QGroupBox("E-Rechnung (ZUGFeRD)");einvoice_layout=QVBoxLayout(einvoice_box)
        self.einvoice_check=QCheckBox("Rechnungen als E-Rechnung ausgeben (PDF mit eingebetteten Rechnungsdaten, Profil EN 16931)")
        self.einvoice_check.setChecked(einvoice_enabled())
        self.einvoice_check.toggled.connect(lambda on:(einvoice_settings().setValue("enabled","true" if on else "false"),einvoice_settings().sync()))
        einvoice_hint=QLabel("Die Rechnung sieht aus wie bisher und lässt sich normal öffnen und drucken. Zusätzlich stecken die Rechnungsdaten "
                             "maschinenlesbar im PDF, wie es für Rechnungen zwischen Unternehmen vorgeschrieben wird. Benötigt werden die eigenen "
                             "Firmendaten oben (mit USt-IdNr. oder Steuernummer) und die Anschrift des Kunden; bei § 13b auch dessen USt-IdNr. "
                             "Unter Rechnungen → Weitere → „E-Rechnung prüfen“ zeigt das Programm, ob etwas fehlt.")
        einvoice_hint.setWordWrap(True);einvoice_layout.addWidget(self.einvoice_check);einvoice_layout.addWidget(einvoice_hint);l.addWidget(einvoice_box)

        lhbox=QGroupBox("Briefbogen (PDF)");lhl=QGridLayout(lhbox)
        lh_info=QLabel("Ist ein Briefbogen hinterlegt, werden Angebote, Rechnungen, Mahnungen, Aufmaße und Briefe darauf gedruckt. "
                       "Logo, Briefkopf und Fußzeile kommen dann aus dem PDF.")
        lh_info.setWordWrap(True);lhl.addWidget(lh_info,0,0,1,4)
        self.lh_labels={}
        for row_index,(key,label) in enumerate([("first","Seite 1"),("follow","Folgeseiten (optional)")],1):
            lhl.addWidget(QLabel(label),row_index,0);name=QLabel();self.lh_labels[key]=name;lhl.addWidget(name,row_index,1)
            choose=QPushButton("PDF auswählen …");choose.clicked.connect(lambda _c=False,k=key:self.choose_letterhead(k))
            remove=QPushButton("Entfernen");remove.clicked.connect(lambda _c=False,k=key:self.remove_letterhead(k))
            lhl.addWidget(choose,row_index,2);lhl.addWidget(remove,row_index,3)
        s=letterhead_settings()
        self.lh_top=QDoubleSpinBox();self.lh_top.setRange(0,200);self.lh_top.setSuffix(" mm");self.lh_top.setValue(float(s.value("top_mm",45) or 45))
        self.lh_bottom=QDoubleSpinBox();self.lh_bottom.setRange(0,200);self.lh_bottom.setSuffix(" mm");self.lh_bottom.setValue(float(s.value("bottom_mm",30) or 30))
        margins=QHBoxLayout();margins.addWidget(QLabel("Freiraum oben:"));margins.addWidget(self.lh_top)
        margins.addSpacing(16);margins.addWidget(QLabel("Freiraum unten:"));margins.addWidget(self.lh_bottom);margins.addStretch()
        lhl.addLayout(margins,3,0,1,4)
        uses=QHBoxLayout();uses.addWidget(QLabel("Verwenden für:"));self.lh_uses={}
        for key,label in LETTERHEAD_KINDS:
            box=QCheckBox(label);box.setChecked(s.value(f"use/{key}",True,type=bool));self.lh_uses[key]=box;uses.addWidget(box)
            box.toggled.connect(self.save_letterhead_options)
        sample=QPushButton("Probeseite ansehen");sample.clicked.connect(self.letterhead_sample);uses.addStretch();uses.addWidget(sample)
        lhl.addLayout(uses,4,0,1,4);lhl.setColumnStretch(1,1)
        self.lh_top.valueChanged.connect(self.save_letterhead_options);self.lh_bottom.valueChanged.connect(self.save_letterhead_options)
        l.addWidget(lhbox);self.update_letterhead_labels()

        nrbox=QGroupBox("Nummernkreise")
        nrl=QVBoxLayout(nrbox)
        info=QLabel("Zentrale Vergabe für Kunden, Projekte, Angebote, Rechnungen und Mahnungen. "
                    "Teil-, Schluss- und andere Rechnungen verwenden gemeinsam den Rechnungsnummernkreis.")
        info.setWordWrap(True);nrl.addWidget(info)
        grid=QGridLayout()
        for col,text in enumerate(["Bereich","Präfix","Nächste Nummer","Stellen","Jahr verwenden","Vorschau"]):
            grid.addWidget(QLabel(f"<b>{text}</b>"),0,col)
        self.nr_widgets={}
        for rowi,r in enumerate(self.db.number_ranges(),1):
            key=r["range_key"];grid.addWidget(QLabel(r["label"]),rowi,0)
            prefix=QLineEdit(r["prefix"] or "");prefix.setMaximumWidth(90)
            nxt=QSpinBox();nxt.setRange(1,999999999);nxt.setValue(int(r["next_value"] or 1));nxt.setMaximumWidth(120)
            digits=QSpinBox();digits.setRange(1,10);digits.setValue(int(r["digits"] or 4));digits.setMaximumWidth(75)
            year=QCheckBox();year.setChecked(bool(r["use_year"]))
            preview=QLabel()
            self.nr_widgets[key]=(prefix,nxt,digits,year,preview)
            grid.addWidget(prefix,rowi,1);grid.addWidget(nxt,rowi,2);grid.addWidget(digits,rowi,3)
            grid.addWidget(year,rowi,4);grid.addWidget(preview,rowi,5)
            def upd(_=None,k=key):
                p,n,d,y,lab=self.nr_widgets[k]
                yr=datetime.now().strftime("%Y")+"-" if y.isChecked() else ""
                lab.setText(f"<b>{p.text()}{yr}{n.value():0{d.value()}d}</b>")
            prefix.textChanged.connect(upd);nxt.valueChanged.connect(upd);digits.valueChanged.connect(upd);year.toggled.connect(upd);upd()
        nrl.addLayout(grid)
        save_nr=icon_button("save","Nummernkreise speichern",self.save_number_ranges);nrl.addWidget(save_nr,0,Qt.AlignLeft)
        l.addWidget(nrbox)
        backup_box=QGroupBox("Datensicherung");backup_layout=QVBoxLayout(backup_box)
        self.backup_page=BackupPage(db);backup_layout.addWidget(self.backup_page);l.addWidget(backup_box);l.addStretch()
    def refresh(self):
        self.backup_page.refresh()
    def update_letterhead_labels(self):
        s=letterhead_settings()
        for key,label in self.lh_labels.items():
            value=str(s.value(key,"") or "")
            label.setText(Path(value).name if value and Path(value).is_file() else
                          ("– wie Seite 1 –" if key=="follow" else "kein Briefbogen hinterlegt"))

    def choose_letterhead(self,key):
        source,_=QFileDialog.getOpenFileName(self,"Briefbogen (PDF) auswählen",str(Path.home()),"PDF-Dateien (*.pdf)")
        if not source:return
        document=QPdfDocument();document.load(source)
        if document.pageCount()<1:
            QMessageBox.warning(self,"Briefbogen","Die PDF-Datei konnte nicht gelesen werden.");return
        target=DATA_ROOT/"settings"/f"briefbogen_{'seite1' if key=='first' else 'folgeseite'}.pdf"
        try:shutil.copy2(source,target)
        except Exception as e:QMessageBox.warning(self,"Briefbogen",f"Der Briefbogen konnte nicht übernommen werden.\n\n{e}");return
        s=letterhead_settings();s.setValue(key,str(target));s.sync();self.update_letterhead_labels()

    def remove_letterhead(self,key):
        s=letterhead_settings();path=str(s.value(key,"") or "");s.remove(key);s.sync()
        if path:Path(path).unlink(missing_ok=True)
        self.update_letterhead_labels()

    def save_letterhead_options(self,*_):
        s=letterhead_settings();s.setValue("top_mm",self.lh_top.value());s.setValue("bottom_mm",self.lh_bottom.value())
        for key,box in self.lh_uses.items():s.setValue(f"use/{key}",box.isChecked())
        s.sync()

    def letterhead_sample(self):
        """Probeseite: Briefbogen mit markiertem Inhaltsbereich (Seite 1 und Folgeseite)."""
        self.save_letterhead_options()
        path=PREVIEW_DIR/"VORSCHAU_Briefbogen.pdf"
        writer=QPdfWriter(str(path));writer.setPageSize(QPageSize(QPageSize.A4));writer.setResolution(96)
        painter=QPainter(writer)
        letterhead=Letterhead("offer",writer);letterhead.active=bool(letterhead.first and Path(letterhead.first).is_file())
        if not letterhead.active:
            painter.end();QMessageBox.information(self,"Briefbogen","Bitte zuerst einen Briefbogen für Seite 1 auswählen.");return
        page=writer.pageLayout().paintRectPixels(writer.resolution());left=48;width=page.width()-96
        for first in (True,False):
            if not first:writer.newPage()
            letterhead.draw(painter,first);top=letterhead.content_top(42);bottom=letterhead.limit(page.height()-74)
            painter.setPen(QColor("#1f77b4"));painter.fillRect(QRectF(left,top,width,bottom-top),QColor(31,119,180,35))
            painter.drawRect(QRectF(left,top,width,bottom-top));painter.setFont(QFont("DejaVu Sans",11,QFont.Bold))
            painter.drawText(QRectF(left,top,width,bottom-top),Qt.AlignCenter,
                f"Inhaltsbereich {'Seite 1' if first else 'Folgeseite'}\nHier stehen Anschrift, Positionen und Summen.")
            painter.setFont(QFont("DejaVu Sans",7));painter.setPen(Qt.black)
            painter.drawText(QRectF(left+width*.84,letterhead.page_number_y(),width*.16,14),Qt.AlignRight|Qt.AlignVCenter,"Seite 1" if first else "Seite 2")
        painter.end();open_desktop_file(path,self,"Briefbogen – Probeseite")

    def change_theme(self,*_):
        main_window=self.window()
        if hasattr(main_window,"apply_theme"):
            main_window.apply_theme(self.theme_selector.currentData(),persist=True)
    def change_language(self,*_):
        settings=QSettings(str(DATA_ROOT / "settings" / "window.ini"),QSettings.IniFormat)
        settings.setValue("appearance/language",self.language_selector.currentData() or "de");settings.sync()
        QMessageBox.information(self,ui("ui_language"),ui("restart_language"))
    def save_number_ranges(self):
        try:
            self.db.backup("vor_nummernkreisen")
            for key,(p,n,d,y,preview) in self.nr_widgets.items():
                self.db.save_number_range(key,p.text(),n.value(),d.value(),y.isChecked())
            QMessageBox.information(self,"Nummernkreise","Die Nummernkreise wurden gespeichert.")
        except Exception as e:
            QMessageBox.warning(self,"Nummernkreise",str(e))
    def save(self):
        self.db.backup("vor_firmendaten")
        vals=[self.widgets[k].text().strip() for k,_ in self.FIELDS]+[self.footer.toPlainText().strip(),self.logo_path,self.invoice_header_color]
        self.db.save_company_settings(vals);QMessageBox.information(self,"Einstellungen","Firmen- und Rechnungsdaten wurden gespeichert.")

    def open_manual(self):
        # Im Programmpaket liegt die Anleitung neben main.py, im Quelltext-Projekt unter docs/.
        source=next((x for x in (BASE_DIR/"Bedienungsanleitung.pdf",BASE_DIR.parent/"docs"/"Bedienungsanleitung.pdf") if x.is_file()),BASE_DIR/"Bedienungsanleitung.pdf")
        if not source.is_file():
            QMessageBox.information(self,"Bedienungsanleitung","Die Anleitung ist in dieser Programmversion nicht enthalten.");return
        # Kopie im Datenordner: Der PDF-Betrachter kann sie auch nach dem Beenden des Programms noch lesen.
        target=DATA_ROOT/"Bedienungsanleitung.pdf"
        try:shutil.copy2(source,target)
        except OSError:target=source
        open_desktop_file(str(target),self,"Bedienungsanleitung")

    def set_invoice_header_color(self,color):
        selected=QColor(color)
        self.invoice_header_color=selected.name() if selected.isValid() else "#a40000"
        self.update_color_preview()

    def choose_invoice_header_color(self):
        selected=QColorDialog.getColor(QColor(self.invoice_header_color),self,"Farbe des Firmenschriftzugs")
        if selected.isValid():self.set_invoice_header_color(selected.name())

    def update_color_preview(self):
        color=QColor(self.invoice_header_color)
        if not color.isValid():color=QColor("#a40000")
        self.color_preview.setStyleSheet(
            f"background:{color.name()};border:1px solid #65727c;border-radius:3px;")
        self.color_preview.setToolTip(color.name())

    def update_logo_preview(self):
        pixmap=QPixmap(self.logo_path) if self.logo_path else QPixmap()
        if pixmap.isNull():self.logo_preview.setText("Kein Logo hinterlegt")
        else:self.logo_preview.setPixmap(pixmap.scaled(self.logo_preview.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation))

    def choose_logo(self):
        source,_=QFileDialog.getOpenFileName(self,"Firmenlogo auswählen",str(Path.home()),"Bilder (*.png *.jpg *.jpeg)")
        if not source:return
        suffix=Path(source).suffix.lower() or ".png"
        target=DATA_ROOT/"settings"/f"company_logo{suffix}"
        try:shutil.copy2(source,target)
        except Exception as e:QMessageBox.warning(self,"Firmenlogo",f"Das Logo konnte nicht übernommen werden.\n\n{e}");return
        self.logo_path=str(target);self.update_logo_preview()

    def remove_logo(self):
        self.logo_path="";self.update_logo_preview()



class ReminderDialog(QDialog):
    def __init__(self,db,iid,parent=None):
        super().__init__(parent);self.db=db;self.iid=iid
        inv=db.invoice(iid);open_amount=db.invoice_open_amount(iid);days=db.days_overdue(iid)
        suggested=min(3,db.next_reminder_level(iid))
        self.setWindowTitle("Mahnung erstellen")
        self.setMinimumWidth(620)
        f=QFormLayout(self)

        self.invoice=QLabel(f'{inv["number"]} · {inv["invoice_type"]}')
        self.customer=QLabel(inv["company"])
        self.project=QLabel(f'{inv["project_number"]} – {inv["project_name"]}')
        self.due=QLabel(inv["due_date"] or "—")
        self.days=QLabel(f"<b>{days} Tage</b>")
        self.amount=QLabel(f"<b>{money(open_amount)}</b>")
        self.level=QComboBox();self.level.addItem("Zahlungserinnerung",0)
        for n in range(1,4):self.level.addItem(f"{n}. Mahnung",n)
        self.level.setCurrentIndex(self.level.findData(suggested if days>0 else 0))
        self.reminder_date=QDateEdit(QDate.currentDate());self.reminder_date.setCalendarPopup(True);self.reminder_date.setDisplayFormat("dd.MM.yyyy")
        self.new_due=QDateEdit(QDate.currentDate().addDays(7));self.new_due.setCalendarPopup(True);self.new_due.setDisplayFormat("dd.MM.yyyy")
        self.note=QTextEdit()
        self.note.setPlainText(
            f"Bitte begleichen Sie den noch offenen Betrag von {money(open_amount)} "
            f"bis zum {self.new_due.date().toString('dd.MM.yyyy')}."
        )

        for a,b in [
            ("Mahnstufe",self.level),
            ("Rechnung",self.invoice),("Kunde",self.customer),("Projekt",self.project),
            ("Ursprünglich fällig",self.due),("Überfällig seit",self.days),
            ("Mahnbarer Betrag",self.amount),("Mahndatum",self.reminder_date),
            ("Neue Zahlungsfrist",self.new_due),("Text / Hinweis",self.note)
        ]:
            f.addRow(a,b)

        info=QLabel(
            "Der mahnbare Betrag wird vor dem Speichern erneut aus Rechnung, "
            "Zahlungseingängen, Skonto und Ausgleich berechnet."
        )
        info.setWordWrap(True);f.addRow("",info)
        email=(inv["customer_email"] or "").strip()
        self.send_mail=QCheckBox(f"Gleich per E-Mail senden an {email}" if email else
                                 "Gleich per E-Mail senden (beim Kunden ist keine E-Mail-Adresse hinterlegt)")
        self.send_mail.setChecked(True);f.addRow("",self.send_mail)

        bb=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        preview=bb.addButton("Vorschau",QDialogButtonBox.ActionRole)
        preview.clicked.connect(self.preview_pdf)
        bb.accepted.connect(self.accept);bb.rejected.connect(self.reject);f.addRow(bb)

    def preview_pdf(self):
        open_amount=self.db.invoice_open_amount(self.iid)
        if open_amount<=0.005:
            QMessageBox.information(self,"Mahnungsvorschau","Diese Rechnung hat keinen mahnbaren offenen Betrag.");return
        level,reminder_date,new_due,note=self.data()
        path=PREVIEW_DIR/f"VORSCHAU_Mahnung_{self.iid}.pdf"
        try:
            # Dieselbe reine PDF-Routine wie beim Speichern, ohne Mahnungseintrag.
            ok,err=InvoicesPage.write_reminder_pdf(
                self,path,self.iid,level,reminder_date,new_due,note,open_amount)
        except Exception as exc:
            ok,err=False,str(exc)
        if not ok:
            QMessageBox.warning(self,"Mahnungsvorschau",f"Die PDF-Vorschau konnte nicht erstellt werden:\n{err}");return
        open_desktop_file(path,self,"Mahnungsvorschau")

    def data(self):
        return (
            self.level.currentData(),
            self.reminder_date.date().toString("yyyy-MM-dd"),
            self.new_due.date().toString("yyyy-MM-dd"),
            self.note.toPlainText().strip()
        )

def create_reminder_with_pdf(parent,db,iid,require_overdue=False):
    """Einziger Mahnablauf im Programm (Dashboard, Rechnungen, Zahlungen):
    Mahnung speichern, PDF erzeugen und auf Wunsch den E-Mail-Entwurf öffnen."""
    inv=db.invoice(iid)
    if not inv:return False
    if inv["status"]=="Entwurf":
        QMessageBox.information(parent,"Mahnung erstellen","Für einen Rechnungsentwurf kann keine Mahnung erstellt werden.");return False
    if db.invoice_open_amount(iid)<=0.005:
        QMessageBox.information(parent,"Mahnung erstellen","Diese Rechnung ist vollständig ausgeglichen.");return False
    if require_overdue and db.days_overdue(iid)<=0:
        QMessageBox.information(parent,"Mahnung erstellen","Diese Rechnung ist noch nicht überfällig.");return False
    d=ReminderDialog(db,iid,parent)
    if not d.exec():return False
    level,reminder_date,new_due,note=d.data()
    # Vor dem Speichern Betrag nochmals frisch bestimmen.
    open_amount=db.invoice_open_amount(iid)
    db.backup("vor_mahnung")
    ok,err=db.add_reminder(iid,level,reminder_date,new_due,open_amount,note)
    if not ok:
        QMessageBox.warning(parent,"Mahnung erstellen",err);return False
    label=_reminder_label(level)
    REMINDER_DOCUMENT_DIR.mkdir(parents=True,exist_ok=True)
    pdf=REMINDER_DOCUMENT_DIR / f'{inv["number"]}_{label.replace(" ","_")}_{reminder_date}.pdf'
    ok,err=InvoicesPage.write_reminder_pdf(d,pdf,iid,level,reminder_date,new_due,note,open_amount)
    if not ok:
        QMessageBox.warning(parent,"Mahnung erstellt",f"Die Mahnung wurde gespeichert, das PDF aber nicht erzeugt:\n{err}");return True
    file_generated_document(db,inv["project_id"],pdf,pdf.name,
        f'{label} zu Rechnung {inv["number"]} vom {de_date(reminder_date)}'
        +(f' – per E-Mail versendet am {today_de()}' if d.send_mail.isChecked() else ""))
    if d.send_mail.isChecked():
        compose_email_with_pdf(parent,pdf,inv["customer_email"],f'{label} zu Rechnung {inv["number"]}',
            f"Guten Tag,\n\nanbei erhalten Sie unsere {label} zu Rechnung {inv['number']}.\n"
            f"Bitte begleichen Sie den offenen Betrag von {money(open_amount)} bis zum {de_date(new_due)}.\n\n"
            "Mit freundlichen Grüßen")
    else:
        QMessageBox.information(parent,"Mahnung erstellt",f"{label} wurde gespeichert.\n\nPDF: {pdf}")
    return True

class PaymentsPage(QWidget):
    def __init__(self,db):
        super().__init__();self.db=db
        o=QVBoxLayout(self)

        top=QHBoxLayout()
        t=QLabel("Zahlungen");t.setObjectName("pageTitle")
        self.search=QLineEdit();self.search.setPlaceholderText("Rechnung, Projekt, Kunde oder Status suchen …")
        self.search.textChanged.connect(self.refresh)
        overdue=QPushButton("Fällige Rechnungen prüfen");overdue.clicked.connect(self.check_overdue)
        reminder=QPushButton("Mahnung");reminder.clicked.connect(self.create_reminder)
        top.addWidget(t);top.addStretch();top.addWidget(self.search);top.addWidget(overdue);top.addWidget(reminder)
        o.addLayout(top)

        totals=QHBoxLayout()
        self.sum_invoices=QLabel()
        self.sum_paid=QLabel()
        self.sum_open=QLabel()
        for w in [self.sum_invoices,self.sum_paid,self.sum_open]:
            w.setObjectName("paymentStat")
            w.setFixedHeight(54);w.setMinimumWidth(190);w.setMaximumWidth(270)
            w.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Fixed)
            totals.addWidget(w)
        totals.addStretch()
        o.addLayout(totals)

        sp=QSplitter(Qt.Horizontal)

        # left: invoice/payment overview
        left=QWidget();ll=QVBoxLayout(left)
        self.table=QTableWidget(0,12)
        self.table.setHorizontalHeaderLabels(
            ["Rg.-Nr.","Projekt","Kunde","Brutto","Bezahlt","Skonto","Ausgleich","Offen","Fällig","Überfällig","Mahnung","Status"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.select_invoice)
        ll.addWidget(self.table)

        # right: selected invoice and its transactions
        right=QWidget();rl=QVBoxLayout(right)

        preview_box=QGroupBox("Rechnungsvorschau")
        pv=QVBoxLayout(preview_box)
        self.preview=compact_hint("Bitte eine Rechnung auswählen.")
        self.preview.setWordWrap(True)
        self.preview.setMinimumHeight(170)
        pv.addWidget(self.preview)
        rl.addWidget(preview_box)

        self.meta=QLabel("")
        self.meta.setWordWrap(True)
        rl.addWidget(self.meta)

        btns=QHBoxLayout()
        add=icon_button("new","Zahlungseingang hinzufügen",self.add_payment)
        adjust=QPushButton("+ Ausgleich");adjust.clicked.connect(self.add_adjustment)
        delete=icon_button("delete","Zahlungsbuchung löschen",self.delete_payment)
        btns.addWidget(add);btns.addWidget(adjust);btns.addWidget(delete);btns.addStretch()
        rl.addLayout(btns)

        self.payments=QTableWidget(0,7)
        self.payments.setHorizontalHeaderLabels(
            ["Datum","Bezahlt","Skonto","Ausgleich","Art","Begründung","Erfasst"]
        )
        self.payments.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.payments.setEditTriggers(QAbstractItemView.NoEditTriggers)
        rl.addWidget(self.payments)

        self.explain=QLabel(
            "Nur ein echter offener Rest bleibt später mahnbar. "
            "Skonto und dokumentierte Ausgleiche mindern den offenen Betrag, "
            "ohne die ursprüngliche Rechnung zu verändern."
        )
        self.explain.setWordWrap(True)
        rl.addWidget(self.explain)

        sp.addWidget(left);sp.addWidget(right);sp.setSizes([900,560])
        o.addWidget(sp)
        self.refresh()

    def current_invoice_id(self):
        r=self.table.currentRow()
        return self.table.item(r,0).data(Qt.UserRole) if r>=0 and self.table.item(r,0) else None

    def current_payment_id(self):
        r=self.payments.currentRow()
        return self.payments.item(r,0).data(Qt.UserRole) if r>=0 and self.payments.item(r,0) else None

    def refresh(self):
        rows=self.db.payment_overview(self.search.text())
        context_project_id=getattr(self,"context_project_id",None)
        if context_project_id is not None:
            rows=[row for row in rows if row["project_id"]==context_project_id]
        self.table.setRowCount(len(rows))

        total_invoice=0.0;total_paid=0.0;total_open=0.0
        for r,x in enumerate(rows):
            gross=float(x["gross_total"] or 0)
            paid=float(x["paid_total"] or 0)
            disc=float(x["discount_total"] or 0)
            adj=float(x["adjustment_total"] or 0)
            payable=float(x["payable_total"] if x["payable_total"] is not None else gross)
            open_amount=max(0.0,payable-paid-disc-adj)

            total_invoice+=gross
            total_paid+=paid
            total_open+=open_amount

            days=self.db.days_overdue(x["id"])
            reminder_label=self.db.last_reminder_label(x["id"])
            vals=[
                x["number"],
                f'{x["project_number"]} – {x["project_name"]}',
                x["company"],
                money(gross),
                money(paid),
                money(disc),
                money(adj),
                money(open_amount),
                x["due_date"] or "",
                f"{days} Tage" if days>0 else "",
                reminder_label,
                x["status"]
            ]
            for c,v in enumerate(vals):
                it=QTableWidgetItem(v)
                if c==0:it.setData(Qt.UserRole,x["id"])
                self.table.setItem(r,c,it)

        self.sum_invoices.setText(f"<b>Rechnungen:</b> {money(total_invoice)}")
        self.sum_paid.setText(f"<b>Bezahlt:</b> {money(total_paid)}")
        self.sum_open.setText(f"<b>Offen:</b> {money(total_open)}")

        self.meta.setText("")
        self.preview.setText("Bitte eine Rechnung auswählen.")
        self.payments.setRowCount(0)

    def select_invoice(self):
        iid=self.current_invoice_id()
        if not iid:return
        inv=self.db.payment_detail(iid)
        paid,discount,adjustment=self.db.payment_totals(iid)
        open_amount=self.db.invoice_open_amount(iid)

        days=self.db.days_overdue(iid)
        reminder_rows=self.db.reminders(iid)
        reminder_text="Keine Mahnung"
        if reminder_rows:
            last=reminder_rows[-1]
            reminder_text=f'{last["reminder_level"]}. Mahnung am {last["reminder_date"]}'
        due_text=inv["due_date"] or "—"
        overdue_text=f'<b>{days} Tage überfällig</b>' if days>0 else "nicht überfällig"

        self.preview.setText(
            f'<b style="font-size:15px">{inv["number"]} · {inv["invoice_type"]}</b><br><br>'
            f'<b>Kunde:</b> {inv["company"]}<br>'
            f'<b>Projekt:</b> {inv["project_number"]} – {inv["project_name"]}<br>'
            f'<b>Rechnungsbetrag:</b> {money(inv["gross_total"])}<br>'
            f'<b>Zahlbetrag nach Rechnungsabzügen:</b> {money(inv["payable_total"])}<br>'
            f'<b>Bezahlt:</b> {money(paid)} &nbsp; <b>Skonto:</b> {money(discount)} &nbsp; '
            f'<b>Ausgleich:</b> {money(adjustment)}<br>'
            f'<b>Noch offen:</b> {money(open_amount)}<br>'
            f'<b>Fällig:</b> {due_text} · {overdue_text}<br>'
            f'<b>Mahnstatus:</b> {reminder_text}'
        )

        self.meta.setText(
            f'<b>{inv["number"]} · {inv["invoice_type"]}</b><br>'
            f'Projekt: {inv["project_number"]} – {inv["project_name"]}<br>'
            f'Kunde: {inv["company"]}<br>'
            f'Rechnungsbetrag: <b>{money(inv["gross_total"])}</b> · '
            f'Bezahlt: {money(paid)} · Skonto: {money(discount)} · '
            f'Ausgleich: {money(adjustment)}<br>'
            f'Offen: <b>{money(open_amount)}</b> · Status: <b>{inv["status"]}</b>'
        )

        rows=self.db.payments(iid)
        self.payments.setRowCount(len(rows))
        for r,p in enumerate(rows):
            vals=[
                p["payment_date"],
                money(p["paid_amount"]),
                money(p["discount_amount"]),
                money(p["adjustment_amount"]),
                p["adjustment_type"] or "",
                p["adjustment_reason"] or "",
                (p["created_at"] or "").replace("T"," ")
            ]
            for c,v in enumerate(vals):
                it=QTableWidgetItem(v)
                if c==0:it.setData(Qt.UserRole,p["id"])
                self.payments.setItem(r,c,it)

    def check_overdue(self):
        rows=self.db.overdue_invoices()
        if not rows:
            QMessageBox.information(self,"Fällige Rechnungen prüfen",
                "Es gibt aktuell keine überfällige Rechnung mit mahnbar offenem Betrag.")
            return

        d=QDialog(self);d.setWindowTitle("Fällige Rechnungen");d.setMinimumSize(980,560)
        l=QVBoxLayout(d)
        info=QLabel(
            f"{len(rows)} überfällige Rechnung(en) wurden gefunden. "
            "Zahlungen, Skonto und dokumentierte Ausgleiche sind bereits berücksichtigt."
        )
        info.setWordWrap(True);l.addWidget(info)
        table=QTableWidget(0,7)
        table.setHorizontalHeaderLabels(
            ["Rg.-Nr.","Projekt","Kunde","Fällig","Überfällig","Mahnbar offen","Letzte Mahnung"]
        )
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setRowCount(len(rows))
        for r,(x,open_amount,days) in enumerate(rows):
            vals=[x["number"],f'{x["project_number"]} – {x["project_name"]}',x["company"],
                  x["due_date"] or "",f"{days} Tage",money(open_amount),self.db.last_reminder_label(x["id"])]
            for c,v in enumerate(vals):
                it=QTableWidgetItem(v)
                if c==0:it.setData(Qt.UserRole,x["id"])
                table.setItem(r,c,it)
        l.addWidget(table)
        btns=QHBoxLayout()
        create=QPushButton("Mahnung für Auswahl")
        close=icon_button("cancel","Mahnungsfenster schließen")
        btns.addWidget(create);btns.addStretch();btns.addWidget(close);l.addLayout(btns)

        def create_selected():
            rr=table.currentRow()
            if rr<0:
                QMessageBox.information(d,"Mahnung","Bitte zuerst eine Rechnung auswählen.");return
            iid=table.item(rr,0).data(Qt.UserRole)
            if self._create_reminder_for_invoice(iid):
                d.accept()
                self.refresh()
        create.clicked.connect(create_selected)
        close.clicked.connect(d.reject)
        d.exec()

    def _create_reminder_for_invoice(self,iid):
        return create_reminder_with_pdf(self,self.db,iid,require_overdue=True)

    def create_reminder(self):
        iid=self.current_invoice_id()
        if not iid:
            QMessageBox.information(self,"Mahnung","Bitte zuerst eine Rechnung auswählen.");return
        if self._create_reminder_for_invoice(iid):
            self.refresh()

    def add_payment(self):
        iid=self.current_invoice_id()
        if not iid:
            QMessageBox.information(self,"Zahlungseingang","Bitte zuerst eine Rechnung auswählen.");return
        if self.db.invoice_open_amount(iid)<=0.005:
            QMessageBox.information(self,"Zahlungseingang","Diese Rechnung ist bereits vollständig ausgeglichen.");return

        d=PaymentDialog(self.db,iid,self)
        if d.exec():
            self.db.backup("vor_zahlungseingang")
            self.db.add_payment(iid,*d.data())
            self.refresh()

    def add_adjustment(self):
        iid=self.current_invoice_id()
        if not iid:
            QMessageBox.information(self,"Ausgleich","Bitte zuerst eine Rechnung auswählen.");return
        open_amount=self.db.invoice_open_amount(iid)
        if open_amount<=0.005:
            QMessageBox.information(self,"Ausgleich","Diese Rechnung ist bereits vollständig ausgeglichen.");return

        d=QDialog(self);d.setWindowTitle("Ausgleich / Abzug erfassen");d.setMinimumWidth(560)
        f=QFormLayout(d)
        date=QDateEdit(QDate.currentDate());date.setCalendarPopup(True);date.setDisplayFormat("dd.MM.yyyy")
        amount=QDoubleSpinBox();amount.setMaximum(999999999);amount.setDecimals(2);amount.setSuffix(" €");amount.setValue(open_amount)
        typ=QComboBox();typ.addItems(["Kürzung Auftraggeber","Mangelabzug","Sicherheitseinbehalt","Rundungsdifferenz","Sonstiger Abzug"])
        reason=QLineEdit()
        before=QLabel(money(open_amount))
        after=QLabel()
        def recalc():
            after.setText(f"<b>{money(max(0.0,open_amount-amount.value()))}</b>")
        amount.valueChanged.connect(recalc);recalc()
        for a,b in [("Offen vor Ausgleich",before),("Datum",date),("Ausgleichsbetrag",amount),
                    ("Art",typ),("Begründung",reason),("Offen danach",after)]:f.addRow(a,b)
        bb=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel)
        bb.accepted.connect(d.accept);bb.rejected.connect(d.reject);f.addRow(bb)

        if d.exec():
            self.db.backup("vor_ausgleich")
            self.db.add_payment(
                iid,date.date().toString("yyyy-MM-dd"),
                0.0,0.0,amount.value(),typ.currentText(),reason.text().strip()
            )
            self.refresh()

    def delete_payment(self):
        pid=self.current_payment_id()
        if not pid:
            QMessageBox.information(self,"Buchung löschen","Bitte zuerst rechts eine Buchung auswählen.");return
        if QMessageBox.question(self,"Buchung löschen",
            "Diese Zahlungs-/Ausgleichsbuchung wirklich löschen?\n\n"
            "Der offene Betrag und der Rechnungsstatus werden anschließend automatisch neu berechnet.",
            QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:return
        self.db.backup("vor_zahlungsbuchung_loeschen")
        ok,err=self.db.delete_payment(pid)
        if not ok:
            QMessageBox.warning(self,"Buchung löschen",err);return
        self.refresh()


class DashboardPage(QWidget):
    """Arbeitszentrale: schmale Kennzahlen, fällige Mahnungen, offene Aufgaben."""
    MODULES={5:"Aufmaß",6:"Rechnungen",7:"Zahlungen"}
    def __init__(self,db):
        super().__init__();self.db=db;self.navigator=None;self.open_module=None
        self._due=[];self._actions=[]
        o=QVBoxLayout(self)
        title=QLabel("Dashboard");title.setObjectName("pageTitle");o.addWidget(title)
        self.backup_warning=QFrame();self.backup_warning.setObjectName("backupWarning")
        self.backup_warning.setStyleSheet("#backupWarning{background:#fff4d8;border:1px solid #e0b64a;border-radius:4px;}")
        warning_layout=QHBoxLayout(self.backup_warning);warning_layout.setContentsMargins(10,6,10,6)
        self.backup_warning_text=QLabel();warning_layout.addWidget(self.backup_warning_text,1)
        backup_now=QPushButton("Jetzt Komplettsicherung speichern …");backup_now.clicked.connect(self.full_backup_now)
        warning_layout.addWidget(backup_now);o.addWidget(self.backup_warning)
        stats=QHBoxLayout();stats.setSpacing(32)
        self.stat_open=QLabel();self.stat_unbilled=QLabel();self.stat_drafts=QLabel();self.stat_incoming=QLabel()
        for w in (self.stat_open,self.stat_unbilled,self.stat_drafts,self.stat_incoming):
            w.setTextFormat(Qt.RichText);w.setObjectName("dashboardStat");stats.addWidget(w)
        stats.addStretch();o.addLayout(stats)

        sp=QSplitter(Qt.Vertical)
        self.reminder_box=QGroupBox("Mahnungen fällig");rl=QVBoxLayout(self.reminder_box)
        self.reminders=QTableWidget(0,8)
        self.reminders.setHorizontalHeaderLabels(["Kunde","Rechnung","Projekt","Offen","Überfällig","Bisher gemahnt","Als Nächstes",""])
        self.reminders.setSelectionBehavior(QAbstractItemView.SelectRows);self.reminders.setSelectionMode(QAbstractItemView.SingleSelection)
        self.reminders.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.reminders.doubleClicked.connect(self.open_reminder_invoice)
        self.reminders.verticalHeader().setDefaultSectionSize(36)
        rl.addWidget(self.reminders)
        self.reminder_empty=QLabel("Aktuell ist keine Mahnung fällig.");rl.addWidget(self.reminder_empty)
        self.reminder_hint=QLabel("„Mahnen“ erstellt die Mahnung als PDF und öffnet auf Wunsch gleich die E-Mail. Doppelklick öffnet die Rechnung.")
        self.reminder_hint.setWordWrap(True);rl.addWidget(self.reminder_hint)
        sp.addWidget(self.reminder_box)

        action_box=QGroupBox("Was ist zu tun?");al=QVBoxLayout(action_box)
        self.actions=QTableWidget(0,6)
        self.actions.setHorizontalHeaderLabels(["Prio","Vorgang","Projekt","Kunde","Hinweis","Betrag"])
        self.actions.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.actions.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.actions.doubleClicked.connect(self.open_action)
        al.addWidget(self.actions)
        hint=QLabel("Doppelklick auf einen Vorgang öffnet den passenden Bereich.");hint.setWordWrap(True);al.addWidget(hint)
        sp.addWidget(action_box);sp.setSizes([420,330])
        o.addWidget(sp,1)
        self.refresh()

    def set_navigator(self,fn):
        self.navigator=fn

    def navigate(self,index):
        if self.navigator:self.navigator(index)

    def _open(self,module,project_id,invoice_id):
        if self.open_module and project_id is not None:self.open_module(module,project_id,invoice_id)
        else:
            pages=getattr(self.window(),"pages",{})
            if module in pages:self.navigate(list(pages).index(module))

    def open_reminder_invoice(self,*_):
        r=self.reminders.currentRow()
        if 0<=r<len(self._due):self._open("Rechnungen",self._due[r]["project_id"],self._due[r]["invoice_id"])

    def open_action(self,*_):
        r=self.actions.currentRow()
        if not 0<=r<len(self._actions):return
        x=self._actions[r];module=self.MODULES.get(int(x["target"]),"Rechnungen")
        self._open(module,x.get("project_id"),x.get("invoice_id") if module!="Aufmaß" else x.get("project_id"))

    def remind(self,invoice_id):
        if create_reminder_with_pdf(self,self.db,invoice_id,require_overdue=True):self.refresh()

    def full_backup_now(self):
        pages=getattr(self.window(),"pages",{})
        if "Einstellungen" in pages:pages["Einstellungen"].backup_page.create_full_backup()

    def selected_reminder_invoice(self):
        r=self.reminders.currentRow()
        return self._due[r]["invoice_id"] if 0<=r<len(self._due) and self.reminders.selectionModel().hasSelection() else None

    def email_selected_reminder(self):
        """E-Mail-Button der Hauptleiste: markierte fällige Mahnung erstellen und senden."""
        iid=self.selected_reminder_invoice()
        if iid is None:
            QMessageBox.information(self,"E-Mail","Bitte zuerst oben unter „Mahnungen fällig“ eine Rechnung markieren.");return
        self.remind(iid)

    def refresh(self):
        s=self.db.dashboard_summary()
        self.stat_open.setText(f'Offene Forderungen: <b>{money(s["open_total"])}</b> '
                               f'({s["open_count"]} Rechnung(en), davon {s["overdue_count"]} überfällig)')
        self.stat_unbilled.setText(f'Noch nicht abgerechnet: <b>{money(s["unbilled_value"])}</b>')
        self.stat_drafts.setText(f'Rechnungsentwürfe: <b>{s["draft_count"]}</b>')
        incoming=self.db.incoming_open_summary();self.stat_incoming.setVisible(incoming["count"]>0)
        overdue=f', davon {incoming["overdue"]} überfällig' if incoming["overdue"] else ""
        self.stat_incoming.setText(f'Eingangsrechnungen offen: <b>{money(incoming["total"])}</b> ({incoming["count"]}{overdue})')
        last=last_full_backup();limit=int(backup_settings().value("remind_days",7) or 7)
        days=(datetime.now()-last).days if last else None
        self.backup_warning.setVisible(days is None or days>=limit)
        self.backup_warning_text.setText("⚠  <b>Es gibt noch keine Komplettsicherung</b> (Daten und Dokumente, z. B. auf einem USB-Stick)." if days is None
            else f"⚠  <b>Letzte Komplettsicherung vor {days} Tagen</b> ({last.strftime('%d.%m.%Y')}). Zeit für eine neue.")

        self._due,waiting=self.db.reminders_due()
        self.reminder_box.setTitle(f"Mahnungen fällig ({len(self._due)})")
        t=self.reminders;t.setRowCount(len(self._due))
        for r,x in enumerate(self._due):
            vals=[x["customer"],x["number"],x["project"],money(x["open_amount"]),f'{x["days"]} Tage',x["previous"],x["next"]]
            for c,v in enumerate(vals):
                it=QTableWidgetItem(v)
                if c in (3,4):it.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
                t.setItem(r,c,it)
            button=QPushButton("Mahnen");button.setToolTip(f'Mahnung zu Rechnung {x["number"]} erstellen und per E-Mail senden')
            button.setStyleSheet("padding:0 12px;min-height:0;margin:2px 4px")
            button.clicked.connect(lambda _checked=False,iid=x["invoice_id"]:self.remind(iid))
            t.setCellWidget(r,7,button)
        t.resizeColumnsToContents();t.setColumnWidth(7,max(96,t.columnWidth(7)))
        t.horizontalHeader().setSectionResizeMode(2,QHeaderView.Stretch)
        t.setVisible(bool(self._due));self.reminder_hint.setVisible(bool(self._due));self.reminder_empty.setVisible(not self._due)

        # Was oben als fällige Mahnung steht, wird unten nicht wiederholt.
        due_ids={x["invoice_id"] for x in self._due};self._actions=[]
        for x in self.db.dashboard_actions():
            if x["type"]=="Überfällige Rechnung":
                if x["invoice_id"] in due_ids:continue
                if x["invoice_id"] in waiting:
                    label,deadline=waiting[x["invoice_id"]]
                    x=dict(x,priority_text="🟠 Frist läuft",hint=f'{x["hint"]} · {label} versandt, Frist bis {de_date(deadline)}')
            self._actions.append(x)
        self.actions.setRowCount(len(self._actions))
        for r,x in enumerate(self._actions):
            vals=[x["priority_text"],x["type"],x["project"],x["customer"],x["hint"],
                  money(x["amount"]) if x["amount"]>0.005 else ""]
            for c,v in enumerate(vals):
                it=QTableWidgetItem(v)
                if c==5:it.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
                self.actions.setItem(r,c,it)
        self.actions.resizeColumnsToContents()
        self.actions.horizontalHeader().setSectionResizeMode(4,QHeaderView.Stretch)

FULL_BACKUP_MANIFEST="aufmasswerk_komplettsicherung.txt"
FULL_BACKUP_DB="aufmasswerk.db"
# Komplettsicherungen aus früheren Fassungen lassen sich weiter einspielen.
LEGACY_BACKUP_MANIFEST="handwerkpro_komplettsicherung.txt";LEGACY_BACKUP_DB="handwerkpro.db"

def backup_settings():
    return QSettings(str(DATA_ROOT/"settings"/"datensicherung.ini"),QSettings.IniFormat)

def last_full_backup():
    value=str(backup_settings().value("last_full","") or "")
    try:return datetime.fromisoformat(value)
    except ValueError:return None

def _rebase_data_path(value):
    """Absoluten Pfad aus einer anderen Installation auf DATA_ROOT umbiegen."""
    p=Path(str(value or ""))
    if not value:return value
    # Immer die mitgesicherte Kopie in der eigenen Firma bevorzugen.
    for anchor in ("documents","settings"):
        if anchor in p.parts:
            candidate=DATA_ROOT.joinpath(*p.parts[p.parts.index(anchor):])
            if candidate.exists():return str(candidate)
    return value

class BackupPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        o = QVBoxLayout(self);o.setContentsMargins(0,0,0,0)
        hint = QLabel("Automatische Sicherungen entstehen beim Starten, Beenden und vor wichtigen Änderungen. "
                      "Aufbewahrt werden: die letzten 2 Tage alle, bis 30 Tage eine pro Tag, bis 6 Monate eine pro Woche, "
                      "danach eine pro Monat. Manuelle Sicherungen bleiben immer erhalten. "
                      "Die Komplettsicherung enthält zusätzlich alle Dokumente, Logo und Briefbogen – ideal für einen USB-Stick.")
        hint.setWordWrap(True);o.addWidget(hint)
        full=QHBoxLayout()
        self.full_info=QLabel();full.addWidget(self.full_info)
        full.addStretch();full.addWidget(QLabel("Hinweis im Dashboard nach"))
        self.remind_days=QSpinBox();self.remind_days.setRange(1,365);self.remind_days.setSuffix(" Tagen")
        self.remind_days.setValue(int(backup_settings().value("remind_days",7) or 7))
        self.remind_days.valueChanged.connect(lambda v:(backup_settings().setValue("remind_days",v)))
        full.addWidget(self.remind_days);o.addLayout(full)
        bar = QHBoxLayout()
        for text,slot in [("Manuelle Sicherung erstellen",self.create_backup),("Sicherung wiederherstellen …",self.restore_backup)]:
            b=QPushButton(text);b.clicked.connect(slot);bar.addWidget(b)
        btn_delete = icon_button("delete","Markierte Sicherung löschen",self.delete_backup);bar.addWidget(btn_delete)
        btn_open = icon_button("open","Sicherungsordner öffnen",self.open_folder);bar.addWidget(btn_open)
        bar.addStretch()
        for text,slot in [("Komplettsicherung speichern …",self.create_full_backup),("Komplettsicherung einspielen …",self.restore_full_backup)]:
            b=QPushButton(text);b.clicked.connect(slot);bar.addWidget(b)
        o.addLayout(bar)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Datum / Uhrzeit", "Anlass", "Größe"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setColumnWidth(0,160);self.table.setColumnWidth(1,420);self.table.setColumnWidth(2,100)
        self.table.setMinimumHeight(280);self.table.doubleClicked.connect(lambda *_:self.restore_backup())
        o.addWidget(self.table)
        self.refresh()

    def refresh(self):
        files=sorted([p for p in BACKUP_DIR.glob("*.db") if BACKUP_NAME_RE.match(p.name)],key=lambda p:backup_info(p)[0],reverse=True) if BACKUP_DIR.exists() else []
        self.table.setRowCount(len(files))
        for r,f in enumerate(files):
            when,reason=backup_info(f)
            it_date=QTableWidgetItem(when.strftime("%d.%m.%Y %H:%M"));it_date.setData(Qt.UserRole,str(f))
            self.table.setItem(r,0,it_date);self.table.setItem(r,1,QTableWidgetItem(backup_label(reason)))
            it_size=QTableWidgetItem(f"{f.stat().st_size/1024/1024:.1f} MB");it_size.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
            self.table.setItem(r,2,it_size)
        last=last_full_backup()
        self.full_info.setText(f"Letzte Komplettsicherung: <b>{last.strftime('%d.%m.%Y %H:%M')}</b>" if last
                               else "Letzte Komplettsicherung: <b>noch keine</b>")

    def selected_backup(self):
        r=self.table.currentRow();item=self.table.item(r,0) if r>=0 else None
        return Path(item.data(Qt.UserRole)) if item and self.table.selectionModel().hasSelection() else None

    def create_backup(self):
        self.db.backup("manuell")
        QMessageBox.information(self,"Datensicherung","Eine manuelle Sicherung wurde erstellt. Sie wird nie automatisch gelöscht.")
        self.refresh()

    def open_folder(self):
        open_desktop_file(BACKUP_DIR,self,"Sicherungsordner öffnen")

    def delete_backup(self):
        path=self.selected_backup()
        if not path:
            QMessageBox.information(self,"Sicherung löschen","Bitte zuerst eine Sicherung in der Liste markieren.");return
        if QMessageBox.question(self,"Sicherung löschen",f"Die Sicherung vom {self.table.item(self.table.currentRow(),0).text()} wirklich löschen?",
                                QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:return
        try:path.unlink()
        except Exception as e:QMessageBox.warning(self,"Fehler",f"Die Sicherung konnte nicht gelöscht werden:\n{e}")
        self.refresh()

    def _restart(self):
        window=self.window()
        if hasattr(window,"restart_program"):window.restart_program()

    def restore_backup(self):
        path=self.selected_backup()
        if not path:
            QMessageBox.information(self,"Sicherung wiederherstellen","Bitte zuerst eine Sicherung in der Liste markieren.");return
        label=f"{self.table.item(self.table.currentRow(),0).text()} ({self.table.item(self.table.currentRow(),1).text()})"
        if QMessageBox.question(self,"Sicherung wiederherstellen",
            f"Die Daten auf den Stand vom {label} zurücksetzen?\n\n"
            "Der aktuelle Stand wird vorher automatisch gesichert – du kannst also jederzeit wieder zurück.\n"
            "Danach startet das Programm neu.",QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:return
        try:
            self.db.backup("vor_wiederherstellung")
            source=sqlite3.connect(str(path));source.backup(self.db.conn);source.close()
        except Exception as e:
            QMessageBox.warning(self,"Sicherung wiederherstellen",f"Die Sicherung konnte nicht eingespielt werden:\n{e}");return
        QMessageBox.information(self,"Sicherung wiederherstellen","Die Sicherung wurde eingespielt. Das Programm startet jetzt neu.")
        self._restart()

    def create_full_backup(self):
        company=self.db.company_settings();name=((company["company_name"] if company else "") or "Firma")
        safe=re.sub(r"[^A-Za-z0-9ÄÖÜäöüß_-]+","_",name).strip("_")
        target,_=QFileDialog.getSaveFileName(self,"Komplettsicherung speichern",
            str(Path.home()/f"Aufmasswerk_Komplettsicherung_{safe}_{date.today().isoformat()}.zip"),"ZIP-Dateien (*.zip)")
        if not target:return
        if not target.lower().endswith(".zip"):target+=".zip"
        try:
            snapshot=BACKUP_DIR/"_komplettsicherung_tmp.db";dc=sqlite3.connect(str(snapshot))
            with dc:self.db.conn.backup(dc)
            dc.close()
            with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED) as z:
                z.write(snapshot,FULL_BACKUP_DB)
                for folder in ("documents","settings"):
                    base=DATA_ROOT/folder
                    if base.is_dir():
                        for f in base.rglob("*"):
                            # Reine Vorschau-Dateien werden nicht gesichert.
                            if f.is_file() and PREVIEW_DIR not in f.parents:z.write(f,f.relative_to(DATA_ROOT).as_posix())
                z.writestr(FULL_BACKUP_MANIFEST,f"{APP_NAME} {APP_VERSION}\nFirma: {name}\nErstellt: {datetime.now().isoformat(timespec='seconds')}\n")
            snapshot.unlink(missing_ok=True)
        except Exception as e:
            QMessageBox.warning(self,"Komplettsicherung",f"Die Komplettsicherung konnte nicht erstellt werden:\n{e}");return
        s=backup_settings();s.setValue("last_full",datetime.now().isoformat(timespec="seconds"));s.sync()
        size=Path(target).stat().st_size/1024/1024
        QMessageBox.information(self,"Komplettsicherung",f"Die Komplettsicherung wurde gespeichert ({size:.1f} MB):\n\n{target}")
        self.refresh()
        window=self.window()
        if hasattr(window,"pages") and "Dashboard" in window.pages:window.pages["Dashboard"].refresh()

    def restore_full_backup(self):
        source,_=QFileDialog.getOpenFileName(self,"Komplettsicherung einspielen",str(Path.home()),"ZIP-Dateien (*.zip)")
        if not source:return
        try:
            with zipfile.ZipFile(source) as z:
                names=z.namelist()
                db_member=next((n for n in (FULL_BACKUP_DB,LEGACY_BACKUP_DB) if n in names),None)
                manifest=next((n for n in (FULL_BACKUP_MANIFEST,LEGACY_BACKUP_MANIFEST) if n in names),None)
                if not db_member or not manifest:
                    QMessageBox.warning(self,"Komplettsicherung","Diese Datei ist keine Aufmaßwerk-Komplettsicherung.");return
                info=z.read(manifest).decode("utf-8","replace")
        except Exception as e:
            QMessageBox.warning(self,"Komplettsicherung",f"Die Datei konnte nicht gelesen werden:\n{e}");return
        company=self.db.company_settings();current=((company["company_name"] if company else "") or "")
        if QMessageBox.question(self,"Komplettsicherung einspielen",
            f"ACHTUNG: Alle Daten der aktuellen Firma „{current}“ werden durch diese Sicherung ersetzt.\n\n{info}\n"
            "Der aktuelle Stand wird vorher automatisch gesichert. Danach startet das Programm neu.\n\nFortfahren?",
            QMessageBox.Yes|QMessageBox.No)!=QMessageBox.Yes:return
        try:
            self.db.backup("vor_komplettsicherung_einspielen")
            with zipfile.ZipFile(source) as z:
                for member in z.namelist():
                    if member.startswith(("documents/","settings/")) and not member.endswith("/"):
                        target=(DATA_ROOT/member).resolve()
                        if DATA_ROOT.resolve() not in target.parents:continue
                        target.parent.mkdir(parents=True,exist_ok=True)
                        with z.open(member) as src_file,open(target,"wb") as out:shutil.copyfileobj(src_file,out)
                extracted=BACKUP_DIR/"_einspielen_tmp.db"
                with z.open(db_member) as src_file,open(extracted,"wb") as out:shutil.copyfileobj(src_file,out)
            con=sqlite3.connect(str(extracted));con.backup(self.db.conn);con.close();extracted.unlink(missing_ok=True)
            # Pfade aus einer anderen Installation (Logo, Altbelege, Briefbogen) anpassen.
            row=self.db.conn.execute("SELECT logo_path FROM company_settings WHERE id=1").fetchone()
            if row and row[0]:self.db.conn.execute("UPDATE company_settings SET logo_path=? WHERE id=1",(_rebase_data_path(row[0]),))
            for iid,pdf in self.db.conn.execute("SELECT id,source_pdf FROM invoices WHERE COALESCE(source_pdf,'')<>''").fetchall():
                self.db.conn.execute("UPDATE invoices SET source_pdf=? WHERE id=?",(_rebase_data_path(pdf),iid))
            self.db.conn.commit()
            s=letterhead_settings()
            for key in ("first","follow"):
                if s.value(key):s.setValue(key,_rebase_data_path(s.value(key)))
            s.sync()
        except Exception as e:
            QMessageBox.warning(self,"Komplettsicherung",f"Die Komplettsicherung konnte nicht eingespielt werden:\n{e}");return
        QMessageBox.information(self,"Komplettsicherung","Die Komplettsicherung wurde eingespielt. Das Programm startet jetzt neu.")
        self._restart()

class DocumentsPage(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        o = QVBoxLayout(self)

        # Header
        top = QHBoxLayout()
        t = QLabel("Dokumente")
        t.setObjectName("pageTitle")
        top.addWidget(t)
        top.addStretch()

        # Kategorie-Filter
        top.addWidget(QLabel("Kategorie:"))
        self.category = QComboBox()
        self.category.addItems(["Alle", "Briefe", "Angebote", "Aufmaß", "Rechnungen", "Mahnungen", "Vorschau"])
        self.category.currentIndexChanged.connect(self.refresh)
        top.addWidget(self.category)
        o.addLayout(top)

        hint = QLabel("Hier findest du alle erstellten PDFs und Dokumente deines Projekts. Per Doppelklick kannst du ein Dokument öffnen.")
        hint.setWordWrap(True)
        o.addWidget(hint)

        # Buttons
        bar = QHBoxLayout()
        btn_open = icon_button("open","Dokument öffnen")
        btn_open.clicked.connect(self.open_doc)
        btn_folder = icon_button("open","Dokumentordner öffnen")
        btn_folder.clicked.connect(self.open_folder)
        btn_delete = icon_button("delete","Dokument löschen")
        btn_delete.clicked.connect(self.delete_doc)

        bar.addWidget(btn_open)
        bar.addWidget(btn_folder)
        bar.addWidget(btn_delete)
        bar.addStretch()
        o.addLayout(bar)

        # Tabelle
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Kategorie", "Dateiname", "Erstellt am", "Größe (KB)"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(1, 400)
        self.table.setColumnWidth(2, 160)
        self.table.setColumnWidth(3, 100)
        self.table.doubleClicked.connect(self.open_doc)
        o.addWidget(self.table)

        self.refresh()

    def refresh(self):
        self.table.setRowCount(0)
        cat = self.category.currentText()

        # Zuordnung der Ordnerpfade
        dirs = {
            "Briefe": LETTER_DOCUMENT_DIR,
            "Angebote": OFFER_DOCUMENT_DIR,
            "Aufmaß": MEASUREMENT_DOCUMENT_DIR,
            "Rechnungen": DOCUMENT_DIR,
            "Mahnungen": REMINDER_DOCUMENT_DIR,
            "Vorschau": PREVIEW_DIR
        }

        files = []
        for name, path in dirs.items():
            if cat == "Alle" or cat == name:
                if path.exists():
                    for f in path.iterdir():
                        if f.is_file():
                            files.append((name, f))

        # Nach Datum sortieren (neueste zuerst)
        files.sort(key=lambda x: x[1].stat().st_mtime, reverse=True)
        self.table.setRowCount(len(files))

        for r, (name, f) in enumerate(files):
            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%d.%m.%Y %H:%M:%S")
            size_kb = f"{f.stat().st_size / 1024:.1f} KB"

            it_cat = QTableWidgetItem(name)
            it_cat.setData(Qt.UserRole, str(f)) # Dateipfad unsichtbar speichern

            self.table.setItem(r, 0, it_cat)
            self.table.setItem(r, 1, QTableWidgetItem(f.name))
            self.table.setItem(r, 2, QTableWidgetItem(mtime))

            it_size = QTableWidgetItem(size_kb)
            it_size.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(r, 3, it_size)

    def selected_document_path(self,title):
        rows=self.table.selectionModel().selectedRows(0)
        if not rows:
            QMessageBox.information(self,title,"Bitte wähle zuerst ein Dokument aus der Liste aus.")
            return None
        value=rows[0].data(Qt.UserRole)
        if not value:
            QMessageBox.warning(self,title,"Für dieses Dokument ist kein Dateipfad hinterlegt.")
            return None
        return Path(value).expanduser().resolve()

    def open_document_target(self,path,title):
        open_desktop_file(path,self,title)

    def open_doc(self):
        path=self.selected_document_path("Dokument öffnen")
        if path is None:return
        if not path.is_file():
            QMessageBox.warning(self,"Dokument öffnen",f"Die gespeicherte Datei wurde nicht gefunden:\n\n{path}")
            return
        self.open_document_target(path,"Dokument öffnen")

    def open_folder(self):
        path=self.selected_document_path("Dokumentordner öffnen")
        if path is None:return
        folder=path.parent
        if not folder.is_dir():
            QMessageBox.warning(self,"Dokumentordner öffnen",f"Der Dokumentordner wurde nicht gefunden:\n\n{folder}")
            return
        self.open_document_target(folder,"Dokumentordner öffnen")

    def delete_doc(self):
        r = self.table.currentRow()
        if r < 0:
            QMessageBox.information(self, "Dokument löschen", "Bitte wähle zuerst ein Dokument aus der Liste aus.")
            return
        path = self.table.item(r, 0).data(Qt.UserRole)
        filename = Path(path).name
        if QMessageBox.question(self, "Dokument löschen", f"Möchtest du das Dokument\n'{filename}'\nwirklich löschen?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                Path(path).unlink();self.refresh()
            except Exception as e:
                QMessageBox.warning(self, "Fehler", f"Das Dokument konnte nicht gelöscht werden:\n{e}")


class BusinessLetterDialog(QDialog):
    """Schlanker Geschäftsbrief mit vorhandenen Kunden- und Firmendaten."""
    def __init__(self,db,customer_id=None,project_id=None,parent=None):
        super().__init__(parent);self.db=db;self.saved_path=None
        self.setWindowTitle("Geschäftsbrief schreiben");self.resize(760,650)
        layout=QVBoxLayout(self)
        title=QLabel("Geschäftsbrief");title.setObjectName("pageTitle");layout.addWidget(title)
        hint=QLabel("Der vorhandene Briefkopf und die Kundenanschrift werden automatisch übernommen. Das Projekt ist optional.")
        hint.setWordWrap(True);layout.addWidget(hint)
        form=QFormLayout()
        self.customer=QComboBox();self.customer.setEditable(True)
        self.customer.addItem("Bitte Kunden auswählen …",None)
        for row in self.db.customers():self.customer.addItem(f'{row["number"]} · {row["company"]}',row["id"])
        self.customer.currentIndexChanged.connect(self.refresh_projects);form.addRow("Kunde *",self.customer)
        self.project=QComboBox();self.project.setEditable(True);form.addRow("Projekt (optional)",self.project)
        self.letter_date=QDateEdit(QDate.currentDate());self.letter_date.setCalendarPopup(True);self.letter_date.setDisplayFormat("dd.MM.yyyy")
        form.addRow("Datum",self.letter_date)
        self.subject=QLineEdit();self.subject.setPlaceholderText("Betreff des Briefes");form.addRow("Betreff *",self.subject)
        layout.addLayout(form)
        layout.addWidget(QLabel("Brieftext *"))
        self.body=QTextEdit();self.body.setPlaceholderText("Schreiben Sie hier Ihren Brieftext …");layout.addWidget(self.body,1)
        buttons=QHBoxLayout();buttons.addStretch()
        preview=QPushButton("Vorschau");preview.clicked.connect(self.preview_pdf);buttons.addWidget(preview)
        cancel=QPushButton("Abbrechen");cancel.clicked.connect(self.reject);buttons.addWidget(cancel)
        save=QPushButton("PDF speichern");save.setDefault(True);save.clicked.connect(self.save_pdf);buttons.addWidget(save)
        layout.addLayout(buttons)
        customer_index=self.customer.findData(customer_id)
        if customer_index>=0:self.customer.setCurrentIndex(customer_index)
        else:self.refresh_projects()
        project_index=self.project.findData(project_id)
        if project_index>=0:self.project.setCurrentIndex(project_index)

    def refresh_projects(self):
        selected=self.project.currentData() if self.project.count() else None
        self.project.blockSignals(True);self.project.clear();self.project.addItem("Ohne Projektbezug",None)
        customer_id=self.customer.currentData()
        if customer_id is not None:
            for row in self.db.projects_for_customer(customer_id):
                self.project.addItem(f'{row["number"]} · {row["name"]}',row["id"])
        index=self.project.findData(selected);self.project.setCurrentIndex(max(0,index));self.project.blockSignals(False)

    def validate(self):
        if self.customer.currentData() is None:
            QMessageBox.information(self,"Geschäftsbrief","Bitte zuerst einen Kunden auswählen.");return False
        if not self.subject.text().strip():
            QMessageBox.information(self,"Geschäftsbrief","Bitte einen Betreff eintragen.");return False
        if not self.body.toPlainText().strip():
            QMessageBox.information(self,"Geschäftsbrief","Bitte den Brieftext eintragen.");return False
        return True

    def target_path(self,preview=False):
        customer=self.db.customer(self.customer.currentData());project_id=self.project.currentData()
        if preview:return PREVIEW_DIR/"VORSCHAU_Geschaeftsbrief.pdf"
        folder=(PROJECT_DOCUMENT_DIR/str(self.db.project(project_id)["number"])) if project_id else LETTER_DOCUMENT_DIR
        folder.mkdir(parents=True,exist_ok=True)
        safe=re.sub(r"[^A-Za-z0-9ÄÖÜäöüß._-]+","_",self.subject.text().strip()).strip("._")[:60] or "Geschaeftsbrief"
        base=f'Brief_{customer["number"]}_{self.letter_date.date().toString("yyyy-MM-dd")}_{safe}'
        path=folder/f"{base}.pdf";counter=2
        while path.exists():path=folder/f"{base}_{counter}.pdf";counter+=1
        return path

    def write_pdf(self,path):
        customer=self.db.customer(self.customer.currentData());project=self.db.project(self.project.currentData()) if self.project.currentData() else None
        company=self.db.company_settings();val=lambda key:(company[key] if company and key in company.keys() else "") or ""
        writer=QPdfWriter(str(path));writer.setPageSize(QPageSize(QPageSize.A4));writer.setResolution(96)
        writer.setTitle(self.subject.text().strip());writer.setCreator(f"Aufmaßwerk {APP_VERSION}")
        painter=QPainter(writer)
        if not painter.isActive():return False
        page=writer.pageLayout().paintRectPixels(writer.resolution());left=65;right=55;top=42;bottom=55;width=page.width()-left-right
        letterhead=Letterhead("letter",writer);letterhead.draw(painter,True)
        def font(size=9,bold=False):f=QFont("DejaVu Sans",size);f.setBold(bold);return f
        def draw(rect,text,size=9,bold=False,align=Qt.AlignLeft|Qt.AlignTop):
            painter.setFont(font(size,bold));painter.drawText(rect,align|Qt.TextWordWrap,str(text or ""))
        def footer():
            if letterhead.active:return
            parts=[val("company_name"),val("street"),(val("zip")+" "+val("city")).strip(),val("phone"),val("email"),val("website")]
            draw(QRectF(left,page.height()-38,width,22)," · ".join(x for x in parts if x),6,False,Qt.AlignHCenter|Qt.AlignVCenter)
        y=top
        if letterhead.active:y=letterhead.content_top(y)
        else:
            draw_pdf_brand(painter,val("logo_path"),val("company_name"),left,y,width*.38,55,17,width*.55)
            company_contact=" · ".join(x for x in [val("street"),(val("zip")+" "+val("city")).strip(),val("phone"),val("email")] if x)
            draw(QRectF(left+width*.48,y,width*.52,55),company_contact,8,False,Qt.AlignRight|Qt.AlignTop);y+=74
        sender=" · ".join(x for x in [val("company_name"),val("street"),(val("zip")+" "+val("city")).strip()] if x)
        draw(QRectF(left,y,width*.62,16),sender,6);y+=19
        recipient=[customer["company"],customer["contact"],customer["street"],(str(customer["zip"] or "")+" "+str(customer["city"] or "")).strip()]
        draw(QRectF(left,y,width*.58,76),"\n".join(x for x in recipient if x),10)
        draw(QRectF(left+width*.65,y,width*.35,25),self.letter_date.date().toString("dd.MM.yyyy"),9,False,Qt.AlignRight|Qt.AlignTop);y+=100
        if project:draw(QRectF(left,y,width,20),f'Projekt: {project["number"]} · {project["name"]}',8);y+=24
        draw(QRectF(left,y,width,30),self.subject.text().strip(),11,True);y+=40
        for paragraph in self.body.toPlainText().split("\n"):
            text=paragraph or " "
            painter.setFont(font(10));needed=painter.boundingRect(QRectF(0,0,width,2000),Qt.AlignLeft|Qt.AlignTop|Qt.TextWordWrap,text).height()+8
            if y+needed>letterhead.limit(page.height()-bottom):
                footer();writer.newPage();y=top;letterhead.draw(painter,False);y=letterhead.content_top(y)
            draw(QRectF(left,y,width,needed),text,10);y+=needed
        footer();painter.end();return True

    def preview_pdf(self):
        if not self.validate():return
        path=self.target_path(True)
        if self.write_pdf(path):open_desktop_file(path,self,"Briefvorschau")
        else:QMessageBox.warning(self,"Geschäftsbrief","Die PDF-Vorschau konnte nicht erstellt werden.")

    def save_pdf(self):
        if not self.validate():return
        path=self.target_path()
        if not self.write_pdf(path):
            QMessageBox.warning(self,"Geschäftsbrief","Der Brief konnte nicht gespeichert werden.");return
        self.db.register_letter(self.customer.currentData(),self.project.currentData(),
            self.letter_date.date().toString("yyyy-MM-dd"),self.subject.text().strip(),path)
        self.saved_path=path;open_desktop_file(path,self,"Geschäftsbrief")
        QMessageBox.information(self,"Geschäftsbrief",f"Der Brief wurde gespeichert und zugeordnet:\n\n{path}")
        self.accept()
class Placeholder(QWidget):
    def __init__(self,title,text):
        super().__init__()
        l=QVBoxLayout(self)
        t=QLabel(title); t.setObjectName("pageTitle")
        x=QLabel(text); x.setWordWrap(True)
        l.addWidget(t); l.addWidget(x); l.addStretch()

class ClientProjectNavigator(QFrame):
    """Kompakter, sichtbarer Weg Kunde -> Projekt nach dem Papierentwurf."""
    def __init__(self,db,customer_selected,project_selected):
        super().__init__();self.db=db;self.customer_selected=customer_selected;self.project_selected=project_selected
        self.setObjectName("clientProjectNavigator");self.setFixedWidth(360)
        outer=QHBoxLayout(self);outer.setContentsMargins(8,10,8,10);outer.setSpacing(8)
        customer_box=QWidget();cl=QVBoxLayout(customer_box);cl.setContentsMargins(0,0,0,0);cl.setSpacing(6)
        customer_title=QLabel("Kunden");customer_title.setObjectName("navigatorTitle");cl.addWidget(customer_title)
        self.customers=QListWidget();self.customers.setObjectName("navigatorList");self.customers.currentItemChanged.connect(self._customer_changed);cl.addWidget(self.customers,1)
        project_box=QWidget();pl=QVBoxLayout(project_box);pl.setContentsMargins(0,0,0,0);pl.setSpacing(6)
        project_title=QLabel("Projekte");project_title.setObjectName("navigatorTitle");pl.addWidget(project_title)
        self.projects=QListWidget();self.projects.setObjectName("navigatorList");self.projects.currentItemChanged.connect(self._project_changed);pl.addWidget(self.projects,1)
        outer.addWidget(customer_box,1);outer.addWidget(project_box,1);self.reload()
    def reload(self,customer_id=None,project_id=None):
        self.customers.blockSignals(True);self.customers.clear()
        for customer in self.db.customers():
            item=QListWidgetItem(f'{customer["number"]}\n{customer["company"]}');item.setData(Qt.UserRole,customer["id"]);self.customers.addItem(item)
            if customer["id"]==customer_id:self.customers.setCurrentItem(item)
        self.customers.blockSignals(False);self._load_projects(customer_id,project_id)
    def _load_projects(self,customer_id,project_id=None):
        self.projects.blockSignals(True);self.projects.clear()
        for project in self.db.projects_for_customer(customer_id) if customer_id else []:
            item=QListWidgetItem(f'{project["number"]}\n{project["name"]}');item.setData(Qt.UserRole,project["id"]);self.projects.addItem(item)
            if project["id"]==project_id:self.projects.setCurrentItem(item)
        self.projects.blockSignals(False)
    def _customer_changed(self,current,_previous):
        customer_id=current.data(Qt.UserRole) if current else None;self._load_projects(customer_id);self.customer_selected(customer_id)
    def _project_changed(self,current,_previous):
        customer=self.customers.currentItem();customer_id=customer.data(Qt.UserRole) if customer else None
        self.project_selected(customer_id,current.data(Qt.UserRole) if current else None)
    def select_context(self,customer_id,project_id=None):
        self.reload(customer_id,project_id)

class ProjectWorkspace(QWidget):
    """Reine Navigations- und Übersichtsseite für den gewählten Projektkontext."""
    def __init__(self,db,open_module,open_project_documents):
        super().__init__();self.db=db;self.project_id=None
        self.open_module=open_module;self.open_project_documents=open_project_documents
        layout=QVBoxLayout(self);layout.setContentsMargins(22,18,22,18);layout.setSpacing(12)
        eyebrow=QLabel("PROJEKTZENTRALE");eyebrow.setObjectName("workspaceEyebrow")
        self.title=QLabel("Projekt auswählen");self.title.setObjectName("pageTitle")
        self.subtitle=QLabel("Links zuerst einen Kunden und danach ein Projekt auswählen.")
        self.subtitle.setObjectName("workspaceSubtitle");self.subtitle.setWordWrap(True)
        layout.addWidget(eyebrow);layout.addWidget(self.title);layout.addWidget(self.subtitle)

        self.info=QFrame();self.info.setObjectName("workspaceInfo")
        info_layout=QGridLayout(self.info);info_layout.setContentsMargins(16,12,16,12)
        self.customer=QLabel("—");self.site=QLabel("—");self.status=QLabel("—")
        info_layout.addWidget(QLabel("Kunde"),0,0);info_layout.addWidget(QLabel("Baustelle / Ort"),0,1);info_layout.addWidget(QLabel("Status"),0,2)
        info_layout.addWidget(self.customer,1,0);info_layout.addWidget(self.site,1,1);info_layout.addWidget(self.status,1,2)
        info_layout.setColumnStretch(0,2);info_layout.setColumnStretch(1,2);info_layout.setColumnStretch(2,1)
        layout.addWidget(self.info)

        hint=QLabel("Alles zum Projekt auf einen Blick – der Weg ist sichtbar, die Reihenfolge bleibt frei.")
        hint.setObjectName("workspaceHint");hint.setWordWrap(True);layout.addWidget(hint)
        self.cards=QGridLayout();self.cards.setHorizontalSpacing(12);self.cards.setVerticalSpacing(12)
        definitions=[
            ("Angebote","📋","Angebote und Positionen",0,0),
            ("Aufmaß","📐","Kumulatives Aufmaß",0,1),
            ("Rechnungen","🧾","Entwürfe und Rechnungen",0,2),
            ("Zahlungen","💰","Zahlungen und offene Beträge",1,0),
            ("Dokumente","📄","Projektunterlagen",1,1),
            ("Projekte","📁","Projektdaten bearbeiten",1,2),
        ]
        self.card_counts={};self.card_buttons=[]
        for module,icon,description,row,column in definitions:
            button=QPushButton();button.setObjectName("workspaceCard")
            button.setMinimumHeight(112);button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(lambda _checked=False,name=module:self._open(name))
            button.setProperty("moduleName",module);button.setToolTip(f"{module} für dieses Projekt öffnen")
            self.cards.addWidget(button,row,column);self.card_buttons.append(button)
            self.card_counts[module]=(icon,description,button)
        for column in range(3):self.cards.setColumnStretch(column,1)
        layout.addLayout(self.cards);layout.addStretch()
        self.set_project(None)

    def _open(self,module):
        if self.project_id is None:return
        if module=="Dokumente":self.open_project_documents(self.project_id)
        else:self.open_module(module,self.project_id)

    def set_project(self,project_id):
        self.project_id=project_id
        project=self.db.project(project_id) if project_id else None
        for button in self.card_buttons:button.setEnabled(project is not None)
        if not project:
            self.title.setText("Projekt auswählen")
            self.subtitle.setText("Links zuerst einen Kunden und danach ein Projekt auswählen.")
            self.customer.setText("—");self.site.setText("—");self.status.setText("—")
            self._set_card_text({});return
        self.title.setText(f'{project["number"]} · {project["name"]}')
        self.subtitle.setText("Von hier aus öffnen sich die vorhandenen Bereiche bereits auf dieses Projekt eingestellt.")
        self.customer.setText(project["company"] or "—")
        self.site.setText(project["site"] or "—");self.status.setText(project["status"] or "—")
        counts={
            "Angebote":self.db.conn.execute("SELECT COUNT(*) FROM offers WHERE project_id=?",(project_id,)).fetchone()[0],
            "Aufmaß":self.db.conn.execute("SELECT COUNT(*) FROM measurement_positions WHERE project_id=?",(project_id,)).fetchone()[0],
            "Rechnungen":self.db.conn.execute("SELECT COUNT(*) FROM invoices WHERE project_id=?",(project_id,)).fetchone()[0],
            "Zahlungen":self.db.conn.execute("SELECT COUNT(*) FROM payments pa JOIN invoices i ON i.id=pa.invoice_id WHERE i.project_id=?",(project_id,)).fetchone()[0],
            "Dokumente":self.db.conn.execute("SELECT COUNT(*) FROM project_documents WHERE project_id=?",(project_id,)).fetchone()[0],
            "Projekte":"öffnen",
        }
        self._set_card_text(counts)

    def _set_card_text(self,counts):
        for module,(icon,description,button) in self.card_counts.items():
            count=counts.get(module,"—")
            suffix=f"{count} Einträge" if isinstance(count,int) else str(count)
            button.setText(f"{icon}  {module}\n{description}\n{suffix}")

class ContextSidebar(QFrame):
    """Schmaler, dauerhaft sichtbarer Kunden-/Projektkontext."""
    def __init__(self,db,customer_changed,project_changed,clear_context):
        super().__init__();self.db=db;self.customer_changed=customer_changed
        self.project_changed=project_changed;self.clear_context=clear_context
        self.setObjectName("contextSidebar");self.setFixedWidth(238)
        layout=QVBoxLayout(self);layout.setContentsMargins(12,14,12,12);layout.setSpacing(9)
        title=QLabel("Arbeitskontext");title.setObjectName("contextTitle");layout.addWidget(title)
        layout.addWidget(QLabel("Kunde"));self.customer=QComboBox();self.customer.setObjectName("contextCustomer")
        self.customer.currentIndexChanged.connect(self._customer_selected);layout.addWidget(self.customer)
        project_title=QHBoxLayout();project_title.addWidget(QLabel("Projekte"));project_title.addStretch()
        self.project_count=QLabel("0");self.project_count.setObjectName("contextCount");project_title.addWidget(self.project_count)
        layout.addLayout(project_title)
        self.projects=QListWidget();self.projects.setObjectName("contextProjects")
        self.projects.currentItemChanged.connect(self._project_selected);layout.addWidget(self.projects,1)
        self.empty=QLabel("Kunde auswählen, um seine Projekte zu sehen.")
        self.empty.setObjectName("contextEmpty");self.empty.setWordWrap(True);layout.addWidget(self.empty)
        clear=QPushButton("Gesamtsicht");clear.setObjectName("contextClear")
        clear.setToolTip("Kunden- und Projektfilter aufheben");clear.clicked.connect(self._clear)
        layout.addWidget(clear);self.reload()

    def reload(self,customer_id=None,project_id=None):
        previous=customer_id if customer_id is not None else self.customer.currentData()
        self.customer.blockSignals(True);self.customer.clear();self.customer.addItem("Kunde auswählen …",None)
        for customer in self.db.customers():self.customer.addItem(f'{customer["number"]} · {customer["company"]}',customer["id"])
        index=self.customer.findData(previous);self.customer.setCurrentIndex(max(0,index))
        self.customer.blockSignals(False);self._load_projects(project_id)

    def _load_projects(self,preferred_project_id=None):
        customer_id=self.customer.currentData();self.projects.blockSignals(True);self.projects.clear()
        rows=self.db.projects_for_customer(customer_id) if customer_id else []
        for project in rows:
            item=QListWidgetItem(f'{project["number"]}\n{project["name"]}')
            item.setData(Qt.UserRole,project["id"]);item.setToolTip(project["site"] or project["name"])
            self.projects.addItem(item)
            if project["id"]==preferred_project_id:self.projects.setCurrentItem(item)
        self.projects.blockSignals(False);self.project_count.setText(str(len(rows)))
        self.empty.setVisible(not rows)
        if preferred_project_id is not None:self._project_selected(self.projects.currentItem(),None)

    def _customer_selected(self):
        self._load_projects();self.customer_changed(self.customer.currentData())
    def _project_selected(self,current,_previous):
        self.project_changed(current.data(Qt.UserRole) if current else None)
    def _clear(self):
        self.customer.setCurrentIndex(0);self.clear_context()

class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db=DB()
        try:self.db.backup("start")
        except:pass

        self._finish_new_company()
        self.setWindowTitle(f"{APP_NAME} – {APP_SUBTITLE} · {self.company_name()}")
        # Keine feste Fenstergroesse: Die Erstgroesse richtet sich nach der
        # nutzbaren Monitorflaeche (inklusive GNOME-Panel/Dock). Eine zuvor
        # gespeicherte Geometrie hat Vorrang.
        self.window_settings = QSettings(
            str(DATA_ROOT / "settings" / "window.ini"), QSettings.IniFormat
        )
        if not self.window_settings.contains("appearance/language"):
            language_dialog=LanguageSelectionDialog(self)
            language="de"
            if language_dialog.exec():language=language_dialog.selected_language()
            self.window_settings.setValue("appearance/language",language);self.window_settings.sync()
        set_ui_language(self.window_settings.value("appearance/language","de",type=str))
        self.ui_translation_filter=UiTranslationFilter(self)
        QApplication.instance().installEventFilter(self.ui_translation_filter)
        initial_theme=self.window_settings.value("appearance/theme",DEFAULT_THEME,type=str)
        if not apply_application_theme(QApplication.instance(),initial_theme):
            apply_application_theme(QApplication.instance(),DEFAULT_THEME)
        available = self.screen().availableGeometry()
        self.resize(
            min(1400, max(760, int(available.width() * 0.90))),
            min(850, max(560, int(available.height() * 0.90))),
        )

        self.context_customer_id=None;self.context_project_id=None
        self.navigation_history=[];self._navigation_ready=False
        c=QWidget(); shell=QVBoxLayout(c); shell.setContentsMargins(0,0,0,0);shell.setSpacing(0)
        topbar=QFrame();topbar.setObjectName("topNavigation")
        top_layout=QHBoxLayout(topbar);top_layout.setContentsMargins(12,7,12,7);top_layout.setSpacing(4)
        brand=QToolButton();brand.setObjectName("topBrand");brand.setPopupMode(QToolButton.InstantPopup)
        brand.setText("🏢  "+self.company_name().replace("&","&&"));brand.setToolTip("Firma wechseln oder neue Firma anlegen")
        company_menu=QMenu(brand);company_menu.aboutToShow.connect(lambda:self._fill_company_menu(company_menu))
        brand.setMenu(company_menu);top_layout.addWidget(brand);self.company_button=brand
        top_layout.addSpacing(8)
        nav_labels=ui("nav")
        self.nav_buttons=[]
        for index,label in enumerate(nav_labels):
            button=QToolButton();button.setObjectName("topNavButton")
            button.setText(label);button.setToolButtonStyle(Qt.ToolButtonTextOnly)
            button.setCheckable(True);button.setAutoExclusive(True)
            button.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Fixed)
            button.clicked.connect(lambda _checked=False,i=index:self.navigate(i))
            top_layout.addWidget(button);self.nav_buttons.append(button)
        top_layout.addStretch()
        self.back_button=QToolButton();self.back_button.setObjectName("topEmailButton");self.back_button.setText("←  Zurück")
        self.back_button.setToolTip("Zurück zur vorherigen Ansicht");self.back_button.setEnabled(False);self.back_button.clicked.connect(self.go_back)
        top_layout.addWidget(self.back_button)
        self.email_button=QToolButton();self.email_button.setObjectName("topEmailButton")
        self.email_button.setText("✉  E-Mail");self.email_button.setToolTip("E-Mail zur aktuellen Auswahl senden")
        self.email_button.clicked.connect(self.send_context_email);top_layout.addWidget(self.email_button)
        self.letter_button=QToolButton();self.letter_button.setObjectName("topEmailButton")
        self.letter_button.setText("📝  Brief");self.letter_button.setToolTip("Geschäftsbrief schreiben")
        self.letter_button.clicked.connect(self.write_business_letter);top_layout.addWidget(self.letter_button)
        shell.addWidget(topbar)

        stack=QStackedWidget()
        # QStackedWidget verwendet sonst den groessten minimumSizeHint aller
        # (auch unsichtbaren) Seiten. Dadurch erzwangen Angebote/Einstellungen
        # bisher ca. 1479x1217 px fuer das gesamte Hauptfenster. Scrollbereiche
        # entkoppeln die Seitengroessen und halten jede Aufloesung bedienbar.
        stack.setMinimumSize(QSize(0, 0))
        self.stack=stack
        dashboard=DashboardPage(self.db)
        self.pages={
            "Dashboard": dashboard,
            "Kunden": CustomersPage(self.db),
            "Leistungen": ServicesCrudPage(self.db),
            "Angebote": OffersPage(self.db),
            "Rechnungen": InvoicesPage(self.db),
            "Einstellungen": CompanySettingsPage(self.db),
        }
        self.page_containers=[]
        for page in self.pages.values():
            container=QScrollArea()
            container.setWidgetResizable(True)
            container.setFrameShape(QFrame.NoFrame)
            container.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            container.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            container.setWidget(page)
            container.setMinimumSize(QSize(0, 0))
            self.page_containers.append(container)
            stack.addWidget(container)

        self.status_delegate=StatusColorDelegate(self)
        for table in stack.findChildren(QTableWidget):
            table.setAlternatingRowColors(True)
            table.setItemDelegate(StatusColorDelegate(table))

        dashboard.set_navigator(self.navigate);dashboard.open_module=self.open_context_module
        self.pages["Kunden"].set_navigator(self.open_context_module,self.update_context)
        self.pages["Kunden"].set_compact_mode()
        body=QWidget();body_layout=QHBoxLayout(body);body_layout.setContentsMargins(0,0,0,0);body_layout.setSpacing(0)
        body_layout.addWidget(stack,1)
        shell.addWidget(body,1)
        self.setCentralWidget(c)
        self.statusBar().showMessage(f"{APP_NAME} {APP_VERSION} · {self.company_name()} · Daten: {DATA_ROOT}")

        geometry=self.window_settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state=self.window_settings.value("state")
        if state:
            self.restoreState(state)
        try:assign_existing_documents(self.db)
        except Exception:pass
        collect_offer_positions(self.db)
        self.navigate(0)
        self._navigation_ready=True
        QTimer.singleShot(0,lambda:translate_widget_tree(self))

    def navigate(self,index,record_history=True):
        if index<0 or index>=len(self.pages):return
        current=self.stack.currentIndex()
        if record_history and self._navigation_ready and current!=index and 0<=current<len(self.pages):
            preview=getattr(self.pages["Kunden"],"_preview_module",None)
            self.navigation_history.append((current,self.context_customer_id,self.context_project_id,preview))
            self.navigation_history=self.navigation_history[-20:];self.back_button.setEnabled(True)
        self.stack.setCurrentIndex(index)
        for i,button in enumerate(self.nav_buttons):button.setChecked(i==index)
        page=list(self.pages.values())[index]
        self._apply_context_to_page(page)
        if hasattr(page,"refresh"):page.refresh()
        if isinstance(page,CustomersPage) and self.context_customer_id is not None:
            page.select_customer(self.context_customer_id,self.context_project_id)

    def _apply_context_to_page(self,page):
        project_id=self.context_project_id
        if isinstance(page,(OffersPage,PaymentsPage)):
            page.context_project_id=project_id
        if isinstance(page,(MeasurementsPage,InvoicesPage)) and project_id is not None:
            page.refresh()
            combo_index=page.project.findData(project_id)
            if combo_index<0 and isinstance(page,MeasurementsPage):
                project=self.db.project(project_id)
                if project:
                    page.project.addItem(
                        f'{project["number"]} – {one_line(project["name"])} – {one_line(project["company"])}',
                        project_id)
                    combo_index=page.project.findData(project_id)
            if combo_index>=0:page.project.setCurrentIndex(combo_index)
        if isinstance(page,ProjectsPage) and project_id is not None:
            page.select_project(project_id)

    def update_context(self,customer_id,project_id):
        self.context_customer_id=customer_id;self.context_project_id=project_id
        for page in (self.pages["Angebote"],):page.context_project_id=project_id
        if project_id:
            project=self.db.project(project_id)
            self.statusBar().showMessage(f'Projektkontext: {project["number"]} · {project["name"]}' if project else "Projektkontext")

    def select_customer_from_navigator(self,customer_id):
        self.update_context(customer_id,None)
        if customer_id is not None:
            self.navigate(list(self.pages.keys()).index("Kunden"));self.pages["Kunden"].select_customer(customer_id)

    def select_project_from_navigator(self,customer_id,project_id):
        self.update_context(customer_id,project_id)
        if customer_id is not None and project_id is not None:
            self.navigate(list(self.pages.keys()).index("Kunden"));self.pages["Kunden"].select_customer(customer_id,project_id)

    def open_context_module(self,module,project_id,record_id=None):
        self.context_project_id=project_id
        if module=="Dokumente":self.open_project_documents(project_id);return
        if module=="Zahlungen":module="Rechnungen"  # Zahlungen stehen jetzt bei der Rechnung.
        if module=="Aufmaß":
            # Das Aufmaß ist jetzt ein Reiter im Modul Angebot & Aufmaß.
            self.navigate(list(self.pages.keys()).index("Angebote"));self.pages["Angebote"].open_measurement(project_id);return
        if module=="Eingangsrechnungen":
            self.navigate(list(self.pages.keys()).index("Rechnungen"));self.pages["Rechnungen"].show_incoming(project_id,record_id);return
        index=list(self.pages.keys()).index(module);self.navigate(index)
        page=self.pages[module]
        if module=="Rechnungen":page.show_view(0)
        if module=="Angebote" and record_id is not None:page.select_offer_by_id(record_id)
        elif module=="Rechnungen" and record_id is not None:page.refresh_keep_invoice(record_id)
        elif module=="Zahlungen" and record_id is not None:
            for row in range(page.table.rowCount()):
                item=page.table.item(row,0)
                if item and item.data(Qt.UserRole)==record_id:page.table.selectRow(row);page.select_invoice();break

    def go_back(self):
        if not self.navigation_history:return
        index,customer_id,project_id,preview=self.navigation_history.pop()
        self.context_customer_id=customer_id;self.context_project_id=project_id
        self.navigate(index,record_history=False)
        if index==list(self.pages.keys()).index("Kunden") and customer_id is not None:
            page=self.pages["Kunden"];page.select_customer(customer_id,project_id)
            if project_id is not None and preview:page.show_preview(preview)
        self.back_button.setEnabled(bool(self.navigation_history))

    def open_project_documents(self,project_id):
        ProjectDocumentsDialog(self.db,project_id,self).exec()
        page=self.pages.get("Kunden")
        if page is not None and page.project_id==project_id:
            module=getattr(page,"_preview_module",None);page.show_project()
            if module:page.show_preview(module)

    def send_context_email(self):
        page=list(self.pages.values())[self.stack.currentIndex()]
        handlers={OffersPage:"send_email_for_current_view",MeasurementsPage:"send_measurement_email",InvoicesPage:"send_invoice_email",
                  DashboardPage:"email_selected_reminder"}
        for page_type,method in handlers.items():
            if isinstance(page,page_type):getattr(page,method)();return
        QMessageBox.information(self,"E-Mail","In der aktuellen Ansicht ist kein versendbares Dokument ausgewählt.\n\nÖffne bitte ein Angebot, ein Aufmaß oder eine Rechnung.")

    def write_business_letter(self):
        dialog=BusinessLetterDialog(self.db,self.context_customer_id,self.context_project_id,self)
        if dialog.exec():
            if self.stack.currentIndex()==list(self.pages.keys()).index("Kunden") and self.context_project_id:
                self.pages["Kunden"].show_project()

    def apply_theme(self,theme_name,persist=False):
        if not apply_application_theme(QApplication.instance(),theme_name):return False
        for button in self.findChildren(QToolButton):
            action=button.property("standardAction")
            if action in ACTION_ICONS:button.setIcon(action_icon(action))
        if persist:
            self.window_settings.setValue("appearance/theme",theme_name)
            self.window_settings.sync()
            self.statusBar().showMessage(
                f"Design: {THEMES[theme_name]['label']} · Daten: {DATA_ROOT}",5000)
        return True

    # --- Mehrere Firmen ---------------------------------------------------------
    def company_name(self,data_root=None):
        """Firmenname aus den Einstellungen der jeweiligen Firma."""
        root=Path(data_root).expanduser() if data_root else DATA_ROOT
        try:
            if root==DATA_ROOT:row=self.db.company_settings()
            elif not (root/db_file_name(root)).is_file():row=None
            else:
                con=sqlite3.connect(str(root/db_file_name(root)));con.row_factory=sqlite3.Row
                row=con.execute("SELECT company_name FROM company_settings WHERE id=1").fetchone();con.close()
            name=(row["company_name"] or "").strip() if row else ""
        except Exception:name=""
        if not name:
            entry=next((c for c in load_company_registry()["companies"] if Path(c["path"]).expanduser()==root),None)
            name=(entry or {}).get("name") or root.name
        return name

    def _finish_new_company(self):
        """Erster Start einer neu angelegten Firma: Namen übernehmen, Merker entfernen."""
        marker=DATA_ROOT/NEW_COMPANY_MARKER
        if not marker.exists():return
        name=marker.read_text(encoding="utf-8").strip()
        if name:
            self.db.conn.execute("""UPDATE company_settings SET company_name=? WHERE id=1""",(name,));self.db.conn.commit()
        marker.unlink(missing_ok=True)

    def _fill_company_menu(self,menu):
        menu.clear();data=load_company_registry()
        for entry in data["companies"]:
            root=Path(entry["path"]).expanduser()
            action=menu.addAction(self.company_name(root).replace("&","&&"));action.setCheckable(True);action.setChecked(root==DATA_ROOT)
            action.triggered.connect(lambda _checked=False,r=root:self.switch_company(r))
        menu.addSeparator();menu.addAction("+ Neue Firma anlegen …",self.add_company)

    def add_company(self):
        name,ok=QInputDialog.getText(self,"Neue Firma anlegen","Name der neuen Firma:")
        name=(name or "").strip()
        if not ok or not name:return
        slug=re.sub(r"[^A-Za-z0-9ÄÖÜäöüß_-]+","_",name).strip("_") or "Firma"
        base=Path.home()/".local"/"share"/_app_folder(Path.home()/".local"/"share","Aufmasswerk-Firmen","HandwerkPro-Firmen");root=base/slug;n=2
        while root.exists():root=base/f"{slug}_{n}";n+=1
        root.mkdir(parents=True);(root/NEW_COMPANY_MARKER).write_text(name,encoding="utf-8")
        # Sprache, Design, Fenster und Spalten übernehmen (sonst fragt der erste Start nach der Sprache).
        (root/"settings").mkdir(exist_ok=True)
        for filename in ("window.ini","column_layouts.ini"):
            if (DATA_ROOT/"settings"/filename).is_file():shutil.copy2(DATA_ROOT/"settings"/filename,root/"settings"/filename)
        data=load_company_registry();data["companies"].append({"path":str(root),"name":name});save_company_registry(data)
        if QMessageBox.question(self,"Neue Firma angelegt",
            f"Die Firma „{name}“ wurde angelegt. Ihre Daten sind vollständig getrennt.\n\n"
            "Jetzt zu dieser Firma wechseln? Danach bitte unter „Einstellungen“ Adresse, Logo, "
            "Bankverbindung und Nummernkreise eintragen.",QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            self.switch_company(root)

    def restart_program(self):
        """Neu starten (z. B. nach dem Wiederherstellen einer Sicherung)."""
        env=dict(os.environ);env["AUFMASSWERK_DATA_DIR"]=str(DATA_ROOT)
        appimage=os.environ.get("APPIMAGE")
        command=[appimage] if appimage else [sys.executable,str(Path(__file__).resolve())]
        try:subprocess.Popen(command,env=env,start_new_session=True)
        except Exception as exc:
            QMessageBox.warning(self,"Neustart",f"Bitte das Programm von Hand neu starten.\n\n{exc}")
        self._skip_close_backup=True;self.close()

    def switch_company(self,root):
        root=Path(root).expanduser()
        if root==DATA_ROOT:return
        data=load_company_registry();data["last"]=str(root);save_company_registry(data)
        env=dict(os.environ);env["AUFMASSWERK_DATA_DIR"]=str(root)
        appimage=os.environ.get("APPIMAGE")
        command=[appimage] if appimage else [sys.executable,str(Path(__file__).resolve())]
        try:subprocess.Popen(command,env=env,start_new_session=True)
        except Exception as exc:
            QMessageBox.warning(self,"Firma wechseln",f"Das Programm konnte nicht neu gestartet werden:\n{exc}");return
        self.close()

    def closeEvent(self,e):
        self.window_settings.setValue("geometry", self.saveGeometry())
        self.window_settings.setValue("state", self.saveState())
        self.window_settings.sync()
        try:self.db.backup("ende")
        except:pass
        e.accept()

if __name__=="__main__":
    app=QApplication(sys.argv)
    w=Main(); w.show()
    sys.exit(app.exec())
