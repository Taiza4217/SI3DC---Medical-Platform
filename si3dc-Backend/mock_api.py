"""SI3DC — Mock API Server (Standalone, sem banco de dados).

Servidor FastAPI leve que simula todos os endpoints necessários
para o frontend funcionar sem PostgreSQL/Redis.

Uso:
    uvicorn mock_api:app --port 8000 --reload
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="SI3DC Mock API",
    version="1.0.0-mock",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════════════════════════════
# MOCK DATA
# ══════════════════════════════════════════════════════════════════════

MOCK_USERS = [
    {
        "id": "101",
        "name": "Dr. Ana Oliveira",
        "professionalId": "123456-SP",
        "password": "password123",
        "healthNetworkId": "hc_sp",
        "permissionLevel": "Básico",
        "specialty": "Clínica Geral",
        "institution": "Hospital das Clínicas - SP",
    },
    {
        "id": "102",
        "name": "Dr. Carlos Santos",
        "professionalId": "789012-SP",
        "password": "password123",
        "healthNetworkId": "hc_sp",
        "permissionLevel": "Médio",
        "specialty": "Cardiologista",
        "institution": "Hospital das Clínicas - SP",
    },
    {
        "id": "103",
        "name": "Gestor Silva",
        "professionalId": "ADM-HCSP-01",
        "password": "adminpass",
        "healthNetworkId": "hc_sp",
        "permissionLevel": "Administrativo",
        "specialty": "Administração",
        "institution": "Hospital das Clínicas - SP",
    },
    {
        "id": "201",
        "name": "Dra. Beatriz Lima",
        "professionalId": "112233-SP",
        "password": "password123",
        "healthNetworkId": "einstein",
        "permissionLevel": "Básico",
        "specialty": "Neurologia",
        "institution": "Hospital Israelita Albert Einstein",
    },
    {
        "id": "202",
        "name": "Gestora Costa",
        "professionalId": "ADM-EINSTEIN-01",
        "password": "adminpass",
        "healthNetworkId": "einstein",
        "permissionLevel": "Administrativo",
        "specialty": "Administração",
        "institution": "Hospital Israelita Albert Einstein",
    },
    {
        "id": "301",
        "name": "Dr. Roberto Alves",
        "professionalId": "445566-RJ",
        "password": "password123",
        "healthNetworkId": "unimed",
        "permissionLevel": "Médio",
        "specialty": "Ortopedia",
        "institution": "Rede Unimed",
    },
    {
        "id": "401",
        "name": "Dr. Usuário Teste",
        "professionalId": "PRO-SL-2024",
        "password": "sirio123",
        "healthNetworkId": "sirio",
        "permissionLevel": "Médio",
        "specialty": "Medicina Interna",
        "institution": "Hospital Sírio-Libanês",
    },
]

MOCK_PATIENTS = [
    {
        "id": "P001",
        "name": "José da Silva",
        "cpf": "123.456.789-00",
        "rg": "12.345.678-9",
        "sus": "898 0012 3456 7890",
        "hospitalId": "HC-2024-0001",
        "age": 68,
        "gender": "Masculino",
        "birthDate": "1958-03-15",
        "bloodType": "O+",
        "phone": "(11) 98765-4321",
        "summary": (
            "Paciente idoso, hipertenso crônico e diabético tipo 2, com histórico de "
            "cirurgia cardíaca (revascularização do miocárdio) há 5 anos. Faz uso contínuo "
            "de anticoagulante e anti-hipertensivos. Apresenta alergia grave a penicilina, "
            "manifestada por anafilaxia."
        ),
        "alerts": [
            {"type": "Alergia Grave", "text": "Penicilina (risco de anafilaxia)"},
            {"type": "Condição Crônica", "text": "Hipertensão e Diabetes Mellitus tipo 2"},
            {"type": "Cirurgia Relevante", "text": "Histórico de cirurgia cardíaca"},
            {"type": "Medicação Crítica", "text": "Uso atual de anticoagulante"},
        ],
    },
    {
        "id": "P002",
        "name": "Maria Oliveira",
        "cpf": "987.654.321-00",
        "rg": "98.765.432-1",
        "sus": "898 0098 7654 3210",
        "hospitalId": "HC-2024-0002",
        "age": 45,
        "gender": "Feminino",
        "birthDate": "1981-07-22",
        "bloodType": "A+",
        "phone": "(11) 91234-5678",
        "summary": (
            "Paciente feminina, 45 anos, em acompanhamento por asma moderada persistente "
            "e hipotireoidismo. Sem alergias medicamentosas conhecidas. História familiar "
            "de câncer de mama (mãe)."
        ),
        "alerts": [
            {"type": "Condição Crônica", "text": "Asma moderada persistente"},
            {"type": "Histórico Familiar", "text": "Câncer de mama (mãe)"},
        ],
    },
    {
        "id": "P003",
        "name": "João Pereira",
        "cpf": "456.789.123-00",
        "rg": "45.678.912-3",
        "sus": "898 0045 6789 1230",
        "hospitalId": "HC-2024-0003",
        "age": 32,
        "gender": "Masculino",
        "birthDate": "1994-01-10",
        "bloodType": "B-",
        "phone": "(11) 97654-3210",
        "summary": (
            "Paciente masculino, 32 anos, atendido previamente por fratura de úmero (2023). "
            "Sem comorbidades crônicas. Alergia a dipirona."
        ),
        "alerts": [
            {"type": "Alergia", "text": "Dipirona (reação cutânea)"},
        ],
    },
    {
        "id": "P004",
        "name": "Ana Costa",
        "cpf": "111.222.333-44",
        "rg": "11.222.333-4",
        "sus": "898 0000 1111 2222",
        "hospitalId": "HC-2024-0004",
        "age": 28,
        "gender": "Feminino",
        "birthDate": "1995-05-20",
        "bloodType": "O-",
        "phone": "(11) 95555-4444",
        "summary": "Paciente gestante (vítima de complicações na gestação anterior), sem alergias conhecidas.",
        "alerts": [
            {"type": "Atenção", "text": "Gestante (20 semanas)"},
        ],
    },
    {
        "id": "P005",
        "name": "Pedro Martins",
        "cpf": "555.666.777-88",
        "rg": "55.666.777-8",
        "sus": "898 0000 5555 6666",
        "hospitalId": "HC-2024-0005",
        "age": 55,
        "gender": "Masculino",
        "birthDate": "1968-09-12",
        "bloodType": "A-",
        "phone": "(11) 98888-7777",
        "summary": "Paciente com diagnóstico recente de DPOC. Tabagista ativo.",
        "alerts": [
            {"type": "Condição Crônica", "text": "DPOC"},
            {"type": "Comportamento", "text": "Tabagista ativo"},
        ],
    },
]

MOCK_EMERGENCY_DATA = {
    "patientName": "José da Silva",
    "criticalInfo": {
        "Alergias Críticas": "Penicilina (Anafilaxia)",
        "Medicamentos Atuais": "Warfarina (Anticoagulante), Losartana (Anti-hipertensivo)",
        "Doenças Crônicas": "Hipertensão, Diabetes Mellitus Tipo 2, Doença Arterial Coronariana",
        "Cirurgias Relevantes": "Revascularização do miocárdio (2019)",
        "Riscos Médicos": "Alto risco de sangramento (uso de anticoagulante)",
        "Alertas de Interação": "Evitar AINEs (risco de sangramento com Warfarina)",
    },
    "governance": {
        "consistency": "99.8%",
        "confidence": "Elevada",
        "sources": ["Prontuário HC-SP", "Dispensação Farmacêutica", "Resultados Laboratoriais"],
    },
}

MOCK_NOTES = []

MOCK_APPOINTMENTS = [
    {"name": "Maria Oliveira", "time": "09:00", "status": "completed", "patientId": "P002"},
    {"name": "João Pereira", "time": "09:30", "status": "completed", "patientId": "P003"},
    {"name": "Ana Costa", "time": "10:00", "status": "current", "patientId": "P004"},
    {"name": "Pedro Martins", "time": "10:30", "status": "upcoming", "patientId": "P005"},
    {"name": "José da Silva", "time": "11:00", "status": "upcoming", "patientId": "P001"},
]

# ══════════════════════════════════════════════════════════════════════
# SCHEMAS
# ══════════════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    professionalId: str
    password: str
    healthNetwork: str


class UploadResponse(BaseModel):
    success: bool
    message: str
    extractedData: dict


# ══════════════════════════════════════════════════════════════════════
# AUTH ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

@app.post("/api/auth/login")
async def login(body: LoginRequest):
    """Autenticar profissional de saúde."""
    user = next(
        (
            u for u in MOCK_USERS
            if u["professionalId"].lower() == body.professionalId.lower()
            and u["healthNetworkId"] == body.healthNetwork
        ),
        None,
    )

    if not user or user["password"] != body.password:
        raise HTTPException(
            status_code=401,
            detail="Credenciais inválidas para esta rede de saúde.",
        )

    # Simular token JWT
    fake_token = f"mock-jwt-{str(uuid.uuid4().hex)[:16]}"

    return {
        "message": "Login bem-sucedido!",
        "token": fake_token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "professionalId": user["professionalId"],
            "permissionLevel": user["permissionLevel"],
            "specialty": user["specialty"],
            "institution": user["institution"],
            "healthNetwork": user["healthNetworkId"],
        },
    }


# ══════════════════════════════════════════════════════════════════════
# PATIENT ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

@app.get("/api/patients/search")
async def search_patients(q: str = ""):
    """Buscar pacientes por CPF, RG, nome, SUS ou ID hospitalar."""
    if not q or len(q) < 2:
        return {"patients": []}

    query = q.lower().replace(".", "").replace("-", "").replace(" ", "")
    results = []
    for p in MOCK_PATIENTS:
        searchable = (
            str(p.get("name", "")).lower()
            + str(p.get("cpf", "")).replace(".", "").replace("-", "")
            + str(p.get("rg", "")).replace(".", "").replace("-", "")
            + str(p.get("sus", "")).replace(" ", "")
            + str(p.get("hospitalId", "")).lower()
        )
        if query in searchable:
            results.append(p)

    return {"patients": results}


@app.get("/api/patients/{patient_id}")
async def get_patient(patient_id: str):
    """Obter detalhes de um paciente por ID."""
    patient = next((p for p in MOCK_PATIENTS if p["id"] == patient_id), None)
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado")
    return patient


# ══════════════════════════════════════════════════════════════════════
# EMERGENCY ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

@app.get("/api/emergency/summary")
async def emergency_summary(q: str = ""):
    """Gerar resumo emergencial por CPF/RG/protocolo. Valida no banco se o paciente existe."""
    if not q:
        raise HTTPException(status_code=400, detail="Código/CPF de emergência é obrigatório")
    
    query = q.lower().replace(".", "").replace("-", "").replace(" ", "")
    patient = None
    for p in MOCK_PATIENTS:
        searchable = (
            str(p.get("cpf", "")).replace(".", "").replace("-", "")
            + str(p.get("rg", "")).replace(".", "").replace("-", "")
            + str(p.get("id", "")).lower()
        )
        if query in searchable:
            patient = p
            break
            
    if not patient:
        raise HTTPException(status_code=404, detail="Paciente não cadastrado na base de dados. Acesso bloqueado.")
        
    return {
        "patientName": patient["name"],
        "criticalInfo": {
            "Alergias Críticas": ", ".join([a["text"] for a in patient.get("alerts", []) if "Alergia" in a.get("type", "")]) or "Nenhuma conhecida",
            "Condições Crônicas": ", ".join([a["text"] for a in patient.get("alerts", []) if "Crônica" in a.get("type", "")]) or "Nenhuma relatada",
            "Resumo Geral": patient.get("summary", ""),
        },
        "governance": {
            "consistency": "99.8%",
            "confidence": "Elevada",
            "sources": ["Prontuário SI3DC", "Registro Base de Dados"],
        },
    }


# ══════════════════════════════════════════════════════════════════════
# CLINICAL/UPLOAD ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

@app.post("/api/clinical/upload")
async def upload_document(
    file: UploadFile = File(...),
    patientName: str = Form(""),
    documentType: str = Form(""),
):
    """Simular upload e processamento de documento clínico por IA."""
    file_content = await file.read()
    file_size = len(file_content)

    return {
        "success": True,
        "message": "Documento processado com sucesso pela IA.",
        "fileName": file.filename,
        "fileSize": file_size,
        "extractedData": {
            "tipo": documentType or "Laudo Médico",
            "confianca_ia": "94.7%",
            "dados_extraidos": [
                "Hemoglobina Glicada: 7.2% (levemente alterado)",
                "Colesterol LDL: 95 mg/dL (dentro da meta)",
                "Creatinina: 1.1 mg/dL (função renal preservada)",
            ],
            "status": "Prontuário atualizado automaticamente",
        },
    }


# ══════════════════════════════════════════════════════════════════════
# DASHBOARD ENDPOINTS
# ══════════════════════════════════════════════════════════════════════

@app.get("/api/dashboard/stats")
async def dashboard_stats():
    """Retornar estatísticas e agenda do dia."""
    return {
        "appointments": MOCK_APPOINTMENTS,
        "stats": {
            "totalPatientsToday": len(MOCK_APPOINTMENTS),
            "completed": sum(1 for a in MOCK_APPOINTMENTS if a["status"] == "completed"),
            "inProgress": sum(1 for a in MOCK_APPOINTMENTS if a["status"] == "current"),
            "waiting": sum(1 for a in MOCK_APPOINTMENTS if a["status"] == "upcoming"),
        },
        "systemHealth": {
            "aiStatus": "Operacional",
            "dbStatus": "Conectado",
            "lastSync": datetime.now(timezone.utc).isoformat(),
        },
    }

@app.post("/api/dashboard/appointments/next")
async def start_next_appointment():
    """Muda o próximo appointment 'upcoming' para 'current'."""
    # Primeiro verifica se não há nenhum atual, ou encerra o atual se houver?
    # O user pediu: O botão "Novo Atendimento" deve: Iniciar o atendimento do próximo paciente na lista.
    # obs: Só funcionar após o médico clicar em "Encerrar Atendimento".
    current = next((a for a in MOCK_APPOINTMENTS if a["status"] == "current"), None)
    if current:
        raise HTTPException(status_code=400, detail="Você deve encerrar o atendimento atual antes de iniciar um novo.")
        
    for a in MOCK_APPOINTMENTS:
        if a["status"] == "upcoming":
            a["status"] = "current"
            return {"success": True, "appointment": a}
            
    raise HTTPException(status_code=404, detail="Não há mais pacientes na fila.")

@app.post("/api/dashboard/appointments/end")
async def end_current_appointment():
    """Muda o appointment 'current' para 'completed'."""
    for a in MOCK_APPOINTMENTS:
        if a["status"] == "current":
            a["status"] = "completed"
            return {"success": True, "appointment": a}
            
    raise HTTPException(status_code=404, detail="Nenhum atendimento em andamento.")


# ══════════════════════════════════════════════════════════════════════
# OBSERVATIONS & NOTES
# ══════════════════════════════════════════════════════════════════════

class NoteRequest(BaseModel):
    patientName: str
    noteType: str  # 'observation' | 'reminder'
    content: str


@app.post("/api/clinical/notes")
async def save_note(body: NoteRequest):
    """Salvar observação clínica ou lembrete pessoal."""
    note = {
        "id": str(uuid.uuid4().hex)[:8],
        "patientName": body.patientName,
        "noteType": body.noteType,
        "content": body.content,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    MOCK_NOTES.append(note)
    return {
        "success": True,
        "message": f"{'Observação' if body.noteType == 'observation' else 'Lembrete'} salva com sucesso.",
        "noteId": note["id"],
        "timestamp": note["timestamp"],
    }

@app.get("/api/clinical/notes/{patient_name}")
async def get_notes(patient_name: str, type: str = None):
    """Retornar notas e observações para um paciente."""
    notes = [n for n in MOCK_NOTES if str(n.get("patientName", "")).lower() == patient_name.lower()]
    if type:
        notes = [n for n in notes if n["noteType"] == type]
    return {"notes": notes}


# ══════════════════════════════════════════════════════════════════════
# LGPD / SESSION MANAGEMENT
# ══════════════════════════════════════════════════════════════════════

class SessionRequest(BaseModel):
    patientId: str
    action: str  # 'start' | 'end'


@app.post("/api/session/access")
async def manage_access(body: SessionRequest):
    """Gerenciar acesso temporário ao prontuário (LGPD)."""
    if body.action == "start":
        return {
            "success": True,
            "message": "Acesso ao prontuário iniciado. Sessão temporária ativada.",
            "sessionId": uuid.uuid4().hex[:12],
            "expiresIn": "30 minutos",
            "auditLog": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "access_granted",
                "patientId": body.patientId,
            },
        }
    else:
        return {
            "success": True,
            "message": "Acesso ao prontuário encerrado. Sessão finalizada.",
            "auditLog": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "access_revoked",
                "patientId": body.patientId,
            },
        }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "SI3DC Mock API", "timestamp": datetime.now(timezone.utc).isoformat()}
