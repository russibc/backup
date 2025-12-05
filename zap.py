import os
import zipfile
import re
from collections import defaultdict

# Regex robusta para formatos comuns do WhatsApp:
# Ex.: "26/11/2025, 21:09 - Nome: mensagem" ou "26/11/25 21:09 - Nome: mensagem"
DATE_TIME_RE = re.compile(r"^(\d{2}/\d{2}/\d{2,4}),?\s+\d{2}:\d{2}\s+-")

def normalize_date(date_str):
    """
    Converte 'DD/MM/YYYY' ou 'DD/MM/YY' para 'YYYY-MM-DD'.
    Se for ano com 2 dígitos, assume 20YY.
    """
    dd, mm, yy = date_str.split('/')
    if len(yy) == 2:
        yy = f"20{yy}"
    return f"{yy}-{mm}-{dd}"

def unzip_all_to_separate_folders(root_folder):
    """
    Encontra todos os .zip recursivamente e extrai cada um
    em uma pasta com o mesmo nome do arquivo (sem extensão),
    na mesma localização do .zip.
    """
    for dirpath, _, filenames in os.walk(root_folder):
        for name in filenames:
            if name.lower().endswith(".zip"):
                zip_path = os.path.join(dirpath, name)
                out_dir = os.path.join(dirpath, os.path.splitext(name)[0])
                os.makedirs(out_dir, exist_ok=True)
                with zipfile.ZipFile(zip_path, 'r') as z:
                    z.extractall(out_dir)

def split_conversations_per_folder_by_day(root_folder):
    """
    Percorre recursivamente as pastas, lê .txt e cria arquivos por dia
    em cada pasta onde os .txt estão. Evita reprocessar arquivos gerados.
    """
    for dirpath, _, filenames in os.walk(root_folder):
        # Map dia -> linhas dentro desta pasta específica
        day_lines = defaultdict(list)

        # Ler todos os .txt de conversa
        for name in filenames:
            if not name.lower().endswith(".txt"):
                continue
            if name.startswith("day-") or name.startswith("conversa_"):
                # Ignora arquivos gerados pelo script
                continue

            txt_path = os.path.join(dirpath, name)
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    current_day = None
                    for raw_line in f:
                        line = raw_line.rstrip("\n")
                        m = DATE_TIME_RE.match(line)
                        if m:
                            # Captura a parte de data (até o primeiro espaço/virgula antes da hora)
                            # O grupo 1 é "DD/MM/YY(YY)"
                            date_part = m.group(1)
                            iso_day = normalize_date(date_part)
                            current_day = iso_day
                            day_lines[current_day].append(line)
                        else:
                            # Linhas de continuação pertencem ao último dia conhecido
                            if current_day is not None and line.strip():
                                day_lines[current_day].append(line)
            except UnicodeDecodeError:
                # Tenta latin-1 caso utf-8 falhe
                with open(txt_path, "r", encoding="latin-1") as f:
                    current_day = None
                    for raw_line in f:
                        line = raw_line.rstrip("\n")
                        m = DATE_TIME_RE.match(line)
                        if m:
                            date_part = m.group(1)
                            iso_day = normalize_date(date_part)
                            current_day = iso_day
                            day_lines[current_day].append(line)
                        else:
                            if current_day is not None and line.strip():
                                day_lines[current_day].append(line)

        # Escreve arquivos por dia nesta pasta (day-YYYY-MM-DD.txt)
        for iso_day, lines in day_lines.items():
            out_path = os.path.join(dirpath, f"day-{iso_day}.txt")
            # Mescla se já existir (evita perda de informação)
            existing = set()
            if os.path.exists(out_path):
                with open(out_path, "r", encoding="utf-8") as f:
                    for l in f:
                        existing.add(l.rstrip("\n"))
            # Adiciona novos sem duplicar
            with open(out_path, "w", encoding="utf-8") as f:
                seen = set(existing)
                for l in existing:
                    f.write(l + "\n")
                for l in lines:
                    if l not in seen:
                        seen.add(l)
                        f.write(l + "\n")

def consolidate_all_days_to_root(root_folder):
    """
    Procura todos os arquivos 'day-YYYY-MM-DD.txt' nas subpastas
    e consolida por dia na pasta raiz como 'conversa_YYYY-MM-DD.txt',
    removendo duplicidades.
    """
    global_day_map = defaultdict(list)

    for dirpath, _, filenames in os.walk(root_folder):
        for name in filenames:
            if name.startswith("day-") and name.endswith(".txt"):
                iso_day = name[4:-4]  # remove 'day-' e '.txt'
                day_path = os.path.join(dirpath, name)

                # Usa set para deduplicar dentro do arquivo
                with open(day_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.rstrip("\n")
                        if line:
                            global_day_map[iso_day].append(line)

    # Consolida na raiz
    for iso_day, lines in global_day_map.items():
        out_path = os.path.join(root_folder, f"conversa_{iso_day}.txt")
        # Dedup global preservando ordem
        seen = set()
        deduped = []
        for l in lines:
            if l not in seen:
                seen.add(l)
                deduped.append(l)

        # Se já existir, mescla sem duplicar
        if os.path.exists(out_path):
            with open(out_path, "r", encoding="utf-8") as f:
                for l in f:
                    l = l.rstrip("\n")
                    if l and l not in seen:
                        seen.add(l)
                        deduped.append(l)

        with open(out_path, "w", encoding="utf-8") as f:
            for l in deduped:
                f.write(l + "\n")

def main():
    root = os.path.dirname(os.path.abspath(__file__))
    unzip_all_to_separate_folders(root)
    split_conversations_per_folder_by_day(root)
    consolidate_all_days_to_root(root)

if __name__ == "__main__":
    main()
