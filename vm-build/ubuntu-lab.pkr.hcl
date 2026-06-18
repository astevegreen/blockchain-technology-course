packer {
  required_plugins {
    qemu = {
      version = "~> 1.0"
      source  = "github.com/hashicorp/qemu"
    }
  }
}

variable "disk_size" {
  type    = string
  default = "60G"
}

variable "base_image_url" {
  type    = string
  default = "https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img"
}

variable "base_image_checksum" {
  type    = string
  default = "file:https://cloud-images.ubuntu.com/jammy/current/SHA256SUMS"
}

variable "accelerator" {
  type    = string
  default = "kvm"
}

source "qemu" "ubuntu" {
  iso_url           = var.base_image_url
  iso_checksum      = var.base_image_checksum
  output_directory  = "/mnt/build/output-qemu"
  vm_name           = "blockchain-lab.qcow2"
  format            = "qcow2"
  skip_compaction   = true
  disk_size         = var.disk_size
  disk_image        = true
  use_backing_file  = false
  accelerator       = var.accelerator
  shutdown_command  = "sudo shutdown -P now"
  ssh_username      = "student"
  ssh_password      = "student"
  ssh_timeout       = "30m"
  net_device        = "virtio-net"
  disk_interface    = "virtio"
  cdrom_interface   = "ide"
  headless          = true
  cpus              = 2
  memory            = 4096
  qemuargs = [
    ["-serial", "file:vm-build/packer-serial.log"]
  ]
  cd_content = {
    "meta-data" = file("http/meta-data")
    "user-data" = file("http/user-data")
  }
  cd_label          = "cidata"
}

build {
  sources = ["source.qemu.ubuntu"]

  provisioner "shell" {
    inline = [
      "echo 'Waiting for cloud-init...'",
      "cloud-init status --wait"
    ]
  }

  provisioner "file" {
    source      = "vm-build/network-fallback.sh"
    destination = "/tmp/network-fallback.sh"
  }

  provisioner "file" {
    source      = "vm-build/network-fallback.service"
    destination = "/tmp/network-fallback.service"
  }

  provisioner "shell" {
    script = "vm-build/provision.sh"
    execute_command = "chmod +x {{ .Path }}; sudo env {{ .Vars }} {{ .Path }}"
  }

  provisioner "shell" {
    inline = [
      "echo 'Verifying passwordless sudo for student...'",
      "sudo -n true",
      "sudo -n -l >/tmp/student-sudo.txt",
      "grep -q 'NOPASSWD: ALL' /tmp/student-sudo.txt"
    ]
  }

  provisioner "file" {
    source      = "dynamic-labs"
    destination = "/tmp/dynamic-labs"
  }

  provisioner "shell" {
    inline = [
      "sudo mv /tmp/dynamic-labs /opt/dynamic-labs",
      "sudo chown -R student:student /opt/dynamic-labs",
      "sudo cp /opt/dynamic-labs/lab-manager.sh /usr/local/bin/lab-manager",
      "sudo cp /opt/dynamic-labs/scripts/classroom-network-helper.sh /usr/local/bin/classroom-network-helper",
      "sudo chmod +x /usr/local/bin/lab-manager",
      "sudo chmod +x /usr/local/bin/classroom-network-helper",
      "echo 'Streaming Docker bundles from host via QEMU gateway...'",
      "mkdir -p /tmp/bundles",
      "cd /tmp/bundles",
      "wget http://10.0.2.2:8000/manifest.txt",
      "while read -r tarfile; do echo \"Streaming and loading $tarfile...\"; curl -fsSL http://10.0.2.2:8000/$tarfile | sudo docker load; done < manifest.txt",
      "cd /",
      "rm -rf /tmp/bundles",
      "cd /opt/dynamic-labs/router && sudo docker network create router-net || true"
    ]
  }

  provisioner "shell" {
    inline = [
      "sudo DEBIAN_FRONTEND=noninteractive apt-get autoremove -y",
      "sudo apt-get clean",
      "sudo rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*"
    ]
  }
}
