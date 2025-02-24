import os
import shutil
import zipfile
import requests
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import subprocess
import psutil
import time

SETTINGS_FILE = "user_settings.json"

languages = {
    'tr': {
        'url_label': 'Kostüm URL\'leri (her satıra bir URL)(dosyanın içinde wad ve meta klasörleri olması gereklidir):',
        'target_dir_label': 'Skinchanger Yolu:(cslol-manager-windows\installed)',
        'download_dir_label': 'Geçici İndirme Yolu:',
        'footer_label': 'Kozarius tarafından ChatGPT ve DeepSeek kullanılarak yapıldı',
        'missing_info': 'Lütfen tüm alanları doldurun.',
        'processing_error': 'Dosya indirilirken veya çıkarılırken bir hata oluştu: {e}',
        'move_error': 'Dosyalar taşınırken bir hata oluştu: {e}',
        'url_processing_error': '{url} işlenirken bir hata oluştu.',
        'success': 'Tüm dosyalar başarıyla işlendi.',
        'select_program': 'Skinchanger programını Seç',
        'start_program': 'Programı ve İşlemi Başlat',
    },
    'en': {
        'url_label': 'Skin URLs (one per line)(there must be wad and meta folders inside the file):',
        'target_dir_label': 'Skinchanger Path:(cslol-manager-windows\installed)',
        'download_dir_label': 'Temp Download Path:',
        'footer_label': 'Made by Kozarius using ChatGPT and DeepSeek',
        'missing_info': 'Please fill in all fields.',
        'processing_error': 'An error occurred while downloading or extracting the file: {e}',
        'move_error': 'An error occurred while moving files: {e}',
        'url_processing_error': 'An error occurred while processing {url}.',
        'success': 'All files processed successfully.',
        'select_program': 'Select Skinchanger Program',
        'start_program': 'Start Program and Process',
    },
    'de': {
        'url_label': 'Skin-URLs (jeweils eine pro Zeile)(in der Datei müssen Wad- und Meta-Ordner vorhanden sein):',
        'target_dir_label': 'Skinchanger-Pfad:(cslol-manager-windows\installed)',
        'download_dir_label': 'Temporärer Download-Pfad:',
        'footer_label': 'Erstellt von Kozarius mit ChatGPT und DeepSeek',
        'missing_info': 'Bitte füllen Sie alle Felder aus.',
        'processing_error': 'Beim Herunterladen oder Extrahieren der Datei ist ein Fehler aufgetreten: {e}',
        'move_error': 'Beim Verschieben der Dateien ist ein Fehler aufgetreten: {e}',
        'url_processing_error': 'Beim Verarbeiten von {url} ist ein Fehler aufgetreten.',
        'success': 'Alle Dateien wurden erfolgreich verarbeitet.',
        'select_program': 'Skinchanger Programm auswählen',
        'start_program': 'Programm starten und Prozess starten',
    },
    'fr': {
        'url_label': 'URLs des skins (une par ligne)(il doit y avoir des dossiers wad et meta à l intérieur du fichier) :',
        'target_dir_label': 'Chemin du Skinchanger :(cslol-manager-windows\installed)',
        'download_dir_label': 'Chemin de téléchargement temporaire :',
        'footer_label': 'Créé par Kozarius avec ChatGPT et DeepSeek',
        'missing_info': 'Veuillez remplir tous les champs.',
        'processing_error': 'Une erreur est survenue lors du téléchargement ou de l\'extraction du fichier : {e}',
        'move_error': 'Une erreur est survenue lors du déplacement des fichiers : {e}',
        'url_processing_error': 'Une erreur est survenue lors du traitement de {url}.',
        'success': 'Tous les fichiers ont été traités avec succès.',
        'select_program': 'Sélectionner le skinchanger programme',
        'start_program': 'Démarrer le programme et le processus',
    }
}

current_language = 'en'

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return {"urls": "", "target_dir": "", "download_dir": "", "language": "en", "program_path": ""}

def save_settings():
    settings = {
        "urls": url_text.get("1.0", "end-1c").strip(),
        "target_dir": target_dir_entry.get().strip(),
        "download_dir": download_dir_entry.get().strip(),
        "language": current_language,
        "program_path": program_entry.get().strip(),
    }
    with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
        json.dump(settings, file, ensure_ascii=False, indent=4)

def set_language(lang):
    global current_language
    current_language = lang
    update_texts()
    save_settings()

def update_texts():
    language = languages[current_language]
    url_label.config(text=language['url_label'])
    target_dir_label.config(text=language['target_dir_label'])
    download_dir_label.config(text=language['download_dir_label'])
    footer_label.config(text=language['footer_label'])
    select_program_button.config(text=language['select_program'])
    start_program_button.config(text=language['start_program'])
    adjust_window_size()

def download_and_extract(url, download_dir, extract_dir):
    try:
        response = requests.get(url)
        response.raise_for_status()
        zip_path = os.path.join(download_dir, os.path.basename(url))
        with open(zip_path, 'wb') as file:
            file.write(response.content)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        return zip_path, extract_dir
    except Exception as e:
        messagebox.showerror("Hata", languages[current_language]['processing_error'].format(e=e))
        return None, None

def move_files(source_dir, target_dir, folder_name):
    try:
        target_folder = os.path.join(target_dir, folder_name)
        os.makedirs(target_folder, exist_ok=True)

        for folder in ['wad', 'meta']:
            source_folder = os.path.join(source_dir, folder)
            if os.path.exists(source_folder):
                target_folder_path = os.path.join(target_folder, folder)
                if os.path.exists(target_folder_path):
                    shutil.rmtree(target_folder_path)
                shutil.move(source_folder, target_folder_path)
        return True
    except Exception as e:
        messagebox.showerror("Hata", languages[current_language]['move_error'].format(e=e))
        return False

def on_process():
    urls = url_text.get("1.0", "end-1c").strip().splitlines()
    target_dir = target_dir_entry.get().strip()
    download_dir = download_dir_entry.get().strip()

    if not urls or not target_dir or not download_dir:
        messagebox.showwarning("Eksik Bilgi", languages[current_language]['missing_info'])
        return

    for url in urls:
        zip_name = os.path.basename(url)
        folder_name = os.path.splitext(zip_name)[0]
        temp_extract_dir = os.path.join(download_dir, folder_name)

        zip_path, extract_dir = download_and_extract(url, download_dir, temp_extract_dir)
        if extract_dir:
            if move_files(extract_dir, target_dir, folder_name):
                pass
            else:
                messagebox.showerror("Hata", languages[current_language]['url_processing_error'].format(url=url))
            
            shutil.rmtree(extract_dir)
            os.remove(zip_path)
        else:
            messagebox.showerror("Hata", languages[current_language]['url_processing_error'].format(url=url))

    messagebox.showinfo("Başarılı", languages[current_language]['success'])
    save_settings()

    # İndirme ve işleme tamamlandıktan sonra programı başlat
    on_start_program()

def on_browse_target():
    target_dir = filedialog.askdirectory()
    if target_dir:
        target_dir_entry.delete(0, tk.END)
        target_dir_entry.insert(0, target_dir)
        save_settings()

def on_browse_download():
    download_dir = filedialog.askdirectory()
    if download_dir:
        download_dir_entry.delete(0, tk.END)
        download_dir_entry.insert(0, download_dir)
        save_settings()

def on_select_program():
    program_path = filedialog.askopenfilename()
    if program_path:
        program_entry.delete(0, tk.END)
        program_entry.insert(0, program_path)
        save_settings()

def is_program_running(program_name):
    """Seçilen programın çalışıp çalışmadığını kontrol eder."""
    for proc in psutil.process_iter(['pid', 'name']):
        if program_name.lower() in proc.info['name'].lower():
            return True
    return False

def on_start_program():
    program_path = program_entry.get().strip()
    if not program_path:
        messagebox.showwarning("Eksik Bilgi", languages[current_language]['missing_info'])
        return

    try:
        # Programı başlat
        subprocess.Popen([program_path])
        
        # Programın açılması için 20 saniye bekle
        time.sleep(20)
        
        # Programın çalışıp çalışmadığını kontrol et
        program_name = os.path.basename(program_path)
        while not is_program_running(program_name):
            time.sleep(1) 
        
        # İşlemi başlat
        on_process()
    except Exception as e:
        messagebox.showerror("Hata", f"Program başlatılırken bir hata oluştu: {e}")

def adjust_window_size():
    """Pencere boyutunu içeriğe göre ayarlar."""
    root.update()  
    width = root.winfo_reqwidth()  
    height = root.winfo_reqheight()  
    root.geometry(f"{width}x{height}")  

root = tk.Tk()
root.title("Skinchanger-Simplifier")

settings = load_settings()

language_frame = tk.Frame(root)
language_frame.pack()
for lang in languages:
    lang_button = tk.Button(language_frame, text=lang.upper(), command=lambda l=lang: set_language(l))
    lang_button.pack(side=tk.LEFT)

footer_label = tk.Label(root, text=languages[current_language]['footer_label'])
footer_label.pack()

url_label = tk.Label(root, text=languages[current_language]['url_label'])
url_label.pack()
url_text = tk.Text(root, height=5, width=50)
url_text.pack()
url_text.insert("1.0", settings["urls"])

target_dir_label = tk.Label(root, text=languages[current_language]['target_dir_label'])
target_dir_label.pack()
target_dir_entry = tk.Entry(root, width=50)
target_dir_entry.pack()
target_dir_entry.insert(0, settings["target_dir"])
target_dir_button = tk.Button(root, text="Gözat", command=on_browse_target)
target_dir_button.pack()

download_dir_label = tk.Label(root, text=languages[current_language]['download_dir_label'])
download_dir_label.pack()
download_dir_entry = tk.Entry(root, width=50)
download_dir_entry.pack()
download_dir_entry.insert(0, settings["download_dir"])
download_dir_button = tk.Button(root, text="Gözat", command=on_browse_download)
download_dir_button.pack()

program_label = tk.Label(root, text="Program Seç:")
program_label.pack()
program_entry = tk.Entry(root, width=50)
program_entry.pack()
program_entry.insert(0, settings["program_path"])
select_program_button = tk.Button(root, text="Program Seç", command=on_select_program)
select_program_button.pack()

start_program_button = tk.Button(root, text=languages[current_language]['start_program'], command=on_start_program)
start_program_button.pack()

adjust_window_size()

root.mainloop()
