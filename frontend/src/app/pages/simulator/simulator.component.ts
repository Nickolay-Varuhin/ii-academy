import { Component, OnInit, AfterViewChecked, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { IconComponent } from '../../components/icon/icon.component';

interface ChatMessage {
  id?: number;
  sender_type: 'user' | 'ai';
  message_text: string;
  created_at?: string | Date;
  isTyping?: boolean;
}

@Component({
  selector: 'app-simulator',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  template: `
    <!-- ВЫБОР СЦЕНАРИЯ -->
    @if (!session) {
      <div style="padding:24px">
        <h2 style="font-size:24px;font-weight:700;margin-bottom:4px">Интерактивный AI-Симулятор</h2>
        <p style="font-size:14px;color:#6b7280;margin-bottom:24px">
          Отрабатывайте реальные рабочие ситуации в безопасной среде.
        </p>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
          @for (sc of scenarios; track sc.id) {
            <div class="card scenario-card" (click)="startDialog(sc)"
                 [style.border]="sc.completed ? '1.5px solid #86efac' : '1px solid #f3f4f6'">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <span [class]="'badge ' + difficultyBadge(sc.difficulty)">
                  {{difficultyLabel(sc.difficulty)}}
                </span>
                @if (sc.completed) {
                  <span class="badge badge-green">
                    <app-icon name="check" [size]="12" color="#16a34a"></app-icon>
                    <span>Пройдено</span>
                  </span>
                }
              </div>

              <h3 style="font-weight:700;font-size:18px;margin-top:12px">{{sc.title}}</h3>
              <p style="font-size:14px;color:#6b7280;margin-top:8px">{{sc.description}}</p>

              @if (sc.attempts_count > 0) {
                <div style="display:flex;justify-content:space-between;align-items:center;margin-top:16px;padding-top:12px;border-top:1px dashed #e5e7eb">
                  <div style="font-size:12px;color:#6b7280;display:flex;align-items:center;gap:4px">
                    <app-icon name="play" [size]="12" color="#6b7280"></app-icon>
                    <span>Попыток: <strong>{{sc.attempts_count}}</strong></span>
                  </div>
                  @if (sc.best_score !== null && sc.best_score !== undefined) {
                    <div style="font-size:12px;color:#16a34a;font-weight:600;display:flex;align-items:center;gap:4px">
                      <app-icon name="trophy" [size]="12" color="#16a34a"></app-icon>
                      <span>{{sc.best_score | number:'1.0-0'}}/100</span>
                    </div>
                  }
                </div>
              } @else {
                <div style="font-size:12px;color:#9ca3af;margin-top:12px;display:flex;align-items:center;gap:4px">
                  <app-icon name="chat" [size]="12" color="#9ca3af"></app-icon>
                  <span>Макс. ходов: {{sc.max_turns}}</span>
                </div>
              }
            </div>
          }
        </div>
      </div>
    }

    <!-- ДИАЛОГ -->
    @if (session) {
      <div style="padding:24px;display:flex;gap:24px;height:calc(100vh - 60px)">
        <div style="width:300px;flex-shrink:0;display:flex;flex-direction:column;gap:16px;overflow-y:auto">
          <div class="card">
            <span [class]="'badge ' + difficultyBadge(selected?.difficulty)">
              {{difficultyLabel(selected?.difficulty)}}
            </span>
            <h3 style="font-weight:700;font-size:18px;margin-top:12px">{{selected?.title}}</h3>
            <p style="font-size:14px;color:#6b7280;margin-top:8px">{{selected?.description}}</p>
          </div>

          <div class="card">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
              <app-icon name="check" [size]="16" color="#16a34a"></app-icon>
              <h4 style="font-weight:600">Учебные цели</h4>
            </div>
            <ul style="font-size:14px;color:#4b5563;list-style:none;display:flex;flex-direction:column;gap:8px">
              <li>— Сохранять спокойный, объективный тон</li>
              <li>— Использовать «Я-сообщения»</li>
              <li>— Направить диалог на совместное решение</li>
            </ul>
          </div>

          <div style="background:#fefce8;border:1px solid #fef3c7;border-radius:12px;padding:16px">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
              <app-icon name="lightbulb" [size]="16" color="#ca8a04"></app-icon>
              <h4 style="font-weight:600">Совет наставника</h4>
            </div>
            <p style="font-size:13px;color:#4b5563;line-height:1.5">
              Начните с признания позиции собеседника, прежде чем переходить
              к обсуждению проблемных моментов.
            </p>
          </div>

          <div style="font-size:13px;color:#6b7280;padding:0 4px">
            Ходов пользователя: <strong>{{userTurns}}</strong> / {{selected?.max_turns}}
          </div>

          @if (session.status === 'active' && !feedback) {
            <button (click)="completeDialog()" [disabled]="aiTyping || waitingUserSave"
              class="btn-ghost" style="justify-content:center">
              <app-icon name="stop" [size]="14"></app-icon>
              <span>Завершить диалог</span>
            </button>
          }
          @if (session.status !== 'active' || feedback) {
            <button (click)="backToScenarios()" class="btn-primary" style="border-radius:8px;justify-content:center">
              <app-icon name="arrow-left" [size]="16" color="#fff"></app-icon>
              <span>Назад к сценариям</span>
            </button>
          }
        </div>

        <div style="flex:1;display:flex;flex-direction:column;background:#fff;border-radius:12px;border:1px solid #f3f4f6">
          <div style="padding:12px 20px;border-bottom:1px solid #f3f4f6;display:flex;align-items:center;gap:12px">
            <div style="width:40px;height:40px;background:#dbeafe;border-radius:50%;display:flex;align-items:center;justify-content:center">
              <app-icon name="robot" [size]="20" color="#2563eb"></app-icon>
            </div>
            <div>
              <div style="font-weight:600;color:#1f2937">AI-Собеседник</div>
              <div style="font-size:12px;font-weight:500"
                   [style.color]="session.status === 'active' ? '#16a34a' : '#9ca3af'">
                @if (aiTyping) { <span>● AI печатает...</span> }
                @else if (session.status === 'active') { <span>● Ожидает ответа</span> }
                @else { <span>● Диалог завершён</span> }
              </div>
            </div>
            <div style="margin-left:auto;font-size:12px;color:#9ca3af">
              Сообщений: {{messages.length}}
            </div>
          </div>

          <div #chatArea style="flex:1;overflow-y:auto;padding:20px">
            @if (selected) {
              <div style="text-align:center;font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:0.05em;padding:8px 0;margin-bottom:16px">
                Начало сценария: {{selected.title}}
              </div>
            }

            @for (m of messages; track trackMessage($index, m)) {
              @if (m.sender_type === 'ai') {
                <div style="display:flex;justify-content:flex-start;margin-bottom:16px">
                  <div style="width:32px;height:32px;background:#dbeafe;border-radius:50%;display:flex;align-items:center;justify-content:center;margin-right:8px;flex-shrink:0">
                    <app-icon name="robot" [size]="16" color="#2563eb"></app-icon>
                  </div>
                  <div style="max-width:480px;padding:12px 16px;border-radius:16px;border-bottom-left-radius:4px;background:#f3f4f6;color:#1f2937;font-size:14px;line-height:1.5">
                    <div style="font-size:12px;color:#9ca3af;margin-bottom:4px">AI-Тьютор</div>
                    <span>{{m.message_text}}</span>@if (m.isTyping) {<span class="cursor">▌</span>}
                  </div>
                </div>
              } @else {
                <div style="display:flex;justify-content:flex-end;margin-bottom:16px">
                  <div style="max-width:480px;padding:12px 16px;border-radius:16px;border-bottom-right-radius:4px;background:#2563eb;color:#fff;font-size:14px;line-height:1.5">
                    {{m.message_text}}
                  </div>
                </div>
              }
            }

            @if (aiTyping && !hasTypingMessage) {
              <div style="display:flex;justify-content:flex-start;margin-bottom:16px">
                <div style="width:32px;height:32px;background:#dbeafe;border-radius:50%;display:flex;align-items:center;justify-content:center;margin-right:8px">
                  <app-icon name="robot" [size]="16" color="#2563eb"></app-icon>
                </div>
                <div style="padding:12px 16px;background:#f3f4f6;border-radius:16px;border-bottom-left-radius:4px">
                  <div class="dots-indicator"><span></span><span></span><span></span></div>
                </div>
              </div>
            }
          </div>

          @if (feedback) {
            <div style="padding:16px 20px;border-top:1px solid #f3f4f6;background:#f0fdf4">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
                <app-icon name="trophy" [size]="18" color="#16a34a"></app-icon>
                <h4 style="font-weight:700">Результаты симуляции</h4>
              </div>
              <div style="font-size:24px;font-weight:700;color:#16a34a;margin-bottom:8px">
                {{feedback.overall_score}}/100
              </div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-bottom:12px">
                @for (entry of feedbackEntries; track entry[0]) {
                  <div style="display:flex;justify-content:space-between;font-size:14px">
                    <span style="color:#4b5563">{{entry[0]}}</span>
                    <span style="font-weight:600">{{entry[1] | number:'1.0-0'}}</span>
                  </div>
                }
              </div>
              <p style="font-size:14px;color:#4b5563">{{feedback.ai_feedback_text}}</p>
              <p style="font-size:14px;color:#2563eb;font-weight:500;margin-top:8px">
                {{feedback.recommendations}}
              </p>
            </div>
          }

          @if (session.status === 'active' && !feedback) {
            <div style="padding:12px 20px;border-top:1px solid #f3f4f6">
              <div style="display:flex;gap:8px">
                <input [(ngModel)]="input"
                       (keydown.enter)="sendMessage()"
                       [disabled]="aiTyping || waitingUserSave"
                       placeholder="Введите ваш ответ..."
                       style="flex:1;border-radius:12px">
                <button (click)="sendMessage()"
                        [disabled]="aiTyping || waitingUserSave || !input.trim()"
                        [style.opacity]="(aiTyping || waitingUserSave || !input.trim()) ? '0.5' : '1'"
                        style="background:#2563eb;color:#fff;border:none;border-radius:12px;padding:0 16px;cursor:pointer;display:flex;align-items:center">
                  <app-icon name="send" [size]="18" color="#fff"></app-icon>
                </button>
              </div>
              <div style="font-size:12px;color:#9ca3af;margin-top:8px">
                ИИ анализирует тональность и эмпатию в реальном времени
              </div>
            </div>
          }
        </div>
      </div>
    }
  `,
  styles: [`
    .scenario-card {
      cursor: pointer;
      transition: border-color 0.2s, transform 0.1s, box-shadow 0.2s;
    }
    .scenario-card:hover {
      border-color: #93c5fd !important;
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
    }
    .cursor {
      display: inline-block; color: #6b7280;
      animation: blink 0.8s step-start infinite;
      margin-left: 2px;
    }
    @keyframes blink { 50% { opacity: 0; } }

    .dots-indicator { display: flex; gap: 4px; align-items: center; height: 20px; }
    .dots-indicator span {
      width: 7px; height: 7px; background: #9ca3af; border-radius: 50%;
      animation: bounce 1.2s infinite ease-in-out both;
    }
    .dots-indicator span:nth-child(1) { animation-delay: -0.32s; }
    .dots-indicator span:nth-child(2) { animation-delay: -0.16s; }
    @keyframes bounce {
      0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
      40%           { transform: scale(1);   opacity: 1; }
    }
  `],
})
export class SimulatorComponent implements OnInit, AfterViewChecked {
  @ViewChild('chatArea') chatArea?: ElementRef<HTMLDivElement>;

  scenarios: any[] = [];
  selected: any = null;
  session: any = null;
  messages: ChatMessage[] = [];
  input = '';

  waitingUserSave = false;
  aiTyping = false;

  feedback: any = null;
  feedbackEntries: [string, number][] = [];

  private shouldScrollToBottom = false;

  constructor(private api: ApiService) {}

  ngOnInit() { this.loadScenarios(); }

  ngAfterViewChecked() {
    if (this.shouldScrollToBottom) {
      this.scrollToBottom();
      this.shouldScrollToBottom = false;
    }
  }

  private loadScenarios() {
    this.api.getScenarios().subscribe((data: any) => {
      this.scenarios = data || [];
    });
  }

  get userTurns(): number {
    return this.messages.filter(m => m.sender_type === 'user').length;
  }

  get hasTypingMessage(): boolean {
    return this.messages.some(m => m.isTyping);
  }

  trackMessage(index: number, m: ChatMessage) {
    return m.id ?? `temp-${index}-${m.sender_type}`;
  }

  difficultyLabel(d?: number): string {
    if (!d) return '';
    if (d >= 3) return 'Сложный уровень';
    if (d >= 2) return 'Средний уровень';
    return 'Начальный уровень';
  }

  difficultyBadge(d?: number): string {
    if (!d) return 'badge-blue';
    if (d >= 3) return 'badge-red';
    if (d >= 2) return 'badge-yellow';
    return 'badge-green';
  }

  private scrollToBottom() {
    if (this.chatArea) {
      const el = this.chatArea.nativeElement;
      el.scrollTop = el.scrollHeight;
    }
  }
  private requestScroll() { this.shouldScrollToBottom = true; }

  startDialog(sc: any) {
    this.selected = sc;
    this.feedback = null;
    this.messages = [];
    this.input = '';
    this.aiTyping = false;
    this.waitingUserSave = false;

    this.api.startDialog(sc.id).subscribe({
      next: (data: any) => {
        this.session = data;
        const welcome = (data.messages && data.messages[0]) || null;
        if (welcome) this.startTypingMessage(welcome);
        this.requestScroll();
      },
      error: (err: any) => console.error('Ошибка старта:', err),
    });
  }

  sendMessage() {
    const text = (this.input || '').trim();
    if (!text || !this.session || this.aiTyping || this.waitingUserSave) return;

    const currentSession = this.session;
    const optimisticMsg: ChatMessage = {
      sender_type: 'user',
      message_text: text,
      created_at: new Date(),
    };
    this.messages = [...this.messages, optimisticMsg];
    this.input = '';
    this.requestScroll();

    this.waitingUserSave = true;
    this.api.sendMessage(currentSession.id, text).subscribe({
      next: (savedMsg: any) => {
        const lastIdx = this.messages.length - 1;
        if (lastIdx >= 0 && this.messages[lastIdx].sender_type === 'user') {
          this.messages[lastIdx] = {
            id: savedMsg.id,
            sender_type: 'user',
            message_text: savedMsg.message_text,
            created_at: savedMsg.created_at,
          };
        }
        this.waitingUserSave = false;
        this.requestAiReply(currentSession.id);
      },
      error: (err: any) => {
        console.error('Ошибка сохранения:', err);
        this.messages = this.messages.filter(m => m !== optimisticMsg);
        this.waitingUserSave = false;
      },
    });
  }

  private requestAiReply(sessionId: number) {
    this.aiTyping = true;
    this.requestScroll();

    this.api.requestAiReply(sessionId).subscribe({
      next: (resp: any) => {
        const aiMsg = resp.message;
        this.startTypingMessage(aiMsg);
        if (resp.session_completed && resp.feedback) {
          setTimeout(() => {
            this.session = { ...this.session, status: 'completed' };
            this.feedback = resp.feedback;
            this.feedbackEntries = Object.entries(resp.feedback.skill_scores || {});
          }, this.estimateTypingDuration(aiMsg.message_text) + 500);
        }
      },
      error: (err: any) => {
        console.error('Ошибка AI-ответа:', err);
        this.aiTyping = false;
      },
    });
  }

  private startTypingMessage(serverMsg: any) {
    const fullText: string = serverMsg.message_text || '';
    const words = fullText.split(/(\s+)/);
    const msg: ChatMessage = {
      id: serverMsg.id,
      sender_type: 'ai',
      message_text: '',
      created_at: serverMsg.created_at,
      isTyping: true,
    };
    this.messages = [...this.messages, msg];
    this.aiTyping = true;

    let i = 0;
    const typeSpeed = 45;
    const interval = setInterval(() => {
      if (i >= words.length) {
        clearInterval(interval);
        msg.isTyping = false;
        this.aiTyping = false;
        this.messages = [...this.messages];
        this.requestScroll();
        return;
      }
      msg.message_text += words[i];
      i++;
      this.messages = [...this.messages];
      this.requestScroll();
    }, typeSpeed);
  }

  private estimateTypingDuration(text: string): number {
    return text.split(/\s+/).length * 45;
  }

  completeDialog() {
    if (!this.session || this.aiTyping || this.waitingUserSave) return;
    this.api.completeDialog(this.session.id).subscribe({
      next: (fb: any) => {
        this.feedback = fb;
        this.feedbackEntries = Object.entries(fb.skill_scores || {});
        this.session = { ...this.session, status: 'completed' };
      },
      error: (err: any) => console.error('Ошибка завершения:', err),
    });
  }

  backToScenarios() {
    this.session = null;
    this.feedback = null;
    this.selected = null;
    this.messages = [];
    this.feedbackEntries = [];
    this.input = '';
    this.aiTyping = false;
    this.waitingUserSave = false;
    this.loadScenarios();
  }
}
