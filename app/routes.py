from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import paramiko
import io
from models import insert_task, update_task_status, insert_log, get_task_status, validate_token

router = APIRouter()

class TaskPayload(BaseModel):
    username: str
    server_ip: str
    server_ssh_port: int
    system_username: str
    system_ssh_key: str
    ssh_key_password: str | None = None
    user_password: str

@router.post("/post_task/{task_id}")
async def receive_task(task_id: int, payload: TaskPayload, request: Request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not validate_token(token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    insert_task(task_id, payload.username, payload.server_ip, payload.server_ssh_port, payload.system_username)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        pkey = paramiko.RSAKey.from_private_key(
            io.StringIO(payload.system_ssh_key),
            password=payload.ssh_key_password
        )
        ssh.connect(payload.server_ip, port=payload.server_ssh_port, username=payload.system_username, pkey=pkey, timeout=10)

        # Build compound provisioning command
        provision_script = f'''
        set -e
        id {payload.username} || useradd -m -s /bin/bash {payload.username}
        echo "{payload.username}:{payload.user_password}" | chpasswd
        if grep -qi ubuntu /etc/os-release; then
            usermod -aG sudo {payload.username}
        else
            usermod -aG wheel {payload.username}
        fi
        '''

        stdin, stdout, stderr = ssh.exec_command(provision_script)
        # Read outputs for debug
        stdout_content = stdout.read()
        stderr_content = stderr.read()
        output = stdout_content.decode() + stderr_content.decode()
        update_task_status(task_id, "done")
    except Exception as e:
        output = str(e)
        update_task_status(task_id, "failed")
    finally:
        insert_log(task_id, output)
        ssh.close()
    return {"status": "ok"}

@router.get("/get_task/{task_id}")
async def get_task_status_view(task_id: int, request: Request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not validate_token(token):
        raise HTTPException(status_code=401, detail="Unauthorized")

    status, log = get_task_status(task_id)
    return {"status": status, "log": log}