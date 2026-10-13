#!/bin/bash
# Lịch chạy scrumbot trên máy Mac này (bot spec §7, confirm.md D54, A71).
#   scripts/lich-chay.sh install    cài lịch: 8h30 và mỗi 30 phút 9h00–17h30, thứ Hai–thứ Sáu
#   scripts/lich-chay.sh uninstall  gỡ lịch: bot không chạy nền nữa
#   scripts/lich-chay.sh status     lịch có đang bật không, và các dòng log mới nhất
#   scripts/lich-chay.sh run-now    chạy ngay một lượt (để macOS hỏi quyền truy cập Desktop lần đầu)
set -euo pipefail

LABEL="com.scrumbot.auto"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
DOMAIN="gui/$(id -u)"
BIN="$REPO/.venv/bin/scrumbot"
LOGS="$REPO/state/log"

calendar_entries() {
  local day hour minute
  for day in 1 2 3 4 5; do
    printf '    <dict><key>Weekday</key><integer>%d</integer><key>Hour</key><integer>8</integer><key>Minute</key><integer>30</integer></dict>\n' "$day"
    for hour in 9 10 11 12 13 14 15 16 17; do
      for minute in 0 30; do
        printf '    <dict><key>Weekday</key><integer>%d</integer><key>Hour</key><integer>%d</integer><key>Minute</key><integer>%d</integer></dict>\n' "$day" "$hour" "$minute"
      done
    done
  done
}

install() {
  if [ ! -x "$BIN" ]; then
    echo "Không thấy $BIN. Chạy 'uv sync' trong $REPO trước." >&2
    exit 2
  fi
  mkdir -p "$LOGS" "$(dirname "$PLIST")"
  cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$BIN</string>
    <string>auto</string>
  </array>
  <key>WorkingDirectory</key><string>$REPO</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key><string>$HOME/.gemini/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    <key>LANG</key><string>en_US.UTF-8</string>
  </dict>
  <key>StartCalendarInterval</key>
  <array>
$(calendar_entries)
  </array>
  <key>StandardOutPath</key><string>$LOGS/launchd.out.log</string>
  <key>StandardErrorPath</key><string>$LOGS/launchd.err.log</string>
</dict>
</plist>
PLIST
  launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
  launchctl bootstrap "$DOMAIN" "$PLIST"
  echo "Đã cài lịch: $PLIST"
  echo "Chạy thử một lượt ngay: scripts/lich-chay.sh run-now (macOS có thể hỏi quyền truy cập Desktop: bấm Allow)."
}

uninstall() {
  launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
  rm -f "$PLIST"
  echo "Đã gỡ lịch; scrumbot không chạy nền nữa."
}

status() {
  if launchctl print "$DOMAIN/$LABEL" >/dev/null 2>&1; then
    echo "Lịch đang bật ($PLIST)."
    launchctl print "$DOMAIN/$LABEL" | grep -E "state =|last exit code|runs =" || true
  else
    echo "Lịch chưa cài."
  fi
  local today="$LOGS/scrumbot-$(date +%Y-%m-%d).log"
  if [ -f "$today" ]; then
    echo "--- $today"
    tail -n 10 "$today"
  fi
  if [ -s "$LOGS/launchd.err.log" ]; then
    echo "--- $LOGS/launchd.err.log"
    tail -n 5 "$LOGS/launchd.err.log"
  fi
}

run_now() {
  launchctl kickstart -k "$DOMAIN/$LABEL"
  echo "Đã chạy một lượt; xem kết quả bằng: scripts/lich-chay.sh status"
}

case "${1:-}" in
  install) install ;;
  uninstall) uninstall ;;
  status) status ;;
  run-now) run_now ;;
  *) echo "Dùng: $0 install|uninstall|status|run-now" >&2; exit 2 ;;
esac
