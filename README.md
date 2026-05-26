# Click iX Enterprise Report Engine
**Core Architecture & Data Migration Engine**

An enterprise-grade, self-hosted operational pipeline designed to manage physical deployments, track structural asset movements, reconcile warehouse consumable adjustments, and capture verified client field reports. Built to map securely against AutoCount bookkeeping IDs without complex programmatic bridges.

## 1. System Architecture Infrastructure Mapping
* **Database Target Engine:** MariaDB Server (Self-hosted, Single Source of Truth).
* **Backend Application Service:** Python 3.10+ (FastAPI running over Uvicorn workers).
* **Authentication Provider Model:** Firebase/Supabase Identity services verifying corporate domains via cryptographic JWT token strings.
* **Storage IO Partition Isolation Configuration:** * Operating System & MariaDB Storage: 256GB NVMe partition (Optimized for quick processing lookups).
  * Binary Deliverables & Photo uploads: Mounted 1TB HDD workspace targeted directly at the `/uploads` file hierarchy.

## 2. Infrastructure Profiles
* **Production Host Node Network Endpoint:** `192.168.100.200`
* **Secure Shell Session User Profile:** `cix-1`
* **Application Repository Working Directory:** `/home/cix-1/cix-report-engine`
* **Hardware Profile Context:** Intel Core i5-9500 @ 3.00GHz (6 Physical Cores), 8GB System Memory.

---

## 3. Server Provisioning Setup Workflow

Run these instructions directly inside the server terminal interface via active SSH connections.

```bash
# 1. Standard package maintenance update commands
sudo apt update && sudo apt upgrade -y
sudo apt install mariadb-server python3-venv python3-pip nginx ghostscript -y

# 2. Hardening database instance configuration parameters
sudo mysql_secure_installation
# Import structures: mysql -u root -p < schema.sql

# 3. Instantiate clean environment execution spaces
cd /home/cix-1/cix-report-engine
python3 -m venv venv
source venv/bin/activate

# 4. Pull core runtime dependency extensions
pip install fastapi uvicorn pydantic python-multipart mysql-connector-python PyJWT pillow

```

---

## 4. Hardware Volume Configuration (1TB HDD Integration)

To preserve drive operations and isolate large asset attachments away from system partitions, the block device mounts directly over target folder structures.

```bash
# 1. Format the storage target disk structure
sudo mkfs.ext4 /dev/sda

# 2. Establish empty mount structures within our directory context
sudo mkdir -p /home/cix-1/cix-report-engine/uploads

# 3. Map disk operations directly onto directory paths
sudo mount /dev/sda /home/cix-1/cix-report-engine/uploads

# 4. Adjust read-write namespace execution privileges to application user context
sudo chown -R cix-1:cix-1 /home/cix-1/cix-report-engine/uploads

# 5. Commit disk configuration to file table profiles to secure persistence across server reboots
echo '/dev/sda /home/cix-1/cix-report-engine/uploads ext4 defaults 0 2' | sudo tee -a /etc/fstab

```

---

## 5. System Daemon Deployment (Systemd Service Wrapper)

To safeguard background continuity and restore service accessibility parameters automatically following power recycles, construct a managed unit runtime handler.

Create the service target configuration tracking file:
`sudo nano /etc/systemd/system/cix-api.service`

Inject the configuration blocks:

```ini
[Unit]
Description=Click iX FastAPI Application Engine
After=network.target mariadb.service

[Service]
User=cix-1
Group=cix-1
WorkingDirectory=/home/cix-1/cix-report-engine
Environment="PATH=/home/cix-1/cix-report-engine/venv/bin"
ExecStart=/home/cix-1/cix-report-engine/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target

```

Commit variables, configure boot dependencies, and launch tracking:

```bash
sudo systemctl daemon-reload
sudo systemctl enable cix-api.service
sudo systemctl start cix-api.service
sudo systemctl status cix-api.service

```

---

## 6. Project Milestone Engineering Sprints (4-Week Agile Roadmap)

* **Sprint 1 (System Core Base & Authentication Infrastructure):** Initialize primary SQL structures, map workspace partitions to the 1TB HDD, spin up raw FastAPI components, and construct the corporate JWT verification middleware layer.
* **Sprint 2 (Sales Handshake & Records Lifecycle):** Build out the Quotation status transition handlers and deploy document-referencing schemas tracking AutoCount invoice indicators.
* **Sprint 3 (Warehouse Operations & Distribution Routines):** Construct Delivery Order systems. Enforce strict procedural branches dividing serialized tracking calculations from bulk volume reduction models. Deploy manual inventory corrections endpoints.
* **Sprint 4 (Field Deployment & Document Verification Delivery):** Deliver tablet layouts for Service Report execution. Map atomic transaction chains executing faulty-device status transformations. Integrate compression pipelines for photo arrays and compile localized PDF generators.
"
## 7.Asset
USE /home/cix-1/cix-report-engine/favicon.ico for the web ico
USE /home/cix-1/cix-report-engine/CIX Black Horizontal Logo.png for company logo in pdf forms and website
USE /home/cix-1/cix-report-engine/Service Report Template V2.0.docx as layout for service reports