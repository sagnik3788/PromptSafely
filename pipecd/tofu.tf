provider "aws" {
  region = "ap-northeast-3"
}

data "aws_ami" "ubuntu_latest" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }
}

data "aws_vpc" "default" {
  default = true
}

resource "aws_security_group" "pipecd_ssh" {
  name        = "pipecd-ssh-access"
  description = "Allow SSH & PipeCD UI access"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "PipeCD UI"
    from_port   = 30000
    to_port     = 32767
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "pipecd_vm" {
  ami                         = data.aws_ami.ubuntu_latest.id
  instance_type               = "t3.small"
  key_name                    = "osaka"
  subnet_id                   = "subnet-00c30a0c908c9f2e1" 
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.pipecd_ssh.id]

  instance_market_options {
    market_type = "spot"
    spot_options {
      spot_instance_type = "one-time"
    }
  }

  provisioner "file" {
    source      = "piped-config.yaml"
    destination = "/tmp/piped-config.yaml"

    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("/home/sangnik/.ssh/osaka.pem")
      host        = self.public_ip
    }
  }

  provisioner "remote-exec" {
    inline = [
      "sudo apt update -y",
      "sudo apt install -y curl unzip docker.io docker-compose",

      "sudo systemctl enable docker",
      "sudo systemctl start docker",

      "curl -sfL https://get.k3s.io | sh -",

      "sudo chmod 644 /etc/rancher/k3s/k3s.yaml",
      "echo 'export KUBECONFIG=/etc/rancher/k3s/k3s.yaml' >> ~/.bashrc",
      "export KUBECONFIG=/etc/rancher/k3s/k3s.yaml",

      "sleep 20",

      "curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash",
      "helm repo add pipecd https://charts.pipecd.dev",
      "helm repo update",

      # Install PipeCD and expose UI using NodePort
      "helm install pipecd pipecd/pipecd --namespace pipecd --create-namespace --set gateway.service.type=NodePort",

      "curl -LO https://github.com/pipe-cd/pipe/releases/download/v0.52.2/piped_v0.52.2_linux_amd64",
      "echo 'ac8f7105836eb11645964a97116f8e5c22f830bf5b2735439feece02986d59dc piped_v0.52.2_linux_amd64' | sha256sum -c -",
      "chmod +x piped_v0.52.2_linux_amd64",
      "sudo mv piped_v0.52.2_linux_amd64 /usr/local/bin/piped",

      "sleep 15",

      # Show access URL
      "export PIPECD_PORT=$(kubectl get svc pipecd-gateway -n pipecd -o=jsonpath='{.spec.ports[0].nodePort}')",
      "export PUBLIC_IP=$(curl -s http://checkip.amazonaws.com)",
      "echo 'PipeCD UI is available at: http://'$PUBLIC_IP':'$PIPECD_PORT"
    ]

    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("/home/sangnik/.ssh/osaka.pem")
      host        = self.public_ip
    }
  }

  tags = {
    Name = "pipecd-vm"
  }
}
