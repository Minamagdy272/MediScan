import { Component, input, output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-composer',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="composer-outer-wrap">
      <div class="composer-card" [class.disabled]="disabled()">
        <!-- Attachment Indicator -->
        @if (attachedFileName()) {
          <div class="attachment-pill">
            <span class="material-symbols-outlined attach-icon">description</span>
            <span class="attach-text">{{ attachedFileName() }}</span>
            <button class="remove-attach-btn" (click)="clearAttachment()" [disabled]="disabled()">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
        }

        <div class="input-row">
          <!-- File Attach Button -->
          <button
            class="attach-btn"
            title="Attach clinical document or report (.txt, .pdf, .md)"
            [disabled]="disabled()"
            (click)="fileInput.click()"
          >
            <span class="material-symbols-outlined">attach_file</span>
          </button>
          <input
            #fileInput
            type="file"
            class="hidden-file-input"
            accept=".txt,.md,.json,.pdf,.doc,.docx"
            (change)="onFileSelected($event)"
          />

          <!-- Text Area Input -->
          <textarea
            class="text-input"
            rows="1"
            placeholder="Ask MediScan a clinical question or describe findings..."
            [(ngModel)]="messageText"
            [disabled]="disabled()"
            (keydown)="onKeyDown($event)"
            (input)="autoGrow($event)"
          ></textarea>

          <!-- Send Button -->
          <button
            class="send-btn"
            title="Send query to MediScan"
            [disabled]="disabled() || (!messageText.trim() && !attachedFileName())"
            (click)="sendMessage()"
          >
            <span class="material-symbols-outlined">arrow_upward</span>
          </button>
        </div>
      </div>

      <!-- Legal & Clinical Disclaimer Subtext -->
      <div class="disclaimer-text">
        MediScan is an AI decision-support research prototype. Verify critical clinical findings with a qualified physician.
      </div>
    </div>
  `,
  styles: [`
    .composer-outer-wrap {
      width: 100%;
      max-width: var(--chat-max-width);
      margin: 0 auto;
      padding: 0 16px 20px;
    }

    .composer-card {
      background-color: #ffffff;
      border: 1.5px solid var(--color-border);
      border-radius: var(--radius-xl);
      box-shadow: var(--shadow-composer);
      padding: 8px 12px;
      transition: all 0.2s ease;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .composer-card:focus-within {
      border-color: var(--color-primary);
      box-shadow: 0 8px 30px rgba(20, 100, 192, 0.12);
    }

    .composer-card.disabled {
      opacity: 0.7;
      background-color: var(--color-surface-soft);
    }

    .attachment-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      background-color: var(--color-surface-cyan);
      border: 1px solid rgba(72, 187, 216, 0.3);
      border-radius: var(--radius-sm);
      font-size: 12px;
      color: var(--color-primary);
      align-self: flex-start;
      margin-left: 36px;
    }

    .attach-icon {
      font-size: 15px;
    }

    .attach-text {
      font-weight: 600;
      max-width: 220px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .remove-attach-btn {
      background: none;
      border: none;
      color: var(--color-primary);
      cursor: pointer;
      display: flex;
      padding: 0;
    }

    .remove-attach-btn span {
      font-size: 14px;
    }

    .input-row {
      display: flex;
      align-items: flex-end;
      gap: 8px;
    }

    .attach-btn {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: none;
      border: none;
      color: var(--color-text-muted);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.15s ease;
      flex-shrink: 0;
    }

    .attach-btn:hover:not(:disabled) {
      background-color: var(--color-surface-soft);
      color: var(--color-primary);
    }

    .hidden-file-input {
      display: none;
    }

    .text-input {
      flex: 1;
      border: none;
      outline: none;
      background: transparent;
      font-family: inherit;
      font-size: 15px;
      color: var(--color-on-surface);
      resize: none;
      max-height: 140px;
      min-height: 24px;
      line-height: 1.5;
      padding: 6px 0;
    }

    .text-input::placeholder {
      color: #94a3b8;
    }

    .send-btn {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background-color: var(--color-primary);
      color: #ffffff;
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s ease;
      flex-shrink: 0;
    }

    .send-btn:hover:not(:disabled) {
      background-color: var(--color-primary-hover);
      transform: scale(1.05);
    }

    .send-btn:disabled {
      background-color: #e2e8f0;
      color: #94a3b8;
      cursor: not-allowed;
      transform: none;
    }

    .disclaimer-text {
      text-align: center;
      font-size: 11px;
      color: var(--color-text-muted);
      margin-top: 8px;
      font-family: var(--font-family-mono);
      line-height: 1.4;
    }
  `]
})
export class ComposerComponent {
  disabled = input<boolean>(false);
  messageSent = output<{ text: string; file?: File }>();

  messageText = '';
  attachedFileName = signal<string>('');
  selectedFile?: File;

  onKeyDown(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  autoGrow(event: Event) {
    const textarea = event.target as HTMLTextAreaElement;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 140) + 'px';
  }

  onFileSelected(event: Event) {
    const target = event.target as HTMLInputElement;
    if (target.files && target.files.length > 0) {
      this.selectedFile = target.files[0];
      this.attachedFileName.set(this.selectedFile.name);
    }
  }

  clearAttachment() {
    this.selectedFile = undefined;
    this.attachedFileName.set('');
  }

  sendMessage() {
    const text = this.messageText.trim();
    if (!text && !this.selectedFile) return;

    this.messageSent.emit({
      text: text || `Uploaded clinical findings from: ${this.selectedFile?.name}`,
      file: this.selectedFile
    });

    this.messageText = '';
    this.clearAttachment();
  }
}
