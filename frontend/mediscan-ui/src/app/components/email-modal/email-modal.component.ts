import { Component, input, output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-email-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="modal-backdrop" (click)="closeModal()">
      <div class="modal-card" (click)="$event.stopPropagation()">
        <div class="modal-header">
          <div class="header-left">
            <span class="material-symbols-outlined header-icon">mail</span>
            <h3 class="modal-title">Email Approved Clinical Report</h3>
          </div>
          <button class="close-btn" (click)="closeModal()">
            <span class="material-symbols-outlined">close</span>
          </button>
        </div>

        <div class="modal-body">
          <p class="modal-desc">
            Send the generated, evidence-grounded PDF report directly to a verified clinical recipient or patient.
          </p>

          @if (pdfFilename()) {
            <div class="file-preview-card">
              <span class="material-symbols-outlined pdf-icon">picture_as_pdf</span>
              <span class="file-name">{{ pdfFilename() }}</span>
            </div>
          }

          <div class="form-group">
            <label class="form-label" for="recipient-email">Recipient Email Address</label>
            <input
              id="recipient-email"
              type="email"
              class="form-input"
              placeholder="e.g. physician@hospital.org"
              [(ngModel)]="emailInput"
              [disabled]="isSending()"
              (keyup.enter)="submitEmail()"
            />
          </div>

          @if (errorMessage()) {
            <div class="error-banner">
              <span class="material-symbols-outlined error-icon">error</span>
              <span>{{ errorMessage() }}</span>
            </div>
          }
        </div>

        <div class="modal-footer">
          <button class="cancel-btn" (click)="closeModal()" [disabled]="isSending()">
            Cancel
          </button>
          <button
            class="send-btn"
            [disabled]="isSending() || !isValidEmail()"
            (click)="submitEmail()"
          >
            @if (isSending()) {
              <span class="btn-spinner"></span>
              <span>Sending...</span>
            } @else {
              <span class="material-symbols-outlined">send</span>
              <span>Send Report</span>
            }
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .modal-backdrop {
      position: fixed;
      inset: 0;
      background-color: rgba(18, 27, 46, 0.45);
      backdrop-filter: blur(4px);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 100;
      padding: 16px;
      animation: fadeIn 0.2s ease;
    }

    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    .modal-card {
      width: 100%;
      max-width: 480px;
      background-color: #ffffff;
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-modal);
      overflow: hidden;
      display: flex;
      flex-direction: column;
      border: 1px solid var(--color-border);
    }

    .modal-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px 20px;
      border-bottom: 1px solid var(--color-border);
      background-color: var(--color-surface-soft);
    }

    .header-left {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .header-icon {
      color: var(--color-primary);
      font-size: 22px;
    }

    .modal-title {
      font-size: 15px;
      font-weight: 700;
      color: var(--color-on-surface);
    }

    .close-btn {
      background: none;
      border: none;
      color: var(--color-text-muted);
      cursor: pointer;
      padding: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 4px;
    }

    .close-btn:hover {
      background-color: var(--color-border);
      color: var(--color-on-surface);
    }

    .modal-body {
      padding: 20px;
    }

    .modal-desc {
      font-size: 13.5px;
      color: var(--color-text-muted);
      margin-bottom: 16px;
      line-height: 1.45;
    }

    .file-preview-card {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 14px;
      background-color: var(--color-surface-soft);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-sm);
      margin-bottom: 18px;
    }

    .pdf-icon {
      color: var(--color-status-critical);
      font-size: 22px;
    }

    .file-name {
      font-size: 13px;
      font-weight: 600;
      color: var(--color-on-surface);
      word-break: break-all;
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .form-label {
      font-size: 12.5px;
      font-weight: 600;
      color: var(--color-on-surface);
    }

    .form-input {
      padding: 10px 14px;
      border: 1.5px solid var(--color-border);
      border-radius: var(--radius-sm);
      font-size: 14px;
      font-family: inherit;
      color: var(--color-on-surface);
      outline: none;
      transition: border-color 0.2s ease;
    }

    .form-input:focus {
      border-color: var(--color-primary);
    }

    .error-banner {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 12px;
      padding: 8px 12px;
      background-color: #fdf2f2;
      border: 1px solid #f8d7da;
      border-radius: var(--radius-sm);
      color: var(--color-status-critical);
      font-size: 12.5px;
    }

    .error-icon {
      font-size: 16px;
    }

    .modal-footer {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 10px;
      padding: 14px 20px;
      background-color: var(--color-surface-soft);
      border-top: 1px solid var(--color-border);
    }

    .cancel-btn {
      padding: 8px 16px;
      background: none;
      border: 1px solid var(--color-border);
      border-radius: var(--radius-sm);
      font-size: 13.5px;
      font-weight: 600;
      color: var(--color-text-muted);
      cursor: pointer;
    }

    .cancel-btn:hover {
      background-color: #ffffff;
      color: var(--color-on-surface);
    }

    .send-btn {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 8px 18px;
      background-color: var(--color-primary);
      border: none;
      border-radius: var(--radius-sm);
      font-size: 13.5px;
      font-weight: 600;
      color: #ffffff;
      cursor: pointer;
      transition: background-color 0.2s ease;
    }

    .send-btn:hover:not(:disabled) {
      background-color: var(--color-primary-hover);
    }

    .send-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .btn-spinner {
      width: 14px;
      height: 14px;
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-top-color: #ffffff;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  `]
})
export class EmailModalComponent {
  pdfFilename = input<string>('');
  isSending = input<boolean>(false);
  errorMessage = input<string>('');

  send = output<string>();
  close = output<void>();

  emailInput = '';

  isValidEmail(): boolean {
    return !!this.emailInput && this.emailInput.includes('@') && this.emailInput.includes('.');
  }

  submitEmail() {
    if (this.isValidEmail()) {
      this.send.emit(this.emailInput.trim());
    }
  }

  closeModal() {
    this.close.emit();
  }
}
