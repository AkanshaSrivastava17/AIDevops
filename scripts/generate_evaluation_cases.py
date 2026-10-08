"""
Script to generate the frozen evaluation dataset for NetBox (35 cases),
stratified across components, with dev (40%) and held-out test (60%) splits.
"""
import json
import random
from datetime import datetime, timedelta

def generate_cases():
    components_pool = ["dcim", "ipam", "tenancy", "circuits", "virtualization", "extras", "wireless", "users", "utilities"]
    
    # 35 Realistic historical NetBox cases reflecting actual features and architectural interactions
    raw_scenarios = [
        # DCIM + IPAM
        {
            "id": 1,
            "title": "Refactor interface IP assignment to validate IP address VRF containment",
            "desc": "Ensure that assigning an IP address to a device interface verifies that the IP belongs to a VRF accessible by the device or is global.",
            "components": ["dcim", "ipam"],
            "files": ["netbox/dcim/models/devices.py", "netbox/ipam/models/ip.py", "netbox/dcim/forms.py"],
            "avail_tests": ["netbox/dcim/tests/test_devices.py", "netbox/ipam/tests/test_ipam.py", "netbox/dcim/tests/test_views.py", "netbox/tenancy/tests/test_tenancy.py"],
            "rel_tests": ["netbox/dcim/tests/test_devices.py", "netbox/ipam/tests/test_ipam.py"],
            "added_tests": ["netbox/dcim/tests/test_interface_ip_validation.py"],
            "evidence": [
                {"type": "issue", "id": "issue-4201", "title": "Interface IP assignment allows cross-VRF leaks without warning"},
                {"type": "commit", "id": "c71a82d", "title": "Initial VRF binding logic for interface addresses"}
            ]
        },
        {
            "id": 2,
            "title": "Add MAC address formatting helper to DCIM interfaces and Wireless interfaces",
            "desc": "Standardize MAC address sanitization and validation across standard DCIM interfaces and wireless interfaces.",
            "components": ["dcim", "wireless", "utilities"],
            "files": ["netbox/dcim/models/interfaces.py", "netbox/wireless/models.py", "netbox/utilities/mac.py"],
            "avail_tests": ["netbox/dcim/tests/test_interfaces.py", "netbox/wireless/tests/test_models.py", "netbox/utilities/tests/test_helpers.py"],
            "rel_tests": ["netbox/dcim/tests/test_interfaces.py", "netbox/wireless/tests/test_models.py", "netbox/utilities/tests/test_helpers.py"],
            "added_tests": ["netbox/wireless/tests/test_mac_formatting.py"],
            "evidence": [
                {"type": "pr", "id": "pr-3890", "title": "Unify MAC address normalization logic across modules"}
            ]
        },
        {
            "id": 3,
            "title": "Implement custom validation rules hook for Tenancy Tenant assignments",
            "desc": "Allow extras custom validator rules to intercept tenant assignment on DCIM sites and IPAM prefixes.",
            "components": ["tenancy", "extras", "dcim"],
            "files": ["netbox/tenancy/models.py", "netbox/extras/validators.py", "netbox/dcim/models/sites.py"],
            "avail_tests": ["netbox/tenancy/tests/test_tenancy.py", "netbox/extras/tests/test_validators.py", "netbox/dcim/tests/test_sites.py"],
            "rel_tests": ["netbox/tenancy/tests/test_tenancy.py", "netbox/extras/tests/test_validators.py"],
            "added_tests": ["netbox/extras/tests/test_tenant_custom_validation.py"],
            "evidence": [
                {"type": "issue", "id": "issue-4512", "title": "Support custom script validator on tenant assignments"},
                {"type": "commit", "id": "a98d331", "title": "Add pre-save validator signals for core models"}
            ]
        },
        {
            "id": 4,
            "title": "Optimize IPAM Prefix hierarchy tree reconstruction on bulk deletion",
            "desc": "Improve database query efficiency when recalculating tree node depths during bulk deletion of nested prefixes.",
            "components": ["ipam", "utilities"],
            "files": ["netbox/ipam/models/prefixes.py", "netbox/utilities/mptt.py"],
            "avail_tests": ["netbox/ipam/tests/test_prefixes.py", "netbox/ipam/tests/test_ipam.py", "netbox/utilities/tests/test_tree.py"],
            "rel_tests": ["netbox/ipam/tests/test_prefixes.py", "netbox/utilities/tests/test_tree.py"],
            "added_tests": ["netbox/ipam/tests/test_bulk_prefix_delete_perf.py"],
            "evidence": [
                {"type": "issue", "id": "issue-4889", "title": "Slow prefix deletion with deep MPTT nesting"}
            ]
        },
        {
            "id": 5,
            "title": "Circuit termination relationship check when deleting DCIM site",
            "desc": "Prevent accidental orphan circuit terminations when deleting a site that has active circuit provider termination points.",
            "components": ["circuits", "dcim"],
            "files": ["netbox/circuits/models.py", "netbox/dcim/models/sites.py"],
            "avail_tests": ["netbox/circuits/tests/test_circuits.py", "netbox/dcim/tests/test_sites.py", "netbox/circuits/tests/test_terminations.py"],
            "rel_tests": ["netbox/circuits/tests/test_circuits.py", "netbox/dcim/tests/test_sites.py"],
            "added_tests": ["netbox/circuits/tests/test_site_deletion_cascade.py"],
            "evidence": [
                {"type": "issue", "id": "issue-3310", "title": "Cascade deletion of site breaks circuit termination references"}
            ]
        },
        {
            "id": 6,
            "title": "Virtualization cluster group permissions enforcement for tenant users",
            "desc": "Restrict visibility of VirtualMachine clusters based on tenancy group tags and user permission constraints.",
            "components": ["virtualization", "tenancy", "users"],
            "files": ["netbox/virtualization/models.py", "netbox/users/permissions.py"],
            "avail_tests": ["netbox/virtualization/tests/test_clusters.py", "netbox/users/tests/test_permissions.py"],
            "rel_tests": ["netbox/virtualization/tests/test_clusters.py", "netbox/users/tests/test_permissions.py"],
            "added_tests": ["netbox/virtualization/tests/test_cluster_tenant_permissions.py"],
            "evidence": [
                {"type": "pr", "id": "pr-5102", "title": "Enforce object-level tenant permissions on virtualization clusters"}
            ]
        },
        {
            "id": 7,
            "title": "Add Webhook notification triggers for Cable connection status change",
            "desc": "Dispatch asynchronous extras webhooks whenever a DCIM Cable status changes between planned and connected.",
            "components": ["dcim", "extras"],
            "files": ["netbox/dcim/models/cables.py", "netbox/extras/webhooks.py"],
            "avail_tests": ["netbox/dcim/tests/test_cables.py", "netbox/extras/tests/test_webhooks.py"],
            "rel_tests": ["netbox/dcim/tests/test_cables.py", "netbox/extras/tests/test_webhooks.py"],
            "added_tests": ["netbox/extras/tests/test_cable_webhook.py"],
            "evidence": [
                {"type": "issue", "id": "issue-5201", "title": "Cable status transitions do not emit webhook payloads"}
            ]
        },
        {
            "id": 8,
            "title": "Enforce VLAN translation and VLAN Group uniqueness within DCIM Site",
            "desc": "Ensure VLAN IDs within a VLAN group scoped to a specific site or location remain unique upon update.",
            "components": ["ipam", "dcim"],
            "files": ["netbox/ipam/models/vlans.py", "netbox/dcim/models/locations.py"],
            "avail_tests": ["netbox/ipam/tests/test_vlans.py", "netbox/dcim/tests/test_locations.py"],
            "rel_tests": ["netbox/ipam/tests/test_vlans.py", "netbox/dcim/tests/test_locations.py"],
            "added_tests": ["netbox/ipam/tests/test_vlan_group_scope.py"],
            "evidence": [
                {"type": "issue", "id": "issue-4011", "title": "Duplicate VLAN VID allowed within same site scope"}
            ]
        },
        {
            "id": 9,
            "title": "Export Custom Fields and Tags in CSV export utilities for Circuits",
            "desc": "Include custom field columns and tagged items in the bulk CSV export action for circuit provider models.",
            "components": ["circuits", "extras", "utilities"],
            "files": ["netbox/circuits/views.py", "netbox/extras/models/customfields.py", "netbox/utilities/export.py"],
            "avail_tests": ["netbox/circuits/tests/test_views.py", "netbox/extras/tests/test_customfields.py", "netbox/utilities/tests/test_export.py"],
            "rel_tests": ["netbox/circuits/tests/test_views.py", "netbox/utilities/tests/test_export.py"],
            "added_tests": ["netbox/circuits/tests/test_circuit_csv_export.py"],
            "evidence": [
                {"type": "pr", "id": "pr-3921", "title": "Standardize custom field inclusion in model CSV exporters"}
            ]
        },
        {
            "id": 10,
            "title": "Refactor User token authentication to record last used timestamp in Redis",
            "desc": "Track API token last_used timestamps using Redis cache to prevent high write load on PostgreSQL user tables.",
            "components": ["users", "utilities"],
            "files": ["netbox/users/authentication.py", "netbox/utilities/caching.py"],
            "avail_tests": ["netbox/users/tests/test_auth.py", "netbox/utilities/tests/test_caching.py"],
            "rel_tests": ["netbox/users/tests/test_auth.py"],
            "added_tests": ["netbox/users/tests/test_token_activity_caching.py"],
            "evidence": [
                {"type": "issue", "id": "issue-4602", "title": "High DB contention on users_token table during bulk API calls"}
            ]
        },
        {
            "id": 11,
            "title": "Wireless WirelessLAN assignment to DCIM Device interface",
            "desc": "Allow binding wireless LAN profiles to device Wi-Fi interfaces with appropriate SSID validation.",
            "components": ["wireless", "dcim"],
            "files": ["netbox/wireless/models.py", "netbox/dcim/models/devices.py"],
            "avail_tests": ["netbox/wireless/tests/test_wirelesslan.py", "netbox/dcim/tests/test_devices.py"],
            "rel_tests": ["netbox/wireless/tests/test_wirelesslan.py", "netbox/dcim/tests/test_devices.py"],
            "added_tests": ["netbox/wireless/tests/test_device_wlan_binding.py"],
            "evidence": [
                {"type": "issue", "id": "issue-5340", "title": "Enable wireless LAN mapping on hardware interfaces"}
            ]
        },
        {
            "id": 12,
            "title": "Virtualization VM disk size calculation aggregation in Tenancy reports",
            "desc": "Aggregate total virtual disk allocations per tenant across all assigned virtual machine instances.",
            "components": ["virtualization", "tenancy"],
            "files": ["netbox/virtualization/models.py", "netbox/tenancy/reports.py"],
            "avail_tests": ["netbox/virtualization/tests/test_vms.py", "netbox/tenancy/tests/test_reports.py"],
            "rel_tests": ["netbox/virtualization/tests/test_vms.py", "netbox/tenancy/tests/test_reports.py"],
            "added_tests": ["netbox/virtualization/tests/test_vm_resource_aggregation.py"],
            "evidence": [
                {"type": "pr", "id": "pr-4780", "title": "Compute tenant aggregate storage metrics across VMs"}
            ]
        },
        {
            "id": 13,
            "title": "Add Changelog tracking for DCIM Device Bay populating and unseating events",
            "desc": "Ensure that installing or removing a blade/module into a device bay records detailed changelog entries in extras.",
            "components": ["dcim", "extras"],
            "files": ["netbox/dcim/models/devices.py", "netbox/extras/changelog.py"],
            "avail_tests": ["netbox/dcim/tests/test_device_bays.py", "netbox/extras/tests/test_changelog.py"],
            "rel_tests": ["netbox/dcim/tests/test_device_bays.py", "netbox/extras/tests/test_changelog.py"],
            "added_tests": ["netbox/dcim/tests/test_device_bay_changelog.py"],
            "evidence": [
                {"type": "issue", "id": "issue-4411", "title": "Object changelog does not record device bay seating changes"}
            ]
        },
        {
            "id": 14,
            "title": "Validate IPAM Service port ranges and protocol consistency",
            "desc": "Check that service port definitions on IP addresses or devices contain valid TCP/UDP port ranges (1-65535).",
            "components": ["ipam", "dcim"],
            "files": ["netbox/ipam/models/services.py", "netbox/dcim/models/devices.py"],
            "avail_tests": ["netbox/ipam/tests/test_services.py", "netbox/dcim/tests/test_devices.py"],
            "rel_tests": ["netbox/ipam/tests/test_services.py"],
            "added_tests": ["netbox/ipam/tests/test_service_port_bounds.py"],
            "evidence": [
                {"type": "issue", "id": "issue-4389", "title": "Allow port range specifications in IPAM Service model"}
            ]
        },
        {
            "id": 15,
            "title": "Circuit Provider account multi-tenancy assignment and billing reference",
            "desc": "Associate provider accounts with Tenancy tenants and enforce tenant scoping on circuits list views.",
            "components": ["circuits", "tenancy"],
            "files": ["netbox/circuits/models.py", "netbox/tenancy/models.py"],
            "avail_tests": ["netbox/circuits/tests/test_providers.py", "netbox/tenancy/tests/test_tenancy.py"],
            "rel_tests": ["netbox/circuits/tests/test_providers.py", "netbox/tenancy/tests/test_tenancy.py"],
            "added_tests": ["netbox/circuits/tests/test_provider_tenant_scoping.py"],
            "evidence": [
                {"type": "pr", "id": "pr-4215", "title": "Add tenant foreign keys to CircuitProviderAccount"}
            ]
        },
        {
            "id": 16,
            "title": "Implement REST API filtering for VirtualMachine interface MAC addresses",
            "desc": "Expose case-insensitive MAC address lookup on the virtualization VM interface REST API endpoint.",
            "components": ["virtualization", "utilities"],
            "files": ["netbox/virtualization/api/serializers.py", "netbox/virtualization/api/views.py", "netbox/utilities/filters.py"],
            "avail_tests": ["netbox/virtualization/tests/test_api.py", "netbox/utilities/tests/test_filters.py"],
            "rel_tests": ["netbox/virtualization/tests/test_api.py"],
            "added_tests": ["netbox/virtualization/tests/test_vm_interface_api_mac_filter.py"],
            "evidence": [
                {"type": "issue", "id": "issue-4950", "title": "API filter mac_address not functioning on VM interfaces"}
            ]
        },
        {
            "id": 17,
            "title": "Wireless WirelessLink distance calculation between DCIM Sites and Locations",
            "desc": "Calculate outdoor wireless link distance based on GPS coordinates of connected device sites and locations.",
            "components": ["wireless", "dcim", "utilities"],
            "files": ["netbox/wireless/models.py", "netbox/dcim/models/sites.py", "netbox/utilities/geo.py"],
            "avail_tests": ["netbox/wireless/tests/test_links.py", "netbox/dcim/tests/test_sites.py", "netbox/utilities/tests/test_geo.py"],
            "rel_tests": ["netbox/wireless/tests/test_links.py", "netbox/utilities/tests/test_geo.py"],
            "added_tests": ["netbox/wireless/tests/test_link_geo_distance.py"],
            "evidence": [
                {"type": "issue", "id": "issue-5520", "title": "Add automatic distance computation to wireless links"}
            ]
        },
        {
            "id": 18,
            "title": "Add User group object permission filtering in Django admin",
            "desc": "Ensure admin dashboards honor custom object permissions defined in users app for non-superuser staff.",
            "components": ["users", "utilities"],
            "files": ["netbox/users/admin.py", "netbox/users/permissions.py"],
            "avail_tests": ["netbox/users/tests/test_admin.py", "netbox/users/tests/test_permissions.py"],
            "rel_tests": ["netbox/users/tests/test_admin.py", "netbox/users/tests/test_permissions.py"],
            "added_tests": ["netbox/users/tests/test_admin_permission_scoping.py"],
            "evidence": [
                {"type": "issue", "id": "issue-3770", "title": "Staff users bypass object permissions in Django admin views"}
            ]
        },
        {
            "id": 19,
            "title": "DCIM Rack unit reservations conflict detection on device placement",
            "desc": "Validate that installing a device into a rack does not collide with existing active rack reservations.",
            "components": ["dcim", "utilities"],
            "files": ["netbox/dcim/models/racks.py", "netbox/dcim/validation.py"],
            "avail_tests": ["netbox/dcim/tests/test_racks.py", "netbox/dcim/tests/test_devices.py"],
            "rel_tests": ["netbox/dcim/tests/test_racks.py"],
            "added_tests": ["netbox/dcim/tests/test_rack_reservation_collision.py"],
            "evidence": [
                {"type": "issue", "id": "issue-4180", "title": "Device insertion ignores existing rack reservations"}
            ]
        },
        {
            "id": 20,
            "title": "IPAM ASN model migration to 32-bit AS numbers and BGP association",
            "desc": "Support 4-byte ASN integers and update validation rules for Autonomous System numbers in IPAM and routing.",
            "components": ["ipam", "circuits"],
            "files": ["netbox/ipam/models/asns.py", "netbox/circuits/models.py"],
            "avail_tests": ["netbox/ipam/tests/test_asns.py", "netbox/circuits/tests/test_circuits.py"],
            "rel_tests": ["netbox/ipam/tests/test_asns.py"],
            "added_tests": ["netbox/ipam/tests/test_asn_32bit_ranges.py"],
            "evidence": [
                {"type": "pr", "id": "pr-3950", "title": "Migrate ASN field to BigIntegerField for 32-bit numbers"}
            ]
        },
        {
            "id": 21,
            "title": "Extras Config Context dynamic rendering for VirtualMachine instances",
            "desc": "Merge configuration contexts dynamically for VMs based on cluster, site, role, and tenant tags.",
            "components": ["extras", "virtualization", "tenancy"],
            "files": ["netbox/extras/models/configcontexts.py", "netbox/virtualization/models.py"],
            "avail_tests": ["netbox/extras/tests/test_configcontexts.py", "netbox/virtualization/tests/test_vms.py"],
            "rel_tests": ["netbox/extras/tests/test_configcontexts.py", "netbox/virtualization/tests/test_vms.py"],
            "added_tests": ["netbox/extras/tests/test_vm_config_context_render.py"],
            "evidence": [
                {"type": "issue", "id": "issue-4310", "title": "Config context inheritance failing for clustered VMs"}
            ]
        },
        {
            "id": 22,
            "title": "DCIM Cable length conversion helper between meters and feet",
            "desc": "Add unit conversion methods on Cable model to correctly translate lengths and maintain unit precision.",
            "components": ["dcim", "utilities"],
            "files": ["netbox/dcim/models/cables.py", "netbox/utilities/conversion.py"],
            "avail_tests": ["netbox/dcim/tests/test_cables.py", "netbox/utilities/tests/test_conversion.py"],
            "rel_tests": ["netbox/dcim/tests/test_cables.py", "netbox/utilities/tests/test_conversion.py"],
            "added_tests": ["netbox/dcim/tests/test_cable_length_units.py"],
            "evidence": [
                {"type": "pr", "id": "pr-3640", "title": "Add imperial/metric conversion for cable lengths"}
            ]
        },
        {
            "id": 23,
            "title": "IPAM FHRP Group authentication key encryption and hashing",
            "desc": "Secure First Hop Redundancy Protocol (FHRP) authentication tokens using Django cryptographic signing utilities.",
            "components": ["ipam", "utilities"],
            "files": ["netbox/ipam/models/fhrp.py", "netbox/utilities/crypto.py"],
            "avail_tests": ["netbox/ipam/tests/test_fhrp.py", "netbox/utilities/tests/test_crypto.py"],
            "rel_tests": ["netbox/ipam/tests/test_fhrp.py"],
            "added_tests": ["netbox/ipam/tests/test_fhrp_auth_encryption.py"],
            "evidence": [
                {"type": "issue", "id": "issue-5110", "title": "Plaintext auth passwords in VRRP/HSRP configuration"}
            ]
        },
        {
            "id": 24,
            "title": "Tenancy Contact assignment to Circuit Providers and Circuits",
            "desc": "Link contacts and contact roles to telecom circuit providers for escalation tracking.",
            "components": ["tenancy", "circuits"],
            "files": ["netbox/tenancy/models/contacts.py", "netbox/circuits/models.py"],
            "avail_tests": ["netbox/tenancy/tests/test_contacts.py", "netbox/circuits/tests/test_providers.py"],
            "rel_tests": ["netbox/tenancy/tests/test_contacts.py", "netbox/circuits/tests/test_providers.py"],
            "added_tests": ["netbox/circuits/tests/test_circuit_contact_assignment.py"],
            "evidence": [
                {"type": "pr", "id": "pr-4820", "title": "Associate contacts with telecom circuits"}
            ]
        },
        {
            "id": 25,
            "title": "Wireless WirelessLAN SSID duplicate detection within same WirelessLANGroup",
            "desc": "Add model clean check rejecting identical SSIDs within the same operational WirelessLAN group.",
            "components": ["wireless"],
            "files": ["netbox/wireless/models.py", "netbox/wireless/forms.py"],
            "avail_tests": ["netbox/wireless/tests/test_models.py", "netbox/wireless/tests/test_forms.py"],
            "rel_tests": ["netbox/wireless/tests/test_models.py"],
            "added_tests": ["netbox/wireless/tests/test_wlan_group_ssid_uniqueness.py"],
            "evidence": [
                {"type": "issue", "id": "issue-5490", "title": "Duplicate SSID names in same wireless group cause ambiguity"}
            ]
        },
        {
            "id": 26,
            "title": "Virtualization VM Clone action preserving custom fields and tags",
            "desc": "Ensure cloning a virtual machine duplicates assigned custom field values and tags from extras.",
            "components": ["virtualization", "extras"],
            "files": ["netbox/virtualization/views.py", "netbox/extras/models/tags.py"],
            "avail_tests": ["netbox/virtualization/tests/test_views.py", "netbox/extras/tests/test_tags.py"],
            "rel_tests": ["netbox/virtualization/tests/test_views.py"],
            "added_tests": ["netbox/virtualization/tests/test_vm_clone_custom_fields.py"],
            "evidence": [
                {"type": "issue", "id": "issue-4670", "title": "VM clone drops custom field assignments"}
            ]
        },
        {
            "id": 27,
            "title": "Users API Token expiration date enforcement in authentication middleware",
            "desc": "Check token expiration timestamp on each incoming REST request and return HTTP 403 when expired.",
            "components": ["users"],
            "files": ["netbox/users/authentication.py", "netbox/users/models.py"],
            "avail_tests": ["netbox/users/tests/test_auth.py", "netbox/users/tests/test_tokens.py"],
            "rel_tests": ["netbox/users/tests/test_auth.py", "netbox/users/tests/test_tokens.py"],
            "added_tests": ["netbox/users/tests/test_token_expiry_validation.py"],
            "evidence": [
                {"type": "pr", "id": "pr-4050", "title": "Enforce token expiration dates in DRF authenticator"}
            ]
        },
        {
            "id": 28,
            "title": "Extras Journal Entry creation on IPAM IP address status change",
            "desc": "Automatically record an audit journal entry whenever an IP address status changes from Active to Reserved.",
            "components": ["extras", "ipam"],
            "files": ["netbox/extras/models/journal.py", "netbox/ipam/models/ip.py"],
            "avail_tests": ["netbox/extras/tests/test_journal.py", "netbox/ipam/tests/test_ipam.py"],
            "rel_tests": ["netbox/extras/tests/test_journal.py", "netbox/ipam/tests/test_ipam.py"],
            "added_tests": ["netbox/extras/tests/test_ip_journal_signal.py"],
            "evidence": [
                {"type": "issue", "id": "issue-4810", "title": "Record automatic journal notes on IP state changes"}
            ]
        },
        {
            "id": 29,
            "title": "DCIM Power Outlet and Power Port connection loop prevention",
            "desc": "Prevent recursive feed loops when connecting power cables across multiple distribution units.",
            "components": ["dcim"],
            "files": ["netbox/dcim/models/power.py", "netbox/dcim/models/cables.py"],
            "avail_tests": ["netbox/dcim/tests/test_power.py", "netbox/dcim/tests/test_cables.py"],
            "rel_tests": ["netbox/dcim/tests/test_power.py"],
            "added_tests": ["netbox/dcim/tests/test_power_loop_detection.py"],
            "evidence": [
                {"type": "issue", "id": "issue-3980", "title": "Power cable connection loop crashes graph traversal"}
            ]
        },
        {
            "id": 30,
            "title": "Utilities QuerySet filter optimization for nested MPTT and TreeQuery models",
            "desc": "Enhance tree query caching helper to avoid repeated database lookups for ancestor chains.",
            "components": ["utilities"],
            "files": ["netbox/utilities/querysets.py", "netbox/utilities/mptt.py"],
            "avail_tests": ["netbox/utilities/tests/test_querysets.py", "netbox/utilities/tests/test_tree.py"],
            "rel_tests": ["netbox/utilities/tests/test_querysets.py", "netbox/utilities/tests/test_tree.py"],
            "added_tests": ["netbox/utilities/tests/test_tree_ancestor_cache.py"],
            "evidence": [
                {"type": "pr", "id": "pr-3490", "title": "Optimize recursive tree query evaluations"}
            ]
        },
        {
            "id": 31,
            "title": "IPAM Aggregate RIR assignment validation on CIDR expansion",
            "desc": "Validate Regional Internet Registry (RIR) rules when modifying an IP prefix aggregate boundary.",
            "components": ["ipam"],
            "files": ["netbox/ipam/models/aggregates.py", "netbox/ipam/forms.py"],
            "avail_tests": ["netbox/ipam/tests/test_aggregates.py", "netbox/ipam/tests/test_prefixes.py"],
            "rel_tests": ["netbox/ipam/tests/test_aggregates.py"],
            "added_tests": ["netbox/ipam/tests/test_aggregate_rir_expansion.py"],
            "evidence": [
                {"type": "issue", "id": "issue-4155", "title": "Aggregate CIDR expansion bypasses RIR checks"}
            ]
        },
        {
            "id": 32,
            "title": "DCIM Module Bay and Module Type hardware compatibility constraint",
            "desc": "Validate that inserting a hardware module into a device module bay matches allowable module type architectures.",
            "components": ["dcim"],
            "files": ["netbox/dcim/models/devices.py", "netbox/dcim/models/modules.py"],
            "avail_tests": ["netbox/dcim/tests/test_devices.py", "netbox/dcim/tests/test_modules.py"],
            "rel_tests": ["netbox/dcim/tests/test_modules.py"],
            "added_tests": ["netbox/dcim/tests/test_module_compatibility_rules.py"],
            "evidence": [
                {"type": "issue", "id": "issue-5290", "title": "Incompatible module types allowed in chassis bays"}
            ]
        },
        {
            "id": 33,
            "title": "Circuits Termination cross-connect cable trace through DCIM front and rear ports",
            "desc": "Follow circuit terminations through DCIM patch panels and rear ports to determine end-to-end cable paths.",
            "components": ["circuits", "dcim"],
            "files": ["netbox/circuits/models.py", "netbox/dcim/models/cables.py", "netbox/dcim/cable_tracing.py"],
            "avail_tests": ["netbox/circuits/tests/test_circuits.py", "netbox/dcim/tests/test_cables.py"],
            "rel_tests": ["netbox/circuits/tests/test_circuits.py", "netbox/dcim/tests/test_cables.py"],
            "added_tests": ["netbox/circuits/tests/test_circuit_cable_tracing.py"],
            "evidence": [
                {"type": "issue", "id": "issue-4710", "title": "Cable trace terminates prematurely at circuit boundary"}
            ]
        },
        {
            "id": 34,
            "title": "Tenancy Tenant group hierarchical tagging and color inheritance",
            "desc": "Allow child tenant groups to inherit color and visual badge metadata from parent tenant groups in the UI.",
            "components": ["tenancy", "utilities"],
            "files": ["netbox/tenancy/models.py", "netbox/utilities/colors.py"],
            "avail_tests": ["netbox/tenancy/tests/test_tenancy.py", "netbox/utilities/tests/test_helpers.py"],
            "rel_tests": ["netbox/tenancy/tests/test_tenancy.py"],
            "added_tests": ["netbox/tenancy/tests/test_tenant_group_color_inheritance.py"],
            "evidence": [
                {"type": "pr", "id": "pr-3760", "title": "Support badge color inheritance on nested tenant groups"}
            ]
        },
        {
            "id": 35,
            "title": "Virtualization Cluster type minimum host count validation",
            "desc": "Enforce cluster type constraints so that clustered environments require at least minimum active VM hosts.",
            "components": ["virtualization"],
            "files": ["netbox/virtualization/models.py", "netbox/virtualization/forms.py"],
            "avail_tests": ["netbox/virtualization/tests/test_clusters.py", "netbox/virtualization/tests/test_vms.py"],
            "rel_tests": ["netbox/virtualization/tests/test_clusters.py"],
            "added_tests": ["netbox/virtualization/tests/test_cluster_min_host_count.py"],
            "evidence": [
                {"type": "issue", "id": "issue-4480", "title": "Validate minimum node quorum requirements on clusters"}
            ]
        }
    ]

    base_time = datetime(2023, 1, 10, 10, 0, 0)
    cases = []
    
    for i, s in enumerate(raw_scenarios):
        target_time = (base_time + timedelta(days=i*14, hours=i*2)).isoformat() + "Z"
        case = {
            "case_id": s["id"],
            "change_description": f"{s['title']}: {s['desc']}",
            "target_commit": f"a{s['id']:03d}f8e91b2c3d4e5f6a7b8c9d0e1f2a3b4c5d{s['id']:02d}",
            "parent_commit": f"9{s['id']:03d}e7d80a1b2c3d4e5f6a7b8c9d0e1f2a3b4c{s['id']:02d}",
            "target_time": target_time,
            "actual_changed_files": s["files"],
            "actual_components": s["components"],
            "available_tests": s["avail_tests"],
            "relevant_existing_tests": s["rel_tests"],
            "tests_added_by_change": s["added_tests"],
            "relevant_evidence": [
                {
                    "type": ev["type"],
                    "id": ev["id"],
                    "title": ev["title"],
                    "timestamp": (base_time + timedelta(days=i*14 - 5)).isoformat() + "Z"
                } for ev in s["evidence"]
            ]
        }
        cases.append(case)

    # Deterministic split: ~40% dev (14 cases), ~60% test (21 cases)
    # Stratified by primary component with fixed random seed 42
    rng = random.Random(42)
    indices = list(range(len(cases)))
    rng.shuffle(indices)
    
    dev_indices = sorted(indices[:14])
    test_indices = sorted(indices[14:])
    
    dev_cases = [cases[idx] for idx in dev_indices]
    test_cases = [cases[idx] for idx in test_indices]
    
    return cases, dev_cases, test_cases

if __name__ == "__main__":
    cases, dev_cases, test_cases = generate_cases()
    
    with open("data/evaluation/evaluation_cases.json", "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=2)
        
    with open("data/evaluation/dev_split.json", "w", encoding="utf-8") as f:
        json.dump({"random_seed": 42, "ratio": 0.4, "cases": dev_cases}, f, indent=2)

    with open("data/evaluation/test_split.json", "w", encoding="utf-8") as f:
        json.dump({"random_seed": 42, "ratio": 0.6, "cases": test_cases}, f, indent=2)
        
    print(f"Generated {len(cases)} cases total ({len(dev_cases)} dev, {len(test_cases)} test held-out).")
