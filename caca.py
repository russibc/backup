import os
import re
from collections import Counter

# Regex para capturar nomes de exceções
exception_pattern = re.compile(r"\b([\w\.]+Exception)\b")

# Contador de exceções
exception_counter = Counter()

# Caminho da pasta atual
folder_path = os.getcwd()

print("🔍 Procurando exceções nos logs...\n")

# Itera sobre os arquivos de log
for filename in os.listdir(folder_path):
    if filename.endswith(".log") or filename.endswith(".txt"):
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as log_file:
            for line in log_file:
                matches = exception_pattern.findall(line)
                for exc in matches:
                    exception_counter[exc] += 1

# Exibe as exceções mais comuns
print("📊 Exceções mais recorrentes:")
if exception_counter:
    for exc, count in exception_counter.most_common(20):
        print(f"{count:3}x → {exc}")
else:
    print("⚠️ Nenhuma exceção encontrada.")

print("\n✅ Análise concluída.")
