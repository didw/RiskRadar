#!/bin/bash

# Setup Daily Report Cron Job
# This script sets up automatic daily report generation

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPORT_SCRIPT="$SCRIPT_DIR/generate_daily_report.py"
LOG_DIR="$SCRIPT_DIR/../logs"
REPORT_DIR="$SCRIPT_DIR/../reports"

# Create directories if they don't exist
mkdir -p "$LOG_DIR"
mkdir -p "$REPORT_DIR"

# Create wrapper script for cron
cat > "$SCRIPT_DIR/run_daily_report.sh" << EOF
#!/bin/bash
# Daily Report Runner

cd "$SCRIPT_DIR/.."
source venv/bin/activate 2>/dev/null || true

# Generate report and save to file
REPORT_DATE=\$(date +%Y%m%d)
REPORT_FILE="$REPORT_DIR/daily_report_\${REPORT_DATE}.txt"

python "$REPORT_SCRIPT" > "\$REPORT_FILE" 2>&1

# Also keep last 7 days of reports
find "$REPORT_DIR" -name "daily_report_*.txt" -mtime +7 -delete

# Log execution
echo "\$(date '+%Y-%m-%d %H:%M:%S') - Daily report generated: \$REPORT_FILE" >> "$LOG_DIR/daily_report.log"
EOF

chmod +x "$SCRIPT_DIR/run_daily_report.sh"

# Add to crontab (runs at 9 AM every day)
echo "To add daily report to cron, run:"
echo ""
echo "  crontab -e"
echo ""
echo "Then add this line:"
echo ""
echo "  0 9 * * * $SCRIPT_DIR/run_daily_report.sh"
echo ""
echo "Or run it manually:"
echo ""
echo "  $SCRIPT_DIR/run_daily_report.sh"
echo ""

# Run once now to test
echo "Running test report generation..."
"$SCRIPT_DIR/run_daily_report.sh"

echo "Setup complete!"
echo "Check the report at: $REPORT_DIR/daily_report_$(date +%Y%m%d).txt"