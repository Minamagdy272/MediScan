import { Injectable, signal } from '@angular/core';
import { ChatSession, ChatMessage } from '../models/chat.models';

@Injectable({
  providedIn: 'root'
})
export class SessionService {
  private readonly STORAGE_KEY_SESSIONS = 'mediscan_sessions';
  private readonly STORAGE_KEY_MESSAGES = 'mediscan_messages_';

  // Signals for modern Angular reactivity
  activeSessionId = signal<string>('default');
  sessions = signal<ChatSession[]>([]);
  messages = signal<ChatMessage[]>([]);

  constructor() {
    this.loadSessions();
  }

  loadSessions() {
    const saved = localStorage.getItem(this.STORAGE_KEY_SESSIONS);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        this.sessions.set(parsed);
      } catch {
        this.initDefaultSession();
      }
    } else {
      this.initDefaultSession();
    }

    if (this.sessions().length > 0) {
      this.switchSession(this.sessions()[0].id);
    }
  }

  private initDefaultSession() {
    const defaultSession: ChatSession = {
      id: `session_${Date.now()}`,
      title: 'New Consultation',
      updatedAt: new Date()
    };
    this.sessions.set([defaultSession]);
    this.saveSessions();
    this.activeSessionId.set(defaultSession.id);
  }

  createSession(): string {
    const newSession: ChatSession = {
      id: `session_${Date.now()}`,
      title: 'New Consultation',
      updatedAt: new Date()
    };
    this.sessions.update(list => [newSession, ...list]);
    this.saveSessions();
    this.switchSession(newSession.id);
    return newSession.id;
  }

  switchSession(sessionId: string) {
    this.activeSessionId.set(sessionId);
    const savedMsgs = localStorage.getItem(this.STORAGE_KEY_MESSAGES + sessionId);
    if (savedMsgs) {
      try {
        const parsed: ChatMessage[] = JSON.parse(savedMsgs);
        this.messages.set(parsed);
      } catch {
        this.messages.set([]);
      }
    } else {
      this.messages.set([]);
    }
  }

  updateSessionTitle(sessionId: string, firstMessage: string) {
    const title = firstMessage.length > 32 ? firstMessage.substring(0, 32) + '...' : firstMessage;
    this.sessions.update(list =>
      list.map(s => (s.id === sessionId ? { ...s, title, updatedAt: new Date() } : s))
    );
    this.saveSessions();
  }

  saveCurrentMessages() {
    const sid = this.activeSessionId();
    localStorage.setItem(this.STORAGE_KEY_MESSAGES + sid, JSON.stringify(this.messages()));
  }

  private saveSessions() {
    localStorage.setItem(this.STORAGE_KEY_SESSIONS, JSON.stringify(this.sessions()));
  }

  deleteSession(sessionId: string) {
    this.sessions.update(list => list.filter(s => s.id !== sessionId));
    localStorage.removeItem(this.STORAGE_KEY_MESSAGES + sessionId);
    this.saveSessions();

    if (this.activeSessionId() === sessionId) {
      if (this.sessions().length > 0) {
        this.switchSession(this.sessions()[0].id);
      } else {
        this.createSession();
      }
    }
  }
}
