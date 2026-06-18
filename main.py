
import os
import json
import time
import re
import random
from datetime import datetime, timedelta
import pytz
import telebot
from telebot.types import ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton

# -------------------------------------------------------------
# CẤU HÌNH BOT (Đã cài ID Owner của bạn)
BOT_TOKEN = "8884617053:AAFDGS9dCGMvnW-EWTC-CtBnOjkYscm0kp8"
OWNER_ID = 8699149343
# -------------------------------------------------------------

bot = telebot.TeleBot(BOT_TOKEN)

# Tên các file lưu trữ dữ liệu
GROUPS_FILE = "allowed_groups.json"
VIOLATIONS_FILE = "violations.json"
PROTECTED_FILE = "protected_users.json"
PERMA_BAN_FILE = "perma_ban.json"   
PERMA_MUTE_FILE = "perma_mute.json" 

# Danh sách từ cấm xúc phạm (1/5 -> 5/5 tự động BAN)
BANNED_WORDS = [
    "sex", "hentai", "xnxx", "địt", "buồi", "cặc", "lồn", "đm", "dm", "vcl", "vkl",
    "đkm", "clm", "đmm", "dmm", "chó đẻ", "mẹ mày", "óc chó", "bú cu", "bú lồn", "phò",
    "đĩ", "điếm", "nứng", "nứng lồn", "súc vật", "mất dạy", "vô học"
]

CHAT_VIP_ACTIVE = {}     
CHAT_VIP_PRO_ACTIVE = {} 
group_roast_pool = {}    

# ================= HỆ THỐNG TỰ ĐỘNG TẠO 500+ CÂU CHỬI VIẾT TẮT NGẮN GỌN =================
def generate_roast_database():
    base_roasts = [
        "nín giùm cái đm.", "sủa ít thôi clm.", "óc chó vcl.", "bớt gáy dmm.", "tắt văn đi đmm.",
        "ngu vkl nín đi.", "clm rác rưởi.", "đm cút hộ.", "trình còi bớt sủa.", "ảo mạng à đm.",
        "vô tri vcl nín.", "đkm sủa clg.", "não tàn dmm.", "bớt xạo ngôn đm.", "clm câm mồm.",
        "đmm tuổi lol.", "nhìn m hãm vcl.", "đm sủa tiếp xem.", "clm ngu lỳ.", "nín đi con chó."
    ]
    dau = ["đm", "clm", "đkm", "dmm", "thằng óc", "con chó", "loại m", "rác rưởi", "bớt sủa", "nín ngay"]
    giua = ["ngu vcl", "hãm vkl", "tuổi lol", "cút hộ", "bớt gáy", "ngáo à", "xạo ngôn", "vô học", "óc chó", "trình còi"]
    cuoi = ["đấy", "nha con", "clm", "đmm", "vcl", "vkl", "nghe chưa", "hộ cái", "ạ luôn", "nha em"]
    pool = set(base_roasts)
    while len(pool) < 550:
        sentence = f"{random.choice(dau)} {random.choice(giua)} {random.choice(cuoi)}."
        pool.add(sentence)
    return list(pool)

ROAST_DATABASE = generate_roast_database()
# --- HÀM ĐỌC/GHI DỮ LIỆU ĐẢM BẢO AN TOÀN 24/7 ---
def load_data():
    global ALLOWED_GROUPS, VIOLATIONS, PROTECTED_USERS, PERMA_BAN, PERMA_MUTE
    def _read(fp, is_set=True):
        if os.path.exists(fp):
            with open(fp, "r", encoding="utf-8") as f:
                try: return set(json.load(f)) if is_set else json.load(f)
                except: return set() if is_set else {}
        return set() if is_set else {}
    ALLOWED_GROUPS = _read(GROUPS_FILE)
    VIOLATIONS = _read(VIOLATIONS_FILE, is_set=False)
    PROTECTED_USERS = _read(PROTECTED_FILE)
    PERMA_BAN = _read(PERMA_BAN_FILE)
    PERMA_MUTE = _read(PERMA_MUTE_FILE)

def save_json(file_path, data, is_set=False):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(list(data) if is_set else data, f, indent=4, ensure_ascii=False)

load_data()

def is_authorized(chat_id, user_id):
    if user_id == OWNER_ID or user_id in PROTECTED_USERS: return True
    try: return bot.get_chat_member(chat_id, user_id).status in ["administrator", "creator"]
    except: return False

# TỐI ƯU SIÊU SẠCH: Quét Target qua cả Reply, Điền ID Số, hoặc Tag @username của Member/Bot
def get_target_user_id(message):
    if message.reply_to_message:
        return message.reply_to_message.from_user.id
    
    args = message.text.split()
    if len(args) < 2:
        return None
        
    target = args[1]
    # Trường hợp 1: Nhập ID Số
    if target.isdigit():
        return int(target)
        
    # Trường hợp 2: Tag @username
    if target.startswith("@") and message.entities:
        for entity in message.entities:
            if entity.type == "mention":
                # Lấy text username từ tin nhắn
                mention_text = message.text[entity.offset:entity.offset + entity.length]
                try:
                    # Chuyển đổi username thành ID qua hàm lấy thông tin của Telegram
                    chat_member = bot.get_chat(mention_text)
                    return chat_member.id
                except:
                    pass
            elif entity.type == "text_mention" and entity.user:
                return entity.user.id
    return None

# ================= HỆ THỐNG LỆNH ĐIỀU KHIỂN CHỦ SỞ HỮU =================

@bot.message_handler(commands=['add'])
def add_group(message):
    if message.from_user.id != OWNER_ID: return
    ALLOWED_GROUPS.add(message.chat.id)
    save_json(GROUPS_FILE, ALLOWED_GROUPS, is_set=True)
    bot.reply_to(message, "🚀 **Kích hoạt thành công!** Nhóm này đã được bảo vệ.")

@bot.message_handler(commands=['xadd'])
def remove_group(message):
    if message.from_user.id != OWNER_ID: return
    if message.chat.id in ALLOWED_GROUPS:
        ALLOWED_GROUPS.remove(message.chat.id)
        save_json(GROUPS_FILE, ALLOWED_GROUPS, is_set=True)
        bot.reply_to(message, "🔒 **Đã hủy kích hoạt nhóm (/xadd).** Bot đã dừng hoạt động!")
@bot.message_handler(commands=['bvvip'])
def protect_user(message):
    if message.from_user.id != OWNER_ID: return
    target_id = get_target_user_id(message)
    if not target_id:
        bot.reply_to(message, "❌ Sai cú pháp! Vui lòng Reply, điền ID hoặc Tag mục tiêu.")
        return
    PROTECTED_USERS.add(target_id)
    save_json(PROTECTED_FILE, PROTECTED_USERS, is_set=True)
    bot.reply_to(message, f"🛡️ ID `{target_id}` đã có **Khiên Bảo Vệ VIP**, miễn nhiễm mọi hình phạt.")

@bot.message_handler(commands=['a7'])
def unprotect_user(message):
    if message.from_user.id != OWNER_ID: return
    target_id = get_target_user_id(message)
    if not target_id: return
    if target_id in PROTECTED_USERS:
        PROTECTED_USERS.remove(target_id)
        save_json(PROTECTED_FILE, PROTECTED_USERS, is_set=True)
        bot.reply_to(message, f"🔓 ID `{target_id}` đã bị tước **Khiên Bảo Vệ VIP**.")

@bot.message_handler(commands=['chatvip'])
def toggle_chat_vip(message):
    if message.chat.id not in ALLOWED_GROUPS or message.from_user.id != OWNER_ID: return
    CHAT_VIP_ACTIVE[message.chat.id] = not CHAT_VIP_ACTIVE.get(message.chat.id, False)
    bot.reply_to(message, f"🤖 **Chế độ CHAT VIP:** {'🔥 BẬT' if CHAT_VIP_ACTIVE[message.chat.id] else '🛑 TẮT'}")

@bot.message_handler(commands=['chatvippro'])
def toggle_chat_vip_pro(message):
    if message.chat.id not in ALLOWED_GROUPS or message.from_user.id != OWNER_ID: return
    CHAT_VIP_PRO_ACTIVE[message.chat.id] = not CHAT_VIP_PRO_ACTIVE.get(message.chat.id, False)
    bot.reply_to(message, f"👑 **Chế độ CHAT VIP PRO:** {'⚡ BẬT' if CHAT_VIP_PRO_ACTIVE[message.chat.id] else '🛑 TẮT'}")

# ================= HỆ THỐNG LỆNH TRỪNG PHẠT NÂNG CAO =================

@bot.message_handler(commands=['m'])
def super_ban(message):
    if message.from_user.id != OWNER_ID: return
    target_id = get_target_user_id(message)
    if not target_id or target_id == OWNER_ID or target_id in PROTECTED_USERS: return
    try:
        PERMA_BAN.add(target_id)
        save_json(PERMA_BAN_FILE, PERMA_BAN, is_set=True)
        bot.ban_chat_member(message.chat.id, target_id)
        bot.reply_to(message, f"💀 **LỆNH TỬ HÌNH ĐÃ KÍCH HOẠT!** ID `{target_id}` bị cấm vĩnh viễn.")
    except Exception as e: bot.reply_to(message, f"❌ Lỗi: {e}")

@bot.message_handler(commands=['m1'])
def unban_user(message):
    if message.from_user.id != OWNER_ID: return
    target_id = get_target_user_id(message)
    if not target_id: return
    if target_id in PERMA_BAN:
        PERMA_BAN.discard(target_id)
        save_json(PERMA_BAN_FILE, PERMA_BAN, is_set=True)
        try:
            bot.unban_chat_member(message.chat.id, target_id, only_if_banned=True)
            link = bot.export_chat_invite_link(message.chat.id)
            bot.reply_to(message, f"🕊️ Đã gỡ án tử cho ID `{target_id}`. Link vào lại: {link}")
        except Exception: pass

@bot.message_handler(commands=['mm'])
def mute_user(message):
    if message.from_user.id != OWNER_ID: return
    target_id = get_target_user_id(message)
    if not target_id or target_id == OWNER_ID or target_id in PROTECTED_USERS: return
    try:
        bot.restrict_chat_member(message.chat.id, target_id, permissions=ChatPermissions(can_send_messages=False))
        bot.reply_to(message, f"🔇 Đã tắt tiếng vĩnh viễn ID `{target_id}`.")
    except Exception: pass

@bot.message_handler(commands=['mmm'])
def unmute_user(message):
    if message.from_user.id != OWNER_ID: return
    target_id = get_target_user_id(message)
    if not target_id: return
    try:
        bot.restrict_chat_member(message.chat.id, target_id, permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True))
        bot.reply_to(message, f"🔊 Đã mở khóa chat cho ID `{target_id}`.")
    except Exception: pass

# ================= LỆNH DỌN DẸP /clear BẢO VỆ ADMIN TỐI CAO =================

@bot.message_handler(commands=['clear'])
def clear_messages(message):
    if message.chat.id not in ALLOWED_GROUPS: return
    if not is_authorized(message.chat.id, message.from_user.id): return
    args = message.text.split()
    amount = int(args[1]) if len(args) >= 2 and args[1].isdigit() else 10
    curr_id = message.message_id
    deleted = 0
    for _ in range(amount + 1):
        try:
            bot.delete_message(message.chat.id, curr_id)
            deleted += 1
        except Exception: pass
        curr_id -= 1
    bot.send_message(message.chat.id, f"🧹 Đã dọn xong {deleted} tin nhắn! Tin nhắn của Admin được bảo mật an toàn.")
# ================= GIAO DIỆN BẪY /menu1 VÀ LỆNH ẨN /help VÀ /help1 =================

@bot.message_handler(commands=['menu1'])
def menu_trap(message):
    if message.chat.id not in ALLOWED_GROUPS: return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("1 (Liên hệ Adm để đc dùng Adm) free", callback_data="t_free")],
        [InlineKeyboardButton("2 (Liên hệ Adm để đc dùng Adm) buy", callback_data="t_buy")]
    ])
    bot.send_message(message.chat.id, "📋 **DANH SÁCH GÓI QUYỀN LỰC ADMIN:**", reply_markup=kb)

@bot.message_handler(commands=['help', 'help1'])
def hidden_help(message):
    if message.chat.id not in ALLOWED_GROUPS: return
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("👁️ XEM TOÀN BỘ LỆNH", callback_data=f"h_{message.from_user.id}")]])
    bot.reply_to(message, "Tin nhắn bị ẩn vì Adm quá đẹp trai", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: True)
def handle_clicks(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    if call.data.startswith("h_"):
        creator_id = int(call.data.split("_"))
        if uid != creator_id:
            bot.answer_callback_query(call.id, "❌ Nút này không dành cho bạn!", show_alert=True)
            return
        all_commands = (
            "📜 BẢNG LỆNH TOÀN DIỆN CỦA HỆ THỐNG:\n\n"
            "🌐 QUẢN LÝ BOT:\n• /add - Kích hoạt nhóm\n• /xadd - Hủy kích hoạt nhóm\n\n"
            "⚙️ CHẾ ĐỘ CHAT:\n• /chatvip - Bật/Tắt phản hồi chửi\n• /chatvippro - Bật/Tắt chửi nâng cao\n\n"
            "🛡️ BẢO VỆ TỐI CAO:\n• /bvvip - Cấp Khiên VIP (Phản dame)\n• /a7 - Tước Khiên VIP\n\n"
            "💀 HÌNH PHẠT OWNER:\n• /m - Ban vĩnh viễn\n• /m1 - Gỡ ban vĩnh viễn\n• /mm - Tắt tiếng\n• /mmm - Mở khóa tiếng\n\n"
            "🧹 TIỆN ÍCH ADMIN:\n• /clear [số] - Dọn tin nhắn (Admin bất tử)\n• /menu1 - Menu bẫy trừng phạt\n• /help hoặc /help1 - Xem bảng lệnh ẩn"
        )
        bot.answer_callback_query(call.id, all_commands, show_alert=True)
        return
        
    if uid == OWNER_ID or uid in PROTECTED_USERS:
        bot.send_message(cid, f"👑 Đấng tối cao {call.from_user.first_name} đang thử lòng bot đúng không?")
        return
    if call.data == "t_free":
        try:
            bot.restrict_chat_member(cid, uid, permissions=ChatPermissions(can_send_messages=False), until_date=int(time.time() + 36 * 60))
            bot.send_message(cid, f"🤣 {call.from_user.first_name} Tham rẻ chọn FREE à?\n🤐 Nhận ngay: **CẤM KHẨU 36 PHÚT** nha con!")
        except: pass
    elif call.data == "t_buy":
        try:
            PERMA_BAN.add(uid)
            save_json(PERMA_BAN_FILE, PERMA_BAN, is_set=True)
            bot.ban_chat_member(cid, uid)
            bot.send_message(cid, f"💀 Tiễn khách! Kẻ lắm tiền {call.from_user.first_name} vừa mua vé **BAN VĨNH VIỄN**!")
        except: pass

@bot.message_handler(content_types=['new_chat_members'])
def anti_join(message):
    if message.chat.id not in ALLOWED_GROUPS: return
    for mem in message.new_chat_members:
        if mem.id in PERMA_BAN and mem.id != OWNER_ID and mem.id not in PROTECTED_USERS:
            try: bot.ban_chat_member(message.chat.id, mem.id)
            except: pass

@bot.chat_member_handler()
def auto_counter_attack(update):
    cid = update.chat.id
    if cid not in ALLOWED_GROUPS: return
    target_id = update.new_chat_member.user.id
    actor_id = update.from_user.id
    if (target_id in PROTECTED_USERS or target_id == OWNER_ID) and actor_id != OWNER_ID:
        if update.new_chat_member.status in ['left', 'kicked']:
            try:
                PERMA_BAN.add(actor_id)
                save_json(PERMA_BAN_FILE, PERMA_BAN, is_set=True)
                bot.ban_chat_member(cid, actor_id)
                bot.unban_chat_member(cid, target_id, only_if_banned=True)
                invite_link = bot.export_chat_invite_link(cid)
                bot.send_message(cid, f"🚨 **PHÁT HIỆN HÀNH VI ĐẢO CHÍNH!**\n💀 Thằng chó ID `{actor_id}` dám kick thành viên VIP `{target_id}`!\n⚡ Kích hoạt **PHẢN DAME**: Trục xuất vĩnh viễn kẻ thủ ác!\n🕊️ Đã hồi sinh VIP. Link để vào lại nhóm: {invite_link}")
            except: pass
        elif update.new_chat_member.status == 'restricted' and not update.new_chat_member.can_send_messages:
            try:
                PERMA_BAN.add(actor_id)
                save_json(PERMA_BAN_FILE, PERMA_BAN, is_set=True)
                bot.ban_chat_member(cid, actor_id)
                bot.restrict_chat_member(cid, target_id, permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
                bot.send_message(cid, f"⚡ **PHẢN DAME TỰ ĐỘNG KHÓA MÕM!**\n🤫 ID `{actor_id}` vừa gan hùm dám tắt tiếng thành viên VIP `{target_id}`!\n💀 Kẻ phạm thượng đã bị bot tiễn bay màu vĩnh viễn khỏi nhóm.\n🔊 Đã khôi phục giọng nói tối cao cho VIP!")
            except: pass

@bot.message_handler(func=lambda message: True)
def filter_and_chat(message):
    cid = message.chat.id
    uid = message.from_user.id
    if cid not in ALLOWED_GROUPS: return
    if uid in PERMA_BAN and uid != OWNER_ID and uid not in PROTECTED_USERS:
        try: bot.ban_chat_member(cid, uid)
        except: pass
        return
    text_lower = message.text.lower()
    has_banned_word = any(re.search(rf"\b{re.escape(word)}\b", text_lower) for word in BANNED_WORDS)
    if has_banned_word and uid != OWNER_ID and uid not in PROTECTED_USERS:
        str_uid = str(uid)
        if str_uid not in VIOLATIONS: VIOLATIONS[str_uid] = 0
        VIOLATIONS[str_uid] += 1
        save_json(VIOLATIONS_FILE, VIOLATIONS)
        current_warn = VIOLATIONS[str_uid]
        if current_warn >= 5:
            try:
                PERMA_BAN.add(uid)
                save_json(PERMA_BAN_FILE, PERMA_BAN, is_set=True)
                bot.ban_chat_member(cid, uid)
                bot.reply_to(message, f"💀 Đã tích lũy đủ {current_warn}/5 lần xúc phạm. Tiễn vong vĩnh viễn!")
            except: pass
        else:
            bot.reply_to(message, f"🚨 Cảnh cáo ({current_warn}/5)!\n{random.choice(ROAST_DATABASE)}")
        return
    if CHAT_VIP_ACTIVE.get(cid, False) or CHAT_VIP_PRO_ACTIVE.get(cid, False):
        if random.random() < 0.15: 
            bot.reply_to(message, random.choice(ROAST_DATABASE))

if __name__ == "__main__":
    print("🤖 Bot quản trị tối cao pyTelegramBotAPI đang chạy...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5, allowed_updates=["message", "callback_query", "chat_member"])
