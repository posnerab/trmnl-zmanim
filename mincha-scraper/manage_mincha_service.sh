#!/bin/bash

# Mincha Scraper Service Management Script

case "$1" in
    start)
        echo "Starting Mincha scraper timer..."
        sudo systemctl start mincha-scraper.timer
        sudo systemctl status mincha-scraper.timer
        ;;
    stop)
        echo "Stopping Mincha scraper timer..."
        sudo systemctl stop mincha-scraper.timer
        ;;
    status)
        echo "Mincha scraper timer status:"
        sudo systemctl status mincha-scraper.timer
        echo ""
        echo "Next run time:"
        sudo systemctl list-timers mincha-scraper.timer
        ;;
    run-now)
        echo "Running Mincha scraper now..."
        sudo systemctl start mincha-scraper.service
        echo ""
        echo "Latest result:"
        if [ -f "mincha_today.json" ]; then
            cat mincha_today.json
        else
            echo "No result file found"
        fi
        ;;
    logs)
        echo "Recent Mincha scraper logs:"
        sudo journalctl -u mincha-scraper.service --since "1 hour ago" -n 20
        ;;
    enable)
        echo "Enabling Mincha scraper timer at startup..."
        sudo systemctl enable mincha-scraper.timer
        ;;
    disable)
        echo "Disabling Mincha scraper timer at startup..."
        sudo systemctl disable mincha-scraper.timer
        ;;
    *)
        echo "Usage: $0 {start|stop|status|run-now|logs|enable|disable}"
        echo ""
        echo "Commands:"
        echo "  start     - Start the timer"
        echo "  stop      - Stop the timer"
        echo "  status    - Show timer status and next run time"
        echo "  run-now   - Run the scraper immediately"
        echo "  logs      - Show recent logs"
        echo "  enable    - Enable timer at startup"
        echo "  disable   - Disable timer at startup"
        exit 1
        ;;
esac
