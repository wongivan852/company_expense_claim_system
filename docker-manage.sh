#!/bin/bash

# Docker management script for Company Expense Claim System

case "$1" in
    "migrate")
        echo "🔄 Running database migrations..."
        docker-compose exec web python manage.py migrate
        ;;
    "collectstatic")
        echo "📦 Collecting static files..."
        docker-compose exec web python manage.py collectstatic --noinput
        ;;
    "createsuperuser")
        echo "👤 Creating superuser..."
        docker-compose exec web python manage.py createsuperuser
        ;;
    "shell")
        echo "🐚 Opening Django shell..."
        docker-compose exec web python manage.py shell
        ;;
    "logs")
        echo "📋 Showing application logs..."
        docker-compose logs -f web
        ;;
    "logs-redis")
        echo "📋 Showing Redis logs..."
        docker-compose logs -f redis
        ;;
    "restart")
        echo "🔄 Restarting application..."
        docker-compose restart web
        ;;
    "rebuild")
        echo "🔨 Rebuilding and restarting..."
        docker-compose up --build -d
        ;;
    "stop")
        echo "⏹️ Stopping application..."
        docker-compose down
        ;;
    "status")
        echo "📊 Container status:"
        docker-compose ps
        ;;
    "backup-db")
        echo "💾 Backing up SQLite database..."
        mkdir -p backups
        docker-compose exec web cp /app/data/db.sqlite3 /app/backups/db_$(date +%Y%m%d_%H%M%S).sqlite3
        echo "✅ Database backup completed"
        ;;
    "clean")
        echo "🧹 Cleaning up Docker resources..."
        docker-compose down -v
        docker system prune -f
        echo "✅ Cleanup completed"
        ;;
    *)
        echo "🐳 Company Expense Claim System - Docker Management"
        echo ""
        echo "Available commands:"
        echo "  migrate        - Run database migrations"
        echo "  collectstatic  - Collect static files"
        echo "  createsuperuser- Create superuser account"
        echo "  shell          - Open Django shell"
        echo "  logs           - Show application logs"
        echo "  logs-redis     - Show Redis logs"
        echo "  restart        - Restart application container"
        echo "  rebuild        - Rebuild and restart"
        echo "  stop           - Stop all containers"
        echo "  status         - Show container status"
        echo "  backup-db      - Backup SQLite database"
        echo "  clean          - Clean up Docker resources"
        echo ""
        echo "Usage: ./docker-manage.sh <command>"
        ;;
esac
