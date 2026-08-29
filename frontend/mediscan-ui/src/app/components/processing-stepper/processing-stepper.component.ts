import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PipelineStageEvent } from '../../models/chat.models';

@Component({
  selector: 'app-processing-stepper',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="stepper-box">
      <div class="stepper-header">
        <div class="spinner-ring"></div>
        <span class="stepper-title">{{ currentMessage() || 'MediScan Clinical RAG Processing...' }}</span>
      </div>

      <div class="steps-flow">
        <!-- Step 1: Extraction -->
        <div class="step-item" [class.completed]="hasStage('extraction_completed')" [class.active]="isCurrent('analysis_started')">
          <div class="step-icon-dot">
            @if (hasStage('extraction_completed')) {
              <span class="material-symbols-outlined check-icon">check</span>
            } @else {
              <span class="dot"></span>
            }
          </div>
          <span class="step-label">Clinical Extraction</span>
        </div>

        <!-- Step 2: Planning -->
        <div class="step-item" [class.completed]="hasStage('planning_completed')" [class.active]="isCurrent('routing_completed')">
          <div class="step-icon-dot">
            @if (hasStage('planning_completed')) {
              <span class="material-symbols-outlined check-icon">check</span>
            } @else {
              <span class="dot"></span>
            }
          </div>
          <span class="step-label">GLM Query Planner</span>
        </div>

        <!-- Step 3: Retrieval -->
        <div class="step-item" [class.completed]="hasStage('retrieval_completed')" [class.active]="isCurrent('retrieval_started')">
          <div class="step-icon-dot">
            @if (hasStage('retrieval_completed')) {
              <span class="material-symbols-outlined check-icon">check</span>
            } @else {
              <span class="dot"></span>
            }
          </div>
          <span class="step-label">Hybrid Reranked VDB</span>
        </div>

        <!-- Step 4: Generation -->
        <div class="step-item" [class.completed]="hasStage('validation_started')" [class.active]="isCurrent('generation_started')">
          <div class="step-icon-dot">
            @if (hasStage('validation_started')) {
              <span class="material-symbols-outlined check-icon">check</span>
            } @else {
              <span class="dot"></span>
            }
          </div>
          <span class="step-label">Report Synthesis</span>
        </div>

        <!-- Step 5: Evaluator & Safety Policy -->
        <div class="step-item" [class.completed]="hasStage('policy_evaluated')" [class.active]="isCurrent('evaluation_started')">
          <div class="step-icon-dot">
            @if (hasStage('policy_evaluated')) {
              <span class="material-symbols-outlined check-icon">check</span>
            } @else {
              <span class="dot"></span>
            }
          </div>
          <span class="step-label">DeepSeek Safety Gate</span>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .stepper-box {
      background-color: var(--color-surface-soft);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-md);
      padding: 14px 18px;
      margin: 8px 0 16px;
      animation: fadeIn 0.3s ease;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(4px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .stepper-header {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 12px;
    }

    .spinner-ring {
      width: 16px;
      height: 16px;
      border: 2px solid rgba(20, 100, 192, 0.2);
      border-top-color: var(--color-primary);
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .stepper-title {
      font-size: 13.5px;
      font-weight: 600;
      color: var(--color-primary);
    }

    .steps-flow {
      display: flex;
      flex-wrap: wrap;
      gap: 12px 18px;
    }

    .step-item {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      color: var(--color-text-muted);
      transition: all 0.2s ease;
    }

    .step-icon-dot {
      width: 18px;
      height: 18px;
      border-radius: 50%;
      border: 1.5px solid var(--color-border);
      background-color: #ffffff;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s ease;
    }

    .dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background-color: var(--color-border);
    }

    .step-item.active {
      color: var(--color-primary);
      font-weight: 600;
    }

    .step-item.active .step-icon-dot {
      border-color: var(--color-primary);
      background-color: var(--color-primary-light);
    }

    .step-item.active .dot {
      background-color: var(--color-primary);
    }

    .step-item.completed {
      color: var(--color-on-surface);
    }

    .step-item.completed .step-icon-dot {
      border-color: var(--color-status-success);
      background-color: var(--color-status-success);
      color: #ffffff;
    }

    .check-icon {
      font-size: 12px;
      font-weight: 700;
    }
  `]
})
export class ProcessingStepperComponent {
  stages = input<PipelineStageEvent[]>([]);
  currentMessage = input<string>('');

  hasStage(stageName: string): boolean {
    const list = this.stages() || [];
    return list.some(s => s.stage === stageName);
  }

  isCurrent(stageName: string): boolean {
    const list = this.stages() || [];
    if (list.length === 0) return false;
    return list[list.length - 1].stage === stageName;
  }
}
