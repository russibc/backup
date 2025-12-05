import os
import shutil

def process_timelines(base_dir):
    # Pastas principais
    folders = ["BORRELIA", "CANDIDA", "EBOLA", "INFLUENZA", "STAPHYLOCOCCUS"]

    # Pasta destino (mesmo local do script)
    destination = os.path.join(base_dir, "timelines_coletados")
    os.makedirs(destination, exist_ok=True)

    for folder in folders:
        folder_path = os.path.join(base_dir, folder)
        timeline_file = os.path.join(folder_path, "timeline.html")

        if os.path.exists(timeline_file):
            # Novo nome do arquivo
            new_name = f"timeline_{folder}.html"
            new_path = os.path.join(folder_path, new_name)

            # Renomear
            os.rename(timeline_file, new_path)

            # Copiar para pasta destino
            shutil.copy(new_path, destination)
            print(f"✅ Arquivo {new_name} copiado para {destination}")
        else:
            print(f"⚠️ Arquivo timeline.html não encontrado em {folder}")

if __name__ == "__main__":
    # Diretório onde está o script (cpu ou gpu)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    process_timelines(base_dir)
