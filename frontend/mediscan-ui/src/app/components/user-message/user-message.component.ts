import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChatMessage } from '../../models/chat.models';

@Component({
  selector: 'app-user-message',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="user-msg-row">
      <div class="user-bubble">
        @if (msg().attachmentName) {
          <div class="attachment-tag">
            <span class="material-symbols-outlined">attachment</span>
            <span>{{ msg().attachmentName }}</span>
          </div>
        }
        <div class="user-text">{{ msg().content }}</div>
      </div>
    </div>
  `,
  styles: [`
    .user-msg-row {
      display: flex;
      justify-content: flex-end;
      width: 100%;
      margin: 12px 0 20px;
    }

    .user-bubble {
      max-width: 80%;
      background-color: var(--color-surface-soft);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-lg);
      border-top-right-radius: 4px;
      padding: 12px 18px;
      color: var(--color-on-surface);
      font-size: 14.5px;
      line-height: 1.5;
      box-shadow: 0 1px 4px rgba(23, 32, 51, 0.04);
    }

    .attachment-tag {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      font-weight: 600;
      color: var(--color-primary);
      background-color: var(--color-surface-cyan);
      padding: 3px 8px;
      border-radius: 4px;
      margin-bottom: 8px;
      border: 1px solid rgba(20, 100, 192, 0.2);
    }

    .attachment-tag span.material-symbols-outlined {
      font-size: 15px;
    }

    .user-text {
      white-space: pre-wrap;
      word-break: break-word;
    }
  `]
})
export class UserMessageComponent {
  msg = input.required<ChatMessage>();
}
