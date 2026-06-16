import sys
import os
import asyncio
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set ALLOWED_CHAT_IDS to mock whitelist
os.environ["ALLOWED_CHAT_IDS"] = "123456789"

from modules.telegram_handlers import (
    spt_check_command,
    spt_pack_command,
    text_message_handler
)

class MockMessage:
    def __init__(self):
        self.text = ""
        self.reply_calls = []
        self.document_calls = []
        
    async def reply_text(self, text, parse_mode=None):
        self.reply_calls.append((text, parse_mode))
        print(f"      -> reply_text: {text.replace('<br/>', '\n')[:200]}...")
        return self
        
    async def reply_document(self, document, filename, caption, parse_mode=None):
        self.document_calls.append((filename, caption))
        print(f"      -> reply_document: {filename} ({caption[:80]}...)")
        return self
        
    async def delete(self):
        pass

class MockChat:
    def __init__(self, chat_id=123456789):
        self.id = chat_id

class MockUser:
    def __init__(self, chat_id=123456789):
        self.id = chat_id

class MockUpdate:
    def __init__(self, text="", chat_id=123456789):
        self.message = MockMessage()
        self.message.text = text
        self.effective_chat = MockChat(chat_id)
        self.effective_user = MockUser(chat_id)

async def test_bot_handlers():
    print("Testing Telegram bot handlers...")
    
    # 1. Test /spt_check
    print("  - Testing spt_check_command...")
    update = MockUpdate(chat_id=123456789)
    await spt_check_command(update, None)
    assert len(update.message.reply_calls) > 0, "No reply sent from spt_check_command"
    print("    OK")
    
    # 2. Test /spt_pack
    print("  - Testing spt_pack_command...")
    update = MockUpdate(chat_id=123456789)
    await spt_pack_command(update, None)
    # Check that a document was sent
    assert len(update.message.document_calls) > 0, "No document sent from spt_pack_command"
    print("    OK")
    
    # 3. Test text_message_handler keywords
    keywords_tests = [
        ("profit hari ini", "overview"), # should map to summary_command
        ("kirim pdf", "laporan harian"), # report_command
        ("apa yang harus dilakukan hari ini", "control room"), # owner_command
        ("laporan keuangan", "laba rugi"), # finance_command
        ("pajak tahun ini", "simulasi pajak"), # tax_command
        ("spt checklist", "checklist pajak"), # spt_check_command
        ("lampiran spt", "paket lampiran") # spt_pack_command
    ]
    
    for kw, label in keywords_tests:
        print(f"  - Testing NLP keyword: '{kw}' ({label})...")
        update = MockUpdate(text=kw, chat_id=123456789)
        await text_message_handler(update, None)
        assert len(update.message.reply_calls) > 0 or len(update.message.document_calls) > 0, f"No action taken for keyword: {kw}"
        print("    OK")
        
    # 4. Test unauthorized user block
    print("  - Testing unauthorized user block...")
    update = MockUpdate(chat_id=999999999) # different chat id
    await spt_check_command(update, None)
    assert len(update.message.reply_calls) > 0, "No response for blocked user"
    assert "akses" in update.message.reply_calls[0][0] or "tidak memiliki" in update.message.reply_calls[0][0], "Akses warning not sent"
    print("    OK (Successfully blocked)")

    print("All Telegram handlers tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_bot_handlers())
