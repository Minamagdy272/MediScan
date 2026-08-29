import { Component, inject, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SessionService } from '../../services/session.service';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule],
  template: `
    <aside class="sidebar-container">
      <!-- Brand Header -->
      <div class="brand-header">
        <div class="logo-circle">
          <span class="material-symbols-outlined logo-icon">medical_services</span>
        </div>
        <div class="brand-text">
          <h1 class="brand-title">MediScan</h1>
          <span class="brand-subtitle">Clinical AI Assistant</span>
        </div>
      </div>

      <!-- New Consultation Button -->
      <button class="new-chat-btn" (click)="onNewChat()">
        <span class="material-symbols-outlined">add</span>
        <span>New Consultation</span>
      </button>

      <!-- Recent Sessions List -->
      <div class="session-section">
        <div class="section-label">Recent Consultations</div>
        <div class="session-list">
          @for (session of sessionService.sessions(); track session.id) {
            <div
              class="session-item"
              [class.active]="session.id === sessionService.activeSessionId()"
              (click)="onSelectSession(session.id)"
            >
              <span class="material-symbols-outlined item-icon">chat_bubble</span>
              <span class="session-title">{{ session.title }}</span>
              <button
                class="delete-btn"
                title="Delete Consultation"
                (click)="onDeleteSession($event, session.id)"
              >
                <span class="material-symbols-outlined">delete</span>
              </button>
            </div>
          } @empty {
            <div class="empty-sessions">No recent chats</div>
          }
        </div>
      </div>

      <!-- Sidebar Footer -->
      <div class="sidebar-footer">
        <div class="system-badge">
          <span class="status-dot"></span>
          <span>NVIDIA NIM & RAG Ready</span>
        </div>
      </div>
    </aside>
  `,
  styles: [`
    .sidebar-container {
      width: var(--sidebar-width);
      height: 100%;
      background-color: var(--color-surface-soft);
      border-right: 1px solid var(--color-border);
      display: flex;
      flex-direction: column;
      padding: 20px 16px;
    }

    .brand-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 24px;
      padding: 0 4px;
    }

    .logo-circle {
      width: 38px;
      height: 38px;
      border-radius: var(--radius-md);
      background: linear-gradient(135deg, var(--color-primary), var(--color-secondary-cyan));
      display: flex;
      align-items: center;
      justify-content: center;
      color: #ffffff;
      box-shadow: 0 2px 8px rgba(20, 100, 192, 0.25);
    }

    .logo-icon {
      font-size: 22px;
    }

    .brand-title {
      font-size: 18px;
      font-weight: 700;
      color: var(--color-primary);
      line-height: 1.1;
      letter-spacing: -0.02em;
    }

    .brand-subtitle {
      font-size: 11px;
      font-weight: 600;
      color: var(--color-text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .new-chat-btn {
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      background-color: var(--color-primary);
      color: #ffffff;
      border: none;
      border-radius: var(--radius-md);
      padding: 12px 16px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: background-color 0.2s ease, transform 0.1s ease;
      margin-bottom: 24px;
    }

    .new-chat-btn:hover {
      background-color: var(--color-primary-hover);
    }

    .new-chat-btn:active {
      transform: scale(0.99);
    }

    .session-section {
      flex: 1;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
    }

    .section-label {
      font-size: 11px;
      font-weight: 700;
      color: var(--color-text-muted);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin-bottom: 8px;
      padding: 0 8px;
    }

    .session-list {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .session-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 9px 12px;
      border-radius: var(--radius-sm);
      color: var(--color-on-surface);
      cursor: pointer;
      transition: all 0.15s ease;
      position: relative;
    }

    .session-item:hover {
      background-color: #e9edff;
      color: var(--color-primary);
    }

    .session-item.active {
      background-color: var(--color-primary-fixed);
      color: var(--color-primary);
      font-weight: 600;
    }

    .item-icon {
      font-size: 18px;
      color: var(--color-text-muted);
    }

    .session-item.active .item-icon,
    .session-item:hover .item-icon {
      color: var(--color-primary);
    }

    .session-title {
      flex: 1;
      font-size: 13.5px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .delete-btn {
      opacity: 0;
      background: none;
      border: none;
      color: var(--color-text-muted);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 4px;
      border-radius: 4px;
      transition: all 0.15s ease;
    }

    .session-item:hover .delete-btn {
      opacity: 0.7;
    }

    .delete-btn:hover {
      opacity: 1 !important;
      color: var(--color-status-critical);
      background: rgba(217, 48, 37, 0.1);
    }

    .empty-sessions {
      font-size: 13px;
      color: var(--color-text-muted);
      padding: 12px 8px;
      font-style: italic;
    }

    .sidebar-footer {
      border-top: 1px solid var(--color-border);
      padding-top: 14px;
      margin-top: auto;
    }

    .system-badge {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      color: var(--color-text-muted);
      padding: 6px 8px;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background-color: var(--color-status-success);
    }
  `]
})
export class SidebarComponent {
  sessionService = inject(SessionService);
  closeMobile = output<void>();

  onNewChat() {
    this.sessionService.createSession();
    this.closeMobile.emit();
  }

  onSelectSession(id: string) {
    this.sessionService.switchSession(id);
    this.closeMobile.emit();
  }

  onDeleteSession(event: Event, id: string) {
    event.stopPropagation();
    this.sessionService.deleteSession(id);
  }
}
