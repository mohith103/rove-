/**
 * Small wrapper around the browser's native WebSocket API.
 *
 * Usage:
 *   const ws = new MissionSocket(url);
 *   ws.onMessage((payload) => console.log(payload));
 *   ws.connect();
 *   ...
 *   ws.close();
 */
import type { StreamPayload } from '../types/mission';

type MessageHandler = (payload: StreamPayload) => void;
type ErrorHandler = (err: Event) => void;
type CloseHandler = (code: number, reason: string) => void;

export class MissionSocket {
  private ws: WebSocket | null = null;
  private messageHandlers: MessageHandler[] = [];
  private errorHandlers: ErrorHandler[] = [];
  private closeHandlers: CloseHandler[] = [];
  private closed = false;

  constructor(private url: string) {}

  connect(): void {
    if (this.ws) return;
    this.closed = false;
    this.ws = new WebSocket(this.url);

    this.ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data as string) as StreamPayload;
        this.messageHandlers.forEach((h) => h(payload));
      } catch (err) {
        console.error('Failed to parse WebSocket payload', err);
      }
    };

    this.ws.onerror = (event) => {
      this.errorHandlers.forEach((h) => h(event));
    };

    this.ws.onclose = (event) => {
      this.closeHandlers.forEach((h) => h(event.code, event.reason));
    };
  }

  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.push(handler);
    return () => {
      this.messageHandlers = this.messageHandlers.filter((h) => h !== handler);
    };
  }

  onError(handler: ErrorHandler): void {
    this.errorHandlers.push(handler);
  }

  onClose(handler: CloseHandler): void {
    this.closeHandlers.push(handler);
  }

  close(): void {
    this.closed = true;
    this.ws?.close();
    this.ws = null;
  }

  isClosed(): boolean {
    return this.closed;
  }
}
