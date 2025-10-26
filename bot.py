import os
import random
import time
import requests
import logging
from threading import Thread
from datetime import datetime

print("🤖 মাল্টি-বট রিয়েকশন সিস্টেম - Railway ভার্সন")
print("🚀 24/7 Running on Railway")

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('multi_bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Environment variable থেকে বট টোকেন নিন
BOT_TOKENS_STR = os.environ.get("BOT_TOKENS", "")

if not BOT_TOKENS_STR:
    print("❌ BOT_TOKENS environment variable সেট করা নেই!")
    print("📝 Railway Dashboard → Variables → BOT_TOKENS")
    exit(1)

# টোকেনগুলো আলাদা করুন
BOT_TOKENS = [token.strip() for token in BOT_TOKENS_STR.split(",") if token.strip()]

if not BOT_TOKENS:
    print("❌ কোনো valid বট টোকেন পাওয়া যায়নি!")
    exit(1)

print(f"📦 {len(BOT_TOKENS)}টি বট টোকেন লোড করা হয়েছে")

# ইমোজি লিস্ট
emojis = ["👍", "❤", "🔥", "👏", "😍", "🎉", "🤩", "💯", "😁", "🥰", "⚡", "✨", "🌟", "💫", "🙏"]

class RailwayMultiBotSystem:
    def __init__(self, tokens):
        self.working_bots = []
        self.start_time = datetime.now()
        self.message_count = 0
        self.successful_reactions = 0
        self.last_update_id = 0  # ✅ FIX: Initialize with 0 instead of None
        
        print("🔍 বটগুলো চেক করা হচ্ছে...")
        
        # প্রতিটি বট টেস্ট করুন
        for i, token in enumerate(tokens, 1):
            if self.test_bot(token):
                bot_info = self.get_bot_info(token)
                if bot_info:
                    self.working_bots.append({
                        "token": token,
                        "base_url": f"https://api.telegram.org/bot{token}",
                        "name": bot_info.get("first_name", f"বট-{i}"),
                        "username": bot_info.get("username", f"bot_{i}")
                    })
                    print(f"✅ বট {i}: {bot_info.get('first_name', 'Unknown')} (@{bot_info.get('username', 'N/A')})")
                else:
                    print(f"⚠️ বট {i}: ইনফো পাওয়া যায়নি")
            else:
                print(f"❌ বট {i}: কাজ করছে না")
        
        print(f"\n🔧 {len(self.working_bots)}টি বট সফলভাবে লোড করা হয়েছে")
        
        if len(self.working_bots) == 0:
            print("❌ কোনো বট কাজ করছে না! সেটআপ চেক করুন")
            return
        
        # সব বটের webhook ডিলিট করুন
        self.delete_all_webhooks()
        
        # Start monitoring thread
        self.monitor_thread = Thread(target=self.monitor_system, daemon=True)
        self.monitor_thread.start()
    
    def test_bot(self, token):
        """বটটি কাজ করছে কিনা চেক করুন"""
        try:
            url = f"https://api.telegram.org/bot{token}/getMe"
            response = requests.get(url, timeout=10)
            result = response.json()
            return result.get('ok', False)
        except Exception as e:
            logger.error(f"Bot test failed: {e}")
            return False
    
    def get_bot_info(self, token):
        """বটের তথ্য নিন"""
        try:
            url = f"https://api.telegram.org/bot{token}/getMe"
            response = requests.get(url, timeout=10)
            result = response.json()
            return result.get('result', {}) if result.get('ok') else {}
        except:
            return {}
    
    def delete_all_webhooks(self):
        """সব বটের webhook ডিলিট করুন"""
        for bot in self.working_bots:
            try:
                requests.get(f"{bot['base_url']}/deleteWebhook", timeout=5)
            except:
                pass
        print("✅ সব বটের ওয়েবহুক ডিলিট করা হয়েছে")
    
    def send_reaction(self, bot, chat_id, message_id, emoji):
        """একটি বট দিয়ে একটি রিয়েকশন দিন"""
        url = f"{bot['base_url']}/setMessageReaction"
        
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "reaction": [{"type": "emoji", "emoji": emoji}]
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                return True
            else:
                error = result.get('description', 'Unknown error')
                if "CHAT_ADMIN_REQUIRED" in error:
                    logger.warning(f"{bot['name']}: অ্যাডমিন পারমিশন প্রয়োজন")
                elif "bot is not a member" in error.lower():
                    logger.warning(f"{bot['name']}: গ্রুপে অ্যাড করা নেই")
                elif "REACTION_INVALID" in error:
                    logger.warning(f"{bot['name']}: ইমোজি সাপোর্ট করে না")
                return False
                
        except Exception as e:
            logger.error(f"{bot['name']} নেটওয়ার্ক এরর: {e}")
            return False
    
    def send_multiple_reactions(self, chat_id, message_id, num_reactions=None):
        """বিভিন্ন বট দিয়ে multiple reactions দিন"""
        if len(self.working_bots) == 0:
            logger.error("❌ কোনো কাজকরা বট নেই!")
            return 0
            
        if num_reactions is None:
            num_reactions = min(len(self.working_bots), 10)  # Max 10 reactions
        
        available_bots = random.sample(self.working_bots, min(num_reactions, len(self.working_bots)))
        
        logger.info(f"🎯 {len(available_bots)}টি রিয়েকশন দিচ্ছি...")
        
        success_count = 0
        
        for i, bot in enumerate(available_bots, 1):
            emoji = random.choice(emojis)
            success = self.send_reaction(bot, chat_id, message_id, emoji)
            
            if success:
                success_count += 1
                self.successful_reactions += 1
                logger.info(f"🤖 {bot['name']}: {emoji} ✅")
            else:
                logger.warning(f"🤖 {bot['name']}: {emoji} ❌")
            
            time.sleep(random.uniform(0.5, 2))  # Random delay to avoid rate limit
        
        logger.info(f"🎊 {success_count}টি রিয়েকশন সফল!")
        return success_count
    
    def get_updates_from_main_bot(self):
        """প্রধান বট থেকে মেসেজ পান"""
        if len(self.working_bots) == 0:
            return None
            
        main_bot = self.working_bots[0]
        url = f"{main_bot['base_url']}/getUpdates"
        
        try:
            # ✅ FIX: Proper offset handling
            params = {
                "timeout": 30, 
                "allowed_updates": ["message"],
                "offset": self.last_update_id + 1  # ✅ Now this will always work
            }
            
            response = requests.get(url, params=params, timeout=35)
            return response.json()
        except Exception as e:
            logger.error(f"Update error: {e}")
            return None
    
    def monitor_system(self):
        """সিস্টেম মনিটরিং"""
        while True:
            try:
                uptime = datetime.now() - self.start_time
                hours = uptime.total_seconds() // 3600
                minutes = (uptime.total_seconds() % 3600) // 60
                
                status_msg = f"""
📊 **System Status - Railway**
⏰ Uptime: {int(hours)}h {int(minutes)}m
🤖 Working Bots: {len(self.working_bots)}
📨 Messages Processed: {self.message_count}
✅ Successful Reactions: {self.successful_reactions}
🟢 Status: ACTIVE
                """
                print(status_msg)
                logger.info(f"Status: {len(self.working_bots)} bots, {self.message_count} msgs, {self.successful_reactions} reactions")
                
            except Exception as e:
                logger.error(f"Monitor error: {e}")
            
            time.sleep(300)  # 5 minutes
    
    def manual_reaction(self, chat_id, message_id, num_reactions=5):
        """ম্যানুয়ালি রিয়েকশন পাঠান"""
        logger.info(f"🔧 Manual reaction: chat={chat_id}, msg={message_id}, count={num_reactions}")
        return self.send_multiple_reactions(chat_id, message_id, num_reactions)
    
    def run_polling(self):
        """পোলিং মোডে চলুন"""
        if len(self.working_bots) == 0:
            logger.error("❌ কোনো কাজকরা বট নেই!")
            print("\n🔧 সমস্যা সমাধানের জন্য:")
            print("1. Railway Dashboard → Variables → BOT_TOKENS চেক করুন")
            print("2. বট টোকেনগুলো সঠিক কিনা চেক করুন")
            print("3. সব বটকে গ্রুপে অ্যাড করুন")
            print("4. সব বটকে অ্যাডমিন করুন") 
            print("5. 'Add reactions' পারমিশন দিন")
            return
        
        print(f"\n🚀 মাল্টি-বট সিস্টেম চালু হয়েছে!")
        print(f"📱 {len(self.working_bots)}টি বট রেডি")
        print("⏰ 24/7 Railway Server এ চলছে")
        print("💬 আপনার গ্রুপে মেসেজ পাঠান...")
        print("📊 স্ট্যাটাস প্রতি ৫ মিনিটে দেখাবে\n")
        
        try:
            while True:
                # নতুন মেসেজ চেক করুন
                updates_result = self.get_updates_from_main_bot()
                
                if updates_result and updates_result.get("ok"):
                    updates = updates_result.get("result", [])
                    
                    for update in updates:
                        update_id = update["update_id"]
                        
                        # ✅ FIX: Always update last_update_id
                        if update_id > self.last_update_id:
                            self.last_update_id = update_id
                        
                        if "message" in update:
                            message = update["message"]
                            # শুধু গ্রুপ মেসেজ প্রসেস করুন
                            if message.get("chat", {}).get("type") in ["group", "supergroup"]:
                                chat_id = message["chat"]["id"]
                                message_id = message["message_id"]
                                user_name = message.get("from", {}).get("first_name", "Unknown")
                                text = message.get("text", "")
                                
                                # কমান্ড চেক করুন
                                if text and text.startswith("/reaction"):
                                    # Manual reaction command
                                    parts = text.split()
                                    if len(parts) >= 4:
                                        try:
                                            target_chat_id = int(parts[1])
                                            target_message_id = int(parts[2])
                                            reaction_count = int(parts[3]) if len(parts) > 3 else 5
                                            
                                            success = self.manual_reaction(target_chat_id, target_message_id, reaction_count)
                                            logger.info(f"Manual reaction completed: {success} reactions")
                                        except ValueError:
                                            logger.error("Invalid manual reaction format")
                                    continue
                                
                                logger.info(f"📨 নতুন মেসেজ: {user_name} in chat {chat_id}")
                                
                                # রিয়েকশন দিন (only if not a command)
                                if not text.startswith('/'):
                                    success = self.send_multiple_reactions(chat_id, message_id)
                                    self.message_count += 1
                                    logger.info(f"📊 মোট মেসেজ: {self.message_count}, সফল রিয়েকশন: {success}")
                
                time.sleep(2)
                
        except KeyboardInterrupt:
            logger.info(f"🛑 সিস্টেম বন্ধ! মোট {self.message_count} মেসেজ প্রসেস করা হয়েছে")
        except Exception as e:
            logger.error(f"💥 মেইন লুপ এরর: {e}")
            print("🔄 ১০ সেকেন্ড পরে রিস্টার্ট হবে...")
            time.sleep(10)
            self.run_polling()  # Auto-restart

# মেইন প্রোগ্রাম
if __name__ == "__main__":
    # Railway-specific settings
    print("=" * 50)
    print("🤖 MULTI-BOT REACTION SYSTEM")
    print("🚀 DEPLOYED ON RAILWAY")
    print("=" * 50)
    
    system = RailwayMultiBotSystem(BOT_TOKENS)
    system.run_polling()