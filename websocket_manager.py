from fastapi import WebSocket
from typing import List, Dict
from sqlalchemy.orm import Session
import database


class ConnectionManager:
    def __init__(self):
        # Dictionary untuk menyimpan koneksi user berdasarkan ID mereka
        # Contoh: { 1: [WebSocket1, WebSocket2], 2: [WebSocket3] }
        self.active_connections: Dict[int, List[WebSocket]] = {}

        # --- BARU: List khusus Admin (untuk update tabel) ---
        self.admin_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, user_id: int):
        # await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        print(f"✅ User {user_id} connected via WebSocket.")

    def disconnect(self, websocket: WebSocket, user_id: int = None):
        if user_id is not None:
            if user_id in self.active_connections:
                if websocket in self.active_connections[user_id]:
                    self.active_connections[user_id].remove(websocket)
                # Jika tidak ada koneksi tersisa untuk user ini, hapus keynya
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            print(f"❌ User {user_id} disconnected.")
        else:
            # Jika tidak ada user_id, mungkin ini adalah admin websocket
            if websocket in self.admin_connections:
                self.admin_connections.remove(websocket)
            print(f"❌ Admin connection closed.")

        # Juga cek dan hapus dari admin connections jika ada
        if websocket in self.admin_connections:
            self.admin_connections.remove(websocket)
        print(f"❌ Connection closed.")

    # --- BARU: Broadcast ke SEMUA Admin ---
    async def broadcast_to_admins(self, message: dict):
        if self.admin_connections:
            for connection in self.admin_connections:
                try:
                    await connection.send_json(message)
                except:
                    pass # Jika admin offline/putus, abaikan

    async def broadcast_to_user(self, user_id: int, message: dict):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass # Jika koneksi putus, abaikan


import database
from sqlalchemy.orm import Session
from sqlalchemy import func


class WebSocketManager(ConnectionManager):
    async def broadcast_topup_update(self, request_id: int, new_status: str):
        """Broadcast update to all admin connections when a topup request status changes"""
        # Send specific request update
        await self.broadcast_to_admins({
            "type": "update_request",
            "id": request_id,
            "new_status": new_status
        })

        # Update stats for admin panel
        try:
            db: Session = database.SessionLocal()
            # Update pending requests count
            pending_requests = db.query(database.TopUpRequest).filter(database.TopUpRequest.status == "Pending").count()

            # Update total revenue
            revenue_result = db.query(func.sum(database.TopUpRequest.price)).filter(database.TopUpRequest.status == "Approved").scalar()
            current_total_revenue = revenue_result if revenue_result else 0

            # Send stats update
            await self.broadcast_to_admins({
                "type": "stats_update",
                "pending_requests": pending_requests,
                "total_revenue": current_total_revenue
            })
        except Exception as e:
            print(f"❌ Error updating stats: {e}")
        finally:
            db.close()


# Create a single instance of the manager
manager = WebSocketManager()