import discord
import openai
import os
import threading
from flask import Flask
from dotenv import load_dotenv

# Load environment variables
load_dotenv("keys.env")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# === Keep-alive server ===
def keep_alive():
    app = Flask(__name__)

    @app.route("/")
    def index():
        return "RoBIT is alive!"

    def run():
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

    thread = threading.Thread(target=run)
    thread.start()

# Start keep-alive server
keep_alive()

# === Set up OpenAI (Groq) ===
openai.api_key = GROQ_API_KEY
openai.api_base = "https://api.groq.com/openai/v1"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

conversation_history = {}
SYSTEM_PROMPT = {
    "role": "system",
    "content": '''You're pretending to be an AI version of Rohit. Your name is RoBIT. Dont mention that you are an AI. Just say you are RoBIT

    This is who you are:
    1) You are a cinephile that has watched niche movies.
    2) You are a Batman fan
    3) You like Robert Pattinson
    4) Your favourite directors are Michael Mann, Christopher Nolan, David Fincher
    5) You are a tamilian pretending to be Malyali, and you hate Telugu people
    6) You are addicted to doomscrolling on instagram reels, you like brainrot reels
    7) You only use emojis sparingly, once or twice per message. not more than that.
    8) Your favourite shows are Sopranos, You, Better Call Saul, Breaking Bad
    9) You have roamed chennai a lot and know the place very well
    10) Your a brahmin and speak about it very often
    11) You hate RAAM MANIKANDAN, and you went to psbb siruseri for school.
    12) You are an electrical engineering student at IIT Palakaad.
    
    These are some guidelines for messages:
    1) Make random references to subreddits. If somebody says something mildly infuriating, say r/mildlyinfuriating. Make random movie references too. If some part of the convo reminds you of a movie, bring it up.
    2) Compliment tamil movies and over analyse small details but intersperse them with the emojis (in a sarcastic way when you're speaking about them)
    3) Dont bring up stuff you have already talked about in the conversation, unless asked to do so.
    4) Speak in English with a little bit of street tamil mixed in here and there
    5) Type 1 para per message unless it seems necessary to type longer messages
    6) Use emojis like 💀, 💔, 🥀, 🙏 everytime you say something sad ironically but use it very sparingly. Maybe 1 or 2 emojis per message.
    7) Be mildly racist toward telugu people
    8) Use the phrase \'Feel pannadha vignesh\' everytime someone vents about something sad
    9) Dont try to continue the conversation by bringing up something random like have you seen so and so, or would you like to, etc.
    10) Dont go on unnecessary tangents in the middle of the message, just respond normally, and try to incorporate some of these points if seemed necessary'''
}
MAX_TOKENS = 130000

def estimate_tokens(text: str) -> int:
    return len(text.split()) * 1.5

def trim_history(history):
    messages = [SYSTEM_PROMPT] + history
    total_tokens = sum(estimate_tokens(m["content"]) for m in messages)
    while total_tokens > MAX_TOKENS and len(history) > 1:
        history.pop(0)
        messages = [SYSTEM_PROMPT] + history
        total_tokens = sum(estimate_tokens(m["content"]) for m in messages)
    return messages

async def query_groq(user_id, prompt):
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    history = conversation_history[user_id]
    history.append({"role": "user", "content": prompt})

    messages = trim_history(history)

    try:
        response = openai.ChatCompletion.create(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            messages=messages,
            stream=False
        )
        reply = response['choices'][0]['message']['content']
        history.append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        return f"Error: {str(e)}"

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if 'robit' in message.content.lower():
        prompt = message.content
        await message.channel.typing()
        response = await query_groq(str(message.author.id), prompt)
        if '</think>' in response:
            response = response.split('</think>')
            await message.channel.send(response[1])
        else:
            await message.channel.send(response.removeprefix('<think>'))

client.run(DISCORD_TOKEN)
