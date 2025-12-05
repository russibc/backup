import os
import gzip
from datetime import datetime

# Intervalo de tempo desejado
start_time = datetime.strptime("07:20:00", "%H:%M:%S").time()
end_time = datetime.strptime("08:20:00", "%H:%M:%S").time()

# Caminho da pasta atual
folder_path = os.getcwd()

# Itera sobre todos os arquivos .gz na pasta
for filename in os.listdir(folder_path):
    if filename.endswith(".gz"):
        gz_path = os.path.join(folder_path, filename)
        extracted_path = os.path.join(folder_path, filename[:-3])  # remove .gz

        # Descomprime o arquivo
        try:
            with gzip.open(gz_path, 'rt', encoding='utf-8', errors='ignore') as gz_file:
                lines = gz_file.readlines()
        except Exception as e:
            print(f"Erro ao descomprimir {filename}: {e}")
            continue

        # Filtra as linhas entre 07:20 e 08:20
        filtered_lines = []
        for line in lines:
            try:
                # Espera que a linha comece com "YYYY-MM-DD HH:MM:SS.mmm"
                timestamp_str = line.strip().split()[1]  # pega HH:MM:SS.mmm
                log_time = datetime.strptime(timestamp_str.split('.')[0], "%H:%M:%S").time()
                if start_time <= log_time <= end_time:
                    filtered_lines.append(line)
            except (IndexError, ValueError):
                continue  # ignora linhas malformadas

        # Salva o conteúdo filtrado no novo arquivo
        with open(extracted_path, 'w', encoding='utf-8') as out_file:
            out_file.writelines(filtered_lines)

        # Remove o arquivo .gz original
        os.remove(gz_path)

print("✅ Processamento concluído. Os arquivos foram filtrados e os .gz removidos.")

