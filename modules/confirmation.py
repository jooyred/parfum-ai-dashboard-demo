import random
import time
from datetime import datetime

# In-memory store for pending actions, keyed by user_id
PENDING_ACTIONS = {}

def create_pending_action(user_id, action_type, payload):
    """
    Generates a 6-digit confirmation code, creates a pending action,
    and sets an expiration time (10 minutes).
    """
    code = f"{random.randint(100000, 999999)}"
    expires_at = time.time() + 600  # 10 minutes from now
    
    pending_action = {
        "code": code,
        "action_type": action_type,
        "payload": payload,
        "expires_at": expires_at
    }
    
    PENDING_ACTIONS[str(user_id)] = pending_action
    return pending_action

def format_confirmation_message(pending_action):
    """
    Formats the confirmation instruction message for the user.
    """
    code = pending_action["code"]
    action_type = pending_action["action_type"]
    expires_in_mins = int((pending_action["expires_at"] - time.time()) / 60)
    if expires_in_mins < 1:
        expires_in_mins = 1
        
    msg = (
        f"⚠️ <b>KONFIRMASI TINDAKAN DIPERLUKAN</b>\n\n"
        f"Tindakan: <b>{action_type}</b>\n"
        f"Kode Konfirmasi: <code>{code}</code>\n"
        f"Berlaku selama: {expires_in_mins} menit\n\n"
        f"Kirim perintah <code>/confirm {code}</code> untuk menyetujui, atau <code>/cancel</code> untuk membatalkan."
    )
    return msg

def confirm_pending_action(user_id, confirmation_text):
    """
    Validates a confirmation code for a user.
    Returns (is_valid, action_type, payload, message).
    """
    u_id = str(user_id)
    if u_id not in PENDING_ACTIONS:
        return False, None, None, "Tidak ada tindakan tertunda yang ditemukan."
        
    pending = PENDING_ACTIONS[u_id]
    
    # Check expiration
    if time.time() > pending["expires_at"]:
        del PENDING_ACTIONS[u_id]
        return False, None, None, "Kode konfirmasi telah kedaluwarsa (lebih dari 10 menit)."
        
    # Check code
    input_code = str(confirmation_text).strip()
    if input_code != pending["code"]:
        return False, None, None, "Kode konfirmasi salah. Silakan coba lagi."
        
    # Valid!
    action_type = pending["action_type"]
    payload = pending["payload"]
    
    # Cleanup
    del PENDING_ACTIONS[u_id]
    return True, action_type, payload, "Konfirmasi berhasil disetujui."

def cancel_pending_action(user_id):
    """
    Cancels a pending action for a user.
    Returns (success, message).
    """
    u_id = str(user_id)
    if u_id in PENDING_ACTIONS:
        del PENDING_ACTIONS[u_id]
        return True, "Tindakan tertunda berhasil dibatalkan."
    return False, "Tidak ada tindakan tertunda untuk dibatalkan."
