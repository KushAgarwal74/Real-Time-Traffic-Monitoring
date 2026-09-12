FROM grafana/grafana:latest

# Copy provisioning files into image so Grafana loads them at startup
COPY provisioning /etc/grafana/provisioning

# Ensure ownership/permissions (Grafana runs as grafana user in image)
RUN chown -R grafana:grafana /etc/grafana/provisioning || true

# Keep default entrypoint/cmd from base image
