#!/bin/bash
# GAKMS Daily News Pipeline — 하루 2회 자동 실행 설정
# 10:00 AM KST (01:00 UTC) + 10:00 PM KST (13:00 UTC)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV="$PROJECT_DIR/.venv/bin/python"
PIPELINE="$PROJECT_DIR/scripts/daily_news_pipeline.py"
LOG_DIR="$PROJECT_DIR/knowledge_base/logs"
mkdir -p "$LOG_DIR"

# Environment variables
ENVVARS="HF_HOME=$PROJECT_DIR/.cache/hf VLLM_BASE_URL=http://localhost:8013/v1 VLLM_MODEL=Qwen/Qwen3.5-35B-A3B-FP8"

CRON_CMD="cd $PROJECT_DIR && $ENVVARS $VENV $PIPELINE --hours 12 >> $LOG_DIR/pipeline_\$(date +\%Y\%m\%d_\%H\%M).log 2>&1"

echo "GAKMS Cron Setup"
echo "  Project: $PROJECT_DIR"
echo "  Python: $VENV"
echo "  Log dir: $LOG_DIR"
echo ""

# Option 1: crontab
echo "=== Option 1: crontab ==="
echo "Run: crontab -e"
echo "Add these lines:"
echo ""
echo "# GAKMS Daily News Pipeline (10AM KST = 01:00 UTC, 10PM KST = 13:00 UTC)"
echo "0 1 * * * $CRON_CMD"
echo "0 13 * * * $CRON_CMD"
echo ""

# Option 2: systemd (user level)
UNIT_DIR="$HOME/.config/systemd/user"
mkdir -p "$UNIT_DIR"

cat > "$UNIT_DIR/gakms-news.service" << EOF
[Unit]
Description=GAKMS Daily News Pipeline
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=$PROJECT_DIR
Environment="HF_HOME=$PROJECT_DIR/.cache/hf"
Environment="VLLM_BASE_URL=http://localhost:8013/v1"
Environment="VLLM_MODEL=Qwen/Qwen3.5-35B-A3B-FP8"
ExecStart=$VENV $PIPELINE --hours 12
StandardOutput=append:$LOG_DIR/pipeline.log
StandardError=append:$LOG_DIR/pipeline.log
EOF

cat > "$UNIT_DIR/gakms-news.timer" << EOF
[Unit]
Description=GAKMS News Timer — 10AM/10PM KST

[Timer]
OnCalendar=*-*-* 01:00:00
OnCalendar=*-*-* 13:00:00
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
EOF

echo "=== Option 2: systemd user timer ==="
echo "Files created:"
echo "  $UNIT_DIR/gakms-news.service"
echo "  $UNIT_DIR/gakms-news.timer"
echo ""
echo "Enable with:"
echo "  systemctl --user daemon-reload"
echo "  systemctl --user enable --now gakms-news.timer"
echo "  systemctl --user status gakms-news.timer"
echo ""
echo "Manual run:"
echo "  systemctl --user start gakms-news.service"
echo ""
echo "View logs:"
echo "  journalctl --user -u gakms-news.service -f"
echo "  ls -la $LOG_DIR/"
