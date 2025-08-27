# Company Expense Claim System - Docker Setup

This guide explains how to run the Company Expense Claim System using Docker with SQLite database on port 8084.

## Prerequisites

- Docker Engine installed and running
- Docker Compose installed
- At least 2GB free disk space
- Port 8084 available on your system

## Quick Start

### 1. Clone/Navigate to the project directory
```bash
cd /path/to/company_expense_claim_system
```

### 2. Start the application
```bash
./docker-startup.sh
```

The application will be available at:
- **Main Application**: http://localhost:8084/
- **Admin Interface**: http://localhost:8084/admin/
- **API Documentation**: http://localhost:8084/docs/ (if FastAPI is enabled)

## Configuration

### Database
- **Type**: SQLite
- **Location**: `./data/db.sqlite3` (mounted as Docker volume)
- **Backup**: Automatically preserved between container restarts

### Ports
- **Application**: 8084 (configurable in docker-compose.yml)
- **Redis**: 6379 (internal, can be exposed if needed)

### Volumes
The following directories are mounted as volumes:
- `./data` - SQLite database
- `./media` - User uploaded files
- `./uploads` - Document uploads
- `./logs` - Application logs

## Management Commands

### Using the management script:
```bash
# Run database migrations
./docker-manage.sh migrate

# Create superuser
./docker-manage.sh createsuperuser

# View logs
./docker-manage.sh logs

# Restart application
./docker-manage.sh restart

# Stop application
./docker-manage.sh stop

# View all available commands
./docker-manage.sh
```

### Manual Docker commands:
```bash
# Build and start
docker-compose up --build -d

# View logs
docker-compose logs -f web

# Stop containers
docker-compose down

# Restart specific service
docker-compose restart web

# Execute commands in container
docker-compose exec web python manage.py shell
```

## Initial Setup

After starting the application for the first time:

1. **Run migrations** (if not done automatically):
   ```bash
   ./docker-manage.sh migrate
   ```

2. **Create a superuser**:
   ```bash
   ./docker-manage.sh createsuperuser
   ```

3. **Access the application**:
   - Go to http://localhost:8084/
   - For admin: http://localhost:8084/admin/

## Database Management

### Backup Database
```bash
./docker-manage.sh backup-db
```
This creates a timestamped backup in the `backups/` directory.

### Restore Database
```bash
# Stop the application
./docker-manage.sh stop

# Replace the database file
cp backups/db_TIMESTAMP.sqlite3 data/db.sqlite3

# Start the application
./docker-startup.sh
```

## Troubleshooting

### Port 8084 already in use
Change the port in `docker-compose.yml`:
```yaml
ports:
  - "8085:8084"  # Use 8085 instead
```

### Container won't start
1. Check Docker is running: `docker info`
2. Check port availability: `lsof -i :8084`
3. View container logs: `./docker-manage.sh logs`

### Database issues
1. Check database file permissions: `ls -la data/`
2. Run migrations: `./docker-manage.sh migrate`
3. Check logs for SQL errors: `./docker-manage.sh logs`

### Redis connection issues
1. Check Redis container: `docker-compose ps redis`
2. View Redis logs: `./docker-manage.sh logs-redis`

## Development

### Local development with Docker:
1. Mount source code as volume in docker-compose.yml
2. Set DEBUG=True in environment variables
3. Use `docker-compose up` (without -d) to see real-time logs

### Debugging:
```bash
# Enter container shell
docker-compose exec web bash

# Access Django shell
./docker-manage.sh shell

# View real-time logs
./docker-manage.sh logs
```

## Production Considerations

1. **Security**:
   - Change SECRET_KEY in docker-compose.yml
   - Set DEBUG=False
   - Configure proper ALLOWED_HOSTS
   - Use HTTPS (enable Nginx service)

2. **Performance**:
   - Enable Redis caching
   - Configure proper resource limits
   - Use production WSGI server (Gunicorn)

3. **Backup**:
   - Regular database backups
   - Volume backups for media files
   - Log rotation

## File Structure

```
company_expense_claim_system/
├── Dockerfile                 # Main application container
├── docker-compose.yml         # Multi-service orchestration
├── docker-startup.sh          # Quick start script
├── docker-manage.sh           # Management utilities
├── .dockerignore              # Exclude files from build
├── .env.docker               # Docker-specific environment
├── data/                     # SQLite database volume
├── media/                    # User uploads volume
├── uploads/                  # Document uploads volume
├── logs/                     # Application logs volume
└── backups/                  # Database backups
```

## Support

For issues or questions:
1. Check the logs: `./docker-manage.sh logs`
2. Verify container status: `./docker-manage.sh status`
3. Review this documentation
4. Check Django/Docker documentation
