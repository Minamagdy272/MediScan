import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { PipelineStageEvent, ChatMessage } from '../models/chat.models';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private readonly baseUrl = 'http://localhost:8000';

  /**
   * SSE Stream Consumer for POST /api/chat/stream
   */
  streamChat(
    message: string,
    sessionId: string,
    generatePdf: boolean = false,
    sendEmail: boolean = false,
    emailRecipient?: string
  ): Observable<{ type: 'stage' | 'done' | 'error'; event?: PipelineStageEvent; finalPayload?: any; error?: string }> {
    return new Observable(observer => {
      const abortController = new AbortController();

      const payload = {
        message,
        session_id: sessionId,
        generate_pdf: generatePdf,
        send_email: sendEmail,
        email_recipient: emailRecipient
      };

      fetch(`${this.baseUrl}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload),
        signal: abortController.signal
      })
      .then(async response => {
        if (!response.ok) {
          throw new Error(`Server returned HTTP ${response.status}`);
        }
        if (!response.body) {
          throw new Error('Response body is empty');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || '';

          for (const block of lines) {
            if (!block.trim()) continue;

            const eventMatch = block.match(/^event:\s*(.+)$/m);
            const dataMatch = block.match(/^data:\s*(.+)$/m);

            const eventName = eventMatch ? eventMatch[1].trim() : 'message';
            const dataStr = dataMatch ? dataMatch[1].trim() : '';

            if (dataStr) {
              try {
                const parsed = JSON.parse(dataStr);

                if (eventName === 'report_ready') {
                  observer.next({ type: 'done', finalPayload: parsed });
                } else if (eventName === 'error') {
                  observer.next({ type: 'error', error: parsed.error || 'Pipeline error' });
                } else {
                  observer.next({ type: 'stage', event: parsed });
                }
              } catch (err) {
                console.warn('Failed to parse SSE line:', dataStr, err);
              }
            }
          }
        }
        observer.complete();
      })
      .catch(error => {
        if (error.name !== 'AbortError') {
          observer.error(error);
        }
      });

      return () => {
        abortController.abort();
      };
    });
  }

  /**
   * Synchronous chat call fallback
   */
  async sendChat(message: string, sessionId: string, generatePdf: boolean = false): Promise<any> {
    const res = await fetch(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        generate_pdf: generatePdf
      })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  /**
   * Generate PDF on demand
   */
  async generatePdf(sessionId: string, reportText?: string): Promise<{ download_url: string; filename: string }> {
    const res = await fetch(`${this.baseUrl}/api/reports/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        report_text: reportText
      })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  /**
   * Send Report Email
   */
  async sendEmail(sessionId: string, recipientEmail: string, pdfFilename?: string): Promise<any> {
    const res = await fetch(`${this.baseUrl}/api/reports/email`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        recipient_email: recipientEmail,
        pdf_filename: pdfFilename
      })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Delivery failed' }));
      throw new Error(err.detail || 'Email delivery failed');
    }
    return res.json();
  }

  /**
   * Upload Document findings
   */
  async uploadFile(file: File): Promise<{ filename: string; extracted_findings: any }> {
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(`${this.baseUrl}/api/upload`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  /**
   * Health check
   */
  async checkHealth(): Promise<boolean> {
    try {
      const res = await fetch(`${this.baseUrl}/api/health`);
      return res.ok;
    } catch {
      return false;
    }
  }
}
