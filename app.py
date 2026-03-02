import streamlit as st
import json
import base64
import os
import time
import streamlit.components.v1 as components
from dotenv import load_dotenv

# Configuração da página - DEVE ser o primeiro comando
st.set_page_config(
    page_title="Simulado AWS CLF-C02 - Por Adalberto Caldeira - Preparatório Escola da Nuvem 2026",
    page_icon="☁️",
    layout="centered"
)

# Carrega as variáveis de ambiente
load_dotenv()

# --- CSS Personalizado ---
st.markdown("""
<style>
    .stRadio > label { font-size: 16px; font-weight: bold; }
    .question-box { 
        background-color: #f0f2f6; 
        color: #0e1117; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 5px solid #ff9900; 
        font-size: 18px;
        margin-bottom: 20px;
    }
    .timer-display {
        font-size: 24px;
        font-weight: bold;
        color: #d9534f;
        text-align: center;
        padding: 10px;
        border: 2px solid #d9534f;
        border-radius: 10px;
        margin-bottom: 20px;
        background-color: #fff5f5;
    }
    .timer-warning {
        color: #ff4500 !important;
        background-color: #ffe0e0 !important;
        border-color: #ff4500 !important;
        animation: pulse 0.8s infinite;
    }
    @keyframes pulse {
        0%   { opacity: 1; }
        50%  { opacity: 0.6; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

TIME_LIMIT = 120  # segundos por questão

# --- Funções Auxiliares ---
def load_questions():
    b64_data = os.getenv("EXAM_DATA_B64")
    if not b64_data:
        st.error("ERRO CRÍTICO: Banco de questões não encontrado.")
        st.stop()
    try:
        json_str = base64.b64decode(b64_data).decode('utf-8')
        return json.loads(json_str)
    except Exception as e:
        st.error(f"Erro ao carregar questões: {e}")
        st.stop()

def verify_password(input_pass):
    b64_pass = os.getenv("EXAM_PASSWORD_B64")
    if not b64_pass:
        st.error("ERRO: Senha não configurada no servidor.")
        st.stop()
    try:
        correct_pass = base64.b64decode(b64_pass).decode('utf-8')
        return input_pass == correct_pass
    except:
        return False

# --- Inicialização de Estado ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'student_name' not in st.session_state:
    st.session_state.student_name = ""
if 'current_q_index' not in st.session_state:
    st.session_state.current_q_index = 0
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'exam_finished' not in st.session_state:
    st.session_state.exam_finished = False
if 'q_start_time' not in st.session_state:
    st.session_state.q_start_time = None  # Será definido após login

# --- LÓGICA DE NAVEGAÇÃO ---
def go_next_question():
    if st.session_state.current_q_index < len(st.session_state.questions) - 1:
        st.session_state.current_q_index += 1
        st.session_state.q_start_time = time.time()  # Reinicia o relógio
    else:
        st.session_state.exam_finished = True
    st.rerun()

def submit_answer(selected_option, auto_timeout=False):
    current_idx = st.session_state.current_q_index
    question_data = st.session_state.questions[current_idx]

    if auto_timeout:
        is_correct = False
        selected_option = "NÃO RESPONDEU (Tempo Esgotado)"
        time_spent = float(TIME_LIMIT)
    else:
        time_spent = time.time() - st.session_state.q_start_time
        is_correct = (selected_option == question_data['answer'])

    st.session_state.user_answers[current_idx] = {
        "selected": selected_option,
        "correct_answer": question_data['answer'],
        "explanation": question_data['explanation'],
        "time_spent": time_spent,
        "is_correct": is_correct,
        "timed_out": auto_timeout,
        "question_text": question_data['question']
    }

    go_next_question()

# =============================================================================
# --- TELA DE LOGIN ---
# =============================================================================
if not st.session_state.logged_in:
    st.title("🔐 Acesso ao Simulado AWS")
    st.markdown("Bem-vindo ao simulado preparatório do **Mentor. Adalberto Caldeira Brant Filho**.")

    with st.form("login_form"):
        st.markdown("### Identificação do Aluno")
        name_input = st.text_input("Nome e Sobrenome", placeholder="Ex: nome ")
        pass_input = st.text_input("Senha do Exame", type="password", placeholder="Digite a senha fornecida")
        submitted = st.form_submit_button("Iniciar Simulado")

        if submitted:
            if not name_input.strip():
                st.warning("Por favor, digite seu nome completo.")
            elif not verify_password(pass_input):
                st.error("Senha incorreta!")
            else:
                st.session_state.logged_in = True
                st.session_state.student_name = name_input.strip()
                st.session_state.questions = load_questions()
                st.session_state.current_q_index = 0
                st.session_state.q_start_time = time.time()
                st.rerun()

# =============================================================================
# --- TELA DO EXAME ---
# =============================================================================
else:
    if not st.session_state.exam_finished:

        q_idx = st.session_state.current_q_index
        q_data = st.session_state.questions[q_idx]

        # --- Cálculo do tempo restante (fonte da verdade: servidor Python) ---
        elapsed_time = time.time() - st.session_state.q_start_time
        remaining_time = TIME_LIMIT - elapsed_time
        is_timeout = remaining_time <= 0

        # --- Timeout detectado pelo servidor: avança automaticamente ---
        if is_timeout:
            # Exibe uma mensagem breve antes de avançar
            st.warning(f"⌛ Tempo esgotado para a Questão {q_idx + 1}! Avançando...")
            time.sleep(2)
            submit_answer(None, auto_timeout=True)
            st.stop()

        # --- Header ---
        st.title("☁️ Simulado AWS CLF-C02")
        st.markdown(
            f"**Aluno:** {st.session_state.student_name} | "
            f"**Questão {q_idx + 1} de {len(st.session_state.questions)}**"
        )

        # --- Timer Visual (JS puro para contagem regressiva suave) ---
        # A chave `q_idx` no ID força o iframe a ser recriado a cada nova questão,
        # reiniciando o JavaScript do zero. Essa é a correção principal do timer.
        warning_class = "timer-warning" if remaining_time < 30 else ""
        timer_html = f"""
        <style>
            .timer-display {{
                font-family: sans-serif;
                font-size: 22px;
                font-weight: bold;
                color: #d9534f;
                text-align: center;
                padding: 10px;
                border: 2px solid #d9534f;
                border-radius: 10px;
                background-color: #fff5f5;
            }}
            .timer-warning {{
                color: #ff4500 !important;
                background-color: #ffe0e0 !important;
                border-color: #ff4500 !important;
                animation: pulse 0.8s infinite;
            }}
            @keyframes pulse {{
                0%   {{ opacity: 1; }}
                50%  {{ opacity: 0.5; }}
                100% {{ opacity: 1; }}
            }}
        </style>
        <div id="timer_q{q_idx}" class="timer-display {warning_class}">
            ⏳ Tempo restante: <span id="time_left">{int(remaining_time)}</span>s
        </div>
        <script>
            (function() {{
                var timeLeft = {int(remaining_time)};
                var el = document.getElementById("time_left");
                var box = document.getElementById("timer_q{q_idx}");

                var countdown = setInterval(function() {{
                    if (timeLeft > 0) {{
                        timeLeft--;
                        el.textContent = timeLeft;
                        if (timeLeft <= 30) {{
                            box.classList.add("timer-warning");
                        }}
                    }} else {{
                        clearInterval(countdown);
                        el.textContent = "0";
                        box.textContent = "⌛ Tempo esgotado!";
                    }}
                }}, 1000);
            }})();
        </script>
        """

        # height precisa ser suficiente para o div; key força recriação do iframe a cada questão
        components.html(timer_html, height=70, scrolling=False)

        # --- Questão ---
        st.markdown(f"""
        <div class="question-box">
            {q_data['question']}
        </div>
        """, unsafe_allow_html=True)

        # --- Formulário de resposta ---
        with st.form(key=f"q_form_{q_idx}"):
            choice = st.radio("Selecione a alternativa correta:", q_data['options'], index=None)
            submit_btn = st.form_submit_button(label="✅ Confirmar Resposta")

            if submit_btn:
                # Recalcula o tempo no momento do clique
                elapsed_now = time.time() - st.session_state.q_start_time
                if elapsed_now > TIME_LIMIT:
                    submit_answer(None, auto_timeout=True)
                elif choice:
                    submit_answer(choice)
                else:
                    st.warning("⚠️ Selecione uma opção antes de confirmar.")

        # --- Auto-rerun a cada 1s para que o Python detecte o timeout ---
        # Isso garante que mesmo sem interação do usuário, o servidor vai checar o tempo.
        time.sleep(1)
        st.rerun()

# =============================================================================
# --- TELA DE RESULTADOS ---
# =============================================================================
    else:
        st.success(f"🏁 Simulado Finalizado, {st.session_state.student_name}!")

        total_q = len(st.session_state.questions)
        correct_count = sum(1 for a in st.session_state.user_answers.values() if a['is_correct'])
        score = (correct_count / total_q) * 100

        col1, col2, col3 = st.columns(3)
        col1.metric("Nota Final", f"{score:.1f}%")
        col2.metric("Acertos", f"{correct_count}/{total_q}")
        col3.metric("Erros", f"{total_q - correct_count}/{total_q}")

        if score >= 80:
            st.balloons()
            st.markdown(f"### ✅ APROVADO! Parabéns, {st.session_state.student_name}.")
        else:
            st.markdown(f"### ⚠️ NECESSITA REVISÃO. O corte é 80%.")

        st.divider()
        st.subheader("📊 Relatório de Desempenho")

        for i in range(total_q):
            ans = st.session_state.user_answers.get(i)
            if not ans:
                continue

            if ans['timed_out']:
                icon = "⌛"
            elif ans['is_correct']:
                icon = "✅"
            else:
                icon = "❌"

            label = f"Questão {i + 1}: {icon} (Tempo: {ans['time_spent']:.0f}s)"
            if ans['timed_out']:
                label += " — TEMPO ESGOTADO"

            with st.expander(label):
                st.markdown(f"**Pergunta:** {ans['question_text']}")

                if ans['timed_out']:
                    st.error("⚠️ **O tempo acabou para esta questão.**")
                    st.markdown(f"**Resposta correta:** :green[{ans['correct_answer']}]")
                elif ans['is_correct']:
                    st.markdown(f"**Sua resposta:** :green[{ans['selected']}]")
                else:
                    st.markdown(f"**Sua resposta:** :red[{ans['selected']}]")
                    st.markdown(f"**Resposta correta:** :green[{ans['correct_answer']}]")

                st.info(f"💡 **Explicação:** {ans['explanation']}")

        if st.button("🔄 Sair / Novo Exame"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
