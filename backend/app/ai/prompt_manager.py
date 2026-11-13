class PromptManager:
    """
    Centralized system prompts and clinical instruction templates for Medicall AI.
    Enforces clinical boundary rules and structured JSON outputs across all AI workflows.
    """

    CORE_CLINICAL_SYSTEM_INSTRUCTION = (
        "You are the Medicall Clinical Assistant, an AI-powered triage and healthcare coordination support agent.\n"
        "STRICT CLINICAL RULES:\n"
        "1. You are NOT a doctor and CANNOT make formal medical diagnoses or prescribe specific medication dosages.\n"
        "2. If the user presents any life-threatening symptoms (chest pain, stroke signs, difficulty breathing), "
        "instruct them to call emergency services immediately.\n"
        "3. Your goal is to help patients understand their symptoms in simple terms, categorize urgency, "
        "and recommend the most appropriate medical specialties.\n"
        "4. Always conclude with the non-diagnostic clinical disclaimer.\n"
    )

    SYMPTOM_ASSESSMENT_PROMPT = (
        CORE_CLINICAL_SYSTEM_INSTRUCTION +
        "\nTask: Analyze the patient's reported symptoms.\n"
        "Input Details:\n"
        "- Symptoms: {symptoms}\n"
        "- Duration: {duration_days} days\n"
        "- Severity Scale (1-10): {severity_scale}\n"
        "- Patient Age: {patient_age}\n\n"
        "Provide a structured assessment identifying urgency level (ROUTINE, MODERATE, URGENT, EMERGENCY), "
        "likely relevant specialties, questions to ask their doctor, and a plain-English preliminary summary."
    )

    TRIAGE_PROMPT = (
        CORE_CLINICAL_SYSTEM_INSTRUCTION +
        "\nTask: Classify patient triage category.\n"
        "Chief Complaint: {chief_complaint}\n"
        "Determine the urgency level and clinical rationale."
    )

    DOCTOR_MATCHING_PROMPT = (
        CORE_CLINICAL_SYSTEM_INSTRUCTION +
        "\nTask: Match the patient's symptoms with the best medical specialty and available doctors.\n"
        "Patient Symptoms: {symptom_summary}\n"
        "Available Doctor Specialties: {available_specialties}\n"
        "Determine which specialty best addresses these symptoms."
    )

    REPORT_SUMMARIZATION_PROMPT = (
        CORE_CLINICAL_SYSTEM_INSTRUCTION +
        "\nTask: Summarize a medical lab or clinical report in clear, reassuring, patient-friendly terms.\n"
        "Clinical Text:\n{report_text}\n\n"
        "Explain key terms simply, highlight primary findings, and provide 3 questions the patient can ask their doctor."
    )

    @classmethod
    def format_symptom_prompt(cls, symptoms: str, duration_days: int = None, severity_scale: int = None, patient_age: int = None) -> str:
        return cls.SYMPTOM_ASSESSMENT_PROMPT.format(
            symptoms=symptoms,
            duration_days=duration_days or "Not specified",
            severity_scale=severity_scale or "Not specified",
            patient_age=patient_age or "Not specified"
        )

    @classmethod
    def format_triage_prompt(cls, chief_complaint: str) -> str:
        return cls.TRIAGE_PROMPT.format(chief_complaint=chief_complaint)

    @classmethod
    def format_matching_prompt(cls, symptom_summary: str, available_specialties: list) -> str:
        return cls.DOCTOR_MATCHING_PROMPT.format(
            symptom_summary=symptom_summary,
            available_specialties=", ".join(available_specialties) if available_specialties else "General Medicine"
        )

    @classmethod
    def format_report_prompt(cls, report_text: str) -> str:
        return cls.REPORT_SUMMARIZATION_PROMPT.format(report_text=report_text)

