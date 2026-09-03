/**
 * WebSocket client with auto-reconnect logic.
 * Handles connection to the backend call session.
 */

export type WSMessageType = 
  | 'transcript'
  | 'analysis'
  | 'status'
  | 'summary'
  | 'error'
  | 'pong';

export interface WSMessage {
  type: WSMessageType;
  data: Record<string, unknown>;
}

export type MessageHandler = (message: WSMessage) => void;

const WS_BASE_URL = import.meta.env.VITE_WS_URL ||
  `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`;
const RECONNECT_DELAY_MS = 2000;
const MAX_RECONNECT_ATTEMPTS = 5;

export class CallWebSocket {
  private ws: WebSocket | null = null;
  private callId: string;
  private handlers: MessageHandler[] = [];
  private reconnectAttempts = 0;
  private shouldReconnect = true;
  private pingInterval: ReturnType<typeof setInterval> | null = null;

  constructor(callId: string) {
    this.callId = callId;
  }

  connect(): void {
    const url = `${WS_BASE_URL}/ws/${this.callId}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log(`[WS] Connected: ${this.callId}`);
      this.reconnectAttempts = 0;
      this._startPing();
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data);
        this.handlers.forEach((h) => h(message));
      } catch (err) {
        console.error('[WS] Failed to parse message:', err);
      }
    };

    this.ws.onclose = () => {
      console.log(`[WS] Disconnected: ${this.callId}`);
      this._stopPing();
      if (this.shouldReconnect && this.reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        this.reconnectAttempts++;
        console.log(`[WS] Reconnecting in ${RECONNECT_DELAY_MS}ms (attempt ${this.reconnectAttempts})...`);
        setTimeout(() => this.connect(), RECONNECT_DELAY_MS);
      }
    };

    this.ws.onerror = (err) => {
      console.error('[WS] Error:', err);
    };
  }

  send(type: string, data: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, data }));
    } else {
      console.warn('[WS] Cannot send — not connected.');
    }
  }

  sendTranscript(speaker: 'customer' | 'agent', text: string, customerId?: string): void {
    this.send('transcript', { speaker, text, customer_id: customerId });
  }

  endCall(): void {
    this.send('end_call', {});
    this.shouldReconnect = false;
  }

  onMessage(handler: MessageHandler): () => void {
    this.handlers.push(handler);
    return () => {
      this.handlers = this.handlers.filter((h) => h !== handler);
    };
  }

  disconnect(): void {
    this.shouldReconnect = false;
    this._stopPing();
    this.ws?.close();
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  private _startPing(): void {
    this.pingInterval = setInterval(() => {
      this.send('ping', {});
    }, 25000);
  }

  private _stopPing(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }
}
