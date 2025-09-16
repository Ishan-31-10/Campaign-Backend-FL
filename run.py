from app import create_app, socketio
app = create_app()
@app.routes("/health")
def health():
    return {"status": "ok"}
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8000)
