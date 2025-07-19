#!/bin/bash
# Daily Report Runner

cd "/home/jyyang/Projects/RiskRadar/scripts/.."
source venv/bin/activate 2>/dev/null || true

# Generate report and save to file
REPORT_DATE=$(date +%Y%m%d)
REPORT_FILE="/home/jyyang/Projects/RiskRadar/scripts/../reports/daily_report_${REPORT_DATE}.txt"

python "/home/jyyang/Projects/RiskRadar/scripts/generate_daily_report.py" > "$REPORT_FILE" 2>&1

# Also keep last 7 days of reports
find "/home/jyyang/Projects/RiskRadar/scripts/../reports" -name "daily_report_*.txt" -mtime +7 -delete

# Log execution
echo "$(date '+%Y-%m-%d %H:%M:%S') - Daily report generated: $REPORT_FILE" >> "/home/jyyang/Projects/RiskRadar/scripts/../logs/daily_report.log"
