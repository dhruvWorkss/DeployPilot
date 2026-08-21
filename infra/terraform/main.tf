locals {name = "deploypilot-${var.environment}"; labels = {application="deploypilot", environment=var.environment, managed_by="terraform"}}

resource "google_project_service" "apis" {
  for_each = toset(["container.googleapis.com", "artifactregistry.googleapis.com", "compute.googleapis.com", "secretmanager.googleapis.com", "monitoring.googleapis.com"])
  project = var.project_id
  service = each.value
  disable_on_destroy = false
}

resource "google_compute_network" "main" {name=local.name; auto_create_subnetworks=false; depends_on=[google_project_service.apis]}
resource "google_compute_subnetwork" "main" {
  name=local.name; network=google_compute_network.main.id; ip_cidr_range=var.network_cidr; region=var.region; private_ip_google_access=true
  secondary_ip_range {range_name="pods"; ip_cidr_range=var.pods_cidr}
  secondary_ip_range {range_name="services"; ip_cidr_range=var.services_cidr}
}

resource "google_compute_router" "main" {name=local.name; network=google_compute_network.main.id; region=var.region}
resource "google_compute_router_nat" "main" {name=local.name; router=google_compute_router.main.name; region=var.region; nat_ip_allocate_option="AUTO_ONLY"; source_subnetwork_ip_ranges_to_nat="ALL_SUBNETWORKS_ALL_IP_RANGES"}

resource "google_container_cluster" "main" {
  name=local.name; location=var.region; network=google_compute_network.main.id; subnetwork=google_compute_subnetwork.main.id
  remove_default_node_pool=true; initial_node_count=1; deletion_protection=var.environment == "production"
  networking_mode="VPC_NATIVE"; datapath_provider="ADVANCED_DATAPATH"; enable_shielded_nodes=true
  ip_allocation_policy {cluster_secondary_range_name="pods"; services_secondary_range_name="services"}
  private_cluster_config {enable_private_nodes=true; enable_private_endpoint=false; master_ipv4_cidr_block="172.16.0.0/28"}
  dynamic "master_authorized_networks_config" {for_each=length(var.master_authorized_networks)>0?[1]:[]; content {dynamic "cidr_blocks" {for_each=var.master_authorized_networks; content {cidr_block=cidr_blocks.value.cidr_block; display_name=cidr_blocks.value.display_name}}}}
  workload_identity_config {workload_pool="${var.project_id}.svc.id.goog"}
  release_channel {channel="REGULAR"}
  addons_config {horizontal_pod_autoscaling {disabled=false}; http_load_balancing {disabled=false}; gcp_filestore_csi_driver_config {enabled=true}}
  maintenance_policy {recurring_window {start_time="2026-01-01T02:00:00Z"; end_time="2026-01-01T06:00:00Z"; recurrence="FREQ=WEEKLY;BYDAY=SU"}}
  resource_labels=local.labels
  depends_on=[google_project_service.apis]
}

resource "google_container_node_pool" "main" {
  name="general"; cluster=google_container_cluster.main.id; location=var.region; initial_node_count=1
  autoscaling {min_node_count=1; max_node_count=5; location_policy="BALANCED"}
  management {auto_repair=true; auto_upgrade=true}
  node_config {machine_type="e2-standard-4"; disk_type="pd-balanced"; disk_size_gb=80; image_type="COS_CONTAINERD"; spot=false; labels=local.labels; workload_metadata_config {mode="GKE_METADATA"}; shielded_instance_config {enable_secure_boot=true; enable_integrity_monitoring=true}; oauth_scopes=["https://www.googleapis.com/auth/cloud-platform"]}
}

resource "google_artifact_registry_repository" "images" {location=var.region; repository_id="deploypilot"; format="DOCKER"; description="Immutable DeployPilot release images"; cleanup_policy_dry_run=false; cleanup_policies {id="retain-recent"; action="KEEP"; most_recent_versions {keep_count=30}}; depends_on=[google_project_service.apis]}
