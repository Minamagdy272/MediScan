import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-empty-state',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="empty-state-wrapper">
      <div class="hero-icon-box">
        <span class="material-symbols-outlined hero-icon">health_metrics</span>
      </div>

      <h2 class="hero-title">How can I assist your clinical analysis?</h2>
      <p class="hero-subtitle">
        Enter your clinical query, question, or chest radiology findings below to begin an evidence-grounded analysis.
      </p>
    </div>
  `,
  styles: [`
    .empty-state-wrapper {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 80px 20px 40px;
      max-width: 600px;
      margin: 0 auto;
      text-align: center;
      animation: fadeIn 0.3s ease;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .hero-icon-box {
      width: 60px;
      height: 60px;
      border-radius: var(--radius-lg);
      background-color: var(--color-surface-cyan);
      color: var(--color-primary);
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 24px;
      border: 1px solid rgba(72, 187, 216, 0.25);
      box-shadow: 0 4px 14px rgba(20, 100, 192, 0.08);
    }

    .hero-icon {
      font-size: 34px;
    }

    .hero-title {
      font-size: 26px;
      font-weight: 700;
      color: var(--color-primary);
      margin-bottom: 12px;
      letter-spacing: -0.02em;
      line-height: 1.25;
    }

    .hero-subtitle {
      font-size: 15px;
      color: var(--color-text-muted);
      max-width: 480px;
      line-height: 1.55;
    }
  `]
})
export class EmptyStateComponent {}
