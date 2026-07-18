# Gitea Runner administration

The package may be installed without registering a runner. This is deliberate: package installation and backup/restore tests must not depend on a permanent external registration credential.

## Register an unregistered installation

1. In Gitea, create a registration credential at instance, organization or repository level.
2. Run the upstream registration command as the dedicated application user, using the package configuration in the persistent data directory.
3. Confirm that `/home/yunohost.app/gitea-runner/.runner` was created.
4. Add the service to YunoHost monitoring and start it.

Use the paths shown by `yunohost app info gitea-runner --full`. On a default installation they are:

```bash
sudo -u gitea-runner \
  /var/www/gitea-runner/runner \
  --config /home/yunohost.app/gitea-runner/config.yaml \
  register

sudo yunohost service add gitea-runner \
  --description="Official Runner for Gitea Actions"

sudo systemctl enable --now gitea-runner
```

The interactive upstream command asks for the instance URL, registration credential, runner name and labels. Do not store the registration credential in shell history, Git, `tests.toml` or the YAML configuration.

## Persistent files

- `/home/yunohost.app/gitea-runner/.runner`: registered runner identity.
- `/home/yunohost.app/gitea-runner/config.yaml`: runner configuration.
- `/var/www/gitea-runner/runner`: replaceable upstream binary.

The identity and configuration are included in package backup/restore and preserved during upgrades.

## Execution model

The service uses the host Docker daemon to isolate workflow jobs in containers. Only attach this runner to trusted repositories. Repository workflows can execute arbitrary commands with the permissions available inside their job containers.

## Upgrade validation

After an upgrade, verify:

```bash
/var/www/gitea-runner/runner --version
systemctl status gitea-runner
journalctl -u gitea-runner --since today
```

Then dispatch a disposable workflow that checks out a repository, runs a shell command, writes a job summary and uploads a small artifact. For Gitea 1.27 or newer, use Runner 2.x or newer so negotiated Actions capabilities are available.
