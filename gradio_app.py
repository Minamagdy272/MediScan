"""A small, user-driven chat interface for the MediScan pipeline with complete dark mode."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from uuid import uuid4

import gradio as gr


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

for path in (PROJECT_ROOT, SRC_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

CUSTOM_CSS = """
:root, html, body, .dark, .light, gradio-app, .gradio-container, #root, .contain {
    background-color: #0b0f19 !important;
    background: #0b0f19 !important;
    color: #f1f5f9 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}

.gradio-container {
    max-width: 900px !important;
    margin: 0 auto !important;
    min-height: 100vh;
    padding: 24px 20px !important;
    background-color: #0b0f19 !important;
}

.brand {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 0 0 22px;
    color: #ffffff !important;
}

.brand-mark {
    display: grid !important;
    place-items: center !important;
    width: 36px !important;
    height: 36px !important;
    border-radius: 10px !important;
    background: #2563eb !important;
    color: #ffffff !important;
    font-size: 18px !important;
    font-weight: 800 !important;
}

.brand h1 {
    margin: 0 !important;
    font-size: 20px !important;
    font-weight: 700 !important;
    color: #ffffff !important;
}

.brand span {
    color: #94a3b8 !important;
    font-size: 13px !important;
}

.welcome {
    padding: 36px 20px 24px !important;
    text-align: center !important;
}

.welcome h2 {
    margin: 0 0 10px !important;
    font-size: 26px !important;
    font-weight: 700 !important;
    color: #ffffff !important;
}

.welcome p {
    max-width: 620px !important;
    margin: 0 auto !important;
    color: #cbd5e1 !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
}

/* Chatbot Area */
.chatbot, [data-testid="chatbot"], .gradio-chatbot {
    border: 1px solid #1f2937 !important;
    border-radius: 14px !important;
    background-color: #111827 !important;
    min-height: 400px !important;
}

.chatbot .message, .chatbot [data-testid="message"], .chatbot p, .chatbot span {
    color: #f1f5f9 !important;
}

.chatbot [data-testid="user"], .chatbot .user {
    background-color: #1d4ed8 !important;
    color: #ffffff !important;
    border-radius: 12px !important;
}

.chatbot [data-testid="bot"], .chatbot .bot {
    background-color: #1e293b !important;
    color: #f1f5f9 !important;
    border: 1px solid #334155 !important;
    border-radius: 12px !important;
}

.chatbot .placeholder, .chatbot .empty {
    color: #94a3b8 !important;
}

/* Input Area */
.message-wrap {
    position: sticky;
    bottom: 0;
    padding: 14px 0 0 !important;
    background: linear-gradient(0deg, #0b0f19 80%, rgba(11, 15, 25, 0)) !important;
}

.message-wrap textarea {
    border: 1px solid #334155 !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4) !important;
    padding: 14px 18px !important;
    background-color: #1e293b !important;
    color: #ffffff !important;
    font-size: 14px !important;
}

.message-wrap textarea::placeholder {
    color: #64748b !important;
}

.message-wrap textarea:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3) !important;
}

.send-button button {
    min-width: 46px !important;
    height: 46px !important;
    border-radius: 12px !important;
    border: 0 !important;
    background-color: #2563eb !important;
    color: #ffffff !important;
    font-size: 18px !important;
    font-weight: bold !important;
    cursor: pointer !important;
    transition: background 0.15s ease !important;
}

.send-button button:hover {
    background-color: #1d4ed8 !important;
}

.clear-button button {
    color: #94a3b8 !important;
    border: 1px solid #1f2937 !important;
    background-color: #111827 !important;
    border-radius: 10px !important;
    padding: 8px 16px !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
    margin-top: 10px !important;
}

.clear-button button:hover {
    background-color: #1e293b !important;
    color: #ffffff !important;
    border-color: #334155 !important;
}

.disclaimer {
    margin: 14px 0 0 !important;
    text-align: center !important;
    color: #64748b !important;
    font-size: 11px !important;
}

footer {
    display: none !important;
}
"""


def new_session_id() -> str:
    """Create an isolated server-side history for one browser session."""
    return f"web-{uuid4().hex}"


def _run_pipeline(message: str, session_id: str):
    """Import the model-dependent pipeline only when a user submits a query."""
    from pipeline.coordinator import run_pipeline

    return run_pipeline(user_message=message, session_id=session_id)


def respond(message: str, history: list, session_id: str):
    """Send user's current text to the pipeline and update history with messages format."""
    message = (message or "").strip()
    history = list(history or [])

    if not message:
        return history, "", session_id

    try:
        result = _run_pipeline(message, session_id)
        response_text = result.final_answer
    except Exception as e:
        response_text = (
            f"I could not complete that analysis right now: {e}. Please check that the "
            "MediScan pipeline and its configured services are available, then try again."
        )

    # Compatible with Gradio 5+ messages format
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": response_text})
    return history, "", session_id


def start_new_chat(session_id: str):
    """Start an isolated conversation without loading model dependencies."""
    return [], new_session_id()


APP_THEME = gr.themes.Default(
    primary_hue="blue",
    neutral_hue="slate",
).set(
    body_background_fill="#0b0f19",
    body_background_fill_dark="#0b0f19",
    body_text_color="#f8fafc",
    body_text_color_dark="#f8fafc",
    body_text_color_subdued="#94a3b8",
    body_text_color_subdued_dark="#94a3b8",
    background_fill_primary="#111827",
    background_fill_primary_dark="#111827",
    background_fill_secondary="#0b0f19",
    background_fill_secondary_dark="#0b0f19",
    border_color_primary="#1f2937",
    border_color_primary_dark="#1f2937",
    block_background_fill="#111827",
    block_background_fill_dark="#111827",
    block_border_color="#1f2937",
    block_border_color_dark="#1f2937",
    block_label_text_color="#94a3b8",
    block_label_text_color_dark="#94a3b8",
    input_background_fill="#1e293b",
    input_background_fill_dark="#1e293b",
    input_border_color="#334155",
    input_border_color_dark="#334155",
    input_border_color_focus="#38bdf8",
    input_border_color_focus_dark="#38bdf8",
)

FORCE_DARK_JS = """
() => {
    document.documentElement.classList.add('dark');
    document.body.classList.add('dark');
}
"""

with gr.Blocks(title="MediScan") as app:
    session_id = gr.State(value=new_session_id)

    gr.HTML(
        """
        <div class="brand">
          <div class="brand-mark">✚</div>
          <div><h1>MediScan</h1><span>Clinical AI assistant</span></div>
        </div>
        """
    )

    gr.HTML(
        """
        <section class="welcome">
          <h2>How can I help with your clinical question?</h2>
          <p>Write a question or paste clinical findings. MediScan will return an evidence-grounded response for the information you provide.</p>
        </section>
        """
    )

    chatbot = gr.Chatbot(
        show_label=False,
        placeholder="Your conversation will appear here.",
        render_markdown=True,
        elem_classes=["chatbot"],
    )

    with gr.Row(elem_classes=["message-wrap"]):
        message = gr.Textbox(
            placeholder="Message MediScan…",
            show_label=False,
            lines=1,
            max_lines=8,
            scale=12,
        )
        send = gr.Button("↑", variant="primary", elem_classes=["send-button"], scale=1)

    clear = gr.Button("New chat", elem_classes=["clear-button"])
    gr.HTML(
        "<p class=\"disclaimer\">MediScan is a research decision-support tool. Verify clinical findings with a qualified clinician.</p>"
    )

    inputs = [message, chatbot, session_id]
    outputs = [chatbot, message, session_id]
    message.submit(fn=respond, inputs=inputs, outputs=outputs)
    send.click(fn=respond, inputs=inputs, outputs=outputs)
    clear.click(fn=start_new_chat, inputs=[session_id], outputs=[chatbot, session_id])


def launch_mediscan_ui(**launch_options):
    """Launch the UI with its dark theme in a script or notebook."""
    gr.close_all()
    return app.launch(theme=APP_THEME, css=CUSTOM_CSS, js=FORCE_DARK_JS, **launch_options)


if __name__ == "__main__":
    launch_mediscan_ui(
        server_name=os.getenv("MEDISCAN_UI_HOST", "127.0.0.1"),
        server_port=int(os.getenv("MEDISCAN_UI_PORT", "7860")),
        share=False,
    )
