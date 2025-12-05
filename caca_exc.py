import os
import re
from collections import Counter

# Regex para capturar mensagens de erro após o separador " : "
error_pattern = re.compile(r":\s+(.*)")

# Contador de mensagens
error_counter = Counter()

# Caminho da pasta atual
folder_path = os.getcwd()

print("🔍 Analisando mensagens de erro nos logs...\n")

# Itera sobre os arquivos de log
for filename in os.listdir(folder_path):
    if filename.endswith(".log") or filename.endswith(".txt"):
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as log_file:
            for line in log_file:
                if "ERROR" in line:
                    match = error_pattern.search(line)
                    if match:
                        message = match.group(1).strip()
                        # Normaliza espaços e remove IDs ou números repetitivos
                        message = re.sub(r"\s+", " ", message)
                        message = re.sub(r"\d{4,}", "", message)
                        error_counter[message] += 1

# Exibe os erros mais comuns
print("📊 Mensagens de erro mais recorrentes:")
if error_counter:
    for msg, count in error_counter.most_common(20):
        print(f"{count:3}x → {msg}")
else:
    print("⚠️ Nenhuma mensagem de erro encontrada.")

print("\n✅ Análise concluída.")
