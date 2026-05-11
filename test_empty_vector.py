import asyncio
import scripts.dependencies as d
from engine.vector import create_vector

async def main():
    d.load_model()
    try:
        vec = await create_vector([])
        print("Success", vec)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
