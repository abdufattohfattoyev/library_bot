from environs import Env

# environs kutubxonasidan foydalanish
env = Env()
env.read_env()

BOT_TOKEN = env.str("BOT_TOKEN")  # Bot token
ADMINS = env.list("ADMINS", subcast=int)  # Adminlar ro'yxati (int sifatida)
IP = env.str("ip")  # Xosting IP manzili

