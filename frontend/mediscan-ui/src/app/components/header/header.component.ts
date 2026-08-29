import { Component, inject, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SessionService } from '../../services/session.service';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule],
  template: `
    <header class="header-container">
      <div class="header-left">
        <button class="mobile-menu-btn" (click)="toggleSidebar.emit()">
          <span class="material-symbols-outlined">menu</span>
        </button>
        <div class="header-title">
          <span class="app-name">MediScan</span>
          <span class="divider">/</span>
          <span class="current-topic">{{ currentSessionTitle() }}</span>
        </div>
      </div>

      <div class="header-actions">
        <button class="quick-new-btn" (click)="onNewChat()" title="Start New Consultation">
          <span class="material-symbols-outlined">add</span>
          <span class="btn-text">New Chat</span>
        </button>
      </div>
    </header>
  `,
  styles: [`
    .header-container {
      height: 56px;
      padding: 0 24px;
      border-bottom: 1px solid var(--color-border);
      display: flex;
      align-items: center;
      justify-content: space-between;
      background-color: rgba(255, 255, 255, 0.9);
      backdrop-filter: blur(8px);
      position: sticky;
      top: 0;
      z-index: 10;
    }

    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .mobile-menu-btn {
      display: none;
      background: none;
      border: none;
      color: var(--color-on-surface);
      cursor: pointer;
      padding: 6px;
      border-radius: var(--radius-sm);
    }

    @media (max-width: 768px) {
      .mobile-menu-btn {
        display: flex;
        align-items: center;
        justify-content: center;
      }
    }

    .header-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
    }

    .app-name {
      font-weight: 700;
      color: var(--color-primary);
    }

    .divider {
      color: var(--color-border);
    }

    .current-topic {
      color: var(--color-text-muted);
      font-weight: 500;
      max-width: 280px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .quick-new-btn {
      display: flex;
      align-items: center;
      gap: 6px;
      background-color: var(--color-surface-soft);
      border: 1px solid var(--color-border);
      color: var(--color-primary);
      padding: 6px 12px;
      border-radius: var(--radius-sm);
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .quick-new-btn:hover {
      background-color: var(--color-primary-light);
      border-color: var(--color-primary);
    }

    @media (max-width: 600px) {
      .btn-text {
        display: none;
      }
      .quick-new-btn {
        padding: 6px;
      }
    }
  `]
})
export class HeaderComponent {
  sessionService = inject(SessionService);
  toggleSidebar = output<void>();

  currentSessionTitle(): string {
    const active = this.sessionService.sessions().find(s => s.id === this.sessionService.activeSessionId());
    return active ? active.title : 'Consultation';
  }

  onNewChat() {
    this.sessionService.createSession();
  }
}
