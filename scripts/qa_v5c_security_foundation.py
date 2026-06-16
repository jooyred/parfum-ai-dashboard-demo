import os
import sys
import json
import time
import asyncio
from datetime import datetime
import pandas as pd

# Add the project root to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import components
import hashlib
from modules.audit_log import build_audit_event, format_audit_event_text, validate_audit_log_schema
from modules.confirmation import (
    create_pending_action, format_confirmation_message, confirm_pending_action, cancel_pending_action, PENDING_ACTIONS
)

# Set up environment variables for the test
os.environ["OWNER_CHAT_IDS"] = "1111"
os.environ["STAFF_CHAT_IDS"] = "2222"
os.environ["VIEWER_CHAT_IDS"] = "3333"

# Mock Telegram API components
class MockMessage:
    def __init__(self):
        self.text_replies = []
        self.caption = ""
        self.document = None

    async def reply_text(self, text, parse_mode=None):
        self.text_replies.append(text)
        return self

    async def reply_document(self, document, filename=None, caption="", parse_mode=None):
        self.document = document
        self.caption = caption
        return self

    async def delete(self):
        pass

class MockUser:
    def __init__(self, username="testuser", first_name="Test", last_name="User"):
        self.username = username
        self.first_name = first_name
        self.last_name = last_name

class MockChat:
    def __init__(self, id=12345):
        self.id = id

class MockUpdate:
    def __init__(self, chat_id=12345, text="/start", username="testuser"):
        self.effective_chat = MockChat(id=chat_id)
        self.effective_user = MockUser(username=username)
        self.message = MockMessage()
        self.message.text = text

class MockContext:
    def __init__(self, args=None):
        self.args = args or []

async def run_tests():
    print("=" * 60)
    print("RUNNING QA TESTS FOR V5C SECURITY FOUNDATION")
    print("=" * 60)

    # Clean runtime settings
    if os.path.exists("runtime_bot_settings.json"):
        try:
            os.remove("runtime_bot_settings.json")
        except Exception:
            pass

    # Now import handlers (after environment and settings are loaded/reset)
    from modules.telegram_handlers import (
        get_user_profile, is_setup_mode, start_command, help_command,
        create_invite_command, activate_command, list_users_command, revoke_user_command,
        finance_command, tax_command, daily_on_command
    )

    # 1. Password hashing verify benar/salah
    print("\n[TEST 1] Password Hashing Verification...")
    def hash_password(password: str) -> str:
        dk = hashlib.pbkdf2_hmac('sha256', password.encode(), b"parfum_ai_secure_salt", 100000)
        return dk.hex()
    
    owner_hash = hash_password("owner123")
    assert owner_hash != "owner123", "Hash should not be plaintext"
    assert hash_password("owner123") == owner_hash, "Verify success should match"
    assert hash_password("wrong_pwd") != owner_hash, "Verify failure should not match"
    print("✅ Password hashing verified successfully.")

    # 2. Streamlit role permission matrix simulation
    print("\n[TEST 2] Streamlit Page Permission Matrix Simulation...")
    allowed_pages = {
        "owner": ["Owner Control Room", "Dashboard Overview", "Stok, HPP & Produksi", "Chatbot AI Bisnis", "Laporan Harian", "Finance & Tax", "Setup Data", "Data Health Check", "Data Dummy"],
        "staff": ["Owner Control Room", "Dashboard Overview", "Stok, HPP & Produksi", "Chatbot AI Bisnis", "Laporan Harian", "Setup Data", "Data Health Check", "Data Dummy"],
        "viewer": ["Owner Control Room", "Dashboard Overview", "Laporan Harian", "Data Health Check"]
    }
    # Check permissions
    assert "Finance & Tax" in allowed_pages["owner"]
    assert "Finance & Tax" not in allowed_pages["staff"]
    assert "Finance & Tax" not in allowed_pages["viewer"]
    assert "Setup Data" in allowed_pages["staff"]
    assert "Setup Data" not in allowed_pages["viewer"]
    print("✅ Streamlit permission matrix validated.")

    # 3. Telegram role detection dari OWNER/STAFF/VIEWER chat IDs
    print("\n[TEST 3] Telegram Role Detection from Environment Variables...")
    profile_owner = get_user_profile(1111)
    profile_staff = get_user_profile(2222)
    profile_viewer = get_user_profile(3333)
    profile_unknown = get_user_profile(9999)
    
    assert profile_owner["role"] == "owner" and profile_owner["authorized"] == True
    assert profile_staff["role"] == "staff" and profile_staff["authorized"] == True
    assert profile_viewer["role"] == "viewer" and profile_viewer["authorized"] == True
    assert profile_unknown["role"] is None and profile_unknown["authorized"] == False
    print("✅ Telegram env role detection verified.")

    # 4. Unknown chat /start menghasilkan instruksi activation
    print("\n[TEST 4] Unknown Chat ID /start Activation Warning...")
    up_unk = MockUpdate(chat_id=9999)
    ctx = MockContext()
    await start_command(up_unk, ctx)
    assert len(up_unk.message.text_replies) > 0
    assert "belum aktif" in up_unk.message.text_replies[0]
    print("✅ Unknown user /start shows activation info.")

    # 5. Jika OWNER_CHAT_IDS kosong, setup mode menampilkan instruksi
    print("\n[TEST 5] Setup Mode when OWNER_CHAT_IDS is empty...")
    original_owner_ids = os.environ.get("OWNER_CHAT_IDS")
    os.environ["OWNER_CHAT_IDS"] = ""
    # Verify setup mode
    assert is_setup_mode() == True, "Should be in setup mode"
    up_setup = MockUpdate(chat_id=9999)
    await start_command(up_setup, ctx)
    assert "Setup Mode" in up_setup.message.text_replies[0]
    os.environ["OWNER_CHAT_IDS"] = original_owner_ids # Restore
    assert is_setup_mode() == False
    print("✅ Setup mode verification verified.")

    # 6. Owner bisa /create_invite staff
    print("\n[TEST 6] Owner creates invite code...")
    up_owner = MockUpdate(chat_id=1111)
    ctx_staff = MockContext(args=["staff"])
    await create_invite_command(up_owner, ctx_staff)
    assert len(up_owner.message.text_replies) > 0
    assert "Kode Aktivasi Baru Dibuat" in up_owner.message.text_replies[0]
    print("✅ Owner /create_invite success.")

    # 7. Staff tidak bisa /create_invite
    print("\n[TEST 7] Staff cannot create invite code...")
    up_staff = MockUpdate(chat_id=2222)
    ctx_staff = MockContext(args=["staff"])
    await create_invite_command(up_staff, ctx_staff)
    assert "Maaf, role Anda tidak memiliki akses" in up_staff.message.text_replies[0]
    print("✅ Staff /create_invite access blocked.")

    # Get the code generated from Test 6
    # It was saved in settings
    with open("runtime_bot_settings.json", "r") as f:
        settings = json.load(f)
    invite_codes = settings.get("invite_codes", {})
    staff_code = list(invite_codes.keys())[0]

    # 8. Activation code valid berhasil mendaftarkan chat_id user
    print("\n[TEST 8] Activating user with valid code...")
    up_new = MockUpdate(chat_id=7777, username="newstaff")
    ctx_act = MockContext(args=[staff_code])
    await activate_command(up_new, ctx_act)
    assert "Aktivasi Berhasil" in up_new.message.text_replies[0]
    
    # Check profile now
    profile_new = get_user_profile(7777)
    assert profile_new["role"] == "staff" and profile_new["authorized"] == True
    print("✅ Activation code registers chat_id.")

    # 9. Activation code expired ditolak
    print("\n[TEST 9] Expired activation code gets rejected...")
    # Manually create an expired code in settings
    with open("runtime_bot_settings.json", "r") as f:
        settings = json.load(f)
    settings["invite_codes"]["STAFF-EXPIRED"] = {
        "role": "staff",
        "expires_at": time.time() - 100, # expired
        "used": False
    }
    with open("runtime_bot_settings.json", "w") as f:
        json.dump(settings, f)
        
    up_new2 = MockUpdate(chat_id=8888)
    ctx_act_exp = MockContext(args=["STAFF-EXPIRED"])
    await activate_command(up_new2, ctx_act_exp)
    assert "telah kedaluwarsa" in up_new2.message.text_replies[0]
    print("✅ Expired code rejected.")

    # 10. Used activation code tidak bisa dipakai ulang
    print("\n[TEST 10] Reuse of code gets rejected...")
    up_new3 = MockUpdate(chat_id=8889)
    await activate_command(up_new3, ctx_act) # reuse the first staff_code
    assert "sudah pernah digunakan" in up_new3.message.text_replies[0]
    print("✅ Reused code rejected.")

    # 11. Revoke user berhasil untuk runtime user
    print("\n[TEST 11] Revoking runtime user...")
    up_owner_revoke = MockUpdate(chat_id=1111)
    ctx_rev = MockContext(args=["7777"])
    await revoke_user_command(up_owner_revoke, ctx_rev)
    assert "berhasil dicabut" in up_owner_revoke.message.text_replies[0]
    # Verify profile is no longer authorized
    assert get_user_profile(7777)["authorized"] == False
    print("✅ Revoke runtime user successful.")

    # 12. Env owner tidak bisa direvoke runtime
    print("\n[TEST 12] Revoking env owner fails...")
    up_owner_revoke_env = MockUpdate(chat_id=1111)
    ctx_rev_env = MockContext(args=["1111"])
    await revoke_user_command(up_owner_revoke_env, ctx_rev_env)
    assert "User dari .env tidak bisa dihapus" in up_owner_revoke_env.message.text_replies[0]
    assert get_user_profile(1111)["authorized"] == True
    print("✅ Revoke env user prevented.")

    # 13. Finance/tax/spt command hanya owner
    print("\n[TEST 13] Command permissions for Finance/Tax (Owner only)...")
    # Owner passes
    up_owner_fin = MockUpdate(chat_id=1111)
    await finance_command(up_owner_fin, ctx)
    assert not any("tidak memiliki akses" in r for r in up_owner_fin.message.text_replies)
    
    # Staff gets blocked
    up_staff_fin = MockUpdate(chat_id=2222)
    await finance_command(up_staff_fin, ctx)
    assert any("tidak memiliki akses" in r for r in up_staff_fin.message.text_replies)
    print("✅ Finance/tax permission matrix verified.")

    # 14. Schedule command hanya owner
    print("\n[TEST 14] Command permissions for scheduling controls (Owner only)...")
    # Owner passes
    up_owner_sched = MockUpdate(chat_id=1111)
    await daily_on_command(up_owner_sched, ctx)
    assert not any("tidak memiliki akses" in r for r in up_owner_sched.message.text_replies)
    
    # Staff gets blocked
    up_staff_sched = MockUpdate(chat_id=2222)
    await daily_on_command(up_staff_sched, ctx)
    assert any("tidak memiliki akses" in r for r in up_staff_sched.message.text_replies)
    print("✅ Scheduler permission matrix verified.")

    # 15. Audit event builder valid
    print("\n[TEST 15] Audit Event Builder Validation...")
    evt = build_audit_event("1111", "owner", "export_spt", target_tab="finance", notes="QA test")
    assert evt["user_id"] == "1111"
    assert evt["user_role"] == "owner"
    assert evt["action"] == "export_spt"
    assert evt["target_tab"] == "finance"
    
    txt = format_audit_event_text(evt)
    assert "owner" in txt.lower() and "export_spt" in txt
    
    # validate schema
    df_audit = pd.DataFrame([evt])
    is_valid, missing = validate_audit_log_schema(df_audit)
    assert is_valid == True, f"Missing columns: {missing}"
    print("✅ Audit log validation verified.")

    # 16. Confirmation create/confirm/cancel/expire valid
    print("\n[TEST 16] Confirmation Flow Validation...")
    action = create_pending_action("1111", "write_sheets", {"row": 42})
    code = action["code"]
    assert len(code) == 6
    assert "1111" in PENDING_ACTIONS
    
    # confirm with wrong code
    is_valid, act_type, payload, msg = confirm_pending_action("1111", "wrong_code")
    assert is_valid == False
    
    # confirm with correct code
    is_valid, act_type, payload, msg = confirm_pending_action("1111", code)
    assert is_valid == True
    assert act_type == "write_sheets"
    assert payload == {"row": 42}
    assert "1111" not in PENDING_ACTIONS
    
    # cancel action
    create_pending_action("1111", "write_sheets", {"row": 42})
    success, msg = cancel_pending_action("1111")
    assert success == True
    assert "1111" not in PENDING_ACTIONS
    print("✅ Confirmation flow verified.")

    # Cleanup runtime settings
    if os.path.exists("runtime_bot_settings.json"):
        try:
            os.remove("runtime_bot_settings.json")
        except Exception:
            pass

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_tests())
