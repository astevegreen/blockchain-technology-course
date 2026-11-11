# Packer and its QEMU plugin are pinned so a rebuild uses the tools the last good build used.
# The workflow installs the same Packer (.github/workflows/vm-build.yml, Setup Packer).
packer {
  required_version = "= 1.16.2"
  required_plugins {
    qemu = {
      version = "= 1.1.8"
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
  default = "https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img"
}

variable "base_image_checksum" {
  type    = string
  default = "file:https://cloud-images.ubuntu.com/noble/current/SHA256SUMS"
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
      "cloud-init status --wait || { cloud-init status --long; exit 1; }"
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
      "echo 'Installing heimdall-rs 0.9.3, the upstream release binary, checked against its published SHA-256...'",
      "case \"$(uname -m)\" in x86_64) asset=heimdall-linux-amd64; sha=8d58c97f56d584d5d0737d0d0895fc8c68b7b8b2b680f2a7842245789f0b4868 ;; aarch64) asset=heimdall-linux-arm64; sha=ef1d236e5e194e1722e12552b66303d3172e0c4cc267b096f7bc8a053f168df8 ;; *) echo \"Unsupported architecture: $(uname -m)\" >&2; exit 1 ;; esac; curl -fsSL -o /tmp/heimdall \"https://github.com/Jon-Becker/heimdall-rs/releases/download/0.9.3/$asset\" && echo \"$sha  /tmp/heimdall\" | sha256sum -c - && sudo install -m 755 /tmp/heimdall /usr/local/bin/heimdall && rm /tmp/heimdall",
      "heimdall --version",
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
