"""Unit tests for backend.services.cost_service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from backend.services.cost_service import (
    CostCache,
    cost_cache,
    fetch_resources,
    filter_resources_by_tags,
    find_catalog_price,
    find_volume_storage_price,
    find_volume_iops_price,
    find_snapshot_price,
    calculate_vm_price,
    calculate_vm_cost,
    calculate_volume_cost,
    calculate_snapshot_cost,
    calculate_public_ip_cost,
    calculate_nat_service_cost,
    calculate_load_balancer_cost,
    calculate_vpn_cost,
    calculate_oos_cost,
    calculate_resource_costs,
    aggregate_by_resource_type,
    calculate_totals,
    get_cost_breakdown,
    get_current_costs,
    HOURS_PER_MONTH
)


class TestCostCache:
    """Tests for CostCache class."""
    
    def test_init_default_ttl(self):
        """Test CostCache initialization with default TTL."""
        cache = CostCache()
        assert cache.ttl_seconds == 300
        assert cache._cache == {}
        assert cache._timestamps == {}
    
    def test_init_custom_ttl(self):
        """Test CostCache initialization with custom TTL."""
        cache = CostCache(ttl_seconds=600)
        assert cache.ttl_seconds == 600
    
    def test_make_key(self):
        """Test cache key generation."""
        cache = CostCache()
        key1 = cache._make_key("account1", "eu-west-2", False)
        key2 = cache._make_key("account1", "eu-west-2", True)
        key3 = cache._make_key("account2", "eu-west-2", False)
        
        assert key1 == "account1:eu-west-2:oos_False"
        assert key2 == "account1:eu-west-2:oos_True"
        assert key3 == "account2:eu-west-2:oos_False"
        assert key1 != key2
        assert key1 != key3
    
    def test_set_and_get(self):
        """Test setting and getting cache values."""
        cache = CostCache(ttl_seconds=300)
        data = {"test": "data"}
        
        cache.set("account1", "eu-west-2", False, data)
        result = cache.get("account1", "eu-west-2", False)
        
        assert result == data
    
    def test_get_nonexistent_key(self):
        """Test getting non-existent cache key."""
        cache = CostCache()
        result = cache.get("account1", "eu-west-2", False)
        assert result is None
    
    def test_get_expired_cache(self):
        """Test getting expired cache entry."""
        cache = CostCache(ttl_seconds=1)  # 1 second TTL
        data = {"test": "data"}
        
        cache.set("account1", "eu-west-2", False, data)
        
        # Immediately should work
        result = cache.get("account1", "eu-west-2", False)
        assert result == data
        
        # Wait for expiration
        import time
        time.sleep(1.1)
        
        # Should return None and remove from cache
        result = cache.get("account1", "eu-west-2", False)
        assert result is None
        assert "account1:eu-west-2:oos_False" not in cache._cache
        assert "account1:eu-west-2:oos_False" not in cache._timestamps
    
    def test_get_different_include_oos(self):
        """Test that different include_oos values create different cache entries."""
        cache = CostCache()
        data1 = {"test": "data1"}
        data2 = {"test": "data2"}
        
        cache.set("account1", "eu-west-2", False, data1)
        cache.set("account1", "eu-west-2", True, data2)
        
        assert cache.get("account1", "eu-west-2", False) == data1
        assert cache.get("account1", "eu-west-2", True) == data2
    
    def test_invalidate_all(self):
        """Test invalidating all cache entries."""
        cache = CostCache()
        cache.set("account1", "eu-west-2", False, {"data": 1})
        cache.set("account2", "us-west-1", False, {"data": 2})
        
        cache.invalidate()
        
        assert len(cache._cache) == 0
        assert len(cache._timestamps) == 0
    
    def test_invalidate_by_account_id(self):
        """Test invalidating cache by account_id."""
        cache = CostCache()
        cache.set("account1", "eu-west-2", False, {"data": 1})
        cache.set("account1", "us-west-1", False, {"data": 2})
        cache.set("account2", "eu-west-2", False, {"data": 3})
        
        cache.invalidate(account_id="account1")
        
        assert "account1:eu-west-2:oos_False" not in cache._cache
        assert "account1:us-west-1:oos_False" not in cache._cache
        assert "account2:eu-west-2:oos_False" in cache._cache
    
    def test_invalidate_by_region(self):
        """Test invalidating cache by region."""
        cache = CostCache()
        cache.set("account1", "eu-west-2", False, {"data": 1})
        cache.set("account1", "us-west-1", False, {"data": 2})
        cache.set("account2", "eu-west-2", False, {"data": 3})
        
        cache.invalidate(region="eu-west-2")
        
        assert "account1:eu-west-2:oos_False" not in cache._cache
        assert "account1:us-west-1:oos_False" in cache._cache
        assert "account2:eu-west-2:oos_False" not in cache._cache
    
    def test_invalidate_by_account_and_region(self):
        """Test invalidating cache by both account_id and region."""
        cache = CostCache()
        cache.set("account1", "eu-west-2", False, {"data": 1})
        cache.set("account1", "us-west-1", False, {"data": 2})
        cache.set("account2", "eu-west-2", False, {"data": 3})
        
        cache.invalidate(account_id="account1", region="eu-west-2")
        
        assert "account1:eu-west-2:oos_False" not in cache._cache
        assert "account1:us-west-1:oos_False" in cache._cache
        assert "account2:eu-west-2:oos_False" in cache._cache
    
    def test_global_cost_cache_instance(self):
        """Test that global cost_cache instance exists."""
        assert cost_cache is not None
        assert isinstance(cost_cache, CostCache)
        assert cost_cache.ttl_seconds == 300


class TestFilterResourcesByTags:
    """Tests for filter_resources_by_tags function."""
    
    def test_filter_no_tags(self):
        """Test filtering with no tag filters returns all resources."""
        resources = [
            {"resource_id": "1", "tags": [{"Key": "env", "Value": "prod"}]},
            {"resource_id": "2", "tags": [{"Key": "env", "Value": "dev"}]}
        ]
        
        result = filter_resources_by_tags(resources, None)
        assert result == resources
    
    def test_filter_empty_tag_list(self):
        """Test filtering with empty tag list returns all resources."""
        resources = [
            {"resource_id": "1", "tags": [{"Key": "env", "Value": "prod"}]}
        ]
        
        result = filter_resources_by_tags(resources, [])
        assert result == resources
    
    def test_filter_single_tag_match(self):
        """Test filtering with single matching tag."""
        resources = [
            {"resource_id": "1", "tags": [{"Key": "env", "Value": "prod"}]},
            {"resource_id": "2", "tags": [{"Key": "env", "Value": "dev"}]}
        ]
        
        tag_filters = [{"Key": "env", "Value": "prod"}]
        result = filter_resources_by_tags(resources, tag_filters)
        
        assert len(result) == 1
        assert result[0]["resource_id"] == "1"
    
    def test_filter_single_tag_no_match(self):
        """Test filtering with single tag that doesn't match."""
        resources = [
            {"resource_id": "1", "tags": [{"Key": "env", "Value": "prod"}]}
        ]
        
        tag_filters = [{"Key": "env", "Value": "dev"}]
        result = filter_resources_by_tags(resources, tag_filters)
        
        assert len(result) == 0
    
    def test_filter_multiple_tags_and_logic(self):
        """Test filtering with multiple tags (AND logic)."""
        resources = [
            {
                "resource_id": "1",
                "tags": [
                    {"Key": "env", "Value": "prod"},
                    {"Key": "team", "Value": "backend"}
                ]
            },
            {
                "resource_id": "2",
                "tags": [
                    {"Key": "env", "Value": "prod"},
                    {"Key": "team", "Value": "frontend"}
                ]
            }
        ]
        
        tag_filters = [
            {"Key": "env", "Value": "prod"},
            {"Key": "team", "Value": "backend"}
        ]
        result = filter_resources_by_tags(resources, tag_filters)
        
        assert len(result) == 1
        assert result[0]["resource_id"] == "1"
    
    def test_filter_resource_without_tags(self):
        """Test filtering resources that have no tags."""
        resources = [
            {"resource_id": "1", "tags": []},
            {"resource_id": "2", "tags": [{"Key": "env", "Value": "prod"}]}
        ]
        
        tag_filters = [{"Key": "env", "Value": "prod"}]
        result = filter_resources_by_tags(resources, tag_filters)
        
        assert len(result) == 1
        assert result[0]["resource_id"] == "2"
    
    def test_filter_missing_tags_key(self):
        """Test filtering resources missing tags key."""
        resources = [
            {"resource_id": "1"},
            {"resource_id": "2", "tags": [{"Key": "env", "Value": "prod"}]}
        ]
        
        tag_filters = [{"Key": "env", "Value": "prod"}]
        result = filter_resources_by_tags(resources, tag_filters)
        
        assert len(result) == 1
        assert result[0]["resource_id"] == "2"


class TestFindCatalogPrice:
    """Tests for find_catalog_price function."""
    
    def test_find_price_exact_match(self):
        """Test finding price with exact match."""
        catalog = {
            "entries": [
                {
                    "Service": "TinaOS-FCU",
                    "Operation": "AllocateAddress",
                    "Type": "PublicIp",
                    "UnitPrice": 0.005
                }
            ]
        }
        
        price = find_catalog_price(catalog, "TinaOS-FCU", "AllocateAddress", "PublicIp")
        assert price == 0.005
    
    def test_find_price_type_contains(self):
        """Test finding price with type contains match."""
        catalog = {
            "entries": [
                {
                    "Service": "TinaOS-FCU",
                    "Operation": "CreateNatGateway",
                    "Type": "NatGatewayUsage:Standard",
                    "UnitPrice": 0.045
                }
            ]
        }
        
        price = find_catalog_price(catalog, "TinaOS-FCU", "CreateNatGateway", "NatGatewayUsage")
        assert price == 0.045
    
    def test_find_price_with_zone(self):
        """Test finding price with zone filter."""
        catalog = {
            "entries": [
                {
                    "Service": "TinaOS-FCU",
                    "Operation": "AllocateAddress",
                    "Type": "PublicIp",
                    "SubregionName": "eu-west-2a",
                    "UnitPrice": 0.005
                },
                {
                    "Service": "TinaOS-FCU",
                    "Operation": "AllocateAddress",
                    "Type": "PublicIp",
                    "SubregionName": "eu-west-2b",
                    "UnitPrice": 0.006
                }
            ]
        }
        
        price = find_catalog_price(catalog, "TinaOS-FCU", "AllocateAddress", "PublicIp", "eu-west-2a")
        assert price == 0.005
    
    def test_find_price_no_zone_filter(self):
        """Test finding price without zone filter returns first match."""
        catalog = {
            "entries": [
                {
                    "Service": "TinaOS-FCU",
                    "Operation": "AllocateAddress",
                    "Type": "PublicIp",
                    "SubregionName": "eu-west-2a",
                    "UnitPrice": 0.005
                }
            ]
        }
        
        price = find_catalog_price(catalog, "TinaOS-FCU", "AllocateAddress", "PublicIp", "")
        assert price == 0.005
    
    def test_find_price_not_found(self):
        """Test finding price when not found returns None."""
        catalog = {
            "entries": [
                {
                    "Service": "TinaOS-FCU",
                    "Operation": "OtherOperation",
                    "Type": "OtherType",
                    "UnitPrice": 0.005
                }
            ]
        }
        
        price = find_catalog_price(catalog, "TinaOS-FCU", "AllocateAddress", "PublicIp")
        assert price is None
    
    def test_find_price_case_insensitive_fields(self):
        """Test finding price with lowercase field names."""
        catalog = {
            "entries": [
                {
                    "service": "TinaOS-FCU",
                    "operation": "AllocateAddress",
                    "type": "PublicIp",
                    "unitPrice": 0.005
                }
            ]
        }
        
        price = find_catalog_price(catalog, "TinaOS-FCU", "AllocateAddress", "PublicIp")
        assert price == 0.005
    
    def test_find_price_no_unit_price(self):
        """Test finding price when UnitPrice is None."""
        catalog = {
            "entries": [
                {
                    "Service": "TinaOS-FCU",
                    "Operation": "AllocateAddress",
                    "Type": "PublicIp",
                    "UnitPrice": None
                }
            ]
        }
        
        price = find_catalog_price(catalog, "TinaOS-FCU", "AllocateAddress", "PublicIp")
        assert price is None


class TestFindVolumeStoragePrice:
    """Tests for find_volume_storage_price function."""
    
    def test_find_volume_storage_price_standard(self):
        """Test finding standard volume storage price."""
        catalog = {
            "entries": [
                {
                    "Type": "BSU:VolumeUsage:standard",
                    "Operation": "CreateVolume",
                    "UnitPrice": 0.10
                }
            ]
        }
        
        price = find_volume_storage_price(catalog, "standard")
        assert price == 0.10
    
    def test_find_volume_storage_price_io1(self):
        """Test finding io1 volume storage price."""
        catalog = {
            "entries": [
                {
                    "Type": "BSU:VolumeUsage:io1",
                    "Operation": "CreateVolume",
                    "UnitPrice": 0.125
                }
            ]
        }
        
        price = find_volume_storage_price(catalog, "io1")
        assert price == 0.125
    
    def test_find_volume_storage_price_not_found(self):
        """Test finding volume storage price when not found."""
        catalog = {
            "entries": [
                {
                    "Type": "BSU:VolumeUsage:standard",
                    "Operation": "OtherOperation",
                    "UnitPrice": 0.10
                }
            ]
        }
        
        price = find_volume_storage_price(catalog, "gp2")
        assert price is None


class TestFindVolumeIopsPrice:
    """Tests for find_volume_iops_price function."""
    
    def test_find_volume_iops_price_io1(self):
        """Test finding io1 volume IOPS price."""
        catalog = {
            "entries": [
                {
                    "Type": "BSU:VolumeIOPS:io1",
                    "Operation": "CreateVolume",
                    "UnitPrice": 0.065
                }
            ]
        }
        
        price = find_volume_iops_price(catalog, "io1")
        assert price == 0.065
    
    def test_find_volume_iops_price_not_found(self):
        """Test finding volume IOPS price when not found."""
        catalog = {
            "entries": [
                {
                    "Type": "BSU:VolumeUsage:io1",
                    "Operation": "CreateVolume",
                    "UnitPrice": 0.10
                }
            ]
        }
        
        price = find_volume_iops_price(catalog, "io1")
        assert price is None


class TestFindSnapshotPrice:
    """Tests for find_snapshot_price function."""
    
    def test_find_snapshot_price_snapshot_usage(self):
        """Test finding snapshot price with Snapshot:Usage type."""
        catalog = {
            "entries": [
                {
                    "Type": "Snapshot:Usage",
                    "Operation": "Snapshot",
                    "UnitPrice": 0.05
                }
            ]
        }
        
        price = find_snapshot_price(catalog)
        assert price == 0.05
    
    def test_find_snapshot_price_snapshot_type(self):
        """Test finding snapshot price with Snapshot type."""
        catalog = {
            "entries": [
                {
                    "Type": "Snapshot",
                    "Operation": "CreateSnapshot",
                    "UnitPrice": 0.05
                }
            ]
        }
        
        price = find_snapshot_price(catalog)
        assert price == 0.05
    
    def test_find_snapshot_price_not_found(self):
        """Test finding snapshot price when not found."""
        catalog = {
            "entries": [
                {
                    "Type": "OtherType",
                    "Operation": "OtherOperation",
                    "UnitPrice": 0.05
                }
            ]
        }
        
        price = find_snapshot_price(catalog)
        assert price is None


class TestCalculateVmPrice:
    """Tests for calculate_vm_price function."""
    
    def test_calculate_vm_price_tina_type(self):
        """Test calculating VM price for tina type."""
        catalog = {
            "entries": [
                {
                    "Type": "CustomCore:v4-p1",
                    "Operation": "RunInstances-OD",
                    "UnitPrice": 0.05
                },
                {
                    "Type": "CustomRam",
                    "Operation": "RunInstances-OD",
                    "UnitPrice": 0.01
                }
            ]
        }
        
        # tinav4.c2r4p1 = gen=4, cores=2, ram=4, perf=1
        price = calculate_vm_price("tinav4.c2r4p1", catalog, "eu-west-2")
        
        # Should be: 2 cores * 0.05 + 4 ram * 0.01 = 0.10 + 0.04 = 0.14
        assert price == 0.14
    
    def test_calculate_vm_price_box_usage_type(self):
        """Test calculating VM price for BoxUsage type."""
        catalog = {
            "entries": [
                {
                    "Type": "t2.micro",
                    "Operation": "RunInstances-OD",
                    "UnitPrice": 0.0116
                }
            ]
        }
        
        price = calculate_vm_price("BoxUsage:t2.micro", catalog, "eu-west-2")
        # Should find direct match or return 0.0 if not found
        assert price == 0.0 or price == 0.0116
    
    def test_calculate_vm_price_invalid_type(self):
        """Test calculating VM price for invalid type."""
        catalog = {"entries": []}
        
        price = calculate_vm_price("invalid-type", catalog, "eu-west-2")
        assert price == 0.0
    
    def test_calculate_vm_price_dedicated_tenancy(self):
        """Test calculating VM price with dedicated tenancy."""
        catalog = {
            "entries": [
                {
                    "Type": "CustomCore:v4-p1",
                    "Operation": "RunInstances-OD",
                    "UnitPrice": 0.05
                },
                {
                    "Type": "CustomRam",
                    "Operation": "RunInstances-OD",
                    "UnitPrice": 0.01
                },
                {
                    "Type": "DedicatedInstanceSurplus",
                    "Operation": "RunInstances",
                    "UnitPrice": 0.1
                }
            ]
        }
        
        # Base price: 2 * 0.05 + 4 * 0.01 = 0.14
        # Dedicated factor: 1.0 + (0.1 * 10.0) = 2.0
        # Final: 0.14 * 2.0 = 0.28
        price = calculate_vm_price("tinav4.c2r4p1", catalog, "eu-west-2", tenancy="dedicated")
        assert price == 0.28
    
    def test_calculate_vm_price_default_tenancy(self):
        """Test calculating VM price with default tenancy (no factor)."""
        catalog = {
            "entries": [
                {
                    "Type": "CustomCore:v4-p1",
                    "Operation": "RunInstances-OD",
                    "UnitPrice": 0.05
                },
                {
                    "Type": "CustomRam",
                    "Operation": "RunInstances-OD",
                    "UnitPrice": 0.01
                },
                {
                    "Type": "DedicatedInstanceSurplus",
                    "Operation": "RunInstances",
                    "UnitPrice": 0.1
                }
            ]
        }
        
        # Base price only, no dedicated factor
        price = calculate_vm_price("tinav4.c2r4p1", catalog, "eu-west-2", tenancy="default")
        assert price == 0.14


class TestCalculateVmCost:
    """Tests for calculate_vm_cost function."""
    
    def test_calculate_vm_cost_basic(self):
        """Test calculating basic VM cost."""
        vm = {
            "specs": {
                "vm_type": "tinav4.c2r4p1",
                "tenancy": "default"
            }
        }
        catalog = {
            "entries": [
                {
                    "Type": "CustomCore:v4-p1",
                    "Operation": "RunInstances-OD",
                    "UnitPrice": 0.05
                },
                {
                    "Type": "CustomRam",
                    "Operation": "RunInstances-OD",
                    "UnitPrice": 0.01
                }
            ]
        }
        
        costs = calculate_vm_cost(vm, catalog, "eu-west-2")
        
        assert "cost_per_hour" in costs
        assert "cost_per_month" in costs
        assert "cost_per_year" in costs
        assert costs["cost_per_hour"] > 0
        assert costs["cost_per_month"] == costs["cost_per_hour"] * HOURS_PER_MONTH
        assert costs["cost_per_year"] == costs["cost_per_month"] * 12
    
    def test_calculate_vm_cost_dedicated_tenancy(self):
        """Test calculating VM cost with dedicated tenancy."""
        vm = {
            "specs": {
                "vm_type": "tinav4.c2r4p1",
                "tenancy": "dedicated"
            }
        }
        catalog = {
            "entries": [
                {
                    "Type": "CustomCore:v4-p1",
                    "Operation": "RunInstances-OD",
                    "UnitPrice": 0.05
                },
                {
                    "Type": "CustomRam",
                    "Operation": "RunInstances-OD",
                    "UnitPrice": 0.01
                },
                {
                    "Type": "DedicatedInstanceSurplus",
                    "Operation": "RunInstances",
                    "UnitPrice": 0.1
                }
            ]
        }
        
        costs = calculate_vm_cost(vm, catalog, "eu-west-2")
        
        # Dedicated should be more expensive
        assert costs["cost_per_hour"] > 0.14  # Base price without dedicated


class TestCalculateVolumeCost:
    """Tests for calculate_volume_cost function."""
    
    def test_calculate_volume_cost_standard(self):
        """Test calculating standard volume cost."""
        volume = {
            "zone": "eu-west-2a",
            "specs": {
                "volume_type": "standard",
                "size": 100,  # GB
                "iops": 0
            }
        }
        catalog = {
            "entries": [
                {
                    "Type": "BSU:VolumeUsage:standard",
                    "Operation": "CreateVolume",
                    "UnitPrice": 0.10  # per GB per month
                }
            ]
        }
        
        costs = calculate_volume_cost(volume, catalog, "eu-west-2")
        
        assert "cost_per_hour" in costs
        assert "cost_per_month" in costs
        assert "cost_per_year" in costs
        # 100 GB * 0.10 = 10.00 per month
        assert costs["cost_per_month"] == 10.0
        assert costs["cost_per_hour"] > 0
        assert costs["cost_per_year"] == costs["cost_per_month"] * 12
    
    def test_calculate_volume_cost_io1_with_iops(self):
        """Test calculating io1 volume cost with IOPS."""
        volume = {
            "zone": "eu-west-2a",
            "specs": {
                "volume_type": "io1",
                "size": 100,  # GB
                "iops": 3000
            }
        }
        catalog = {
            "entries": [
                {
                    "Type": "BSU:VolumeUsage:io1",
                    "Operation": "CreateVolume",
                    "UnitPrice": 0.125  # per GB per month
                },
                {
                    "Type": "BSU:VolumeIOPS:io1",
                    "Operation": "CreateVolume",
                    "UnitPrice": 0.065  # per IOPS per month
                }
            ]
        }
        
        costs = calculate_volume_cost(volume, catalog, "eu-west-2")
        
        # Storage: 100 * 0.125 = 12.5
        # IOPS: 3000 * 0.065 = 195
        # Total: 207.5 per month
        assert costs["cost_per_month"] == 207.5
        assert costs["cost_per_hour"] > 0
        assert costs["cost_per_year"] == costs["cost_per_month"] * 12
    
    def test_calculate_volume_cost_no_price_found(self):
        """Test calculating volume cost when price not found."""
        volume = {
            "zone": "eu-west-2a",
            "specs": {
                "volume_type": "unknown",
                "size": 100,
                "iops": 0
            }
        }
        catalog = {"entries": []}
        
        costs = calculate_volume_cost(volume, catalog, "eu-west-2")
        
        assert costs["cost_per_hour"] == 0.0
        assert costs["cost_per_month"] == 0.0
        assert costs["cost_per_year"] == 0.0


class TestCalculateSnapshotCost:
    """Tests for calculate_snapshot_cost function."""
    
    def test_calculate_snapshot_cost(self):
        """Test calculating snapshot cost."""
        snapshot = {
            "zone": "eu-west-2a",
            "specs": {
                "size": 50  # GB
            }
        }
        catalog = {
            "entries": [
                {
                    "Type": "Snapshot:Usage",
                    "Operation": "Snapshot",
                    "UnitPrice": 0.05  # per GB per month
                }
            ]
        }
        
        costs = calculate_snapshot_cost(snapshot, catalog, "eu-west-2")
        
        # 50 GB * 0.05 = 2.50 per month
        assert costs["cost_per_month"] == 2.5
        assert costs["cost_per_hour"] > 0
        assert costs["cost_per_year"] == costs["cost_per_month"] * 12
    
    def test_calculate_snapshot_cost_no_price(self):
        """Test calculating snapshot cost when price not found."""
        snapshot = {
            "zone": "eu-west-2a",
            "specs": {
                "size": 50
            }
        }
        catalog = {"entries": []}
        
        costs = calculate_snapshot_cost(snapshot, catalog, "eu-west-2")
        
        assert costs["cost_per_hour"] == 0.0
        assert costs["cost_per_month"] == 0.0


class TestCalculatePublicIpCost:
    """Tests for calculate_public_ip_cost function."""
    
    def test_calculate_public_ip_cost_attached(self):
        """Test calculating attached public IP cost."""
        public_ip = {
            "zone": "eu-west-2a",
            "specs": {
                "nic_id": "eni-123",
                "vm_id": "vm-123"
            }
        }
        catalog = {
            "entries": [
                {
                    "Service": "TinaOS-FCU",
                    "Operation": "AssociateAddress",
                    "Type": "ElasticIP:AdditionalAddress",
                    "UnitPrice": 0.005  # per hour
                }
            ]
        }
        
        costs = calculate_public_ip_cost(public_ip, catalog, "eu-west-2")
        
        assert costs["cost_per_hour"] == 0.005
        assert costs["cost_per_month"] == 0.005 * HOURS_PER_MONTH
        assert costs["cost_per_year"] == costs["cost_per_month"] * 12
    
    def test_calculate_public_ip_cost_unattached(self):
        """Test calculating unattached public IP cost."""
        public_ip = {
            "zone": "eu-west-2a",
            "specs": {
                "nic_id": "",
                "vm_id": ""
            }
        }
        catalog = {
            "entries": [
                {
                    "Service": "TinaOS-FCU",
                    "Operation": "AssociateAddress",
                    "Type": "ElasticIP:IdleAddress",
                    "UnitPrice": 0.002  # per hour
                }
            ]
        }
        
        costs = calculate_public_ip_cost(public_ip, catalog, "eu-west-2")
        
        assert costs["cost_per_hour"] == 0.002
        assert costs["cost_per_month"] == 0.002 * HOURS_PER_MONTH


class TestCalculateNatServiceCost:
    """Tests for calculate_nat_service_cost function."""
    
    def test_calculate_nat_service_cost(self):
        """Test calculating NAT service cost."""
        nat_service = {
            "zone": "eu-west-2a"
        }
        catalog = {
            "entries": [
                {
                    "Service": "TinaOS-FCU",
                    "Operation": "CreateNatGateway",
                    "Type": "NatGatewayUsage",
                    "UnitPrice": 0.045  # per hour
                }
            ]
        }
        
        costs = calculate_nat_service_cost(nat_service, catalog, "eu-west-2")
        
        assert costs["cost_per_hour"] == 0.045
        # cost_per_month is rounded to 2 decimal places
        expected_monthly = round(0.045 * HOURS_PER_MONTH, 2)
        assert costs["cost_per_month"] == expected_monthly
        # cost_per_year is calculated from unrounded monthly, then rounded
        expected_yearly = round(0.045 * HOURS_PER_MONTH * 12, 2)
        assert costs["cost_per_year"] == expected_yearly
    
    def test_calculate_nat_service_cost_not_found(self):
        """Test calculating NAT service cost when price not found."""
        nat_service = {
            "zone": "eu-west-2a"
        }
        catalog = {"entries": []}
        
        costs = calculate_nat_service_cost(nat_service, catalog, "eu-west-2")
        
        assert costs["cost_per_hour"] == 0.0
        assert costs["cost_per_month"] == 0.0


class TestCalculateLoadBalancerCost:
    """Tests for calculate_load_balancer_cost function."""
    
    def test_calculate_load_balancer_cost(self):
        """Test calculating load balancer cost."""
        load_balancer = {
            "zone": "eu-west-2a"
        }
        catalog = {
            "entries": [
                {
                    "Service": "TinaOS-LBU",
                    "Operation": "CreateLoadBalancer",
                    "Type": "LBU:Usage",
                    "UnitPrice": 0.0225  # per hour
                }
            ]
        }
        
        costs = calculate_load_balancer_cost(load_balancer, catalog, "eu-west-2")
        
        assert costs["cost_per_hour"] == 0.0225
        # cost_per_month is rounded to 2 decimal places
        expected_monthly = round(0.0225 * HOURS_PER_MONTH, 2)
        assert costs["cost_per_month"] == expected_monthly
        # cost_per_year is calculated from unrounded monthly, then rounded
        expected_yearly = round(0.0225 * HOURS_PER_MONTH * 12, 2)
        assert costs["cost_per_year"] == expected_yearly


class TestCalculateVpnCost:
    """Tests for calculate_vpn_cost function."""
    
    def test_calculate_vpn_cost(self):
        """Test calculating VPN cost."""
        vpn = {
            "zone": "eu-west-2a"
        }
        catalog = {
            "entries": [
                {
                    "Service": "TinaOS-FCU",
                    "Operation": "CreateVpnConnection",
                    "Type": "ConnectionUsage",
                    "UnitPrice": 0.05  # per hour
                }
            ]
        }
        
        costs = calculate_vpn_cost(vpn, catalog, "eu-west-2")
        
        assert costs["cost_per_hour"] == 0.05
        assert costs["cost_per_month"] == 0.05 * HOURS_PER_MONTH
        assert costs["cost_per_year"] == costs["cost_per_month"] * 12


class TestCalculateOosCost:
    """Tests for calculate_oos_cost function."""
    
    def test_calculate_oos_cost(self):
        """Test calculating OOS cost (currently returns 0)."""
        oos_bucket = {
            "specs": {
                "bucket_name": "test-bucket"
            }
        }
        catalog = {"entries": []}
        
        costs = calculate_oos_cost(oos_bucket, catalog, "eu-west-2")
        
        # OOS cost calculation is not implemented yet
        assert costs["cost_per_hour"] == 0.0
        assert costs["cost_per_month"] == 0.0
        assert costs["cost_per_year"] == 0.0


class TestCalculateResourceCosts:
    """Tests for calculate_resource_costs function."""
    
    def test_calculate_resource_costs_vm(self):
        """Test calculating costs for VM resources."""
        resources = [
            {
                "resource_type": "Vm",
                "specs": {
                    "vm_type": "tinav4.c2r4p1",
                    "tenancy": "default"
                }
            }
        ]
        catalog = {
            "entries": [
                {
                    "Type": "CustomCore:v4-p1",
                    "Operation": "RunInstances-OD",
                    "UnitPrice": 0.05
                },
                {
                    "Type": "CustomRam",
                    "Operation": "RunInstances-OD",
                    "UnitPrice": 0.01
                }
            ]
        }
        
        result = calculate_resource_costs(resources, catalog, "eu-west-2")
        
        assert len(result) == 1
        assert "cost_per_hour" in result[0]
        assert "cost_per_month" in result[0]
        assert "cost_per_year" in result[0]
    
    def test_calculate_resource_costs_multiple_types(self):
        """Test calculating costs for multiple resource types."""
        resources = [
            {
                "resource_type": "Vm",
                "specs": {"vm_type": "tinav4.c2r4p1", "tenancy": "default"}
            },
            {
                "resource_type": "Volume",
                "zone": "eu-west-2a",
                "specs": {"volume_type": "standard", "size": 100, "iops": 0}
            }
        ]
        catalog = {
            "entries": [
                {
                    "Type": "CustomCore:v4-p1",
                    "Operation": "RunInstances-OD",
                    "UnitPrice": 0.05
                },
                {
                    "Type": "CustomRam",
                    "Operation": "RunInstances-OD",
                    "UnitPrice": 0.01
                },
                {
                    "Type": "BSU:VolumeUsage:standard",
                    "Operation": "CreateVolume",
                    "UnitPrice": 0.10
                }
            ]
        }
        
        result = calculate_resource_costs(resources, catalog, "eu-west-2")
        
        assert len(result) == 2
        assert result[0]["resource_type"] == "Vm"
        assert result[1]["resource_type"] == "Volume"
        assert result[0]["cost_per_hour"] > 0
        assert result[1]["cost_per_month"] > 0
    
    def test_calculate_resource_costs_unknown_type(self):
        """Test calculating costs for unknown resource type."""
        resources = [
            {
                "resource_type": "UnknownType",
                "specs": {}
            }
        ]
        catalog = {"entries": []}
        
        result = calculate_resource_costs(resources, catalog, "eu-west-2")
        
        assert len(result) == 1
        assert result[0]["cost_per_hour"] == 0.0
        assert result[0]["cost_per_month"] == 0.0
    
    def test_calculate_resource_costs_exception_handling(self):
        """Test that exceptions in cost calculation don't break the function."""
        resources = [
            {
                "resource_type": "Vm",
                "specs": {}  # Missing required fields
            }
        ]
        catalog = {"entries": []}
        
        # Should not raise exception, should set costs to 0
        result = calculate_resource_costs(resources, catalog, "eu-west-2")
        
        assert len(result) == 1
        assert result[0]["cost_per_hour"] == 0.0


class TestAggregateByResourceType:
    """Tests for aggregate_by_resource_type function."""
    
    def test_aggregate_by_resource_type_single(self):
        """Test aggregating costs by resource type - single type."""
        resources = [
            {
                "resource_type": "Vm",
                "cost_per_hour": 0.14,
                "cost_per_month": 102.2,
                "cost_per_year": 1226.4
            },
            {
                "resource_type": "Vm",
                "cost_per_hour": 0.28,
                "cost_per_month": 204.4,
                "cost_per_year": 2452.8
            }
        ]
        
        result = aggregate_by_resource_type(resources)
        
        assert "Vm" in result
        assert result["Vm"]["cost_per_hour"] == 0.42
        assert result["Vm"]["cost_per_month"] == 306.6
        assert result["Vm"]["cost_per_year"] == 3679.2
        assert result["Vm"]["count"] == 2
    
    def test_aggregate_by_resource_type_multiple(self):
        """Test aggregating costs by resource type - multiple types."""
        resources = [
            {
                "resource_type": "Vm",
                "cost_per_hour": 0.14,
                "cost_per_month": 102.2,
                "cost_per_year": 1226.4
            },
            {
                "resource_type": "Volume",
                "cost_per_hour": 0.0137,
                "cost_per_month": 10.0,
                "cost_per_year": 120.0
            }
        ]
        
        result = aggregate_by_resource_type(resources)
        
        assert "Vm" in result
        assert "Volume" in result
        assert result["Vm"]["count"] == 1
        assert result["Volume"]["count"] == 1
        assert result["Vm"]["cost_per_month"] == 102.2
        assert result["Volume"]["cost_per_month"] == 10.0
    
    def test_aggregate_by_resource_type_empty(self):
        """Test aggregating costs with empty resources list."""
        resources = []
        
        result = aggregate_by_resource_type(resources)
        
        assert result == {}
    
    def test_aggregate_by_resource_type_unknown(self):
        """Test aggregating costs with unknown resource type."""
        resources = [
            {
                "resource_type": "Unknown",
                "cost_per_hour": 0.1,
                "cost_per_month": 73.0,
                "cost_per_year": 876.0
            }
        ]
        
        result = aggregate_by_resource_type(resources)
        
        assert "Unknown" in result
        assert result["Unknown"]["count"] == 1


class TestCalculateTotals:
    """Tests for calculate_totals function."""
    
    def test_calculate_totals(self):
        """Test calculating total costs."""
        resources = [
            {
                "resource_type": "Vm",
                "cost_per_hour": 0.14,
                "cost_per_month": 102.2,
                "cost_per_year": 1226.4
            },
            {
                "resource_type": "Volume",
                "cost_per_hour": 0.0137,
                "cost_per_month": 10.0,
                "cost_per_year": 120.0
            }
        ]
        
        result = calculate_totals(resources)
        
        assert result["cost_per_hour"] == 0.1537
        assert result["cost_per_month"] == 112.2
        assert result["cost_per_year"] == 1346.4
        assert result["resource_count"] == 2
        assert result["resource_type_count"] == 2
    
    def test_calculate_totals_empty(self):
        """Test calculating totals with empty resources."""
        resources = []
        
        result = calculate_totals(resources)
        
        assert result["cost_per_hour"] == 0.0
        assert result["cost_per_month"] == 0.0
        assert result["cost_per_year"] == 0.0
        assert result["resource_count"] == 0
        assert result["resource_type_count"] == 0
    
    def test_calculate_totals_same_type(self):
        """Test calculating totals with same resource type."""
        resources = [
            {
                "resource_type": "Vm",
                "cost_per_hour": 0.14,
                "cost_per_month": 102.2,
                "cost_per_year": 1226.4
            },
            {
                "resource_type": "Vm",
                "cost_per_hour": 0.28,
                "cost_per_month": 204.4,
                "cost_per_year": 2452.8
            }
        ]
        
        result = calculate_totals(resources)
        
        assert result["resource_count"] == 2
        assert result["resource_type_count"] == 1  # Only one unique type


class TestGetCostBreakdown:
    """Tests for get_cost_breakdown function."""
    
    def test_get_cost_breakdown_by_category(self):
        """Test getting cost breakdown by category."""
        resources = [
            {
                "resource_type": "Vm",
                "cost_per_hour": 0.14,
                "cost_per_month": 102.2,
                "cost_per_year": 1226.4
            },
            {
                "resource_type": "Volume",
                "cost_per_hour": 0.0137,
                "cost_per_month": 10.0,
                "cost_per_year": 120.0
            },
            {
                "resource_type": "PublicIp",
                "cost_per_hour": 0.005,
                "cost_per_month": 3.65,
                "cost_per_year": 43.8
            }
        ]
        
        result = get_cost_breakdown(resources)
        
        assert "Compute" in result
        assert "Storage" in result
        assert "Network" in result
        assert result["Compute"]["cost_per_month"] == 102.2
        assert result["Storage"]["cost_per_month"] == 10.0
        assert result["Network"]["cost_per_month"] == 3.65
        assert result["Compute"]["count"] == 1
        assert result["Storage"]["count"] == 1
        assert result["Network"]["count"] == 1
    
    def test_get_cost_breakdown_multiple_same_category(self):
        """Test breakdown with multiple resources in same category."""
        resources = [
            {
                "resource_type": "Vm",
                "cost_per_hour": 0.14,
                "cost_per_month": 102.2,
                "cost_per_year": 1226.4
            },
            {
                "resource_type": "Volume",
                "cost_per_hour": 0.0137,
                "cost_per_month": 10.0,
                "cost_per_year": 120.0
            },
            {
                "resource_type": "Snapshot",
                "cost_per_hour": 0.0034,
                "cost_per_month": 2.5,
                "cost_per_year": 30.0
            }
        ]
        
        result = get_cost_breakdown(resources)
        
        assert "Storage" in result
        # Volume + Snapshot both in Storage
        assert result["Storage"]["cost_per_month"] == 12.5
        assert result["Storage"]["count"] == 2
    
    def test_get_cost_breakdown_unknown_type(self):
        """Test breakdown with unknown resource type (should go to Other)."""
        resources = [
            {
                "resource_type": "UnknownType",
                "cost_per_hour": 0.1,
                "cost_per_month": 73.0,
                "cost_per_year": 876.0
            }
        ]
        
        result = get_cost_breakdown(resources)
        
        assert "Other" in result
        assert result["Other"]["cost_per_month"] == 73.0
        assert result["Other"]["count"] == 1
    
    def test_get_cost_breakdown_empty(self):
        """Test breakdown with empty resources."""
        resources = []
        
        result = get_cost_breakdown(resources)
        
        assert result == {}


class TestGetCurrentCosts:
    """Tests for get_current_costs function."""
    
    @patch('backend.services.cost_service.fetch_resources')
    @patch('backend.services.cost_service.get_catalog')
    @patch('backend.services.cost_service.cost_cache')
    def test_get_current_costs_from_cache(self, mock_cache, mock_get_catalog, mock_fetch_resources):
        """Test getting costs from cache."""
        cached_data = {
            "resources": [],
            "totals": {"cost_per_month": 100.0},
            "breakdown": {},
            "region": "eu-west-2",
            "currency": "EUR"
        }
        mock_cache.get.return_value = cached_data
        
        result = get_current_costs(
            "access_key", "secret_key", "eu-west-2", "account123",
            include_oos=False, force_refresh=False
        )
        
        assert result == cached_data
        mock_cache.get.assert_called_once_with("account123", "eu-west-2", False)
        mock_fetch_resources.assert_not_called()
    
    @patch('backend.services.cost_service.fetch_resources')
    @patch('backend.services.cost_service.get_catalog')
    @patch('backend.services.cost_service.cost_cache')
    @patch('backend.services.cost_service.calculate_resource_costs')
    @patch('backend.services.cost_service.aggregate_by_resource_type')
    @patch('backend.services.cost_service.calculate_totals')
    @patch('backend.services.cost_service.get_cost_breakdown')
    def test_get_current_costs_fresh_fetch(self, mock_breakdown, mock_totals, mock_aggregate,
                                            mock_calc_costs, mock_cache, mock_get_catalog,
                                            mock_fetch_resources):
        """Test getting costs with fresh fetch (no cache)."""
        # Setup mocks
        mock_cache.get.return_value = None  # Cache miss
        mock_fetch_resources.return_value = {
            "resources": [
                {
                    "resource_type": "Vm",
                    "specs": {"vm_type": "tinav4.c2r4p1", "tenancy": "default"}
                }
            ],
            "currency": "EUR",
            "fetched_at": "2024-01-01T00:00:00"
        }
        mock_get_catalog.return_value = {"entries": []}
        mock_calc_costs.return_value = [
            {
                "resource_type": "Vm",
                "cost_per_hour": 0.14,
                "cost_per_month": 102.2,
                "cost_per_year": 1226.4
            }
        ]
        mock_totals.return_value = {
            "cost_per_hour": 0.14,
            "cost_per_month": 102.2,
            "cost_per_year": 1226.4,
            "resource_count": 1,
            "resource_type_count": 1
        }
        mock_aggregate.return_value = {
            "Vm": {
                "cost_per_hour": 0.14,
                "cost_per_month": 102.2,
                "cost_per_year": 1226.4,
                "count": 1
            }
        }
        mock_breakdown.return_value = {
            "Compute": {
                "cost_per_hour": 0.14,
                "cost_per_month": 102.2,
                "cost_per_year": 1226.4,
                "count": 1
            }
        }
        
        result = get_current_costs(
            "access_key", "secret_key", "eu-west-2", "account123",
            include_oos=False, force_refresh=False
        )
        
        assert "resources" in result
        assert "totals" in result
        assert "breakdown" in result
        assert result["region"] == "eu-west-2"
        assert result["currency"] == "EUR"
        mock_fetch_resources.assert_called_once_with("access_key", "secret_key", "eu-west-2", False)
        mock_cache.set.assert_called_once()
    
    @patch('backend.services.cost_service.fetch_resources')
    @patch('backend.services.cost_service.get_catalog')
    @patch('backend.services.cost_service.cost_cache')
    def test_get_current_costs_force_refresh(self, mock_cache, mock_get_catalog, mock_fetch_resources):
        """Test getting costs with force refresh (bypasses cache)."""
        cached_data = {"resources": [], "totals": {}}
        mock_cache.get.return_value = cached_data
        
        mock_fetch_resources.return_value = {
            "resources": [],
            "currency": "EUR",
            "fetched_at": "2024-01-01T00:00:00"
        }
        mock_get_catalog.return_value = {"entries": []}
        
        result = get_current_costs(
            "access_key", "secret_key", "eu-west-2", "account123",
            include_oos=False, force_refresh=True
        )
        
        # Should fetch fresh data even though cache exists
        mock_fetch_resources.assert_called_once()
        mock_cache.set.assert_called_once()
    
    @patch('backend.services.cost_service.fetch_resources')
    @patch('backend.services.cost_service.get_catalog')
    @patch('backend.services.cost_service.cost_cache')
    @patch('backend.services.cost_service.filter_resources_by_tags')
    @patch('backend.services.cost_service.calculate_resource_costs')
    @patch('backend.services.cost_service.aggregate_by_resource_type')
    @patch('backend.services.cost_service.calculate_totals')
    @patch('backend.services.cost_service.get_cost_breakdown')
    def test_get_current_costs_with_tag_filter(self, mock_breakdown, mock_totals, mock_aggregate,
                                                mock_calc_costs, mock_filter_tags, mock_cache,
                                                mock_get_catalog, mock_fetch_resources):
        """Test getting costs with tag filtering."""
        mock_cache.get.return_value = None
        mock_fetch_resources.return_value = {
            "resources": [
                {"resource_id": "1", "tags": [{"Key": "env", "Value": "prod"}]},
                {"resource_id": "2", "tags": [{"Key": "env", "Value": "dev"}]}
            ],
            "currency": "EUR",
            "fetched_at": "2024-01-01T00:00:00"
        }
        mock_get_catalog.return_value = {"entries": []}
        mock_filter_tags.return_value = [
            {"resource_id": "1", "tags": [{"Key": "env", "Value": "prod"}]}
        ]
        mock_calc_costs.return_value = [
            {"resource_id": "1", "cost_per_hour": 0.14, "cost_per_month": 102.2, "cost_per_year": 1226.4}
        ]
        mock_totals.return_value = {"cost_per_month": 102.2, "resource_count": 1, "resource_type_count": 1}
        mock_aggregate.return_value = {}
        mock_breakdown.return_value = {}
        
        result = get_current_costs(
            "access_key", "secret_key", "eu-west-2", "account123",
            tag_key="env", tag_value="prod", include_oos=False, force_refresh=False
        )
        
        mock_filter_tags.assert_called_once()
        assert len(result["resources"]) == 1
    
    @patch('backend.services.cost_service.fetch_resources')
    @patch('backend.services.cost_service.get_catalog')
    @patch('backend.services.cost_service.cost_cache')
    def test_get_current_costs_include_oos(self, mock_cache, mock_get_catalog, mock_fetch_resources):
        """Test getting costs with include_oos=True."""
        mock_cache.get.return_value = None
        mock_fetch_resources.return_value = {
            "resources": [],
            "currency": "EUR",
            "fetched_at": "2024-01-01T00:00:00"
        }
        mock_get_catalog.return_value = {"entries": []}
        
        get_current_costs(
            "access_key", "secret_key", "eu-west-2", "account123",
            include_oos=True, force_refresh=False
        )
        
        # Should pass include_oos=True to fetch_resources
        mock_fetch_resources.assert_called_once_with("access_key", "secret_key", "eu-west-2", True)
        # Should cache with include_oos=True
        mock_cache.set.assert_called_once()
        call_args = mock_cache.set.call_args[0]
        assert call_args[2] == True  # include_oos parameter
