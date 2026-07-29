# Cisco Secure Firewall Management Center (FMC) provider.
#
# Credentials may be supplied either through the variables below (see
# variables.tf / terraform.tfvars) OR via the provider's environment
# variables: FMC_URL, FMC_USERNAME, FMC_PASSWORD, FMC_INSECURE.
#
# NEVER commit real passwords. Prefer:  export TF_VAR_fmc_password='...'
provider "fmc" {
  url      = var.fmc_url
  username = var.fmc_username
  password = var.fmc_password
  insecure = var.fmc_insecure
}
