import { Component, input, output, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { marked } from 'marked';
import { ChatMessage } from '../../models/chat.models';
import { EvidenceCardComponent } from '../evidence-card/evidence-card.component';
import { ProcessingStepperComponent } from '../processing-stepper/processing-stepper.component';

@Component({
  selector: 'app-assistant-message',
  standalone: true,
  imports: [CommonModule, EvidenceCardComponent, ProcessingStepperComponent],
  template: `
    <div class="assistant-msg-wrap">
      <!-- Assistant Avatar & Title -->
      <div class="assistant-head">
        <div class="avatar-box">
          <span class="material-symbols-outlined avatar-icon">smart_toy</span>
        </div>
        <div class="assistant-meta">
          <span class="assistant-name">MediScan</span>
          <span class="badge-grounded">Evidence-Grounded</span>
        </div>
      </div>

      <!-- Live Stepper while processing -->
      @if (msg().status === 'processing') {
        <app-processing-stepper
          [stages]="msg().stages || []"
          [currentMessage]="msg().currentStageMessage || ''"
        ></app-processing-stepper>
      }

      <!-- Safety Notice Banners if Escalated or Insufficient -->
      @if (msg().final_action === 'ESCALATE') {
        <div class="safety-banner escalation-banner">
          <span class="material-symbols-outlined banner-icon">warning</span>
          <div class="banner-content">
            <span class="banner-title">Clinical Escalation Notice</span>
            <span class="banner-desc">Evidence was insufficient or requires urgent specialist radiologist verification.</span>
          </div>
        </div>
      }

      <!-- Main Clinical Content Area (Markdown formatted) -->
      @if (msg().content) {
        <div class="markdown-content" [innerHTML]="renderedHtml()"></div>
      }

      <!-- Evidence Cards Section -->
      @if (msg().evidence_used && msg().evidence_used!.length > 0) {
        <app-evidence-card [evidenceList]="msg().evidence_used!"></app-evidence-card>
      }

      <!-- Action Buttons for Approved Reports (PDF & Email) -->
      @if (msg().status === 'done' && msg().final_action === 'ACCEPT') {
        <div class="report-actions-bar">
          <!-- Download / Generate PDF -->
          @if (msg().pdf_download_url) {
            <a
              class="action-btn pdf-btn"
              [href]="'http://localhost:8000' + msg().pdf_download_url"
              target="_blank"
              download
            >
              <span class="material-symbols-outlined">download</span>
              <span>Download PDF Report</span>
            </a>
          } @else {
            <button class="action-btn pdf-btn" (click)="generatePdf.emit(msg())">
              <span class="material-symbols-outlined">picture_as_pdf</span>
              <span>Generate PDF</span>
            </button>
          }

          <!-- Send Email -->
          <button class="action-btn email-btn" (click)="openEmailModal.emit(msg())">
            <span class="material-symbols-outlined">mail</span>
            <span>Email Report</span>
          </button>
        </div>

        @if (msg().email_sent) {
          <div class="email-success-badge">
            <span class="material-symbols-outlined">check_circle</span>
            <span>Report successfully delivered to recipient email.</span>
          </div>
        }
      }
    </div>
  `,
  styles: [`
    .assistant-msg-wrap {
      width: 100%;
      padding: 12px 0 24px;
      display: flex;
      flex-direction: column;
      animation: fadeIn 0.25s ease;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(4px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .assistant-head {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 12px;
    }

    .avatar-box {
      width: 28px;
      height: 28px;
      border-radius: var(--radius-sm);
      background-color: var(--color-primary-fixed);
      color: var(--color-primary);
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .avatar-icon {
      font-size: 17px;
    }

    .assistant-meta {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .assistant-name {
      font-size: 14px;
      font-weight: 700;
      color: var(--color-on-surface);
    }

    .badge-grounded {
      font-size: 10.5px;
      font-weight: 600;
      color: var(--color-primary);
      background-color: var(--color-surface-cyan);
      border: 1px solid rgba(20, 100, 192, 0.2);
      padding: 1px 7px;
      border-radius: var(--radius-full);
      letter-spacing: 0.02em;
    }

    .safety-banner {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 12px 16px;
      border-radius: var(--radius-sm);
      margin-bottom: 14px;
    }

    .escalation-banner {
      background-color: #fef2f2;
      border: 1px solid #fecaca;
      color: var(--color-status-critical);
    }

    .banner-icon {
      font-size: 20px;
      margin-top: 1px;
    }

    .banner-content {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .banner-title {
      font-size: 13.5px;
      font-weight: 700;
    }

    .banner-desc {
      font-size: 12.5px;
      color: #7f1d1d;
    }

    .report-actions-bar {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-top: 14px;
      padding-top: 12px;
      border-top: 1px solid var(--color-border-light);
    }

    .action-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 7px 14px;
      border-radius: var(--radius-sm);
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
      transition: all 0.15s ease;
    }

    .pdf-btn {
      background-color: var(--color-surface-soft);
      border: 1.5px solid var(--color-primary);
      color: var(--color-primary);
    }

    .pdf-btn:hover {
      background-color: var(--color-primary);
      color: #ffffff;
    }

    .email-btn {
      background-color: transparent;
      border: 1px solid var(--color-border);
      color: var(--color-on-surface);
    }

    .email-btn:hover {
      background-color: var(--color-surface-soft);
      border-color: var(--color-primary);
      color: var(--color-primary);
    }

    .email-success-badge {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-top: 10px;
      font-size: 12.5px;
      color: var(--color-status-success);
      font-weight: 500;
    }

    .email-success-badge span {
      font-size: 16px;
    }
  `]
})
export class AssistantMessageComponent {
  msg = input.required<ChatMessage>();

  generatePdf = output<ChatMessage>();
  openEmailModal = output<ChatMessage>();

  renderedHtml = computed(() => {
    const raw = this.msg().content || '';
    if (!raw) return '';
    try {
      return marked.parse(raw) as string;
    } catch {
      return raw;
    }
  });
}
