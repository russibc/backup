import os
import shutil

# Mapeamento de extensões para categorias
CATEGORIES = {
    "IMAGES": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".svg"],
    "VIDEOS": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv"],
    "DOCUMENTS": [".pdf", ".doc", ".docx", ".odt", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"],
    "AUDIO": [".mp3", ".wav", ".aac", ".flac", ".ogg"],
    "CODE": [".py", ".java", ".c", ".cpp", ".js", ".html", ".css", ".php", ".rb"],
    "ARCHIVES": [".zip", ".rar", ".tar", ".gz", ".7z"],
}

REST_FOLDER = "RESTO"

def ensure_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_category(ext):
    ext = ext.lower()
    for category, extensions in CATEGORIES.items():
        if ext in extensions:
            return category
    return REST_FOLDER

def unique_name(dest_folder, filename):
    """
    Garante que o arquivo não sobrescreva outro já existente.
    Se existir, adiciona números ao final.
    """
    name, ext = os.path.splitext(filename)
    candidate = filename
    while os.path.exists(os.path.join(dest_folder, candidate)):
        candidate = name + "1" + ext
        name = name + "1"  # acumula os números
    return candidate

def organize_directory(root_dir):
    # Cria pastas principais
    for category in CATEGORIES.keys():
        ensure_folder(os.path.join(root_dir, category))
    ensure_folder(os.path.join(root_dir, REST_FOLDER))

    # Percorre recursivamente
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
        # Ignora as pastas de destino
        if os.path.basename(dirpath).upper() in list(CATEGORIES.keys()) + [REST_FOLDER]:
            continue

        for file in filenames:
            file_path = os.path.join(dirpath, file)
            ext = os.path.splitext(file)[1]
            category = get_category(ext)
            dest_folder = os.path.join(root_dir, category)

            # Resolve conflitos de nome
            new_name = unique_name(dest_folder, file)
            dest_path = os.path.join(dest_folder, new_name)

            # Move arquivo
            shutil.move(file_path, dest_path)

        # Move pastas vazias ou não categorizadas para RESTO
        if dirpath != root_dir and not os.listdir(dirpath):
            shutil.rmtree(dirpath, ignore_errors=True)
        elif dirpath != root_dir:
            # Se sobrou algo não categorizado
            dest_folder = os.path.join(root_dir, REST_FOLDER)
            for leftover in os.listdir(dirpath):
                src_path = os.path.join(dirpath, leftover)
                dest_path = os.path.join(dest_folder, unique_name(dest_folder, leftover))
                shutil.move(src_path, dest_path)
            shutil.rmtree(dirpath, ignore_errors=True)

if __name__ == "__main__":
    root = os.getcwd()  # Diretório atual
    organize_directory(root)
    print("Organização concluída!")

