import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EvidenceRecord } from '../../models/chat.models';

@Component({
  selector: 'app-evidence-card',
  standalone: true,
  imports: [CommonModule],
  template: `
    @if (evidenceList() && evidenceList().length > 0) {
      <div class="evidence-section">
        <div class="section-header" (click)="toggleAll()">
          <div class="header-left">
            <span class="material-symbols-outlined header-icon">menu_book</span>
            <span class="header-title">Retrieved Clinical Evidence</span>
            <span class="evidence-count">{{ evidenceList().length }} sources</span>
          </div>
          <span class="material-symbols-outlined expand-chevron" [class.rotated]="isAllExpanded">
            expand_more
          </span>
        </div>

        @if (isAllExpanded) {
          <div class="cards-stack">
            @for (item of evidenceList(); track item.chunk_id) {
              <div class="evidence-card" [class.item-expanded]="item.expanded">
                <div class="card-top" (click)="toggleItem(item)">
                  <div class="top-meta">
                    <span class="citation-badge">[{{ item.evidence_id }}]</span>
                    <span class="source-title" [title]="item.source_title">{{ item.source_title }}</span>
                    <span class="source-type-pill">{{ item.source_type }}</span>
                  </div>
                  <div class="score-badge" title="Reranker Relevance Score">
                    Score: {{ (item.score * 100) | number:'1.0-1' }}%
                  </div>
                </div>

                @if (item.expanded) {
                  <div class="card-body">
                    <div class="chunk-meta">
                      <span><strong>Chunk ID:</strong> {{ item.chunk_id }}</span>
                      <span><strong>Source ID:</strong> {{ item.source_id }}</span>
                    </div>
                    <div class="chunk-content">{{ item.content }}</div>
                  </div>
                }
              </div>
            }
          </div>
        }
      </div>
    }
  `,
  styles: [`
    .evidence-section {
      background-color: var(--color-surface-soft);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-md);
      margin: 16px 0;
      overflow: hidden;
    }

    .section-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 16px;
      cursor: pointer;
      user-select: none;
      background-color: var(--color-surface-soft);
      transition: background-color 0.15s ease;
    }

    .section-header:hover {
      background-color: #edf5fc;
    }

    .header-left {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .header-icon {
      font-size: 18px;
      color: var(--color-primary);
    }

    .header-title {
      font-size: 13px;
      font-weight: 600;
      color: var(--color-on-surface);
    }

    .evidence-count {
      font-size: 11.5px;
      font-weight: 600;
      color: var(--color-primary);
      background-color: var(--color-surface-cyan);
      padding: 2px 8px;
      border-radius: var(--radius-full);
      border: 1px solid rgba(72, 187, 216, 0.3);
    }

    .expand-chevron {
      font-size: 20px;
      color: var(--color-text-muted);
      transition: transform 0.2s ease;
    }

    .expand-chevron.rotated {
      transform: rotate(180deg);
    }

    .cards-stack {
      padding: 8px 12px 12px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      border-top: 1px solid var(--color-border);
    }

    .evidence-card {
      background-color: #ffffff;
      border: 1px solid var(--color-border);
      border-radius: var(--radius-sm);
      overflow: hidden;
      transition: border-color 0.15s ease;
    }

    .evidence-card:hover {
      border-color: var(--color-primary);
    }

    .card-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 12px;
      cursor: pointer;
      gap: 10px;
    }

    .top-meta {
      display: flex;
      align-items: center;
      gap: 8px;
      overflow: hidden;
      flex: 1;
    }

    .citation-badge {
      font-family: var(--font-family-mono);
      font-size: 11px;
      font-weight: 700;
      color: var(--color-primary);
      background-color: var(--color-surface-cyan);
      padding: 2px 6px;
      border-radius: 4px;
      border: 1px solid rgba(20, 100, 192, 0.2);
      flex-shrink: 0;
    }

    .source-title {
      font-size: 12.5px;
      font-weight: 600;
      color: var(--color-on-surface);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .source-type-pill {
      font-size: 10.5px;
      color: var(--color-text-muted);
      background-color: var(--color-surface-soft);
      padding: 1px 6px;
      border-radius: 4px;
      border: 1px solid var(--color-border);
      flex-shrink: 0;
      text-transform: capitalize;
    }

    .score-badge {
      font-size: 11px;
      font-weight: 600;
      color: var(--color-primary);
      flex-shrink: 0;
    }

    .card-body {
      padding: 10px 12px;
      border-top: 1px solid var(--color-border-light);
      background-color: #fafcff;
      font-size: 12.5px;
      line-height: 1.5;
    }

    .chunk-meta {
      display: flex;
      gap: 16px;
      margin-bottom: 8px;
      font-size: 11px;
      color: var(--color-text-muted);
      font-family: var(--font-family-mono);
    }

    .chunk-content {
      color: #334155;
      white-space: pre-wrap;
    }
  `]
})
export class EvidenceCardComponent {
  evidenceList = input<EvidenceRecord[]>([]);
  isAllExpanded = false;

  toggleAll() {
    this.isAllExpanded = !this.isAllExpanded;
  }

  toggleItem(item: EvidenceRecord) {
    item.expanded = !item.expanded;
  }
}
