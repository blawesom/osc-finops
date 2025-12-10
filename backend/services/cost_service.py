"""Cost service for fetching current resources and calculating costs."""
import re
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
from backend.services.catalog_service import get_catalog
from backend.utils.api_call_logger import create_logged_gateway, process_and_log_api_call

# Constants
HOURS_PER_MONTH = (365 * 24) / 12  # 730 hours per month


class CostCache:
    """In-memory cost cache with TTL."""
    
    def __init__(self, ttl_seconds: int = 300):  # 5 minutes default
        self._cache: Dict[str, Dict] = {}
        self._timestamps: Dict[str, datetime] = {}
        self.ttl_seconds = ttl_seconds
    
    def _make_key(self, account_id: str, region: str, include_oos: bool) -> str:
        """Create cache key from parameters."""
        return f"{account_id}:{region}:oos_{include_oos}"
    
    def get(self, account_id: str, region: str, include_oos: bool) -> Optional[Dict]:
        """Get cost data from cache if not expired."""
        key = self._make_key(account_id, region, include_oos)
        
        if key not in self._cache:
            return None
        
        timestamp = self._timestamps.get(key)
        if timestamp and datetime.utcnow() - timestamp < timedelta(seconds=self.ttl_seconds):
            return self._cache[key]
        
        # Cache expired
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        return None
    
    def set(self, account_id: str, region: str, include_oos: bool, data: Dict) -> None:
        """Store cost data in cache with current timestamp."""
        key = self._make_key(account_id, region, include_oos)
        self._cache[key] = data
        self._timestamps[key] = datetime.utcnow()
    
    def invalidate(self, account_id: Optional[str] = None, region: Optional[str] = None) -> None:
        """Invalidate cache for specific account/region or all."""
        if account_id or region:
            keys_to_remove = []
            for key in self._cache.keys():
                if account_id and account_id not in key:
                    continue
                if region and region not in key:
                    continue
                keys_to_remove.append(key)
            
            for key in keys_to_remove:
                self._cache.pop(key, None)
                self._timestamps.pop(key, None)
        else:
            self._cache.clear()
            self._timestamps.clear()


# Global cost cache instance
cost_cache = CostCache(ttl_seconds=300)  # 5 minutes


def fetch_resources(
    access_key: str,
    secret_key: str,
    region: str,
    include_oos: bool = False
) -> Dict:
    """
    Fetch all resource types from Outscale API.
    
    Args:
        access_key: Outscale access key
        secret_key: Outscale secret key
        region: Region name
        include_oos: If True, fetch OOS buckets (can take up to 10 minutes, default: False)
    
    Returns:
        Dictionary with resources list and metadata
    
    Raises:
        Exception: If API call fails
    """
    try:
        # Create gateway with credentials and logging enabled
        gateway = create_logged_gateway(
            access_key=access_key,
            secret_key=secret_key,
            region=region
        )
        
        resources = []
        
        # Fetch VMs
        try:
            vms_response = process_and_log_api_call(
                gateway=gateway,
                api_method="ReadVms",
                call_func=lambda: gateway.ReadVms()
            )
            vms = vms_response.get("Vms", [])
            for vm in vms:
                resources.append({
                    "resource_id": vm.get("VmId", ""),
                    "resource_type": "Vm",
                    "region": region,
                    "zone": vm.get("Placement", {}).get("SubregionName", ""),
                    "specs": {
                        "vm_type": vm.get("VmType", ""),
                        "state": vm.get("State", ""),
                        "tags": vm.get("Tags", []),
                        "tenancy": vm.get("Placement", {}).get("Tenancy", "default"),
                        "image_id": vm.get("ImageId", ""),
                        "keypair_name": vm.get("KeypairName", ""),
                        "security_groups": vm.get("SecurityGroups", []),
                        "nics": vm.get("Nics", []),
                        "architecture": vm.get("Architecture", ""),
                        "root_device_type": vm.get("RootDeviceType", ""),
                        "bsu_optimized": vm.get("BsuOptimized", False),
                        "performance": vm.get("Performance", ""),
                        "vm_initiated_shutdown_behavior": vm.get("VmInitiatedShutdownBehavior", ""),
                        "is_source_dest_checked": vm.get("IsSourceDestChecked", False),
                        "private_dns_name": vm.get("PrivateDnsName", ""),
                        "public_dns_name": vm.get("PublicDnsName", ""),
                        "private_ip": vm.get("PrivateIp", ""),
                        "public_ip": vm.get("PublicIp", ""),
                        "reservation_id": vm.get("ReservationId", ""),
                        "subnet_id": vm.get("SubnetId", ""),
                        "vpc_id": vm.get("VpcId", ""),
                    },
                    "tags": vm.get("Tags", [])
                })
        except Exception as e:
            # Log error but continue with other resources
            pass
        
        # Fetch Volumes
        try:
            volumes_response = process_and_log_api_call(
                gateway=gateway,
                api_method="ReadVolumes",
                call_func=lambda: gateway.ReadVolumes()
            )
            volumes = volumes_response.get("Volumes", [])
            for volume in volumes:
                resources.append({
                    "resource_id": volume.get("VolumeId", ""),
                    "resource_type": "Volume",
                    "region": region,
                    "zone": volume.get("SubregionName", ""),
                    "specs": {
                        "size": volume.get("Size", 0),
                        "volume_type": volume.get("VolumeType", ""),
                        "iops": volume.get("Iops", 0),
                        "state": volume.get("State", ""),
                        "snapshot_id": volume.get("SnapshotId", ""),
                        "creation_date": volume.get("CreationDate", ""),
                        "linked_volumes": volume.get("LinkedVolumes", []),
                    },
                    "tags": volume.get("Tags", [])
                })
        except Exception as e:
            pass
        
        # Fetch Snapshots
        try:
            snapshots_response = process_and_log_api_call(
                gateway=gateway,
                api_method="ReadSnapshots",
                call_func=lambda: gateway.ReadSnapshots()
            )
            snapshots = snapshots_response.get("Snapshots", [])
            for snapshot in snapshots:
                resources.append({
                    "resource_id": snapshot.get("SnapshotId", ""),
                    "resource_type": "Snapshot",
                    "region": region,
                    "zone": snapshot.get("SubregionName", ""),
                    "specs": {
                        "volume_id": snapshot.get("VolumeId", ""),
                        "size": snapshot.get("VolumeSize", 0),
                        "state": snapshot.get("State", ""),
                        "creation_date": snapshot.get("CreationDate", ""),
                        "progress": snapshot.get("Progress", ""),
                    },
                    "tags": snapshot.get("Tags", [])
                })
        except Exception as e:
            pass
        
        # Fetch Public IPs
        try:
            public_ips_response = process_and_log_api_call(
                gateway=gateway,
                api_method="ReadPublicIps",
                call_func=lambda: gateway.ReadPublicIps()
            )
            public_ips = public_ips_response.get("PublicIps", [])
            for public_ip in public_ips:
                resources.append({
                    "resource_id": public_ip.get("PublicIp", ""),
                    "resource_type": "PublicIp",
                    "region": region,
                    "zone": public_ip.get("SubregionName", ""),
                    "specs": {
                        "public_ip": public_ip.get("PublicIp", ""),
                        "link_public_ip_id": public_ip.get("LinkPublicIpId", ""),
                        "nic_id": public_ip.get("NicId", ""),
                        "vm_id": public_ip.get("VmId", ""),
                    },
                    "tags": public_ip.get("Tags", [])
                })
        except Exception as e:
            pass
        
        # Fetch NAT Services
        try:
            nat_services_response = process_and_log_api_call(
                gateway=gateway,
                api_method="ReadNatServices",
                call_func=lambda: gateway.ReadNatServices()
            )
            nat_services = nat_services_response.get("NatServices", [])
            for nat_service in nat_services:
                resources.append({
                    "resource_id": nat_service.get("NatServiceId", ""),
                    "resource_type": "NatService",
                    "region": region,
                    "zone": nat_service.get("SubregionName", ""),
                    "specs": {
                        "nat_service_id": nat_service.get("NatServiceId", ""),
                        "public_ips": nat_service.get("PublicIps", []),
                        "subnet_id": nat_service.get("SubnetId", ""),
                        "vpc_id": nat_service.get("VpcId", ""),
                        "state": nat_service.get("State", ""),
                        "tags": nat_service.get("Tags", []),
                    },
                    "tags": nat_service.get("Tags", [])
                })
        except Exception as e:
            pass
        
        # Fetch Load Balancers
        try:
            load_balancers_response = process_and_log_api_call(
                gateway=gateway,
                api_method="ReadLoadBalancers",
                call_func=lambda: gateway.ReadLoadBalancers()
            )
            load_balancers = load_balancers_response.get("LoadBalancers", [])
            for lb in load_balancers:
                resources.append({
                    "resource_id": lb.get("LoadBalancerName", ""),
                    "resource_type": "LoadBalancer",
                    "region": region,
                    "zone": lb.get("SubregionNames", [""])[0] if lb.get("SubregionNames") else "",
                    "specs": {
                        "load_balancer_name": lb.get("LoadBalancerName", ""),
                        "dns_name": lb.get("DnsName", ""),
                        "load_balancer_type": lb.get("LoadBalancerType", ""),
                        "state": lb.get("State", ""),
                        "subnets": lb.get("Subnets", []),
                        "security_groups": lb.get("SecurityGroups", []),
                        "listeners": lb.get("Listeners", []),
                        "backend_vm_ids": lb.get("BackendVmIds", []),
                        "tags": lb.get("Tags", []),
                    },
                    "tags": lb.get("Tags", [])
                })
        except Exception as e:
            pass
        
        # Fetch VPNs
        try:
            vpns_response = process_and_log_api_call(
                gateway=gateway,
                api_method="ReadVpns",
                call_func=lambda: gateway.ReadVpns()
            )
            vpns = vpns_response.get("Vpns", [])
            for vpn in vpns:
                resources.append({
                    "resource_id": vpn.get("VpnConnectionId", ""),
                    "resource_type": "Vpn",
                    "region": region,
                    "zone": vpn.get("SubregionName", ""),
                    "specs": {
                        "vpn_connection_id": vpn.get("VpnConnectionId", ""),
                        "state": vpn.get("State", ""),
                        "vgw_id": vpn.get("VgwId", ""),
                        "vgw_route_table_id": vpn.get("VgwRouteTableId", ""),
                        "vgw_telemetries": vpn.get("VgwTelemetries", []),
                        "client_gateway_id": vpn.get("ClientGatewayId", ""),
                        "connection_type": vpn.get("ConnectionType", ""),
                        "static_routes_only": vpn.get("StaticRoutesOnly", False),
                        "tags": vpn.get("Tags", []),
                    },
                    "tags": vpn.get("Tags", [])
                })
        except Exception as e:
            pass
        
        # Fetch OOS buckets (only if include_oos=True, can take up to 10 minutes)
        if include_oos:
            try:
                oos_buckets_response = process_and_log_api_call(
                    gateway=gateway,
                    api_method="ReadOosBuckets",
                    call_func=lambda: gateway.ReadOosBuckets()
                )
                oos_buckets = oos_buckets_response.get("Buckets", [])
                for bucket in oos_buckets:
                    resources.append({
                        "resource_id": bucket.get("BucketName", ""),
                        "resource_type": "Oos",
                        "region": region,
                        "zone": "",  # OOS doesn't have zones
                        "specs": {
                            "bucket_name": bucket.get("BucketName", ""),
                            "creation_date": bucket.get("CreationDate", ""),
                            "region": bucket.get("Region", region),
                        },
                        "tags": bucket.get("Tags", [])
                    })
            except Exception as e:
                # OOS can fail or take very long, log but don't fail entire request
                pass
        
        # Get currency from catalog for this region
        currency = None
        try:
            catalog = get_catalog(region, force_refresh=False)
            currency = catalog.get("currency", "EUR")
        except Exception:
            currency = "EUR"
        
        return {
            "region": region,
            "currency": currency,
            "resources": resources,
            "resource_count": len(resources),
            "fetched_at": datetime.utcnow().isoformat(),
            "include_oos": include_oos
        }
    
    except Exception as e:
        raise Exception(f"Failed to fetch resources: {str(e)}")


def filter_resources_by_tags(resources: List[Dict], tag_filters: Optional[List[Dict]] = None) -> List[Dict]:
    """
    Filter resources by tag keys/values.
    
    Args:
        resources: List of resource dictionaries
        tag_filters: List of tag filters, each with "Key" and "Value" (AND logic)
    
    Returns:
        Filtered list of resources
    """
    if not tag_filters:
        return resources
    
    filtered = []
    for resource in resources:
        resource_tags = resource.get("tags", [])
        resource_tag_dict = {}
        for tag in resource_tags:
            key = tag.get("Key", "")
            value = tag.get("Value", "")
            resource_tag_dict[key] = value
        
        # Check if resource matches all tag filters (AND logic)
        matches_all = True
        for tag_filter in tag_filters:
            filter_key = tag_filter.get("Key", "")
            filter_value = tag_filter.get("Value", "")
            
            if filter_key not in resource_tag_dict:
                matches_all = False
                break
            
            if resource_tag_dict[filter_key] != filter_value:
                matches_all = False
                break
        
        if matches_all:
            filtered.append(resource)
    
    return filtered


def find_catalog_price(catalog: Dict, service: str, operation: str, resource_type: str, zone: str = "") -> Optional[float]:
    """
    Find catalog price for a resource using actual catalog structure.
    
    Args:
        catalog: Catalog dictionary with entries
        service: Service name (e.g., "TinaOS-FCU")
        operation: Operation name (e.g., "CreateVolume", "AllocateAddress")
        resource_type: Resource type (e.g., "PublicIp", "NatService", "LoadBalancer", "Vpn")
        zone: Zone name (optional, for filtering by SubregionName)
    
    Returns:
        Price in currency units (EUR/USD per hour), or None if not found
    """
    entries = catalog.get("entries", [])
    
    # Match on Service, Operation, and Type fields
    # Resource type matching can be flexible (exact match or contains)
    for entry in entries:
        entry_service = entry.get("Service", "") or entry.get("service", "")
        entry_operation = entry.get("Operation", "") or entry.get("operation", "")
        entry_type = entry.get("Type", "") or entry.get("type", "")
        entry_zone = entry.get("SubregionName", "") or entry.get("subregionName", "")
        
        # Match service and operation
        if entry_service == service and entry_operation == operation:
            # Match resource type (exact or contains)
            if resource_type in entry_type or entry_type == resource_type:
                # Optional zone filtering
                if not zone or entry_zone == zone or not entry_zone:
                    # UnitPrice is already in currency units (no conversion needed)
                    unit_price = entry.get("UnitPrice") or entry.get("unitPrice")
                    if unit_price is not None:
                        return float(unit_price)
    
    return None


def find_volume_storage_price(catalog: Dict, volume_type: str, zone: str = "") -> Optional[float]:
    """
    Find volume storage price from catalog using actual catalog structure.
    
    Args:
        catalog: Catalog dictionary with entries
        volume_type: Volume type (e.g., "standard", "io1", "gp2")
        zone: Zone name (optional)
    
    Returns:
        Price per GB per month in currency units, or None if not found
    """
    entries = catalog.get("entries", [])
    
    # Match Type: "BSU:VolumeUsage:{volume_type}" and Operation: "CreateVolume"
    type_pattern = f"BSU:VolumeUsage:{volume_type}"
    
    for entry in entries:
        entry_type = entry.get("Type", "") or entry.get("type", "")
        operation = entry.get("Operation", "") or entry.get("operation", "")
        
        if type_pattern in entry_type and operation == "CreateVolume":
            # UnitPrice is already in currency units (no conversion needed)
            unit_price = entry.get("UnitPrice") or entry.get("unitPrice")
            if unit_price is not None:
                return float(unit_price)
    return None


def find_volume_iops_price(catalog: Dict, volume_type: str, zone: str = "") -> Optional[float]:
    """
    Find volume IOPS price from catalog using actual catalog structure.
    
    Args:
        catalog: Catalog dictionary with entries
        volume_type: Volume type (e.g., "io1")
        zone: Zone name (optional)
    
    Returns:
        Price per IOPS per month in currency units, or None if not found
    """
    entries = catalog.get("entries", [])
    
    # Match Type: "BSU:VolumeIOPS:{volume_type}" and Operation: "CreateVolume"
    type_pattern = f"BSU:VolumeIOPS:{volume_type}"
    
    for entry in entries:
        entry_type = entry.get("Type", "") or entry.get("type", "")
        operation = entry.get("Operation", "") or entry.get("operation", "")
        
        if type_pattern in entry_type and operation == "CreateVolume":
            # UnitPrice is already in currency units (no conversion needed)
            unit_price = entry.get("UnitPrice") or entry.get("unitPrice")
            if unit_price is not None:
                return float(unit_price)
    return None


def find_snapshot_price(catalog: Dict, zone: str = "") -> Optional[float]:
    """
    Find snapshot storage price from catalog using actual catalog structure.
    
    Args:
        catalog: Catalog dictionary with entries
        zone: Zone name (optional)
    
    Returns:
        Price per GB per month in currency units, or None if not found
    """
    entries = catalog.get("entries", [])
    
    # Match Type: "Snapshot:Usage" or "Snapshot" and Operation: "Snapshot" or "CreateSnapshot"
    for entry in entries:
        entry_type = entry.get("Type", "") or entry.get("type", "")
        operation = entry.get("Operation", "") or entry.get("operation", "")
        
        # Match snapshot types
        if ("Snapshot:Usage" in entry_type or entry_type == "Snapshot") and \
           (operation == "Snapshot" or operation == "CreateSnapshot"):
            # UnitPrice is already in currency units (no conversion needed)
            unit_price = entry.get("UnitPrice") or entry.get("unitPrice")
            if unit_price is not None:
                return float(unit_price)
    return None


def calculate_vm_price(vm_type: str, catalog: Dict, region: str, tenancy: str = "default", flexible_gpus: List[Dict] = None) -> float:
    """
    Calculate VM price from catalog (reused from consumption service and reference implementation).
    
    Args:
        vm_type: VM type (e.g., "tinav4.c2r4" or "BoxUsage:t2.micro")
        catalog: Catalog dictionary with entries
        region: Region name
        tenancy: Tenancy type ("default" or "dedicated")
        flexible_gpus: List of flexible GPUs attached to this VM
    
    Returns:
        Price per hour in currency units
    """
    entries = catalog.get("entries", [])
    
    gen = None
    core_count = 0
    ram_count = 0
    perf = None
    gpu_count = 0
    gpu_model = ""
    
    # Parse VM type
    if vm_type.startswith("BoxUsage:"):
        # AWS-compatible type, would need VM_MAP for translation
        # For now, try to find direct catalog entry
        vm_type_short = vm_type.split(":")[1]
        for entry in entries:
            entry_type = entry.get("Type", "") or entry.get("type", "")
            operation = entry.get("Operation", "") or entry.get("operation", "")
            
            # Try to match BoxUsage types (may not be in catalog directly)
            if vm_type_short in entry_type and operation == "RunInstances-OD":
                unit_price = entry.get("UnitPrice") or entry.get("unitPrice")
                if unit_price is not None:
                    return float(unit_price)
        return 0.0
    elif vm_type.startswith("tinav"):
        # Parse tina type: tinavX.cXrXpX
        match = re.search(r'tinav(\d+)\.c(\d+)r(\d+)p(\d+)', vm_type)
        if match:
            gen = int(match.group(1))
            core_count = int(match.group(2))
            ram_count = int(match.group(3))
            perf = int(match.group(4))
    
    if gen is None:
        return 0.0
    
    # Look up prices from catalog using actual catalog structure
    core_price = 0.0
    ram_price = 0.0
    gpu_price = 0.0
    
    for entry in entries:
        entry_type = entry.get("Type", "") or entry.get("type", "")
        operation = entry.get("Operation", "") or entry.get("operation", "")
        
        # Match CustomCore: Type="CustomCore:v{gen}-p{perf}", Operation="RunInstances-OD"
        if f'CustomCore:v{gen}-p{perf}' in entry_type and operation == "RunInstances-OD":
            unit_price = entry.get("UnitPrice") or entry.get("unitPrice")
            if unit_price is not None:
                core_price = float(unit_price)
        # Match CustomRam: Type="CustomRam", Operation="RunInstances-OD"
        elif entry_type == "CustomRam" and operation == "RunInstances-OD":
            unit_price = entry.get("UnitPrice") or entry.get("unitPrice")
            if unit_price is not None:
                ram_price = float(unit_price)
        # Match GPU: Type="Gpu:attach:{gpu_model}", Operation="AllocateGpu"
        elif flexible_gpus and gpu_count > 0:
            if f'Gpu:attach:{gpu_model}' in entry_type and operation == "AllocateGpu":
                unit_price = entry.get("UnitPrice") or entry.get("unitPrice")
                if unit_price is not None:
                    gpu_price = float(unit_price)
    
    # Calculate base price
    unit_price = core_count * core_price + ram_count * ram_price + gpu_count * gpu_price
    
    # Apply dedicated instance factor if needed (osc-cost pattern)
    if tenancy == "dedicated":
        # Look up dedicated instance surplus from catalog
        # Match Type="DedicatedInstanceSurplus", Operation="RunInstances"
        # Factor is expressed as per thousand (‰), formula: 1.0 + (unit_price * 10.0)
        for entry in entries:
            entry_type = entry.get("Type", "") or entry.get("type", "")
            operation = entry.get("Operation", "") or entry.get("operation", "")
            
            if entry_type == "DedicatedInstanceSurplus" and operation == "RunInstances":
                unit_price_factor = entry.get("UnitPrice") or entry.get("unitPrice")
                if unit_price_factor is not None:
                    # UnitPrice is already in currency units, apply osc-cost formula
                    factor_vm_additional_cost = 1.0 + (float(unit_price_factor) * 10.0)
                    unit_price *= factor_vm_additional_cost
                break
    
    return unit_price


def calculate_vm_cost(vm: Dict, catalog: Dict, region: str, flexible_gpus: List[Dict] = None) -> Dict:
    """
    Calculate VM cost.
    
    Args:
        vm: VM resource dictionary
        catalog: Catalog dictionary
        region: Region name
        flexible_gpus: List of flexible GPUs (optional)
    
    Returns:
        Dictionary with cost_per_hour, cost_per_month, cost_per_year
    """
    specs = vm.get("specs", {})
    vm_type = specs.get("vm_type", "")
    tenancy = specs.get("tenancy", "default")
    
    cost_per_hour = calculate_vm_price(vm_type, catalog, region, tenancy, flexible_gpus)
    cost_per_month = cost_per_hour * HOURS_PER_MONTH
    cost_per_year = cost_per_month * 12
    
    return {
        "cost_per_hour": round(cost_per_hour, 4),
        "cost_per_month": round(cost_per_month, 2),
        "cost_per_year": round(cost_per_year, 2)
    }


def calculate_volume_cost(volume: Dict, catalog: Dict, region: str) -> Dict:
    """
    Calculate volume cost (storage + IOPS if applicable).
    Following osc-cost pattern: calculate monthly first, then convert to hourly.
    
    Args:
        volume: Volume resource dictionary
        catalog: Catalog dictionary
        region: Region name
    
    Returns:
        Dictionary with cost_per_hour, cost_per_month, cost_per_year
    """
    specs = volume.get("specs", {})
    volume_type = specs.get("volume_type", "standard")  # Default to standard if not specified
    size = specs.get("size", 0)
    iops = specs.get("iops", 0)
    zone = volume.get("zone", "")
    
    # Get storage price per GB per month (osc-cost pattern: BSU:VolumeUsage:{volume_type})
    storage_price_per_month = find_volume_storage_price(catalog, volume_type, zone) or 0.0
    
    # Calculate monthly storage cost
    storage_cost_per_month = size * storage_price_per_month if storage_price_per_month else 0.0
    
    # IOPS cost per month (for io1 volumes)
    iops_cost_per_month = 0.0
    if volume_type == "io1" and iops > 0:
        iops_price_per_month = find_volume_iops_price(catalog, volume_type, zone) or 0.0
        iops_cost_per_month = iops * iops_price_per_month if iops_price_per_month else 0.0
    
    # Total monthly cost
    cost_per_month = storage_cost_per_month + iops_cost_per_month
    
    # Convert to hourly and yearly (osc-cost pattern)
    cost_per_hour = cost_per_month / HOURS_PER_MONTH if cost_per_month > 0 else 0.0
    cost_per_year = cost_per_month * 12
    
    return {
        "cost_per_hour": round(cost_per_hour, 4),
        "cost_per_month": round(cost_per_month, 2),
        "cost_per_year": round(cost_per_year, 2)
    }


def calculate_snapshot_cost(snapshot: Dict, catalog: Dict, region: str) -> Dict:
    """
    Calculate snapshot cost.
    Following osc-cost pattern: calculate monthly first, then convert to hourly.
    
    Args:
        snapshot: Snapshot resource dictionary
        catalog: Catalog dictionary
        region: Region name
    
    Returns:
        Dictionary with cost_per_hour, cost_per_month, cost_per_year
    """
    specs = snapshot.get("specs", {})
    size = specs.get("size", 0)
    zone = snapshot.get("zone", "")
    
    # Get snapshot storage price per GB per month (osc-cost pattern: Snapshot)
    snapshot_price_per_month = find_snapshot_price(catalog, zone) or 0.0
    
    # Calculate monthly cost
    cost_per_month = size * snapshot_price_per_month if snapshot_price_per_month else 0.0
    
    # Convert to hourly and yearly (osc-cost pattern)
    cost_per_hour = cost_per_month / HOURS_PER_MONTH if cost_per_month > 0 else 0.0
    cost_per_year = cost_per_month * 12
    
    return {
        "cost_per_hour": round(cost_per_hour, 4),
        "cost_per_month": round(cost_per_month, 2),
        "cost_per_year": round(cost_per_year, 2)
    }


def calculate_public_ip_cost(public_ip: Dict, catalog: Dict, region: str) -> Dict:
    """
    Calculate public IP cost.
    
    Args:
        public_ip: Public IP resource dictionary
        catalog: Catalog dictionary
        region: Region name
    
    Returns:
        Dictionary with cost_per_hour, cost_per_month, cost_per_year
    """
    specs = public_ip.get("specs", {})
    nic_id = specs.get("nic_id", "")
    vm_id = specs.get("vm_id", "")
    zone = public_ip.get("zone", "")
    
    # Check if IP is attached (has nic_id or vm_id)
    is_attached = bool(nic_id or vm_id)
    
    if is_attached:
        # Attached IP pricing - Type: "ElasticIP:AdditionalAddress", Operation: "AssociateAddress" or "AssociateAddressVPC"
        price = find_catalog_price(
            catalog, "TinaOS-FCU", "AssociateAddress", "ElasticIP:AdditionalAddress", zone
        ) or find_catalog_price(
            catalog, "TinaOS-FCU", "AssociateAddressVPC", "ElasticIP:AdditionalAddress", zone
        ) or 0.0
    else:
        # Non-attached IP pricing - Type: "ElasticIP:IdleAddress"
        price = find_catalog_price(
            catalog, "TinaOS-FCU", "AssociateAddress", "ElasticIP:IdleAddress", zone
        ) or find_catalog_price(
            catalog, "TinaOS-FCU", "AssociateAddressVPC", "ElasticIP:IdleAddress", zone
        ) or 0.0
    
    cost_per_hour = price
    cost_per_month = cost_per_hour * HOURS_PER_MONTH
    cost_per_year = cost_per_month * 12
    
    return {
        "cost_per_hour": round(cost_per_hour, 4),
        "cost_per_month": round(cost_per_month, 2),
        "cost_per_year": round(cost_per_year, 2)
    }


def calculate_nat_service_cost(nat_service: Dict, catalog: Dict, region: str) -> Dict:
    """
    Calculate NAT service cost.
    
    Args:
        nat_service: NAT service resource dictionary
        catalog: Catalog dictionary
        region: Region name
    
    Returns:
        Dictionary with cost_per_hour, cost_per_month, cost_per_year
    """
    zone = nat_service.get("zone", "")
    
    # NAT Service - Type: "NatGatewayUsage", Operation: "CreateNatGateway"
    price = find_catalog_price(
        catalog, "TinaOS-FCU", "CreateNatGateway", "NatGatewayUsage", zone
    ) or 0.0
    
    cost_per_hour = price
    cost_per_month = cost_per_hour * HOURS_PER_MONTH
    cost_per_year = cost_per_month * 12
    
    return {
        "cost_per_hour": round(cost_per_hour, 4),
        "cost_per_month": round(cost_per_month, 2),
        "cost_per_year": round(cost_per_year, 2)
    }


def calculate_load_balancer_cost(load_balancer: Dict, catalog: Dict, region: str) -> Dict:
    """
    Calculate load balancer cost.
    
    Args:
        load_balancer: Load balancer resource dictionary
        catalog: Catalog dictionary
        region: Region name
    
    Returns:
        Dictionary with cost_per_hour, cost_per_month, cost_per_year
    """
    zone = load_balancer.get("zone", "")
    
    # Load Balancer - Type: "LBU:Usage", Operation: "CreateLoadBalancer"
    price = find_catalog_price(
        catalog, "TinaOS-LBU", "CreateLoadBalancer", "LBU:Usage", zone
    ) or 0.0
    
    cost_per_hour = price
    cost_per_month = cost_per_hour * HOURS_PER_MONTH
    cost_per_year = cost_per_month * 12
    
    return {
        "cost_per_hour": round(cost_per_hour, 4),
        "cost_per_month": round(cost_per_month, 2),
        "cost_per_year": round(cost_per_year, 2)
    }


def calculate_vpn_cost(vpn: Dict, catalog: Dict, region: str) -> Dict:
    """
    Calculate VPN cost.
    
    Args:
        vpn: VPN resource dictionary
        catalog: Catalog dictionary
        region: Region name
    
    Returns:
        Dictionary with cost_per_hour, cost_per_month, cost_per_year
    """
    zone = vpn.get("zone", "")
    
    # VPN - Type: "ConnectionUsage", Operation: "CreateVpnConnection"
    price = find_catalog_price(
        catalog, "TinaOS-FCU", "CreateVpnConnection", "ConnectionUsage", zone
    ) or 0.0
    
    cost_per_hour = price
    cost_per_month = cost_per_hour * HOURS_PER_MONTH
    cost_per_year = cost_per_month * 12
    
    return {
        "cost_per_hour": round(cost_per_hour, 4),
        "cost_per_month": round(cost_per_month, 2),
        "cost_per_year": round(cost_per_year, 2)
    }


def calculate_oos_cost(oos_bucket: Dict, catalog: Dict, region: str) -> Dict:
    """
    Calculate OOS bucket cost (storage + requests).
    
    Args:
        oos_bucket: OOS bucket resource dictionary
        catalog: Catalog dictionary
        region: Region name
    
    Returns:
        Dictionary with cost_per_hour, cost_per_month, cost_per_year
    """
    # OOS pricing is complex (storage + requests)
    # For now, return 0 as it requires listing all objects (can take 10+ minutes)
    # This can be enhanced later with actual object listing if needed
    return {
        "cost_per_hour": 0.0,
        "cost_per_month": 0.0,
        "cost_per_year": 0.0
    }


def calculate_resource_costs(resources: List[Dict], catalog: Dict, region: str) -> List[Dict]:
    """
    Calculate costs for all resources.
    
    Args:
        resources: List of resource dictionaries
        catalog: Catalog dictionary
        region: Region name
    
    Returns:
        List of resources with cost information added
    """
    enriched_resources = []
    
    for resource in resources:
        resource_type = resource.get("resource_type", "")
        costs = {
            "cost_per_hour": 0.0,
            "cost_per_month": 0.0,
            "cost_per_year": 0.0
        }
        
        try:
            if resource_type == "Vm":
                costs = calculate_vm_cost(resource, catalog, region)
            elif resource_type == "Volume":
                costs = calculate_volume_cost(resource, catalog, region)
            elif resource_type == "Snapshot":
                costs = calculate_snapshot_cost(resource, catalog, region)
            elif resource_type == "PublicIp":
                costs = calculate_public_ip_cost(resource, catalog, region)
            elif resource_type == "NatService":
                costs = calculate_nat_service_cost(resource, catalog, region)
            elif resource_type == "LoadBalancer":
                costs = calculate_load_balancer_cost(resource, catalog, region)
            elif resource_type == "Vpn":
                costs = calculate_vpn_cost(resource, catalog, region)
            elif resource_type == "Oos":
                costs = calculate_oos_cost(resource, catalog, region)
        except Exception as e:
            # If calculation fails, keep costs at 0
            pass
        
        # Add costs to resource
        resource["cost_per_hour"] = costs["cost_per_hour"]
        resource["cost_per_month"] = costs["cost_per_month"]
        resource["cost_per_year"] = costs["cost_per_year"]
        
        enriched_resources.append(resource)
    
    return enriched_resources


def aggregate_by_resource_type(resources: List[Dict]) -> Dict:
    """
    Group costs by resource type.
    
    Args:
        resources: List of resources with costs
    
    Returns:
        Dictionary with resource type as key and aggregated costs
    """
    grouped = defaultdict(lambda: {
        "cost_per_hour": 0.0,
        "cost_per_month": 0.0,
        "cost_per_year": 0.0,
        "count": 0
    })
    
    for resource in resources:
        resource_type = resource.get("resource_type", "Unknown")
        grouped[resource_type]["cost_per_hour"] += resource.get("cost_per_hour", 0.0)
        grouped[resource_type]["cost_per_month"] += resource.get("cost_per_month", 0.0)
        grouped[resource_type]["cost_per_year"] += resource.get("cost_per_year", 0.0)
        grouped[resource_type]["count"] += 1
    
    # Round values
    result = {}
    for resource_type, values in grouped.items():
        result[resource_type] = {
            "cost_per_hour": round(values["cost_per_hour"], 4),
            "cost_per_month": round(values["cost_per_month"], 2),
            "cost_per_year": round(values["cost_per_year"], 2),
            "count": values["count"]
        }
    
    return result


def calculate_totals(resources: List[Dict]) -> Dict:
    """
    Calculate overall totals.
    
    Args:
        resources: List of resources with costs
    
    Returns:
        Dictionary with total costs and counts
    """
    total_cost_per_hour = sum(r.get("cost_per_hour", 0.0) for r in resources)
    total_cost_per_month = sum(r.get("cost_per_month", 0.0) for r in resources)
    total_cost_per_year = sum(r.get("cost_per_year", 0.0) for r in resources)
    
    resource_types = set(r.get("resource_type", "Unknown") for r in resources)
    
    return {
        "cost_per_hour": round(total_cost_per_hour, 4),
        "cost_per_month": round(total_cost_per_month, 2),
        "cost_per_year": round(total_cost_per_year, 2),
        "resource_count": len(resources),
        "resource_type_count": len(resource_types)
    }


def get_cost_breakdown(resources: List[Dict]) -> Dict:
    """
    Get cost breakdown by category.
    
    Args:
        resources: List of resources with costs
    
    Returns:
        Dictionary with breakdown by category
    """
    # Category mapping
    category_map = {
        "Vm": "Compute",
        "Volume": "Storage",
        "Snapshot": "Storage",
        "PublicIp": "Network",
        "NatService": "Network",
        "LoadBalancer": "Network",
        "Vpn": "Network",
        "Oos": "Storage"
    }
    
    by_category = defaultdict(lambda: {
        "cost_per_hour": 0.0,
        "cost_per_month": 0.0,
        "cost_per_year": 0.0,
        "count": 0
    })
    
    for resource in resources:
        resource_type = resource.get("resource_type", "Unknown")
        category = category_map.get(resource_type, "Other")
        
        by_category[category]["cost_per_hour"] += resource.get("cost_per_hour", 0.0)
        by_category[category]["cost_per_month"] += resource.get("cost_per_month", 0.0)
        by_category[category]["cost_per_year"] += resource.get("cost_per_year", 0.0)
        by_category[category]["count"] += 1
    
    # Round values
    result = {}
    for category, values in by_category.items():
        result[category] = {
            "cost_per_hour": round(values["cost_per_hour"], 4),
            "cost_per_month": round(values["cost_per_month"], 2),
            "cost_per_year": round(values["cost_per_year"], 2),
            "count": values["count"]
        }
    
    return result


def get_current_costs(
    access_key: str,
    secret_key: str,
    region: str,
    account_id: str,
    tag_key: Optional[str] = None,
    tag_value: Optional[str] = None,
    include_oos: bool = False,
    force_refresh: bool = False
) -> Dict:
    """
    Get current costs for all resources.
    
    Args:
        access_key: Outscale access key
        secret_key: Outscale secret key
        region: Region name
        account_id: Account ID for cache key
        tag_key: Optional tag key to filter by
        tag_value: Optional tag value to filter by
        include_oos: Include OOS buckets (default: False)
        force_refresh: Force refresh cache (default: False)
    
    Returns:
        Dictionary with resources, totals, and breakdown
    """
    # Check cache first
    if not force_refresh:
        cached = cost_cache.get(account_id, region, include_oos)
        if cached:
            return cached
    
    # Fetch resources
    resource_data = fetch_resources(access_key, secret_key, region, include_oos)
    resources = resource_data.get("resources", [])
    
    # Apply tag filters if provided
    if tag_key and tag_value:
        tag_filters = [{"Key": tag_key, "Value": tag_value}]
        resources = filter_resources_by_tags(resources, tag_filters)
    
    # Get catalog for cost calculation
    catalog = get_catalog(region, force_refresh=False)
    
    # Calculate costs
    resources_with_costs = calculate_resource_costs(resources, catalog, region)
    
    # Calculate totals and breakdown
    totals = calculate_totals(resources_with_costs)
    breakdown_by_type = aggregate_by_resource_type(resources_with_costs)
    breakdown_by_category = get_cost_breakdown(resources_with_costs)
    
    result = {
        "resources": resources_with_costs,
        "totals": totals,
        "breakdown": {
            "by_resource_type": breakdown_by_type,
            "by_category": breakdown_by_category
        },
        "region": region,
        "currency": resource_data.get("currency", "EUR"),
        "fetched_at": resource_data.get("fetched_at"),
        "include_oos": include_oos
    }
    
    # Cache result
    cost_cache.set(account_id, region, include_oos, result)
    
    return result

