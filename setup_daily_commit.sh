#!/usr/bin/env bash

# Diretório de configuração do systemd para o usuário
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

# Cria o diretório se não existir
mkdir -p "$SYSTEMD_USER_DIR"

# Cria o service
cat > "$SYSTEMD_USER_DIR/daily-commit.service" << 'EOF'
[Unit]
Description=Daily commit across dev_utils and py_media_utils

[Service]
Type=oneshot
ExecStart=/home/bioinfo/github/daily_commit.sh
WorkingDirectory=/home/bioinfo/github
EOF

# Cria o timer
cat > "$SYSTEMD_USER_DIR/daily-commit.timer" << 'EOF'
[Unit]
Description=Agendamento diário do commit às 07h

[Timer]
OnCalendar=*-*-* 07:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Recarrega systemd do usuário
systemctl --user daemon-reload

# Habilita e inicia o timer
systemctl --user enable --now daily-commit.timer

echo "✅ daily-commit.service e daily-commit.timer criados e habilitados."
echo "Verifique com: systemctl --user list-timers | grep daily-commit"

