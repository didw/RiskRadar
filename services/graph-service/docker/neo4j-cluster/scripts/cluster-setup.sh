#!/bin/bash

# Neo4j Enterprise Cluster Setup Script
# RiskRadar Graph Service

set -e

echo "🚀 Neo4j Enterprise Cluster Setup Starting..."

# Configuration
COMPOSE_FILE="docker-compose.cluster.yml"
CLUSTER_NAME="riskradar-neo4j"
TIMEOUT=300  # 5 minutes

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if Neo4j Enterprise license is accepted
    if [ -z "$NEO4J_ACCEPT_LICENSE_AGREEMENT" ]; then
        log_warn "Neo4j Enterprise license must be accepted"
        log_warn "Set NEO4J_ACCEPT_LICENSE_AGREEMENT=yes environment variable"
        export NEO4J_ACCEPT_LICENSE_AGREEMENT=yes
    fi
    
    log_info "Prerequisites check passed"
}

# Clean up existing containers
cleanup() {
    log_info "Cleaning up existing containers..."
    docker-compose -f $COMPOSE_FILE down -v --remove-orphans 2>/dev/null || true
    
    # Remove orphaned volumes
    docker volume prune -f 2>/dev/null || true
    
    log_info "Cleanup completed"
}

# Start cluster
start_cluster() {
    log_info "Starting Neo4j Enterprise Cluster..."
    
    # Start core servers first
    log_info "Starting core servers..."
    docker-compose -f $COMPOSE_FILE up -d neo4j-core-1 neo4j-core-2 neo4j-core-3
    
    # Wait for core cluster formation
    log_info "Waiting for core cluster formation..."
    sleep 30
    
    # Check core cluster status
    for i in {1..30}; do
        if check_cluster_status; then
            log_info "Core cluster formed successfully"
            break
        fi
        log_info "Waiting for cluster formation... ($i/30)"
        sleep 10
    done
    
    # Start read replica
    log_info "Starting read replica..."
    docker-compose -f $COMPOSE_FILE up -d neo4j-replica-1
    
    # Start load balancer
    log_info "Starting load balancer..."
    docker-compose -f $COMPOSE_FILE up -d neo4j-proxy
    
    log_info "Cluster startup completed"
}

# Check cluster status
check_cluster_status() {
    local core1_status=$(docker exec neo4j-core-1 cypher-shell -u neo4j -p riskradar2024 "SHOW SERVERS" 2>/dev/null | grep -c "Enabled" || echo "0")
    
    if [ "$core1_status" -ge 3 ]; then
        return 0
    else
        return 1
    fi
}

# Wait for cluster to be ready
wait_for_cluster() {
    log_info "Waiting for cluster to be ready..."
    
    local max_attempts=60
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log_info "Checking cluster health... ($attempt/$max_attempts)"
        
        if check_all_services_healthy; then
            log_info "✅ Cluster is healthy and ready!"
            return 0
        fi
        
        sleep 5
        ((attempt++))
    done
    
    log_error "❌ Cluster failed to become ready within timeout"
    return 1
}

# Check all services health
check_all_services_healthy() {
    local services=("neo4j-core-1" "neo4j-core-2" "neo4j-core-3" "neo4j-replica-1")
    
    for service in "${services[@]}"; do
        if ! docker exec $service cypher-shell -u neo4j -p riskradar2024 "RETURN 1" &>/dev/null; then
            return 1
        fi
    done
    
    # Check HAProxy
    if ! curl -s http://localhost:8080/health &>/dev/null; then
        return 1
    fi
    
    return 0
}

# Initialize cluster
initialize_cluster() {
    log_info "Initializing cluster..."
    
    # Create default graph database
    docker exec neo4j-core-1 cypher-shell -u neo4j -p riskradar2024 \
        "CREATE DATABASE IF NOT EXISTS graph" 2>/dev/null || true
    
    # Install APOC and GDS plugins
    log_info "Installing plugins..."
    install_plugins
    
    # Set up monitoring
    log_info "Setting up monitoring..."
    setup_monitoring
    
    log_info "Cluster initialization completed"
}

# Install plugins
install_plugins() {
    local plugins=("neo4j-core-1" "neo4j-core-2" "neo4j-core-3" "neo4j-replica-1")
    
    for service in "${plugins[@]}"; do
        log_info "Installing plugins on $service..."
        
        # Download APOC
        docker exec $service sh -c '
            cd /var/lib/neo4j/plugins &&
            curl -L -O https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/download/5.0.0/apoc-5.0.0-core.jar
        ' 2>/dev/null || log_warn "Failed to install APOC on $service"
        
        # Download GDS
        docker exec $service sh -c '
            cd /var/lib/neo4j/plugins &&
            curl -L -O https://github.com/neo4j/graph-data-science/releases/download/2.0.0/neo4j-graph-data-science-2.0.0.jar
        ' 2>/dev/null || log_warn "Failed to install GDS on $service"
    done
}

# Setup monitoring
setup_monitoring() {
    # Create monitoring endpoints
    log_info "Monitoring endpoints:"
    log_info "  - Neo4j Browser: http://localhost:7474"
    log_info "  - HAProxy Stats: http://localhost:8404/stats"
    log_info "  - Health Check: http://localhost:8080/health"
    log_info "  - Prometheus Metrics: http://localhost:2004/metrics"
}

# Show cluster information
show_cluster_info() {
    log_info "🎉 Neo4j Enterprise Cluster is ready!"
    echo
    echo "Cluster Information:"
    echo "==================="
    echo "Cluster Name: $CLUSTER_NAME"
    echo "Core Servers: 3"
    echo "Read Replicas: 1"
    echo
    echo "Connection Endpoints:"
    echo "-------------------"
    echo "Primary (Write):  bolt://localhost:7687"
    echo "Read-only:       bolt://localhost:7688"
    echo "HTTP Browser:    http://localhost:7474"
    echo
    echo "Load Balancer:"
    echo "-------------"
    echo "HAProxy Stats:   http://localhost:8404/stats"
    echo "Health Check:    http://localhost:8080/health"
    echo
    echo "Credentials:"
    echo "-----------"
    echo "Username: neo4j"
    echo "Password: riskradar2024"
    echo
    echo "Monitoring:"
    echo "----------"
    echo "Prometheus:      http://localhost:2004/metrics"
    echo "JMX Port:        3637"
    echo
    echo "Management Commands:"
    echo "------------------"
    echo "View cluster:    docker exec neo4j-core-1 cypher-shell -u neo4j -p riskradar2024 'SHOW SERVERS'"
    echo "View databases:  docker exec neo4j-core-1 cypher-shell -u neo4j -p riskradar2024 'SHOW DATABASES'"
    echo "Stop cluster:    docker-compose -f docker-compose.cluster.yml down"
    echo
}

# Backup cluster
backup_cluster() {
    log_info "Creating cluster backup..."
    
    local backup_dir="./backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup from core-1
    docker exec neo4j-core-1 neo4j-admin dump --database=graph --to=/var/lib/neo4j/backup/graph_backup.dump
    docker cp neo4j-core-1:/var/lib/neo4j/backup/graph_backup.dump "$backup_dir/"
    
    log_info "Backup created at: $backup_dir"
}

# Main execution
main() {
    case "${1:-start}" in
        "start")
            check_prerequisites
            cleanup
            start_cluster
            wait_for_cluster
            initialize_cluster
            show_cluster_info
            ;;
        "stop")
            log_info "Stopping cluster..."
            docker-compose -f $COMPOSE_FILE down
            log_info "Cluster stopped"
            ;;
        "restart")
            log_info "Restarting cluster..."
            docker-compose -f $COMPOSE_FILE restart
            wait_for_cluster
            log_info "Cluster restarted"
            ;;
        "status")
            if check_all_services_healthy; then
                log_info "✅ Cluster is healthy"
                docker exec neo4j-core-1 cypher-shell -u neo4j -p riskradar2024 "SHOW SERVERS"
            else
                log_error "❌ Cluster is not healthy"
            fi
            ;;
        "backup")
            backup_cluster
            ;;
        "clean")
            cleanup
            log_info "Cluster cleaned"
            ;;
        *)
            echo "Usage: $0 {start|stop|restart|status|backup|clean}"
            echo
            echo "Commands:"
            echo "  start   - Start the Neo4j cluster"
            echo "  stop    - Stop the Neo4j cluster"
            echo "  restart - Restart the Neo4j cluster"
            echo "  status  - Check cluster health"
            echo "  backup  - Create a backup"
            echo "  clean   - Clean up all containers and volumes"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"