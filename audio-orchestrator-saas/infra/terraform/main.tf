terraform {
  required_version = ">= 1.5.0"
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_image" "redis" {
  name = "redis:7-alpine"
}

resource "docker_container" "redis_cache" {
  name  = "audio-orchestrator-redis"
  image = docker_image.redis.image_id

  ports {
    internal = 6379
    external = 6379
  }

  restart = "unless-stopped"
}

output "redis_container_name" {
  value = docker_container.redis_cache.name
}
