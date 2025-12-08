import asyncio
import socketio
import random

SERVER_URL = 'http://localhost:5000'
BOT_COUNT = 100

# List of random base names to make it look like a real class
NAMES = [
    "Alice", "Bob", "Charlie", "Dave", "Eve", "Frank", "Grace", "Heidi",
    "Ivan", "Judy", "Kevin", "Larry", "Mallory", "Ned", "Olivia", "Peggy",
    "Quentin", "Rupert", "Steve", "Trent", "Ursula", "Victor", "Walter",
    "Xavier", "Yvonne", "Zelda", "Aron", "Brody", "Caleb", "Drake"
]

async def start_bot(bot_id):
    avatar_id = random.randint(1, 10)
    # Create a unique client instance for this bot
    sio = socketio.AsyncClient()
    
    # Generate a name (e.g., "Steve_12")
    base_name = random.choice(NAMES)
    bot_name = f"{base_name}_{bot_id}"

    @sio.event
    async def connect():
        # print(f"[{bot_name}] Connected!")
        #await sio.emit('join_game', {'name': bot_name})
        await sio.emit('join_game', {'name': bot_name, 'avatar': avatar_id})

    @sio.event
    async def new_question(data):
        # 1. Simulate "Reading/Thinking" time (0.5s to 8s)
        # This tests your scoring logic's time decay
        delay = random.uniform(0.5, 8.0)
        await asyncio.sleep(delay)
        
        # 2. Pick a random answer
        choice = random.choice(['A', 'B', 'C', 'D'])
        
        # print(f"[{bot_name}] Answering {choice} after {delay:.1f}s")
        await sio.emit('submit_answer', {'answer': choice})

    @sio.event
    async def game_over(data):
        print(f"[{bot_name}] Game Over signal received. Disconnecting.")
        await sio.disconnect()

    try:
        await sio.connect(SERVER_URL)
        await sio.wait()
    except Exception as e:
        print(f"[{bot_name}] Connection Error: {e}")

async def main():
    print(f"--- Spawning {BOT_COUNT} bots ---")
    
    # Create a list of tasks (one for each bot)
    tasks = []
    for i in range(BOT_COUNT):
        tasks.append(start_bot(i))
        # Stagger connections slightly so they don't all hit at exact ms
        await asyncio.sleep(0.05)
    
    print("--- All bots running. Start the game on the Host screen! ---")
    
    # Keep them running
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopping stress test...")
