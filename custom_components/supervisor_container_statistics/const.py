"""Constants for supervisor_container_statistics."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "supervisor_container_statistics"

# Keys as returned by the Supervisor's per-container stats endpoints
# (/addons/{slug}/stats, /core/stats, /supervisor/stats).
ATTR_CPU_PERCENT = "cpu_percent"
ATTR_MEMORY_USAGE = "memory_usage"
ATTR_NETWORK_RX = "network_rx"
ATTR_NETWORK_TX = "network_tx"
ATTR_BLK_READ = "blk_read"
ATTR_BLK_WRITE = "blk_write"
