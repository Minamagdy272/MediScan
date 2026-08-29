import { Component, inject, signal, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SessionService } from './services/session.service';
import { ApiService } from './services/api.service';
import { ChatMessage, PipelineStageEvent } from './models/chat.models';

import { SidebarComponent } from './components/sidebar/sidebar.component';
import { HeaderComponent } from './components/header/header.component';
import { EmptyStateComponent } from './components/empty-state/empty-state.component';
import { UserMessageComponent } from './components/user-message/user-message.component';
import { AssistantMessageComponent } from './components/assistant-message/assistant-message.component';
import { ComposerComponent } from './components/composer/composer.component';
import { EmailModalComponent } from './components/email-modal/email-modal.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    SidebarComponent,
    HeaderComponent,
    EmptyStateComponent,
    UserMessageComponent,
    AssistantMessageComponent,
    ComposerComponent,
    EmailModalComponent
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements AfterViewChecked {
  sessionService = inject(SessionService);
  apiService = inject(ApiService);

  @ViewChild('chatScrollArea') private scrollArea?: ElementRef<HTMLDivElement>;

  mobileSidebarOpen = signal<boolean>(false);
  isProcessing = signal<boolean>(false);

  // Email modal state
  emailModalOpen = signal<boolean>(false);
  emailModalMsg = signal<ChatMessage | null>(null);
  isSendingEmail = signal<boolean>(false);
  emailErrorMessage = signal<string>('');

  private shouldScroll = false;

  ngAfterViewChecked() {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  scrollToBottom() {
    try {
      if (this.scrollArea) {
        this.scrollArea.nativeElement.scrollTop = this.scrollArea.nativeElement.scrollHeight;
      }
    } catch {}
  }

  toggleMobileSidebar() {
    this.mobileSidebarOpen.update(v => !v);
  }

  closeMobileSidebar() {
    this.mobileSidebarOpen.set(false);
  }

  async handleSendMessage(payload: { text: string; file?: File }) {
    if (this.isProcessing()) return;

    const activeSessionId = this.sessionService.activeSessionId();
    let userContent = payload.text;
    let attachmentName = payload.file ? payload.file.name : undefined;

    // 1. Add User Message
    const userMsg: ChatMessage = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: userContent,
      timestamp: new Date(),
      attachmentName
    };

    // If first message in session, update title
    if (this.sessionService.messages().length === 0) {
      this.sessionService.updateSessionTitle(activeSessionId, userContent);
    }

    // 2. Prepare Assistant Placeholder
    const assistantMsg: ChatMessage = {
      id: `asst_${Date.now()}`,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      status: 'processing',
      stages: [],
      currentStageMessage: 'Initializing MediScan clinical evaluation...'
    };

    this.sessionService.messages.update(list => [...list, userMsg, assistantMsg]);
    this.sessionService.saveCurrentMessages();
    this.isProcessing.set(true);
    this.shouldScroll = true;

    // 3. Optional File Extraction upload first
    if (payload.file) {
      try {
        assistantMsg.currentStageMessage = 'Extracting findings from uploaded document...';
        const uploadRes = await this.apiService.uploadFile(payload.file);
        userContent += `\n[Uploaded Document: ${payload.file.name}]\nExtracted Findings: ${JSON.stringify(uploadRes.extracted_findings)}`;
      } catch (err) {
        console.warn('Upload extraction fallback:', err);
      }
    }

    // 4. Stream Pipeline Execution
    this.apiService.streamChat(userContent, activeSessionId).subscribe({
      next: (update) => {
        this.shouldScroll = true;
        if (update.type === 'stage' && update.event) {
          const event: PipelineStageEvent = update.event;
          if (!assistantMsg.stages) assistantMsg.stages = [];
          assistantMsg.stages.push(event);
          assistantMsg.currentStageMessage = event.message || assistantMsg.currentStageMessage;
          this.sessionService.saveCurrentMessages();
        } else if (update.type === 'done' && update.finalPayload) {
          const final = update.finalPayload;
          assistantMsg.content = final.final_answer;
          assistantMsg.status = 'done';
          assistantMsg.final_action = final.final_action;
          assistantMsg.attempts_made = final.attempts_made;
          assistantMsg.evidence_used = final.evidence_used;
          assistantMsg.plan = final.plan;
          assistantMsg.pdf_download_url = final.pdf_download_url;
          assistantMsg.pdf_filename = final.pdf_path ? final.pdf_path.split(/[/\\\\]/).pop() : undefined;
          assistantMsg.email_sent = final.email_sent;
          assistantMsg.email_status = final.email_status;

          this.isProcessing.set(false);
          this.sessionService.saveCurrentMessages();
        } else if (update.type === 'error') {
          assistantMsg.status = 'error';
          assistantMsg.content = `### Clinical Processing Error\n\n${update.error || 'An unexpected error occurred during execution.'}\n\nPlease try rephrasing your question.`;
          this.isProcessing.set(false);
          this.sessionService.saveCurrentMessages();
        }
      },
      error: (err) => {
        assistantMsg.status = 'error';
        assistantMsg.content = `### Connection Error\n\nFailed to reach the MediScan FastAPI backend at \`http://localhost:8000\`.\n\nMake sure the backend is running.\nDetails: ${err.message}`;
        this.isProcessing.set(false);
        this.sessionService.saveCurrentMessages();
        this.shouldScroll = true;
      }
    });
  }

  async onGeneratePdf(msg: ChatMessage) {
    try {
      const res = await this.apiService.generatePdf(this.sessionService.activeSessionId(), msg.content);
      msg.pdf_download_url = res.download_url;
      msg.pdf_filename = res.filename;
      this.sessionService.saveCurrentMessages();
      window.open(`http://localhost:8000${res.download_url}`, '_blank');
    } catch (err: any) {
      alert(`PDF generation failed: ${err.message}`);
    }
  }

  onOpenEmailModal(msg: ChatMessage) {
    this.emailModalMsg.set(msg);
    this.emailErrorMessage.set('');
    this.emailModalOpen.set(true);
  }

  onCloseEmailModal() {
    this.emailModalOpen.set(false);
    this.emailModalMsg.set(null);
  }

  async onSendEmail(recipientEmail: string) {
    const msg = this.emailModalMsg();
    if (!msg) return;

    this.isSendingEmail.set(true);
    this.emailErrorMessage.set('');

    try {
      const res = await this.apiService.sendEmail(
        this.sessionService.activeSessionId(),
        recipientEmail,
        msg.pdf_filename
      );
      msg.email_sent = true;
      msg.email_status = res.delivery_message;
      this.sessionService.saveCurrentMessages();
      this.onCloseEmailModal();
    } catch (err: any) {
      this.emailErrorMessage.set(err.message || 'Failed to dispatch email.');
    } finally {
      this.isSendingEmail.set(false);
    }
  }
}
