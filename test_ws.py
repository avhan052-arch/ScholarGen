from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws/test")
async def websocket_test(websocket: WebSocket):
    await websocket.accept()
    print("🚀 TEST: Koneksi Masuk!")
    
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Pesan: {data}")
    except:
        print("🚀 TEST: Koneksi Terputus")