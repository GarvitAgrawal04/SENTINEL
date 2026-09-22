# ansible — IT Automation Engine
# D:\Repositories\ansible\CLAUDE.md

## What This Is
IT automation engine. Agentless configuration management, application deployment, and
orchestration via SSH. Playbooks (YAML) for declarative automation. 3,000+ built-in
modules. Roles for reusable automation. Galaxy for community roles. Vault for encrypted
secrets. Check mode (dry run). Idempotent execution. Tower/AWX for web UI.

## When to Load This
- Server configuration management (install packages, configure services)
- Multi-server application deployment
- SSH-based automation (no agents needed on target)
- Compliance enforcement across infrastructure
- Infrastructure provisioning on bare metal / VPS
- Automated security hardening
- Database setup and configuration
- Docker host setup

---

## CORE API

### Inventory
```yaml
# hosts.yml
all:
  children:
    webservers:
      hosts:
        web1:
          ansible_host: 192.168.1.10
        web2:
          ansible_host: 192.168.1.11
      vars:
        nginx_port: 80
    dbservers:
      hosts:
        db1:
          ansible_host: 192.168.1.20
      vars:
        postgres_version: 16
    workers:
      hosts:
        worker[1:5]:
          ansible_host: 192.168.1.3{{item}}
  vars:
    ansible_user: deploy
    ansible_ssh_private_key_file: ~/.ssh/deploy_key
```

### Playbook — Web Server Setup
```yaml
# deploy.yml
---
- name: Setup web servers
  hosts: webservers
  become: true
  vars:
    app_name: my-api
    app_port: 3000

  tasks:
    - name: Update apt cache
      apt:
        update_cache: yes
        cache_valid_time: 3600

    - name: Install system packages
      apt:
        name:
          - nginx
          - certbot
          - ufw
          - fail2ban
        state: present

    - name: Install Node.js 20
      shell: |
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
        apt-get install -y nodejs
      args:
        creates: /usr/bin/node

    - name: Create app directory
      file:
        path: /opt/{{ app_name }}
        state: directory
        owner: deploy
        group: deploy

    - name: Copy application files
      synchronize:
        src: ./dist/
        dest: /opt/{{ app_name }}/
      notify: Restart app

    - name: Install npm dependencies
      npm:
        path: /opt/{{ app_name }}
        production: yes

    - name: Configure nginx reverse proxy
      template:
        src: templates/nginx.conf.j2
        dest: /etc/nginx/sites-available/{{ app_name }}
      notify: Reload nginx

    - name: Enable nginx site
      file:
        src: /etc/nginx/sites-available/{{ app_name }}
        dest: /etc/nginx/sites-enabled/{{ app_name }}
        state: link
      notify: Reload nginx

    - name: Configure UFW firewall
      ufw:
        rule: allow
        port: "{{ item }}"
      loop: ['22', '80', '443']

    - name: Enable UFW
      ufw:
        state: enabled
        policy: deny

  handlers:
    - name: Restart app
      systemd:
        name: "{{ app_name }}"
        state: restarted

    - name: Reload nginx
      systemd:
        name: nginx
        state: reloaded
```

### Playbook — Database Setup
```yaml
- name: Setup PostgreSQL
  hosts: dbservers
  become: true
  vars:
    db_name: myapp
    db_user: app

  tasks:
    - name: Install PostgreSQL
      apt:
        name:
          - "postgresql-{{ postgres_version }}"
          - python3-psycopg2
        state: present

    - name: Create database
      postgresql_db:
        name: "{{ db_name }}"
        state: present
      become_user: postgres

    - name: Create database user
      postgresql_user:
        name: "{{ db_user }}"
        password: "{{ db_password }}"
        db: "{{ db_name }}"
        priv: "ALL"
      become_user: postgres

    - name: Configure pg_hba for app access
      postgresql_pg_hba:
        dest: /etc/postgresql/{{ postgres_version }}/main/pg_hba.conf
        contype: host
        users: "{{ db_user }}"
        source: "192.168.1.0/24"
        databases: "{{ db_name }}"
        method: md5
      notify: Restart PostgreSQL

  handlers:
    - name: Restart PostgreSQL
      systemd:
        name: postgresql
        state: restarted
```

### Roles
```bash
# Create role structure
ansible-galaxy role init my_role

# roles/webserver/
# ├── defaults/main.yml     # Default variables
# ├── handlers/main.yml     # Handlers
# ├── tasks/main.yml        # Tasks
# ├── templates/             # Jinja2 templates
# └── files/                 # Static files

# Use role in playbook
- hosts: webservers
  roles:
    - webserver
    - common
    - security
```

### Vault (Encrypted Secrets)
```bash
# Encrypt file
ansible-vault encrypt secrets.yml

# Decrypt file
ansible-vault decrypt secrets.yml

# Edit encrypted file
ansible-vault edit secrets.yml

# Run playbook with vault
ansible-playbook deploy.yml --ask-vault-pass
ansible-playbook deploy.yml --vault-password-file .vault_pass
```

---

## ESSENTIAL COMMANDS

```bash
pip install ansible

# Run playbook
ansible-playbook -i hosts.yml deploy.yml

# Dry run (check mode)
ansible-playbook deploy.yml --check

# Limit to specific hosts
ansible-playbook deploy.yml --limit web1

# Ad-hoc commands
ansible webservers -m ping                    # Ping all web servers
ansible webservers -m shell -a "uptime"       # Run command
ansible webservers -m apt -a "name=nginx state=present" --become
```

---

## SELF-HEALING

| Error | Fix |
|---|---|
| SSH connection refused | Verify SSH key, port, and host reachability |
| Permission denied | Add `become: true` for root tasks |
| Module not found | Install collection: `ansible-galaxy collection install community.docker` |
| Vault password wrong | Re-check vault password or re-encrypt |
| Host unreachable | Check inventory file and DNS/IP resolution |

---

## ANTI-PATTERNS

- Do NOT use for cloud resource creation — use Pulumi/Terraform
- Do NOT store secrets in plaintext — use ansible-vault
- Do NOT run playbooks without `--check` on new environments
- Do NOT hardcode IPs — use dynamic inventory
- Do NOT ignore idempotency — tasks should be safe to re-run

---

## INTEGRATION POINTS — CROSS-DEPARTMENT ROUTING

| Department | Repo | Relationship |
|---|---|---|
| INFRA | pulumi | Complement: Pulumi for provisioning; Ansible for configuration |
| INFRA | coolify | Alternative: Coolify for PaaS; Ansible for custom server setup |
| INFRA | kamal | Alternative: Kamal for Docker deploy; Ansible for general automation |
| INFRA | pm2 | Ansible can manage pm2 processes on remote servers |
| INFRA | compose | Ansible can deploy Docker Compose stacks |

## OUTPUT CONTRACT
Delivers: Automated server configuration and application deployment via SSH.
Install: `pip install ansible`
Docs: docs.ansible.com
