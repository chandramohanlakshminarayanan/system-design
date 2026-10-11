import apple_fm_sdk as fm
import asyncio

async def main():
    model = fm.SystemLanguageModel()
    
    is_available, reason = model.is_available()
    
    if is_available:
        session = fm.LanguageModelSession(model=model)
        response = await session.respond(prompt="Hello!")
        print(response)
    else:
        print(f"Not available: {reason}")

if __name__ == "__main__":
    asyncio.run(main())